# -*- coding: utf-8 -*-
##############################################################################
#
#    School App for Odoo
#    Copyright (C) 2015
#       Pere Ramon Erro Mas <pereerro@tecnoba.com> All Rights Reserved.
#
#    This file is a part of School App for Odoo
#
#    School App for Odoo is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    School App for Odoo is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import copy
from lxml import etree
from openerp.osv import orm, osv, fields
import base64
from math import floor
import collections
from openerp.tools.translate import _

def floats_to_school_fet_hour(hour_from,hour_to):
    return "%02d:%02d-%02d:%02d" % (hour_from,(hour_from-floor(hour_from))*60,hour_to,(hour_to-floor(hour_to))*60) 
    

class school_fet_export(osv.osv_memory):
    _name = 'school.fet.export'

    _columns = {
        'iwl_ids' : fields.many2many('school.impartition_week_line','school_fet_export_iwl_rel','fetex_id','iwl_id',string='IWLs',),
        'file' : fields.binary('File',),
    }

    _defaults = {
        'iwl_ids' : lambda self,cr,uid,context={} : context.get('active_ids',[])
    }

    def act_cancel(self, cr, uid, ids, context=None):
        pass

    def posa_hores(self, cr, uid, root, context=None):
        hlist=etree.SubElement(root,"Hours_List")
        fet_hour_ids=self.pool.get('school.fet.hour').search(cr, uid, [], context=context)
        if not fet_hour_ids:
            raise orm.except_orm('No Hours!','Impossible FET exportation. We need hours!')
        nhlist=etree.SubElement(hlist,"Number")
        nhlist.text=str(len(fet_hour_ids))
        for (hour_id,hour_name) in self.pool.get('school.fet.hour').name_get(cr, uid, fet_hour_ids):
            elem=etree.SubElement(hlist,"Name")
            elem.text=hour_name
        
    def posa_dies(self, cr, uid, root, context=None):
        dlist=etree.SubElement(root,"Days_List")
        fet_day_ids=self.pool.get('school.fet.day').search(cr, uid, [], context=context)
        if not fet_day_ids:
            raise orm.except_orm('No Days!','Impossible FET exportation. We need days!')
        ndlist=etree.SubElement(dlist,"Number")
        ndlist.text=str(len(fet_day_ids))
        for data in self.pool.get('school.fet.day').read(cr, uid, fet_day_ids, ['name'], context=context):
            elem=etree.SubElement(dlist,"Name")
            elem.text=data['name']

    def prepara_edificis(self, cr, uid, context=None):
        building_list=etree.Element("Buildings_List")
        ids2=self.pool.get('school.building').search(cr, uid, [], context=context)
        for item in self.pool.get('school.building').browse(cr, uid, ids2, context=context):
            subelement=etree.SubElement(building_list,"Building")
            subelement=etree.SubElement(subelement,"Name")
            subelement.text="%s,%s" % (item.id,item.name)
        return building_list
        
    def prepara_aules(self, cr, uid, context=None):
        rooms = set()
        room_list=etree.Element("Rooms_List")
        ids2=self.pool.get('school.room').search(cr, uid, [], context=context)
        for item in self.pool.get('school.room').browse(cr, uid, ids2, context=context):
            room_key="%s,%s" % (item.id,item.name)
            rooms.add(room_key)
            subelement=etree.SubElement(room_list,"Room")
            subelement2=etree.SubElement(subelement,"Name")
            subelement2.text=room_key
            if item.building_id:
                subelement2=etree.SubElement(subelement,"Building")
                subelement2.text="%s,%s" % (item.building_id.id,item.building_id.name)
            subelement2=etree.SubElement(subelement,"Capacity")
            subelement2.text=str(item.capacity)
        return rooms, room_list
        
    def prepara_etiquetes(self, cr, uid, context=None):
        tag_list=etree.Element("Activity_Tags_List")
        ids2=self.pool.get('school.fet.tag').search(cr, uid, [], context=context)
        for item in self.pool.get('school.fet.tag').browse(cr, uid, ids2, context=context):
            tag_key="%s,%s" % (item.id,item.name)
            subelement=etree.SubElement(tag_list,"Activity_Tag")
            subelement2=etree.SubElement(subelement,"Name")
            subelement2.text=tag_key
        return tag_list

    def prepara_activitats(self, cr, uid, fex, context=None):
            # contemplem només l'assignació de grups en aquest moment
            parts=set()
            groups={}
            teachers=set()
            courses=set()
            activities={}
            iwl_ids=[]
            teacher_ids=set()
            group_ids=set()
            for iwl in fex.iwl_ids:
                iwl_ids.append(iwl.id)
                tags=set()
                for tag in iwl.tag_ids:
                    tag_key="%s,%s" % (tag.id,tag.name)
                    tags.add(tag_key)
                activity={'teachers': set(),'classe_id': iwl.classe_id.id,'tags': tags}
                activity_key=str(iwl.id)
                activities[activity_key]=activity
                course_key="%s,%s" % (iwl.classe_id.course_id.id,iwl.classe_id.course_id.name)
                courses.add(course_key)
                for teacher_data in iwl.teachers:
                    teacher_key="%s,%s" % (teacher_data.teacher_id.id,teacher_data.teacher_id.name)
                    teacher_ids.add(teacher_data.teacher_id.id)
                    teachers.add(teacher_key)
                    activity['teachers'].add(teacher_key)
                activity['course']=course_key
                if iwl.group_id:
                    group_ids.add(iwl.group_id.id)
                    group_key="%s,%s" % (iwl.group_id.id,iwl.group_id.name)
                    activity['group']=group_key
                    if group_key not in groups:
                        groups[group_key]=set()
                        query="SELECT ga.participation_id FROM groups_group_assignation AS ga WHERE ga.group_id=%s AND now() BETWEEN ga.datetime_from AND ga.datetime_to"
                        cr.execute(query,(iwl.group_id.id,))
                        for (part_id,) in cr.fetchall():
                            parts.add(part_id)
                            groups[group_key].add(part_id)
            return parts, groups, teachers, courses, activities, iwl_ids, teacher_ids, group_ids

    def posa_estudiants(self, cr, uid, root, parts, groups, context=None):
        slist=etree.SubElement(root,"Students_List")
        year=etree.SubElement(slist,"Year")
        year_name=etree.SubElement(year,"Name")
        year_name.text="now"
        year_nos=etree.SubElement(year,"Number_of_Students")
        year_nos.text=str(len(parts))
        for (group_key,student_set) in groups.items():
            group=etree.SubElement(year,"Group")
            group_name=etree.SubElement(group,"Name")
            group_name.text=group_key
            group_nos=etree.SubElement(group,"Number_of_Students")
            group_nos.text=str(len(student_set))
            for student in student_set:
                subgroup=etree.SubElement(group,"Subgroup")
                subgroup_name=etree.SubElement(subgroup,"Name")
                subgroup_name.text=str(student)
                subgroup_nos=etree.SubElement(subgroup,"Number_of_Students")
                subgroup_nos.text="1"
        
    def posa_professors(self, cr, uid, root, teachers, context=None):
        tlist=etree.SubElement(root,"Teachers_List")
        for teacher_key in teachers:
            subelement=etree.SubElement(tlist,"Teacher")
            subelement2=etree.SubElement(subelement,"Name")
            subelement2.text=teacher_key
        
    def posa_materies(self, cr, uid, root, courses, context=None):
            su_list=etree.SubElement(root,"Subjects_List")
            for course_key in courses:
                subelement=etree.SubElement(su_list,"Subject")
                subelement2=etree.SubElement(subelement,"Name")
                subelement2.text=course_key
    def posa_activitats(self, cr, uid, root, activities, context=None):
        a_list=etree.SubElement(root,"Activities_List")
        for (activity_key,activity) in activities.items():
            subelement=etree.SubElement(a_list,"Activity")
            for teacher_key in activity['teachers']:
                subelement2=etree.SubElement(subelement,"Teacher")
                subelement2.text=teacher_key
            subelement2=etree.SubElement(subelement,"Subject")
            subelement2.text=activity['course']
            for tag_key in activity['tags']:
                subelement2=etree.SubElement(subelement,"Activity_Tag")
                subelement2.text=tag_key
            subelement2=etree.SubElement(subelement,"Duration")
            subelement2.text="1"
            subelement2=etree.SubElement(subelement,"Id")
            subelement2.text=activity_key
            subelement2=etree.SubElement(subelement,"Activity_Group_Id")
            subelement2.text=str(activity['classe_id'])
            subelement2=etree.SubElement(subelement,"Active")
            subelement2.text="true"
            if 'group' in activity:
                subelement2=etree.SubElement(subelement,"Students")
                subelement2.text=activity['group']

    def posa_hores_no_disp_de_profe(self, cr, uid, root, iwl_ids, teacher_ids, context=None):
        query="""
        SELECT td.teacher_id,iwl.week_day,sfh.hour_from,sfh.hour_to
        FROM school_impartition_week_line AS iwl
            INNER JOIN school_teacher_data AS td ON iwl.id=td.iwl_id
            INNER JOIN school_fet_hour AS sfh ON iwl.hour_from<sfh.hour_to AND iwl.hour_from+iwl.duration>sfh.hour_from
        WHERE iwl.week_day IS NOT NULL AND iwl.hour_from IS NOT NULL AND iwl.duration IS NOT NULL
            AND iwl.id NOT IN %s AND td.teacher_id IN %s
        ORDER BY td.teacher_id
        """
        cr.execute(query, (tuple(iwl_ids),tuple(teacher_ids),) )
        teacher_data = collections.defaultdict(set)
        for (teacher_id,week_day,hour_from,hour_to) in cr.fetchall():
            week_day_name=None
            for (day_code,day_name) in [('1','monday'),('2','tuesday'),('3','wednesday'),('4','thursday'),('5','friday'),('6','saturday'),('7','sunday')]:
                if day_code==week_day:
                    week_day_name=day_name
            teacher_data[teacher_id].add( (week_day_name,hour_from,hour_to) )
        for item in self.pool.get('school.teacher').browse(cr, uid, teacher_data.keys(), context=context):
            ctnat=etree.SubElement(root, "ConstraintTeacherNotAvailableTimes")
            subelement=etree.SubElement(ctnat,"Weight_Percentage")
            subelement.text="100"
            teacher_key="%s,%s" % (item.id,item.name)
            subelement=etree.SubElement(ctnat,"Teacher")
            subelement.text=teacher_key
            subelement=etree.SubElement(ctnat,"Number_of_Not_Available_Times")
            subelement.text=str(len(teacher_data[item.id]))
            for (week_day,hour_from,hour_to) in teacher_data[item.id]:
                subelement=etree.SubElement(ctnat,"Not_Available_Time")
                subelement2=etree.SubElement(subelement,"Day")
                subelement2.text=week_day
                subelement2=etree.SubElement(subelement,"Hour")
                subelement2.text=floats_to_school_fet_hour(hour_from,hour_to)

    def posa_hores_no_disp_de_grup(self, cr, uid, root, iwl_ids, group_ids, context=None):
        query="""
        SELECT COALESCE(iwl.subgroup,cl.group_id),iwl.week_day,sfh.hour_from,sfh.hour_to
        FROM school_impartition_week_line AS iwl
            INNER JOIN school_classe AS cl ON iwl.classe_id=cl.id
            INNER JOIN school_fet_hour AS sfh ON iwl.hour_from<sfh.hour_to AND iwl.hour_from+iwl.duration>sfh.hour_from
        WHERE iwl.week_day IS NOT NULL AND iwl.hour_from IS NOT NULL AND iwl.duration IS NOT NULL
            AND iwl.id NOT IN %s AND COALESCE(iwl.subgroup,cl.group_id) IN %s
        ORDER BY COALESCE(iwl.subgroup,cl.group_id)
        """
        cr.execute(query, (tuple(iwl_ids),tuple(group_ids),) )
        group_data = collections.defaultdict(set)
        for (group_id,week_day,hour_from,hour_to) in cr.fetchall():
            week_day_name = None
            for (day_code,day_name) in [('1','monday'),('2','tuesday'),('3','wednesday'),('4','thursday'),('5','friday'),('6','saturday'),('7','sunday')]:
                if day_code == week_day:
                    week_day_name = day_name
            group_data[group_id].add( (week_day_name,hour_from,hour_to) )
        for item in self.pool.get('groups.group').browse(cr, uid, group_data.keys(), context=context):
            cgnat=etree.SubElement(tc_list,"ConstraintStudentsSetNotAvailableTimes")
            subelement=etree.SubElement(cgnat,"Weight_Percentage")
            subelement.text="100"
            students_key="%s,%s" % (item.id,item.name)
            subelement=etree.SubElement(cgnat,"Students")
            subelement.text=students_key
            subelement=etree.SubElement(cgnat,"Number_of_Not_Available_Times")
            subelement.text=str(len(group_data[item.id]))
            for (week_day,hour_from,hour_to) in group_data[item.id]:
                subelement=etree.SubElement(cgnat,"Not_Available_Time")
                subelement2=etree.SubElement(subelement,"Day")
                subelement2.text=week_day
                subelement2=etree.SubElement(subelement,"Hour")
                subelement2.text=floats_to_school_fet_hour(hour_from,hour_to)
        
    def posa_pref_aules_propies(self, cr, uid, root, rooms, groups, context=None):
        for group_key in groups.keys():
            csshr=etree.SubElement(root,"ConstraintStudentsSetHomeRooms")
            subelement=etree.SubElement(csshr,"Weight_Percentage")
            subelement.text="10"
            subelement=etree.SubElement(csshr,"Students")
            subelement.text=group_key
            subelement=etree.SubElement(csshr,"Number_of_Preferred_Rooms")
            subelement.text=str(len(rooms))
            for room_key in rooms:
                subelement=etree.SubElement(csshr,"Preferred_Room")
                subelement.text=room_key
        
    def posa_hores_no_disp_d_aula(self, cr, uid, root, iwl_ids, context=None):
        # Not available room hours
        query="""
        SELECT iwl.room_id,iwl.week_day,sfh.hour_from,sfh.hour_to
        FROM school_impartition_week_line AS iwl
            INNER JOIN school_fet_hour AS sfh ON iwl.hour_from<sfh.hour_to AND iwl.hour_from+iwl.duration>sfh.hour_from
        WHERE iwl.room_id IS NOT NULL AND iwl.week_day IS NOT NULL AND iwl.hour_from IS NOT NULL AND iwl.duration IS NOT NULL
            AND iwl.id NOT IN %s
        ORDER BY iwl.room_id
        """
        cr.execute(query, (tuple([0,0]+iwl_ids),) )
        room_data = collections.defaultdict(set)
        for (room_id,week_day,hour_from,hour_to) in cr.fetchall():
            week_day_name=None
            for (day_code,day_name) in [('1','monday'),('2','tuesday'),('3','wednesday'),('4','thursday'),('5','friday'),('6','saturday'),('7','sunday')]:
                if day_code == week_day:
                    week_day_name=day_name
            room_data[room_id].add( (week_day_name,hour_from,hour_to) )
        for item in self.pool.get('school.room').browse(cr, uid, room_data.keys(), context=context):
            crnat=etree.SubElement(sc_list,"ConstraintRoomNotAvailableTimes")
            subelement=etree.SubElement(crnat,"Weight_Percentage")
            subelement.text="100"
            room_key="%s,%s" % (item.id,item.name)
            subelement=etree.SubElement(crnat,"Room")
            subelement.text=room_key
            subelement=etree.SubElement(crnat,"Number_of_Not_Available_Times")
            subelement.text=str(len(room_data[item.id]))
            for (week_day,hour_from,hour_to) in room_data[item.id]:
                subelement=etree.SubElement(crnat,"Not_Available_Time")
                subelement2=etree.SubElement(subelement,"Day")
                subelement2.text=week_day
                subelement2=etree.SubElement(subelement,"Hour")
                subelement2.text=floats_to_school_fet_hour(hour_from,hour_to)
        
    def generate_file(self, cr, uid, ids, context=None):
        root=etree.Element('fet')
        root.set("version","5.13.4")
        iname=etree.SubElement(root,"Institution_Name")
        iname.text="A Institution Name"
        iname=etree.SubElement(root,"Comments")
        iname.text="Comentaris predeterminats"

        self.posa_hores(cr, uid, root, context=context)
        self.posa_dies(cr, uid, root, context=context)
        building_list = self.prepara_edificis(cr, uid, context=context)
        rooms, room_list = self.prepara_aules(cr, uid, context=context)
        tag_list = self.prepara_etiquetes(cr, uid, context=context)

        for fex in self.browse(cr, uid, ids, context=context):
            root2 = copy.deepcopy( root )
            
            (parts, groups, teachers, courses, activities, iwl_ids,
            teacher_ids, group_ids) = self.prepara_activitats(
                                        cr, uid, fex, context=context)

            self.posa_estudiants(cr, uid, root2, parts, groups, context=context)
            self.posa_professors(cr, uid, root2, teachers, context=context)
            self.posa_materies(cr, uid, root2, courses, context=context)
            
            root2.append( copy.deepcopy(tag_list) )

            self.posa_activitats(cr, uid, root2, activities, context=context)
            
            root2.append( copy.deepcopy(building_list) )
            root2.append( copy.deepcopy(room_list) )

            tc_list=etree.SubElement(root2,"Time_Constraints_List")
            cbct=etree.SubElement(tc_list,"ConstraintBasicCompulsoryTime")
            wp=etree.SubElement(cbct,"Weight_Percentage")
            wp.text="100"

            if teacher_ids:
                self.posa_hores_no_disp_de_profe(cr, uid, tc_list, iwl_ids, teacher_ids, context=context)
            if group_ids:
                self.posa_hores_no_disp_de_grup(cr, uid, tc_list, iwl_ids, group_ids, context=context)
                
            # All activities with rooms
            sc_list=etree.SubElement(root2,"Space_Constraints_List")
            cbcs=etree.SubElement(sc_list,"ConstraintBasicCompulsorySpace")
            wp=etree.SubElement(cbcs,"Weight_Percentage")
            wp.text="100"
            
            if rooms:
                self.posa_pref_aules_propies(cr, uid, sc_list, rooms, groups, context=context)
            self.posa_hores_no_disp_d_aula(cr, uid, sc_list, iwl_ids, context=context)
             
            self.write(cr, uid, [fex.id], {'file': base64.encodestring(etree.tostring(root2)) })

        return {
                'name': _('Download file'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'school.fet.export',
                'res_id' : ids[0],
                'view_id': False,
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context' : context,
                }

    
school_fet_export()

class school_fet_import(osv.osv_memory):
    _name = 'school.fet.import'

    _columns = {
        'file' : fields.binary('File',),
    }

    def act_cancel(self, cr, uid, ids, context=None):
        pass

    def import_file(self, cr, uid, ids, context=None):
        for fex in self.browse(cr, uid, ids, context=context):
            root=etree.fromstring(base64.decodestring(fex.file))
            iwl_data={}
            for data in root.findall('Time_Constraints_List/ConstraintActivityPreferredStartingTime'):
                iwl_id=int(data.find('Activity_Id').text)
                dia=data.find('Preferred_Day').text
                hora=data.find('Preferred_Hour').text
                week_day=False
                for (week_day_candidate,week_day_name) in [('1','monday'),('2','tuesday'),('3','wednesday'),('4','thursday'),('5','friday'),('6','saturday'),('7','sunday')]:
                    if week_day_name==dia: week_day=week_day_candidate

                hours=hora.split('-')
                if week_day and len(hours)>1:
                    (hour,minute)=hours[0].split(':')
                    hour_ids=self.pool.get('school.fet.hour').search(cr, uid, [('hour_from','=',str(float(hour)+float(minute)/60))])
                    for hour_data in self.pool.get('school.fet.hour').browse(cr, uid, hour_ids):
                        iwl_data[iwl_id]={'week_day': week_day, 'hour_from': hour_data.hour_from, }

            for data in root.findall('Space_Constraints_List/ConstraintActivityPreferredRoom'):
                iwl_id=int(data.find('Activity_Id').text)
                room=data.find('Room').text
                room_parts=room.split(',',1)
                if len(room_parts)==2:
                    iwl_data[iwl_id]['room_id']=int(room_parts[0])

            for iwl_id in iwl_data.keys():
                self.pool.get('school.impartition_week_line').write(cr, uid, [iwl_id], iwl_data[iwl_id])

school_fet_import()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
