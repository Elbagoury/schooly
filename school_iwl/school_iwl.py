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

import math
import collections
from openerp.osv import osv, fields
from datetime import datetime, date, timedelta
from openerp.tools.translate import _
from collections import defaultdict

_MIN_DATETIME='1970-01-01 00:00:00'
_MAX_DATETIME='2099-12-31 23:59:59'

class school_impartition_week_line(osv.osv):
    _name = 'school.impartition_week_line'
school_impartition_week_line()

class school_teacher_data(osv.osv):
    _name = 'school.teacher_data'
    _rec_name = 'teacher_id'

    def name_get(self, cr, uid, ids, context = None):
        iwl_dicci = collections.defaultdict(list)
        for item in self.browse(cr, uid, ids, context = context):
            iwl_dicci[item.iwl_id.id].append( (item.id,item.teacher_id.teacher_name) )
        ret = {}
        for (iwl_id, iwl_name) in self.pool.get('school.impartition_week_line').name_get(cr, uid, iwl_dicci.keys(), context = context):
            for (id,teacher_name) in iwl_dicci[iwl_id]:
                ret[id] = "%s | %s" % (iwl_name,teacher_name)
        return [(id, ret[id]) for id in ids]
    
    def _get_td_from_classe(self, cr, uid, ids, context = None):
        ret = []
        for classe in self.pool.get('school.classe').browse(cr, uid, ids, context = context):
            for iwl in classe.impartition_week_line_ids:
                for td in iwl.teachers:
                    ret.append(td.id)
        return ret

    def _get_td_from_impartition_week_line(self, cr, uid, ids, context = None):
        ret = []
        for iwl in self.pool.get('school.impartition_week_line').browse(cr, uid, ids, context = context):
            for td in iwl.teachers:
                ret.append(td.id)
        return ret

    def _get_limits(self, cr, uid, ids, field_name, arg, context = None):
        ret = collections.defaultdict(dict)
        for td in self.browse(cr, uid, ids):
            ret[td.id]['limit_from'] = max(td.datetime_from or _MIN_DATETIME,td.iwl_id.date_from or _MIN_DATETIME,td.iwl_id.classe_id.date_from)
            ret[td.id]['limit_to'] = min(td.datetime_to or _MAX_DATETIME,td.iwl_id.date_to or _MAX_DATETIME,td.iwl_id.classe_id.date_to)
        return ret

    _columns = {
        'teacher_id' : fields.many2one('school.teacher', 'Teacher', required=True, select=1, ),
        'iwl_id' : fields.many2one('school.impartition_week_line',string='Week Hour', required=True, select=1, ondelete='cascade',),
        'title' : fields.selection([('imperative','Imperative'),('needed','Needed'),('optional','Optional'),('advisable','Advisable')], 'Title', ),
        'datetime_from' : fields.datetime('From',),
        'datetime_to' : fields.datetime('To',),
        'classe_id' : fields.related('iwl_id','classe_id',type='many2one',relation='school.classe',string="Classe",),
        'week_day' : fields.related('iwl_id','week_day',type='selection',string="Week day",selection=[('1','monday'),('2','tuesday'),('3','wednesday'),('4','thursday'),('5','friday'),('6','saturday'),('7','sunday')],),
        'hour_from' : fields.related('iwl_id','hour_from',type='float',string="Hour from",),
        'duration' : fields.related('iwl_id','duration',type='float',string="Hour to",),
        'weeks_to_pass' : fields.related('iwl_id','weeks_to_pass',string='Week to pass',type='integer',help="Weeks to pass until next week",),
        'week_to_init' : fields.related('iwl_id','week_to_init',string='Week to init',type='integer',help="Weeks to pass until first week"),
        'limit_from' : fields.function(_get_limits, string='Limit from', method = True, type = 'datetime', multi = 'limits', store = {
                'school.classe' : (_get_td_from_classe,['date_from','date_to'],10),
                'school.impartition_week_line' : (_get_td_from_impartition_week_line,['classe_id','date_from','date_to'],15),
                'school.teacher_data' : (lambda self,cr,uid,ids,context={}: ids,['iwl_id','datetime_from','datetime_to'],20),
            }),
        'limit_to' : fields.function(_get_limits, string='Limit to', method = True, type = 'datetime', multi = 'limits', store = {
                'school.classe' : (_get_td_from_classe,['date_from','date_to'],10),
                'school.impartition_week_line' : (_get_td_from_impartition_week_line,['classe_id','date_from','date_to'],15),
                'school.teacher_data' : (lambda self,cr,uid,ids,context={}: ids,['iwl_id','datetime_from','datetime_to'],20),
            }),
    }

    def _no_overlaps(self, cr, uid, ids, context = None):
        for item in self.browse(cr, uid, ids):
            query = """
                SELECT td.id
                FROM school_teacher_data AS td
                    LEFT JOIN school_impartition_week_line AS iwl ON td.iwl_id=iwl.id
                    LEFT JOIN school_classe AS cl ON iwl.classe_id=cl.id
                WHERE td.iwl_id=%s AND td.teacher_id=%s AND COALESCE(td.datetime_from,iwl.date_from,cl.date_from)<%s AND COALESCE(td.datetime_to,iwl.date_to,cl.date_to)>%s AND td.id<>%s
                LIMIT 1"""
            limit_to = item.datetime_to or item.iwl_id.date_to or item.iwl_id.classe_id.date_to
            limit_from = item.datetime_from or item.iwl_id.date_from or item.iwl_id.classe_id.date_from
            params = (item.iwl_id.id,item.teacher_id.id,limit_to,limit_from,item.id) 
            cr.execute(query,params)
            for (lid,) in cr.fetchall():
                return False
        return True
            
    _constraints = [(_no_overlaps, 'Overlaps!',['teacher_id','iwl_id','datetime_from','datetime_to'])]
                
school_teacher_data()

class school_teacher(osv.osv):
    _name = 'school.teacher'
    _inherit = 'school.teacher'
    
    _columns = {
        'teacher_data_ids' : fields.one2many('school.teacher_data','teacher_id',string='Week Hours',),
    }

school_teacher()

class school_room(osv.osv):
    _name = 'school.room'
    _inherit = 'school.room'
    _columns = {
        'impartition_week_lines' : fields.one2many('school.impartition_week_line','room_id','Horary',select=0),
    }
school_room()

class school_impartition_week_line(osv.osv):
    _name = 'school.impartition_week_line'
    _inherit = 'util.periodicity'

    def _get_days_no_work(self,cr, uid, iwl_ids):
            days_no_work_by_classe={}
            for iwl in self.browse(cr, uid, iwl_ids):
                if iwl.classe_id.id not in days_no_work_by_classe:                    
                    if iwl.classe_id.holidays_calendar_id and iwl.classe_id.holidays_calendar_id.holidays:
                        days_no_work=[]
                        for holiday in iwl.classe_id.holidays_calendar_id.holidays:
                            cdate=holiday.date_from
                            days_no_work.append(cdate)
                            while cdate<holiday.date_to:
                                cdate=(datetime.strptime(cdate,'%Y-%m-%d')+timedelta(days=1)).strftime('%Y-%m-%d')
                                days_no_work.append(cdate)
                        days_no_work_by_classe[iwl.classe_id.id]=days_no_work
                    else:
                        days_no_work_by_classe[iwl.classe_id.id]=[]
            return days_no_work_by_classe

    def _create_seances_sub(self, cr, uid, iwl, dates_list):
        teachers = defaultdict(list)
        for data in iwl.teachers:
            teacher_id = data.teacher_id.id
            if teacher_id not in teachers:
                teachers[(data.datetime_from or _MIN_DATETIME,data.datetime_to or _MAX_DATETIME)] += [(0,0,{'teacher_id': teacher_id, 'title': data.title})]
        for date_from in dates_list:
            date_to=datetime.strptime(date_from,'%Y-%m-%d %H:%M:%S')+timedelta(hours=iwl.duration)
            vals_teachers=[]
            for (dtf,dtt) in teachers.keys():
                if date_from < dtt and date_to.strftime('%Y-%m-%d %H:%M:%S') > dtf:
                    vals_teachers += teachers[(dtf,dtt)]
            vals={'date': date_from,
                'date_to': date_to.strftime('%Y-%m-%d %H:%M:%S'),
                'classe_id' : iwl.classe_id.id,
                'iwl_id': iwl.id,
                'room_id': iwl.room_id.id,
                'group_id': iwl.subgroup.id,
                'teachers': vals_teachers,
            }
            self.pool.get('school.seance').create(cr, uid, vals)
        return

    def check_seances(self, cr, uid, ids, context=None):
        if not context: context={}
        seance_ids_to_unlink=[]
        days_no_work_by_classe=self._get_days_no_work(cr, uid, ids)
        for iwl in self.browse(cr, uid, ids):
            dates_to_create=self.periodicity_datetimes_str(\
                    date_from=iwl.limit_from,\
                    date_to=iwl.limit_to,\
                    hour_from=iwl.hour_from,\
                    tz=iwl.tz or context.get('tz','Europe/Madrid'),\
                    week_day=iwl.week_day,\
                    weeks_to_pass=iwl.weeks_to_pass,\
                    week_to_init=iwl.week_to_init,\
                    days_no_work=days_no_work_by_classe[iwl.classe_id.id])
            for seance in iwl.seance_ids:
                if seance.date not in dates_to_create:
                    seance_ids_to_unlink.append(seance.id)
                else:
                    dates_to_create.remove(seance.date)
            self._create_seances_sub(cr, uid, iwl, dates_to_create)
        self.pool.get('school.seance').unlink(cr, uid, seance_ids_to_unlink)
        return

    def name_get(self, cr, uid, ids, context = None):
        ret=[]
        for iwl in self.browse(cr, uid, ids):
            ret.append((iwl.id,"%(course_name)s [%(group_name)s] %(week_day)s-%(hour_from)s:%(minute_from)s%(weeks)s%(hours)s" % {
                'course_name': iwl.classe_id.course_id.name,
                'group_name': iwl.subgroup.name,
                'week_day': (',',_('monday'),_('tuesday'),_('wednesday'),_('thursday'),_('friday'),_('saturday'),_('sunday'))[int(iwl.week_day)],
                'hour_from': int(iwl.hour_from),
                'minute_from' : int( (iwl.hour_from - int(iwl.hour_from) ) * 60 ),
                'weeks' : (iwl.weeks_to_pass or iwl.week_to_init) and "-%(weeks_to_pass)s%(week_to_init)s" % {'weeks_to_pass': iwl.weeks_to_pass,'week_to_init': iwl.week_to_init,} or '',
                'hours' : (iwl.date_from or iwl.date_to) and " (%(date_from)s-%(date_to)s)" % {'date_from': iwl.date_from or '','date_to': iwl.date_to or ''} or '',
                }))
        return ret

    def name_search(self, cr, uid, name='', args=[], operator='ilike', context=None, limit=80):
        ids = self.search(cr, uid, args, context = context, limit = limit)
        print "name, args, operator : ", name, args, operator
        return self.name_get(cr, uid, ids, context = context)

    def _get_hour_to(self, cr, uid, ids, field_name, arg, context = None):
        ret = {}
        for data in self.read(cr, uid, ids, ['hour_from','duration'], context = context):
            ret[data['id']] = data['hour_from'] + data['duration']
        return ret

    def _limits(self, cr, uid, ids, field_name, arg, context=None):
        res={}
        for iwl in self.browse(cr, uid, ids):
            id=iwl.id
            res[id]={'limit_from' : iwl.date_from or _MIN_DATETIME[0:10], 'limit_to' : iwl.date_to or _MAX_DATETIME[0:10]}
            if res[id]['limit_from']<iwl.classe_id.date_from:
                res[id]['limit_from']=iwl.classe_id.date_from
            if res[id]['limit_to']>iwl.classe_id.date_to:
                res[id]['limit_to']=iwl.classe_id.date_to
        return res

    _columns = {
        'classe_id' : fields.many2one('school.classe','Classe', ondelete="cascade",select=1,required=True),
        'group_id' : fields.related('classe_id','group_id',string='Group',type='many2one',relation='groups.group'),
        'duration' : fields.float('Duration',help="Duration in hours",),
        'hour_to' : fields.function(_get_hour_to, type = 'float', method = True, string = 'Hour to', store = {
            'school.impartition_week_line' : (lambda self,cr,uid,ids,context={}: ids,['hour_from','duration'],10)}),
        'room_id' : fields.many2one('school.room','Room',select=1,required=False),
        'teachers' : fields.one2many('school.teacher_data','iwl_id',string="Teachers"),
        'subgroup' : fields.many2one('groups.group',string='Subgroup',ondelete='restrict',),
        'seance_ids' : fields.one2many('school.seance','iwl_id',string="Seances"),                
        'limit_from' : fields.function(_limits, type='date', method=True, string='Limit from', multi='limits',store={
            'school.classe': (lambda self, cr, uid, ids, context: self.pool.get('school.impartition_week_line').search(cr, uid, [('classe_id','in',ids)]),['date_from','date_to'],10),
            'school.impartition_week_line': (lambda self, cr, uid, ids, context: ids ,['classe_id','date_from','date_to'],15)
            }),
        'limit_to' : fields.function(_limits, type='date', method=True, string='Limit to', multi='limits',store={
            'school.classe': (lambda self, cr, uid, ids, context: self.pool.get('school.impartition_week_line').search(cr, uid, [('classe_id','in',ids)]),['date_from','date_to'],10),
            'school.impartition_week_line': (lambda self, cr, uid, ids, context: ids ,['classe_id','date_from','date_to'],15)
            }),
    }

    def _subgroup_son_of_classe_group(self, cr, uid, ids, context=None):
        ret = True
        for item in self.browse(cr, uid, ids, context=context):
            if not item.classe_id.group_id or not item.subgroup:
                continue
            g_obj = self.pool.get('groups.group')
            subgs = g_obj._get_group_ids_and_our_children(
                        cr, uid, [item.classe_id.group_id.id], context=context)
            if item.subgroup.id not in subgs:
                ret |= True
        return ret

    _constraints = [(_subgroup_son_of_classe_group, 'The group must be subgroup of the classe group', ['subgroup','classe_id'])]
    
    def on_change_classe(self, cr, uid, ids, classe_id, subgroup, context=None):
        if not classe_id:
            ret = {'value': {'subgroup': False,}, 'domain': {'subgroup': False,}}
        else:
            c_obj = self.pool.get('school.classe')
            classe = c_obj.browse(cr, uid, classe_id, context=context)
            if classe.group_id:
                g_obj = self.pool.get('groups.group')
                g_ids = g_obj._get_group_ids_and_our_children(
                        cr, uid, [classe.group_id.id], context=context)
                ret = {'domain': {'subgroup': [('id','in',g_ids)]}}
                if subgroup not in ret['domain']['subgroup']:
                    ret.update({'value': {'subgroup': False,},})
        return ret
    
    def write(self, cr, uid, ids, vals, context=None):
        ret=super(school_impartition_week_line, self).write(cr, uid, ids, vals, context=context)
        self.check_seances(cr, uid, ids, context=context)
        # Updating related seances
        vals2 = {}
        if 'room_id' in vals:
            vals2.update({'room_id': vals['room_id'] })
        if 'subgroup' in vals:
            vals2.update({'group_id': vals['subgroup'] })
        s_obj = self.pool.get('school.seance')
        seance_ids = s_obj.search(cr, uid, [('iwl_id','in',ids)])
        if seance_ids:
            s_obj.write(cr, uid, seance_ids, vals2)
        return ret

    def create(self, cr, uid, vals, context=None):
        if not 'subgroup' in vals or not vals['subgroup']:
            classe = self.pool.get('school.classe').browse(cr, uid, vals['classe_id'])
            vals['subgroup'] = classe.group_id.id
        ret=super(school_impartition_week_line, self).create(cr, uid, vals, context=context)
        self.check_seances(cr, uid, [ret], context=context)
        return ret

school_impartition_week_line()

class school_classe(osv.osv):
    _name = 'school.classe'
    _inherit = 'school.classe'
    
    _columns = {
        'impartition_week_line_ids': fields.one2many('school.impartition_week_line','classe_id',string='Week hours',required=False,),
    }

    def generate_iwls(self, cr, uid, ids, context=None):
        for item in self.browse(cr, uid, ids, context=context):
            act_hours = sum(x.duration for x in item.impartition_week_line_ids)
            td = datetime.strptime(item.date_to, '%Y-%m-%d') - \
                 datetime.strptime(item.date_from, '%Y-%m-%d')
            min_hours = math.ceil(float(item.course_id.min_hours * 7) / td.days)
            iwls_to_create = []
            while act_hours < min_hours:
                iwls_to_create += [(0,0,{'duration': 1,})]
                act_hours += 1
            self.write(cr, uid, [item.id], {'impartition_week_line_ids': iwls_to_create,}, context=context)
    
school_classe()

class school_seance(osv.osv):
    _name = 'school.seance'
    _inherit = 'school.seance'

    _columns = {
        'iwl_id' : fields.many2one('school.impartition_week_line', 'IWL', select=1, ondelete='cascade'),
    }
    
school_seance()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
