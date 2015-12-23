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

from openerp.osv import osv, fields, orm
from datetime import datetime, date, timedelta
from openerp.tools.translate import _

class school_building(osv.osv):
    _name = 'school.building'
school_building()

class school_room(osv.osv):
    _name = 'school.room'
    _columns = {
        'name' : fields.char('Name', size=32, required=True, select=1, help="The room name"),
        'seance_ids' : fields.one2many('school.seance','room_id','Seances',select=1),
        'capacity' : fields.integer('Capacity',),
        'building_id' : fields.many2one('school.building',string='Building',ondelete='set null',),
    }
    _defaults = {
        'capacity' : lambda *a : 50,
    }
    _order = 'name'
school_room()

class school_building(osv.osv):
    _name = 'school.building'
    _columns = {
        'name' : fields.char('Name', size=32, required=True, select=1, help="The building name"),
        'rooms' : fields.one2many('school.room','building_id',string='Rooms',),
    }
    _order = 'name'
school_building()

class school_classe(osv.osv):
    _name = 'school.classe'
school_classe()

class school_teacher_classe(osv.osv):
    _name = 'school.teacher_classe'

    _columns = {
        'classe_id' : fields.many2one('school.classe','Classe',ondelete='cascade',required=True,),
        'teacher_id' : fields.many2one('school.teacher','Teacher',ondelete='cascade',required=True,),
        'sequence' : fields.integer('Sequence',),
    }
    
    _sql_constraints = [('teacher_classe_unique','UNIQUE (teacher_id,classe_id)','A teacher entry must be unique!'),]

school_teacher_classe()

class school_classe(osv.osv):
    _name = 'school.classe'
    
    _columns = {
        'name' : fields.char('Name',size=200,select=1,help="The class name",),
        'course_id' : fields.many2one('school.course','Course',required=True,readonly=False,help="The course",ondelete='cascade'),
        'seance_ids' : fields.one2many('school.seance','classe_id',string='Seances',help='List of the seances for a class.',),
        'date_from': fields.date('Date From',required=True,),
        'date_to': fields.date('Date To',required=True,),
        'group_id': fields.many2one('groups.group','Group',select=1,help='A group linked',readonly=False,ondelete='restrict',),
        'holidays_calendar_id' : fields.many2one('school.holidays_calendar',string="Holidays Calendar",ondelete="set null",),
        'teachers' : fields.one2many('school.teacher_classe','classe_id',string='Teachers in Seances',help="Teachers in seances", readonly=True,),
    }

    _order = 'name'
    
    _sql_constraints = [('wrong_dates','CHECK (date_from < date_to)','Wrong Dates'),]
            
school_classe()

class school_seance(osv.osv):
    _name = 'school.seance'
school_seance()

class school_teacher_seance(osv.osv):
    _name = 'school.teacher_seance'
    _columns = {
        'teacher_id' : fields.many2one('school.teacher', 'Teacher', required=True, select=1, ),
        'seance_id' : fields.many2one('school.seance','Seance', required=True, select=1, ondelete='cascade' ),
        'title' : fields.selection([('imperative','Imperative'),('needed','Needed'),('optional','Optional'),('advisable','Advisable')], 'Title', ),
    }

    _sql_constraints = [('teacher_seance_unique','UNIQUE (teacher_id,seance_id)','A teacher entry must be unique!'),]

    def name_get(self, cr, uid, ids, context=None):
        pre_ret=[]
        seance_name_by_id={}
        teacher_name_by_id={}
        for item in self.browse(cr, uid, ids, context=context):
            seance_name_by_id[item.seance_id.id]=""
            teacher_name_by_id[item.teacher_id.id]=""
            pre_ret.append( (item.id,item.seance_id.id,item.teacher_id.id) )
        for (id,name) in self.pool.get('school.seance').name_get(cr, uid, seance_name_by_id.keys(), context=context):
            seance_name_by_id[id]=name
        for (id,name) in self.pool.get('school.teacher').name_get(cr, uid, teacher_name_by_id.keys(), context=context):
            teacher_name_by_id[id]=name
        return [(id,"%s - %s" % (teacher_name_by_id[teacher_id],seance_name_by_id[seance_id])) for (id,seance_id,teacher_id) in pre_ret]
    
    def teacher_classe_keys(self, cr, uid, ts_ids, context=None):
        ret = set()
        for ts in self.browse(cr, uid, ts_ids):
            ret.add((ts.teacher_id.id,ts.seance_id.classe_id.id))
        return ret

    def sincronize_teacher_classes(self, cr, uid, tck_before, tck_after):
        tc_obj = self.pool.get('school.teacher_classe')
        for (t_id, c_id) in list(tck_after - tck_before):
            crit = [('teacher_id','=',t_id),('classe_id','=',c_id)]
            if not tc_obj.search(cr, uid, crit):
                tc_obj.create(cr, uid, {'teacher_id': t_id, 'classe_id': c_id})
        for (t_id, c_id) in list(tck_before - tck_after):
            if not self.search(cr, uid, [('teacher_id','=',t_id),('seance_id.classe_id','=',c_id)]):
                tc_obj.unlink(cr, uid, tc_obj.search(cr, uid, crit))
                
    def create(self, cr, uid, vals, context=None):
        ret = super(school_teacher_seance, self).create(cr, uid, vals, context=context)
        tck_a = self.teacher_classe_keys(cr, uid, [ret])
        self.sincronize_teacher_classes(cr, uid, set(), tck_a)
        return ret
        
    def write(self, cr, uid, ids, vals, context=None):
        tck_b = self.teacher_classe_keys(cr, uid, ids)
        ret = super(school_teacher_seance, self).write(cr, uid, ids, vals, context=context)
        tck_a = self.teacher_classe_keys(cr, uid, ids)
        self.sincronize_teacher_classes(cr, uid, tck_b, tck_a)
        return ret
    
    def unlink(self, cr, uid, ids, context=None):
        tck_b = self.teacher_classe_keys(cr, uid, ids)
        ret = super(school_teacher_seance, self).unlink(cr, uid, ids, context=context)
        self.sincronize_teacher_classes(cr, uid, tck_b, set())
        return ret
        
school_teacher_seance()

class school_teacher(osv.osv):
    _name = 'school.teacher'
    _inherit = 'school.teacher'
    
    _columns = {
        'teacher_seance_ids' : fields.one2many('school.teacher_seance','teacher_id',string='Seances',),
    }

school_teacher()

class school_seance(osv.osv):
    _name = 'school.seance'

    def name_get(self, cr, uid, ids, context=None):
        ret=[]
        for seance in self.browse(cr, uid, ids):
            ret.append((seance.id,"%(classe_name)s-%(date)s-%(room_name)s" % {
                'classe_name':seance.classe_id.name,
                'date': seance.date,
                'room_name': seance.room_id.name,
                }))
        return ret

    def _main_teacher(self, cr, uid, ids, field_name, arg, context=None):
        ret={}
        priority=dict([('imperative',0),('needed',1),('optional',2),('advisable',3)])
        for seance in self.browse(cr, uid, ids, context):
            ret[seance.id]=None
            priority_act=-1
            for teacher_data in seance.teachers:
                if priority_act<0 or priority[teacher_data.title]<priority_act:
                    ret[seance.id]=teacher_data.teacher_id.id
        return ret

    _columns = {
        'room_id' : fields.many2one('school.room','Room', required=False, select=1, help="The seance's room"),
        'classe_id' : fields.many2one('school.classe', 'Class', required=True, help="The class", ondelete="cascade", readonly=True, select=1),
        'date' : fields.datetime('Date', required=True, select=1),
        'date_to' : fields.datetime('Date to', required=True, select=1,),
        'teachers' : fields.one2many('school.teacher_seance','seance_id',),
        'group_id' : fields.many2one('groups.group', string='Group', required=True, ondelete='restrict',),
        'course_id': fields.related('classe_id','course_id',type='many2one',relation='school.course',string='Course'),
        'teacher_id': fields.function(_main_teacher,type='many2one',obj='school.teacher',method=True,string="Main teacher",),
    }

    _order = 'date desc'

    def _group_son_of_classe_group(self, cr, uid, ids, context=None):
        ret = True
        for item in self.browse(cr, uid, ids, context=context):
            if not item.classe_id.group_id or not item.group_id:
                continue
            g_obj = self.pool.get('groups.group')
            subgs = g_obj._get_group_ids_and_our_children(
                        cr, uid, [item.classe_id.group_id.id], context=context)
            if item.group_id.id not in subgs:
                ret |= True
        return ret

    _constraints = [(_group_son_of_classe_group, 'The group must be subgroup of the classe group', ['group_id','classe_id'])]
    
    def on_change_classe(self, cr, uid, ids, classe_id, group_id, context=None):
        if not classe_id:
            ret = {'value': {'group_id': False,}, 'domain': {'group_id': False,}}
        else:
            c_obj = self.pool.get('school.classe')
            classe = c_obj.browse(cr, uid, classe_id, context=context)
            if classe.group_id:
                g_obj = self.pool.get('groups.group')
                g_ids = g_obj._get_group_ids_and_our_children(
                        cr, uid, [classe.group_id.id], context=context)
                ret = {'domain': {'group_id': [('id','in',g_ids)]}}
                if subgroup not in ret['domain']['group_id']:
                    ret.update({'value': {'group_id': False,},})
        return ret
    
    def create(self, cr, uid, vals, context=None):
        if 'group_id' not in vals or not vals['group_id']:
            classe = self.pool.get('school.classe').browse(cr, uid, vals['classe_id'])
            vals['group_id'] = classe.group_id.id
        ret = super(school_seance, self).create(cr, uid, vals, context=context)
        return ret

school_seance()

class school_course(osv.osv):
    _name = "school.course"
    _inherit = "school.course"
    
    _columns = {
        'classe_ids': fields.one2many('school.classe','course_id', string='Classes'),
    }
    
school_course()

class school_holidays_calendar(osv.osv):
    _name = 'school.holidays_calendar'
    _inherit = 'school.holidays_calendar'
    _columns = {
        'classe_ids' : fields.one2many('school.classe','holidays_calendar_id',string="Classes"),
    }

school_holidays_calendar()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
