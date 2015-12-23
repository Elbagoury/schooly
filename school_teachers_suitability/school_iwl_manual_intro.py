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

from openerp.osv import osv, fields
from datetime import datetime, timedelta, time
import sys,os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir,"timed_groups")))
from timed_groups import _MAX_DATETIME, _MIN_DATETIME
import math
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir,"school_iwl")))
import util_periodicity
from openerp.tools.translate import _
from collections import defaultdict

class school_iwl_def_hours(osv.osv):
    _name = 'school.iwl.def_hours'
school_iwl_def_hours()

def float2time(float_hour):
    return time(hour=int(float_hour),minute=int( (float_hour - math.floor(float_hour)) * 60))

def next_week_day(date, week_day, before = False):
    """
    Retorna la seguent data a partir de la donada amb el dia de la setmana que s'apunta.
    Parametres:
        date : dia a partir del qual es cercara la data demanada
        week_day : dia de la setmana (0 dilluns fins a 6 diumenge)
    """
    days = week_day - date.weekday()
    if days < 0 and not before:
        days = 7 - days
    if days > 0 and before:
        days = days - 7
    return date + timedelta(days = days)

def periodicitat_coincident(tupla1, tupla2):
    """
    Retorna cert si les periodicitats coincideixen en algun dia
    Entrada: dues definicions de dies de la setmana entre dues dates i fent salts de setmana
    Les definicions son tuples: data inicial, data final i salt de setmanes.
    IMPORTANT: S'enten que les dues dates inicials tenen el mateix dia de la setmana i hora
    """
    (ldate_from, ldate_to, weeks_to_pass) = tupla1
    (ldate_from2, ldate_to2, weeks_to_pass2) = tupla2
    
    ldate_from_max = max(ldate_from2, ldate_from)
    ldate_from_min = min(ldate_from2, ldate_from)
    ldate_to_min = min(ldate_to2, ldate_to)
    weeks_delay = (ldate_from_max - ldate_from_min).days / 7
    weeks_between = (ldate_to_min - ldate_from_max).days / 7
    def mcd(a,b): # maxim comu divisor
        while a != 0: a ,b = b % a, a
        return b
    def mcm(a,b):
        return a * b / mcd(a,b)
    lmcm = mcm(weeks_to_pass + 1, weeks_to_pass2 + 1)
    if weeks_between > lmcm - weeks_delay:
        return True
    return False

_week_day_selection = util_periodicity.week_day_selection

class school_iwl_def_hour(osv.osv):
    _name = 'school.iwl.def_hour'
    
    _columns = {
        'def_hours_id' : fields.many2one('school.iwl.def_hours','Def hours',ondelete = 'cascade',),
        'week_day' : fields.selection(_week_day_selection, string = 'Week day',),
        'hour_from' : fields.float('Hour from',),
        'hour_to' : fields.float('Hour to',),
    }

    def name_get(self, cr, uid, ids, context = None):
        ret = []
        for item in self.read(cr, uid, ids, ['hour_from', 'hour_to', 'week_day'], context = context):
            ret.append( (item['id'], "%s,%s-%s" % (
                                        [x for x in _week_day_selection if x[0]==item['week_day']][0][1],
                                        float2time(item['hour_from']).strftime('%H:%M'),
                                        float2time(item['hour_to']).strftime('%H:%M'),
                                                ) ) )
        return ret

    def name_search(self, cr, uid, name='',args=None, operator='ilike',context=None, limit=80):
        args2 = list(args)
        num = ''
        char = ''
        week_day_by_char = {'l': '1', 'm': '2', 'x': '3', 'j': '4', 'v': '5', 's': '6', 'd': '7',}
        for c in name:
            if c.isdigit():
                num += c
            else:
                char = c
        if num:
            args2 += [('hour_from','>=',int(num)),('hour_from','<',int(num)+1)]
        if char in week_day_by_char:
            args2 += [('week_day','=',week_day_by_char[char])]
        ids = self.search(cr, uid, args2)
        return self.name_get(cr, uid, ids, context = context)
    
school_iwl_def_hour()

    
class school_iwl_def_hours(osv.osv):
    _name = 'school.iwl.def_hours'
    
    _columns = {
        'name' : fields.char('Name', help = "Hours definition name", size = 30, required = True,),
        'hours' : fields.one2many('school.iwl.def_hour','def_hours_id',string = 'Hours',),
    }
school_iwl_def_hours()

def is_domain(field_name):
    return len(field_name)>len('_domain') and field_name[-len('_domain'):]=='_domain'

class school_iwl_manual_intro_wizard(osv.osv_memory):
    _name = 'school.iwl.manual_intro_wizard'
    wizard_datas = defaultdict(dict)
    
    def get_id_from_xmlid(self, cr, uid, model, xml_id, context=None):
        imd_obj=self.pool.get('ir.model.data')
        id=False
        ir_model_data_ids=imd_obj.search(cr, uid, [('model','=',model),('name','=',xml_id)])
        if ir_model_data_ids:
            for data in imd_obj.read(cr, uid, ir_model_data_ids, ['res_id']):
                if not self.pool.get(model).search(cr, uid, [('id','=',data['res_id'])]):
                    imd_obj.unlink(cr, uid, [data['id']])
                else:
                    id=data['res_id']
        return id
        
    def create_wizard(self, cr, uid, ids, context = None):
        return {
                'name': _('IWL Manual Intro Wizard'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'school.iwl.manual_intro_wizard',
                'res_id' : ids[0],
                'views' : [(self.get_id_from_xmlid(cr, uid, 'ir.ui.view', 'school_iwl_manual_intro_form_view1', context=context),'form')],
                'view_id': False,
                'type': 'ir.actions.act_window',
                'context' : context,
        }

    def _get_parent_ids(self, cr, uid, group_id):
        group = self.pool.get('groups.group').browse(cr, uid, group_id)
        parent_ids = set([group.id])
        def recursiu(parents, parent_ids):
            if not parents: return
            for parent in parents:
                new_parent = parent.parent_id
                if new_parent.id not in parent_ids:
                    parent_ids.add(new_parent.id)
                    recursiu(new_parent.parent_ids, parent_ids)
        recursiu(group.parent_ids, parent_ids)
        return list(parent_ids)
    
    domain_fields = ['teacher_domain', 'hour_domain', 'course_domain', 'group_domain', 'room_domain', 'classe_domain', 'iwl_domain']                    

    def _get_groups_to_complete_course(self, cr, uid, course_id, date_from, date_to, context = None):
        ret = []
        # Tots els grups excepte aquells quines totes les participacions ja tenen complertes les hores minimes segons la seva oferta
        # Primer busquem les sessions amb participacions que poden estar en aquests grups
        session_ids = self.pool.get('school.session').search(cr, uid, [('date_to','>',date_from),('date_from','<',date_to),('offer.courses_lines.course_id','=',course_id)])
        part_ids = self.pool.get('groups.participation').search(cr, uid, [('session_id','in',session_ids)])
        pcd_ids = self.pool.get('school.participation_course_data').search(cr, uid, [('course_id','=',course_id),('participation_id','in',part_ids)])
        part_ids_ko = set(part_ids)
        for item2 in self.pool.get('school.participation_course_data').browse(cr, uid, pcd_ids) :
            if item2.scheduled >= item2.course_id.min_hours and item2.participation_id.id in part_ids_ko:
                part_ids_ko.remove(item2.participation_id.id)
        ga_ids = self.pool.get('groups.group_assignation').search(cr, uid, [('participation_id','in',list(part_ids_ko)),('limit_from','<',date_to),('limit_to','>',date_from)])
        for ga in self.pool.get('groups.group_assignation').browse(cr, uid, ga_ids):
            ret.append(ga.group_id.id)
        return ret
    
    def _get_teacher_no_max_hours(self, cr, uid, date_from, date_to, context = None):
        if not context: context = {}
        context2 = dict(context)
        context2.update({'date_from': date_from, 'date_to': date_to,})
        ret = []
        for item in self.pool.get('school.teacher').browse(cr, uid, self.pool.get('school.teacher').search(cr, uid, []), context2):
            if item.max_assigned_hours < item.max_week_hours:
                ret.append(item.id)
        return ret

    def get_hour_dict(self, cr, uid, def_hour_ids, context = None):
        dh_obj = self.pool.get('school.iwl.def_hour')
        return dict( (x.id, {'free': True,
                             'week_day': x.week_day,
                             'hour_from': x.hour_from,
                             'hour_to': x.hour_to,} ) for x in dh_obj.browse(cr, uid, def_hour_ids) )                
                        
    def hours_from_teacher(self, cr, uid, def_hour_ids, values, context = None):

        if filter(lambda x: not values[x],['teacher_id','date_from','date_to']): return def_hour_ids
        (teacher_id, date_from, date_to, weeks_to_pass, week_to_init) = map(lambda x: values.get(x,0), ['teacher_id','date_from','date_to','weeks_to_pass','week_to_init'])
        ldate_from = datetime.strptime(date_from, '%Y-%m-%d') + timedelta(days = 7 * week_to_init)
        ldate_to = datetime.strptime(date_to, '%Y-%m-%d')
        hour_dict = self.get_hour_dict(cr, uid, def_hour_ids, context = context)
        td_ids = self.pool.get('school.teacher_data').search(cr, uid, [('teacher_id','=',teacher_id),('limit_from','<',date_to),('limit_to','>',date_from)])
        for item in self.pool.get('school.teacher_data').browse(cr, uid, td_ids, context = context):
            week_day = int(item.iwl_id.week_day) - 1
            
            # Correction for the periodicity of teacher service
            ldate_iwl_from = next_week_day(datetime.strptime(item.iwl_id.limit_from, '%Y-%m-%d') + timedelta(days = 7 * item.iwl_id.week_to_init), week_day)
            ldate_td_from = next_week_day(datetime.strptime(item.limit_from, '%Y-%m-%d %H:%M:%S'), week_day)
            ldate_td_to = next_week_day(datetime.strptime(item.limit_to, '%Y-%m-%d %H:%M:%S'), week_day, before = True)
            if ldate_td_from > ldate_iwl_from:
                # Updating the date begining to sincronize with iwl periodicity
                nweeks =  int( (ldate_td_from - ldate_iwl_from).days / 7 )
                mod_weeks = item.iwl_id.weeks_to_pass + 1
                ldate_td_from += timedelta(days = 7 * ( mod_weeks - nweeks % mod_weeks ) )
            else:
                ldate_td_from = ldate_iwl_from
            
            # Checking hours dictionary for mark coincidences 
            if ldate_td_from > ldate_td_to: continue
            for dicci in hour_dict.values():
                if item.iwl_id.week_day == dicci['week_day'] and item.iwl_id.hour_from < dicci['hour_to'] and item.iwl_id.hour_from + item.iwl_id.duration > dicci['hour_from']:
                    ldate_from2 = next_week_day(ldate_from, week_day)
                    ldate_to2 = next_week_day(ldate_to, week_day, before = True)
                    if ldate_from2 > ldate_to2: continue
                    if periodicitat_coincident( (ldate_from2, ldate_to2, weeks_to_pass), (ldate_td_from, ldate_td_to, item.iwl_id.weeks_to_pass)):
                        dicci['free'] = False
                        
        return [hour_id for hour_id,dicci in hour_dict.items() if dicci['free']]
        
    def update_hour_dict_from_iwls(self, cr, uid, hour_dict, iwl_ids, date_from, date_to, weeks_to_pass, week_to_init, context = None):
        ldate_from = datetime.strptime(date_from, '%Y-%m-%d') + timedelta(days = 7 * week_to_init)
        ldate_to = datetime.strptime(date_to, '%Y-%m-%d')
        for item in self.pool.get('school.impartition_week_line').browse(cr, uid, iwl_ids, context = context):
            week_day = int(item.week_day) - 1
            ldate_iwl_from = next_week_day(datetime.strptime(item.limit_from, '%Y-%m-%d') + timedelta(days = 7 * item.week_to_init), week_day)
            ldate_iwl_to = next_week_day(datetime.strptime(item.limit_to, '%Y-%m-%d'), week_day, before = True)
            if ldate_iwl_from > ldate_iwl_to:
                continue
            for hour_id,dicci in hour_dict.items():
                if item.week_day == dicci['week_day'] and item.hour_from < dicci['hour_to'] and item.hour_from + item.duration > dicci['hour_from']:
                    ldate_from2 = next_week_day(ldate_from, week_day)
                    ldate_to2 = next_week_day(ldate_to, week_day, before = True)
                    if ldate_from2 > ldate_to2:
                        continue
                    dicci['free'] &= not periodicitat_coincident( (ldate_from2, ldate_to2, weeks_to_pass), (ldate_iwl_from, ldate_iwl_to, item.weeks_to_pass))
        
    def hours_from_room(self, cr, uid, def_hour_ids, values, context = None):
        if filter(lambda x: not values[x],['room_id','date_from','date_to']): return def_hour_ids
        (room_id, date_from, date_to, weeks_to_pass, week_to_init) = map(lambda x: values.get(x,0), ['room_id','date_from','date_to','weeks_to_pass','week_to_init'])
        hour_dict = self.get_hour_dict(cr, uid, def_hour_ids, context = context)
        iwl_ids = self.pool.get('school.impartition_week_line').search(cr, uid, [('room_id','=',room_id),('limit_from','<',date_to),('limit_to','>',date_from)])
        self.update_hour_dict_from_iwls(cr, uid, hour_dict, iwl_ids, date_from, date_to, weeks_to_pass, week_to_init, context = context)
        return [hour_id for hour_id,dicci in hour_dict.items() if dicci['free']]

    def hours_from_group(self, cr, uid, def_hour_ids, values, context = None):
        if filter(lambda x: not values[x],['group_id','date_from','date_to']): return def_hour_ids
        (group_id, date_from, date_to, weeks_to_pass, week_to_init) = map(lambda x: values.get(x,0), ['group_id','date_from','date_to','weeks_to_pass','week_to_init'])
        hour_dict = self.get_hour_dict(cr, uid, def_hour_ids, context = context)
        iwl_ids = self.pool.get('school.impartition_week_line').search(cr, uid, [('group_id','=',group_id),('limit_from','<',date_to),('limit_to','>',date_from)])
        self.update_hour_dict_from_iwls(cr, uid, hour_dict, iwl_ids, date_from, date_to, weeks_to_pass, week_to_init, context = context)
        return [hour_id for hour_id,dicci in hour_dict.items() if dicci['free']]

    def _get_courses_for_teacher(self, cr, uid, teacher_id, date_from, date_to, context = None):
        if not context: context = {}
        ret = []
        tcs_ids = self.pool.get('school.teacher_course_suitability').search(cr, uid, [('teacher_id','=',teacher_id)], context = context)
        context2 = dict(context)
        context2.update({'date_from': date_from, 'date_to': date_to,})
        for tcs in self.pool.get('school.teacher_course_suitability').browse(cr, uid, tcs_ids, context = context2):
            if tcs.max_assigned_hours < tcs.max_week_hours:
                ret.append(tcs.course_id.id)
        return ret

    def _get_values(self, cr, uid, wid, context = None):
        other_fields = []
        domain_fields = []
        for field_name in self._columns.keys():
            if is_domain(field_name):
                domain_fields.append(field_name)
            else:
                other_fields.append(field_name)
        item = self.read(cr, uid, [wid], other_fields, context = context)
        if 'actual' not in self.wizard_datas[wid]:
            self.wizard_datas[wid]['actual'] = {}
        data = self.wizard_datas[wid]['actual']
        values = {}
        domains = dict.fromkeys(domain_fields, [0])
        for field_name in other_fields:
            default_value = item[0][field_name]
            values[field_name] = data.get(field_name, default_value)
            if field_name[-3:]=='_id' and type(values[field_name]) in (list,tuple):
                values[field_name] = values[field_name] and values[field_name][0]
        return (values, domains)

    def _get_values2(self, cr, uid, wid, context = None):
        iwl_obj = self.pool.get('school.impartition_week_line')
        (values,domains) = self._get_values(cr, uid, wid, context = context)
        
        date_from = values['date_from'] or _MIN_DATETIME
        date_to = values['date_to'] or _MAX_DATETIME
        
        domains['room_domain'] = False
        if values['mode'] == 'to complete':
            if values['priority'] == 'teacher0':
                if values['teacher_suitability_option']:
                    domains['teacher_domain'] = [0] + self._get_teacher_no_max_hours(cr, uid, date_from, date_to, context = context)
                else:
                    domains['teacher_domain'] = False
                if domains['teacher_domain']:
                    values['teacher_id'] = len(domains['teacher_domain'])==2 and domains['teacher_domain'][1] or values['teacher_id'] in domains['teacher_domain'] and values['teacher_id'] or False
                if values['teacher_id']:
                    if values['teacher_suitability_option']:
                        domains['course_domain'] = [0] + self._get_courses_for_teacher(cr, uid, values['teacher_id'], date_from, date_to, context = context)
                    else:
                        domains['course_domain'] = False
                    if domains['course_domain']:
                        values['course_id'] = len(domains['course_domain'])==2 and domains['course_domain'][1] or values['course_id'] in domains['course_domain'] and values['course_id'] or False
                    if values['course_id']:
                        if values['groups_to_complete_course_option']:
                            domains['group_domain'] = [0] + self._get_groups_to_complete_course(cr, uid, values['course_id'], date_from, date_to, context = context)
                        else:
                            query = "SELECT g.id FROM groups_group AS g LEFT JOIN groups_group_assignation AS ga ON g.id=ga.group_id WHERE ga.id IS NULL"
                            cr.execute(query)
                            domains['group_domain'] = [x for (x,) in cr.fetchall()]
                            domains['group_domain'] += [0] + \
                                self.pool.get('groups.group').\
                                    search(cr, uid, [('assignation_ids.limit_from','<',date_to),
                                        ('assignation_ids.limit_to','>',date_from)])

                        if domains['group_domain']:
                            values['group_id'] = len(domains['group_domain'])==2 and domains['group_domain'][1] or values['group_id'] in domains['group_domain'] and values['group_id'] or False
                    else:
                        values['group_id'] = False
                else:
                    values['course_id'] = False
                    values['group_id'] = False
            if values['course_id']:
                args2 = [('course_id','=',values['course_id']),('date_from','<',date_to),('date_to','>',date_from)]
                if values['group_id']:
                    parent_ids = self._get_parent_ids(cr, uid, values['group_id'])
                    args2 += [('group_id','in',parent_ids)]
                else:
                    args2 += [('group_id','=',False)]
                domains['classe_domain'] = [0] + self.pool.get('school.classe').search(cr, uid, args2)
                if not domains['classe_domain'] or len(domains['classe_domain']) > 1:
                    values['classe_id'] = len(domains['classe_domain'])==2 and domains['classe_domain'][1] or values['classe_id'] in domains['classe_domain'] and values['classe_id'] or False
                    if values['classe_id']and values['def_hour_id']:
                        def_hour = self.pool.get('school.iwl.def_hour').read(cr, uid, [values['def_hour_id']], ['week_day','hour_from','hour_to'])[0]
                        args2 = [('classe_id','=',values['classe_id']),
                                 ('week_day','=',def_hour['week_day']),
                                 ('hour_from','<',def_hour['hour_to']),
                                 ('hour_to','>',def_hour['hour_from']),
                                 ('weeks_to_pass','=',values['weeks_to_pass']),
                                 ('week_to_init','=',values['week_to_init'])]
                        if values['group_id']:
                            args2 += [('group_id','in',parent_ids)]
                        domains['iwl_domain'] = [0] + self.pool.get('school.impartition_week_line').search(cr, uid, args2)
                        if not domains['iwl_domain'] or len(domains['iwl_domain']) > 1:
                            values['iwl_id'] = len(domains['iwl_domain'])==2 and domains['iwl_domain'][1] or values['iwl_id'] in domains['iwl_domain'] and values['iwl_id'] or False
                            if values['iwl_id']:
                                domains['teacher_data_domain'] = [0] + self.pool.get('school.teacher_data').search(cr, uid, [('iwl_id','=',values['iwl_id']),('teacher_id','=',values['teacher_id']),])
                                if not domains['teacher_data_domain'] or len(domains['teacher_data_domain']) > 1:
                                    values['teacher_data_id'] = len(domains['teacher_data_domain'])==2 and domains['teacher_data_domain'][1] or values['teacher_data_id'] in domains['teacher_data_domain'] and values['teacher_data_id'] or False
                                else:
                                    values['teacher_data_id'] = False
                            else:
                                values['teacher_data_id'] = False
                        else:
                            values['iwl_id'] = False
                            values['teacher_data_id'] = False
                    else:
                        values['iwl_id'] = False
                        values['teacher_data_id'] = False
                else:
                    values['classe_id'] = False
                    values['iwl_id'] = False
                    values['teacher_data_id'] = False
            else:
                values['classe_id'] = False
                values['iwl_id'] = False
                values['teacher_data_id'] = False
            hour_ids = self.pool.get('school.iwl.def_hour').search(cr, uid, [('def_hours_id','=',values['def_hours_id'])])
            hour_ids = self.hours_from_teacher(cr, uid, hour_ids, values, context = context)
            hour_ids = self.hours_from_group(cr, uid, hour_ids, values, context = context)
            hour_ids = self.hours_from_room(cr, uid, hour_ids, values, context = context)
            domains['hour_domain'] = [0] + hour_ids
            if len(domains['hour_domain']) == 2:
                values['def_hour_id'] = domains['hour_domain'][1]
            else:
                if values['def_hour_id'] not in domains['hour_domain']:
                    values['def_hour_id'] = False
        else:
            if values['priority'] == 'teacher0':
                domains2 = {'classe': set(), 'iwl': set(), 'td': set(),}
                domains['teacher_domain'] = [0] + self.pool.get('school.teacher').search(cr, uid, [('teacher_data_ids.limit_from','<',date_to),('teacher_data_ids.limit_to','>',date_from)], context = context)
                if domains['teacher_domain']:
                    values['teacher_id'] = len(domains['teacher_domain'])==2 and domains['teacher_domain'][1] or values['teacher_id'] in domains['teacher_domain'] and values['teacher_id'] or False
                    if values['teacher_id']:
                        td_ids = self.pool.get('school.teacher_data').search(cr, uid, [('teacher_id','=',values['teacher_id']),('limit_from','<',date_to),('limit_to','>',date_from)])
                        course_domain = set()
                        domains2 = {'classe': set(), 'iwl': set(), 'td': set(),}
                        def _add2(dicci,domains2):
                            map(lambda (key,value): domains2[key].add(value),dicci.items())
                        for item in self.pool.get('school.teacher_data').browse(cr, uid, td_ids):
                            _add2({'td': item.id, 'iwl': item.iwl_id.id, 'classe': item.iwl_id.classe_id.id}, domains2)
                            course_domain.add(item.iwl_id.classe_id.course_id.id)
                        domains['course_domain'] = list(course_domain)
                        if domains['course_domain']:
                            values['course_id'] = len(domains['course_domain'])==1 and domains['course_domain'][0] or values['course_id'] in domains['course_domain'] and values['course_id'] or False                            
                            if values['course_id']:
                                td_ids = self.pool.get('school.teacher_data').search(cr, uid, [('id','in',td_ids),('iwl_id.classe_id.course_id','=',values['course_id'])])
                                group_domain = set()
                                domains2 = {'classe': set(), 'iwl': set(), 'td': set(),}
                                for item in self.pool.get('school.teacher_data').browse(cr, uid, td_ids):
                                    _add2({'td': item.id, 'iwl': item.iwl_id.id, 'classe': item.iwl_id.classe_id.id}, domains2)
                                    group_domain.add(item.iwl_id.group_id.id)
                                domains['group_domain'] = list(group_domain)
                                if values['group_id']:
                                    td_ids = self.pool.get('school.teacher_data').search(cr, uid, [('id','in',td_ids),('iwl_id.group_id','=',values['group_id'])])
                                    domains2 = {'classe': set(), 'iwl': set(), 'td': set(),}
                                    for item in self.pool.get('school.teacher_data').browse(cr, uid, td_ids):
                                        _add2({'td': item.id, 'iwl': item.iwl_id.id, 'classe': item.iwl_id.classe_id.id}, domains2)
                domains['classe_domain'] = [0] + list(domains2['classe'])
                if len(domains['classe_domain']) == 2:
                    values['classe_id'] = domains['classe_domain'][1]
                else:
                    if values['classe_id'] not in domains['classe_domain']:
                        values['classe_id'] = False
                domains['iwl_domain'] = [0] + list(domains2['iwl'])
                if len(domains['iwl_domain']) == 2:
                    values['iwl_id'] = domains['iwl_domain'][1]
                else:
                    if values['iwl_id'] not in domains['iwl_domain']:
                        values['iwl_id'] = False
                domains['td_domain'] = [0] + list(domains2['td'])
                if len(domains['td_domain']) == 2:
                    values['teacher_data_id'] = domains['td_domain'][1]
                else:
                    if values['teacher_data_id'] not in domains['td_domain']:
                        values['teacher_data_id'] = False
        values['create_ok'] = (values['course_id'] and not values['classe_id']) or \
           (values['classe_id'] and values['def_hour_id'] and not values['iwl_id']) or \
           (values['iwl_id'] and values['teacher_id'] and not values['teacher_data_id'])
                
        ids2 = []
        if values['teacher_id']:
            ids2 = iwl_obj.search(cr, uid, [('teachers.teacher_id','=',values['teacher_id'])])
        values['teacher_iwl_ids'] = ids2
        ids2 = []
        if values['room_id']:
            ids2 = iwl_obj.search(cr, uid, [('room_id','=',values['room_id'])])
        values['room_iwl_ids'] = ids2
        ids2 = []
        if values['group_id']:
            ids2 = iwl_obj.search(cr, uid, [('group_id','in',self._get_parent_ids(cr, uid, values['group_id']))])
        values['group_iwl_ids'] = ids2
        return (values, domains)
        
    def _get_teacher_iwl_ids(self, cr, uid, ids, field_name, arg, context = None):
        ret = {}
        iwl_obj = self.pool.get('school.impartition_week_line')
        for item in self.read(cr, uid, ids, ['teacher_id'], context = context):
            ids2 = iwl_obj.search(cr, uid, [('teachers.teacher_id','=',item['teacher_id'] and item['teacher_id'][0])])
            ret[item['id']] = ids2
        return ret

    def _get_group_iwl_ids(self, cr, uid, ids, field_name, arg, context = None):
        ret = {}
        iwl_obj = self.pool.get('school.impartition_week_line')
        for item in self.read(cr, uid, ids, ['group_id'], context = context):
            ids2 = []
            if item['group_id']:
                ids2 = iwl_obj.search(cr, uid, [('group_id','in',self._get_parent_ids(cr, uid, item['group_id'] and item['group_id'][0]))])
            ret[item['id']] = ids2
        return ret

    def _get_room_iwl_ids(self, cr, uid, ids, field_name, arg, context = None):
        ret = {}
        iwl_obj = self.pool.get('school.impartition_week_line')
        for item in self.read(cr, uid, ids, ['room_id'], context = context):
            ids2 = iwl_obj.search(cr, uid, [('room_id','=',item['room_id'] and item['room_id'][0])])
            ret[item['id']] = ids2
        return ret

    _columns = {
        'date_from' : fields.date('Date from', help = "Date from for all considerations",),
        'date_to' : fields.date('Date to', help = "Date to to search classes",),
        'calendar_id' : fields.many2one('school.holidays_calendar', string='Holidays Calendar', help='Holidays Calendar for new classes', required=True,),
        'priority' : fields.selection([('teacher0','Teacher-Course-Group-Hour'),], string = 'Priority',),
        'mode' : fields.selection([('to complete','To Complete'),('to edit','To Edit')], string = 'Mode',),

        'teacher_id' : fields.many2one('school.teacher', string = 'Teacher', domain = "teacher_domain and [('id','in',map(int,teacher_domain.split(',')))] or []"),
        'teacher_domain' : fields.text('Teacher Domain',),
        'teacher_suitability_option' : fields.boolean('Teachers suitability option',),

        'def_hours_id' : fields.many2one('school.iwl.def_hours', string = 'Hours definition',),
        'def_hour_id' : fields.many2one('school.iwl.def_hour', 'Time range', domain = "[('id','in',hour_domain and map(int,hour_domain.split(',')) or [])]"),
        'hour_domain' : fields.text('Hour Domain',),
        'weeks_to_pass' : fields.integer('Weeks to pass', help = 'Weeks to pass between seances',),
        'week_to_init' : fields.integer('Week to init', help = 'Week first seance from date classe beginings',),

        'course_id' : fields.many2one('school.course', string = 'Course', domain = "course_domain and [('id','in',map(int,course_domain.split(',')))] or []",),
        'course_domain' : fields.text('Course Domain',),

        'group_id' : fields.many2one('groups.group', string = 'Group', domain = "group_domain and [('id','in',map(int,group_domain.split(',')))] or []",),
        'group_domain' : fields.text('Group Domain', ),
        'groups_to_complete_course_option' : fields.boolean('Groups to complete course option',),

        'room_id' : fields.many2one('school.room', string = 'Room', domain = "room_domain and [('id','in',map(int,room_domain.split(',')))] or []",),
        'room_domain' : fields.text('Room Domain',),

        'classe_id' : fields.many2one('school.classe', string = 'Classe', domain = "[('id','in',map(int,classe_domain.split(',')))]",),
        'classe_domain' : fields.text('Classe Domain',),

        'iwl_id' : fields.many2one('school.impartition_week_line', string = 'IWL', domain = "[('id','in',map(int,iwl_domain.split(',')))]",),
        'iwl_domain' : fields.text('IWL Domain',),

        'teacher_iwl_ids' : fields.function(_get_teacher_iwl_ids, type='many2many', method=True, obj='school.impartition_week_line',string='Teacher IWL',),

        'group_iwl_ids' : fields.function(_get_group_iwl_ids, type='many2many', method=True, obj='school.impartition_week_line',string='Group IWL',),

        'room_iwl_ids' : fields.function(_get_room_iwl_ids, type='many2many', method=True, obj='school.impartition_week_line',string='Room IWL',),

        'teacher_data_id' : fields.many2one('school.teacher_data', string = 'Selected hour', domain = "[('teacher_id','=',teacher_id),('iwl_id','=',iwl_id)]",),
        'teacher_data_domain' : fields.text('Teacher Data Domain',),

        'create_ok' : fields.boolean('Create ok',),
    }
    
    def _check_dates(self, cr, uid, ids, context=None):
        ret = True
        for item in self.browse(cr, uid, ids, context=context):
            ret &= item.date_from < item.date_to
        return ret
    
    _constraints = [(_check_dates, _('Wrong dates'), ['date_from','date_to'])]
    
    def read(self, cr, uid, ids, fields_to_read, context=None, load='_classic_read'):
        ret = super(school_iwl_manual_intro_wizard, self).read(cr, uid, ids, fields_to_read, context=context, load=load)
        if filter(lambda x : is_domain(x), fields_to_read):
            for item in ret:
                (values, domains) = self._get_values2(cr, uid, item['id'], context = context)
                item.update(dict( (key,value and ','.join(map(str,value)) or []) for key,value in domains.items() if key in fields_to_read) )
        return ret

    def _get_def_hours_id_default(self, cr, uid, context = None):
        l=self.pool.get('school.iwl.def_hours').search(cr,uid,[]);
        return len(l)==1 and l[0] or False

    _defaults = {
        'priority' : lambda *a : 'teacher0',
        'mode' : lambda *a : 'to complete',
        'weeks_to_pass' : lambda *a : 0,
        'week_to_init' : lambda *a : 0,
        'date_from' : lambda *a : '2011-04-01',
        'date_to' : lambda *a : '2011-08-31',
        'def_hours_id' : _get_def_hours_id_default,
    }
    
    def create_all(self, cr, uid, ids, context = None):
        ret = False
        for item in self.browse(cr, uid, ids, context = context):
            (classe_id, iwl_id, teacher_data_id) = (item.classe_id and item.classe_id.id or False,
                                                    item.iwl_id and item.iwl_id.id or False,
                                                    item.teacher_data_id and item.teacher_data_id.id or False)
            if not teacher_data_id:
                if not iwl_id:
                    if not classe_id and item.course_id:
                        classe_id = self.pool.get('school.classe').create(cr, uid, {
                                                        'date_from': item.date_from,
                                                        'holidays_calendar_id' : item.calendar_id.id,
                                                        'date_to': item.date_to,
                                                        'course_id': item.course_id.id,
                                                        'group_id': item.group_id.id,}, context = context)
                    if classe_id and item.def_hour_id and item.weeks_to_pass>=0 and item.week_to_init>=0:
                        iwl_id = self.pool.get('school.impartition_week_line').create(cr, uid, {
                                                        'classe_id': classe_id,
                                                        'subgroup' : item.group_id.id,
                                                        'room_id' : item.room_id.id,
                                                        'week_day': item.def_hour_id.week_day,
                                                        'hour_from': item.def_hour_id.hour_from,
                                                        'duration': item.def_hour_id.hour_to - item.def_hour_id.hour_from,
                                                        'weeks_to_pass': item.weeks_to_pass,
                                                        'week_to_init': item.week_to_init,}, context = context)
                        # Saving the last room for the group
                        if item.group_id and item.room_id:
                            ids2 = self.pool.get('school.iwl_manual_intro.last_room_by_group').search(cr, uid, [('group_id','=',item.group_id.id)])
                            if ids2:
                                self.pool.get('school.iwl_manual_intro.last_room_by_group').write(cr, uid, ids2, {'room_id': item.room_id.id})
                            else:
                                self.pool.get('school.iwl_manual_intro.last_room_by_group').create(cr, uid, {'group_id': item.group_id.id,'room_id': item.room_id.id})
                if iwl_id and item.teacher_id:
                    teacher_data_id = self.pool.get('school.teacher_data').create(cr, uid, {
                                                    'iwl_id': iwl_id,
                                                    'teacher_id': item.teacher_id.id,}, context = context)
            ret |= self.write(cr, uid, [item.id], {'create_ok': False, 'classe_id': classe_id, 'iwl_id': iwl_id, 'teacher_data_id': teacher_data_id,})
        return ret

    def delete_td(self, cr, uid, ids, context = None):
        ret = False
        for item in self.browse(cr, uid, ids, context = context):
            teacher_data_id = item.teacher_data_id and item.teacher_data_id.id or False
            if teacher_data_id:
                ret |= self.pool.get('school.teacher_data').unlink(cr, uid, [teacher_data_id], context = context)
        self.write(cr, uid, ids, {'create_ok': True, 'teacher_data_id': False,})
        return ret

    def delete_iwl(self, cr, uid, ids, context = None):
        ret = False
        for item in self.browse(cr, uid, ids, context = context):
            iwl_id = item.iwl_id and item.iwl_id.id or False
            if iwl_id:
                ret |= self.pool.get('school.impartition_week_line').unlink(cr, uid, [iwl_id], context = context)
        self.write(cr, uid, ids, {'create_ok': True, 'iwl_id': False,'teacher_data_id': False,})
        return ret

    def delete_classe(self, cr, uid, ids, context = None):
        ret = False
        for item in self.browse(cr, uid, ids, context = context):
            classe_id = item.classe_id and item.classe_id.id or False
            if classe_id:
                ret |= self.pool.get('school.classe').unlink(cr, uid, [classe_id], context = context)
        self.write(cr, uid, ids, {'create_ok': True, 'classe_id': False, 'iwl_id': False,'teacher_data_id': False,})
        return ret

    def on_change(self, cr, uid, ids, field, value, context = None):
        lid = ids[0]
        dicci = self.wizard_datas[lid]
        if 'actual' not in dicci:
            dicci['actual'] = {}
        dicci['actual'][field] = value
        if field == 'group_id' and value:
            ids2 = self.pool.get('school.iwl_manual_intro.last_room_by_group').search(cr, uid, [('group_id','=',value)])
            for item in self.pool.get('school.iwl_manual_intro.last_room_by_group').browse(cr, uid, ids2):
                dicci['actual']['room_id'] = item.room_id.id            
        (values, domains) = self._get_values2(cr, uid, lid, context = context)
        for key,value2 in domains.items():
            values[key] = value2 and ','.join(map(str,value2)) or False
        return {
            'value' : values,
        }
    
school_iwl_manual_intro_wizard()

class school_iwl_manual_intro_last_room_by_group(osv.osv):
    _name = 'school.iwl_manual_intro.last_room_by_group'
    _columns = {
                'group_id' : fields.many2one('groups.group',string='Group',ondelete='cascade',select=True,),
                'room_id' : fields.many2one('school.room',string='Room',ondelete='cascade',select=True,),
                }
school_iwl_manual_intro_last_room_by_group()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
