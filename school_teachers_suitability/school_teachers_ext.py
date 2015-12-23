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

import collections
import bisect
from openerp.osv import fields,osv
import os.path
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir,"timed_groups")))
from timed_groups import _MAX_DATETIME, _MIN_DATETIME

def posa_interval(listi, date_from, date_to, duration):
        if not duration or date_to<=date_from: return list(listi) # nothing to add
        # location
        begin = bisect.bisect_left(listi, (date_from, 0) )
        duration2 = 0
        new = listi[:begin] # remains left
        
        if begin:
            duration2 = listi[begin-1][1] # update last duration
        if len(listi) == begin or listi[begin][0] != date_from:
            new += [(date_from, duration2 + duration)] # interval between last and actual
        while begin < len(listi) and listi[begin][0] < date_to: # adding value until date_to
            duration2 = listi[begin][1]  # update last duration
            if not new or new[-1][1] != duration2 + duration: # no same value to last interval
                new += [(listi[begin][0], duration2 + duration)]
            begin += 1
        if begin == len(listi) or listi[begin][0] != date_to: # interval no coincidence, some interval between actual and next
            new += [(date_to, duration2)]
        while begin < len(listi) and listi[begin][1] == duration2:
            begin += 1 # next values equals to last one
        new += listi[begin:] # remains right
        return new

class school_teacher(osv.osv):
    _name = 'school.teacher'
    _inherit = 'school.teacher'

    def _compute_assigned_hours(self, cr, uid, ids, field_name, arg, context=None):
        td_obj = self.pool.get('school.teacher_data')
        if not context:
            context = {}
        ret = dict.fromkeys(ids,{'max_assigned_hours': 0, 'min_assigned_hours': 0,})
        date_from = max(
                context.get('date_from', _MIN_DATETIME) or _MIN_DATETIME,
                _MIN_DATETIME
                )
        date_to = min(context.get('date_to', _MAX_DATETIME) or _MAX_DATETIME, _MAX_DATETIME)
        criteria = [('teacher_id','in',ids),('limit_to','>',date_from),('limit_from','<',date_to)]
        td_ids = td_obj.search(cr, uid, criteria)
        dicci = {}
        for td in td_obj.browse(cr, uid, td_ids):
            if td.teacher_id.id not in dicci:
                dicci[td.teacher_id.id] = [(date_from,0)]
            dicci[td.teacher_id.id] = posa_interval(
                dicci[td.teacher_id.id], max(td.limit_from,date_from),
                min(td.limit_to,date_to),
                td.iwl_id.duration/(td.iwl_id.weeks_to_pass+1)  )
        for (teacher_id,llista) in dicci.items():
            ret[teacher_id] = {
                    'max_assigned_hours': max(x[1] for x in llista),
                    'min_assigned_hours': min(x[1] for x in llista),
            }
        return ret

    def _search_assigned_hours(self, cr, uid, obj, name, args, context = None):
        if not context: context = {}
        args2 = [(field,op,value) for (field,op,value) in args if field not in ('max_assigned_hours','min_assigned_hours')]
        if len(args) > len(args2):
            teacher_ids = self.search(cr, uid, args2, context = context)
            date_from = max(context.get('date_from', _MIN_DATETIME) or _MIN_DATETIME, _MIN_DATETIME)
            date_to = min(context.get('date_to', _MAX_DATETIME) or _MAX_DATETIME, _MAX_DATETIME)
            td_ids = self.pool.get('school.teacher_data').search(cr, uid, [('teacher_id','in',teacher_ids),('limit_to','>',date_from),('limit_from','<',date_to)])

            dicci = {}
            for item in self.pool.get('school.teacher_data').browse(cr, uid, td_ids):
                if item.teacher_id.id not in dicci:
                    dicci[item.teacher_id.id] = [(date_from,0)]
                dicci[item.teacher_id.id] = posa_interval(dicci[item.teacher_id.id], max(item.limit_from,date_from), min(item.limit_to,date_to), item.iwl_id.duration)

            teacher_ids = []
            for (teacher_id,llista) in dicci.items():
                minim = min(x[1] for x in llista)
                maxim = max(x[1] for x in llista)
                f = True
                for arg in args:
                    value = minim
                    if arg[0] == 'max_assigned_hours':
                        value = maxim
                    elif arg[0] == 'min_assigned_hours':
                        value = minim
                    else:
                        continue
                    if arg[1] == '=':
                        val = eval(value + '==' + arg[2], locals())
                    elif arg[1] in ['<', '>', 'in', 'not in', '<=', '>=', '<>']:
                        val = eval(value + arg[1] + arg[2], locals())
                    f = f and val
                if f:
                    teacher_ids.append(teacher_id)

            return [('id','in',teacher_ids)]
        return args2
        
    _columns = {
        'max_assigned_hours': fields.function(_compute_assigned_hours, fnct_search = _search_assigned_hours, type='float', method=True, string='Max assig hours', multi = 'assigned_hours',),
        'min_assigned_hours': fields.function(_compute_assigned_hours, fnct_search = _search_assigned_hours, type='float', method=True, string='Min assig hours', multi = 'assigned_hours',),
    }

school_teacher()

class school_teacher_course_suitability(osv.osv):
    _name = 'school.teacher_course_suitability'
    _inherit = 'school.teacher_course_suitability'

    def _compute_assigned_hours(self, cr, uid, ids, field_name, arg, context=None):
        td_obj = self.pool.get('school.teacher_data')
        if not context:
            context = {}
        ret = {}
        
        # contexte que limita el periode a calcular
        date_from = max(context.get('date_from', _MIN_DATETIME) or _MIN_DATETIME, _MIN_DATETIME)
        date_to = min(context.get('date_to', _MAX_DATETIME) or _MAX_DATETIME, _MAX_DATETIME)
        
        for cs in self.browse(cr, uid, ids, context = context):
            ret[cs.id] = {}
            iwl_ids = self.pool.get('school.impartition_week_line').search(cr, uid, [('classe_id.course_id','=',cs.course_id.id)])
            criteria = [('teacher_id','=',cs.teacher_id.id),
                        ('iwl_id','in',iwl_ids),
                        ('limit_to','>',date_from),
                        ('limit_from','<',date_to)]
            llista = [(date_from,0)]
            td_ids = td_obj.search(cr, uid, criteria)
            for td in td_obj.browse(cr, uid, td_ids):
                llista = posa_interval(
                            llista,
                            max(td.limit_from,date_from), # limita a periode
                            min(td.limit_to,date_to), # limita a periode
                            td.iwl_id.duration/(td.iwl_id.weeks_to_pass+1) )
            ret[cs.id] = {'max_assigned_hours': max(x[1] for x in llista),
                          'min_assigned_hours': min(x[1] for x in llista),
                          'total_max_assigned_hours': cs.teacher_id.max_assigned_hours,
                          'total_min_assigned_hours': cs.teacher_id.min_assigned_hours,}
        return ret

    def _search_assigned_hours(self, cr, uid, obj, name, args, context = None):
        if not context: context = {}
        
        args2 = []
        teacher_args_transform = {'total_max_assigned_hours': 'max_assigned_hours', 'total_min_assigned_hours': 'min_assigned_hours'}
        teacher_args = [(teacher_args_transform[field],op,value) for (field,op,value) in args if field in teacher_args_transform]
        if teacher_args:
            for (field,op,value) in args:
                parts = field.split('.')
                if parts[0] == 'teacher_id':
                    if len(parts) < 2: parts.append('id')
                    teacher_args.append( ('.'.join(parts[1:]),op,value) )
                else:
                    args2 += (field,op,value)
            teacher_ids = self.pool.get('school.teacher').search(cr, uid, teacher_args, context = context)
            args2 += [('teacher_id','in',teacher_ids)]
        else:
            args2 = args

        args3 = [(field,op,value) for (field,op,value) in args2 if field not in ['max_assigned_hours','min_assigned_hours']]
        if len(args3) < len(args2):
            cs_ids = self.search(cr, uid, args3, context = context)
            cd_ids2 = []
            for cs in self.browse(cr, uid, cs_ids):
                date_from = max(context.get('date_from', _MIN_DATETIME) or _MIN_DATETIME, _MIN_DATETIME)
                date_to = min(context.get('date_to', _MAX_DATETIME) or _MAX_DATETIME, _MAX_DATETIME)
                td_ids = self.pool.get('school.teacher_data').search(cr, uid, [('teacher_id','=',cs.teacher_id.id),('iwl_id.classe_id.course_id','=',cs.course_id.id),('limit_to','>',date_from),('limit_from','<',date_to)])

                llista = [(date_from,0)]
                for item in self.pool.get('school.teacher_data').browse(cr, uid, td_ids):
                    llista = posa_interval(llista, max(item.limit_from,date_from), min(item.limit_to,date_to), item.iwl_id.duration)

                minim = min(x[1] for x in llista)
                maxim = max(x[1] for x in llista)
                f = True
                for arg in args:
                    value = arg[0]=='min_assigned_hours' and minim or arg[0]=='max_assigned_hours' and maxim or -1
                    if value < 0: continue
                    if arg[1] == '=':
                        val = eval(value + '==' + arg[2], locals())
                    elif arg[1] in ['<', '>', 'in', 'not in', '<=', '>=', '<>']:
                        val = eval(value + arg[1] + arg[2], locals())
                    f = f and val
                if f:
                    cd_ids2.append(cs.id)
            args3 += [('id','in',cs_ids2)]
        return args3
        
    _columns = {
        'max_assigned_hours': fields.function(_compute_assigned_hours, fnct_search = _search_assigned_hours, type='float', method=True, string='Max assig hours', multi = 'assigned_hours',),
        'min_assigned_hours': fields.function(_compute_assigned_hours, fnct_search = _search_assigned_hours, type='float', method=True, string='Min assig hours', multi = 'assigned_hours',),
        'total_max_assigned_hours': fields.function(_compute_assigned_hours, fnct_search = _search_assigned_hours, type='float', method=True, string='Total Max assig hours', multi = 'assigned_hours',),
        'total_min_assigned_hours': fields.function(_compute_assigned_hours, fnct_search = _search_assigned_hours, type='float', method=True, string='Total Min assig hours', multi = 'assigned_hours',),
    }

school_teacher_course_suitability()

class school_impartition_week_line(osv.osv):
    _name = 'school.impartition_week_line'
    _inherit = 'school.impartition_week_line'
    
    def _compute_needed(self, cr, uid, ids, field_name, arg, context=None):
        ret = {}
        for iwl in self.browse(cr, uid, ids):
            ret[iwl.id] = max(iwl.teachers_needed - len(iwl.teachers),0)
        return ret

    def _get_iwl_ids_from_td_ids(self, cr, uid, ids, context=None):
        ret = set()
        for td in self.browse(cr, uid, ids):
            ret.add(td.iwl_id.id)
        return list(ret)
    
    _columns = {
        'teachers_lack': fields.function(_compute_needed, type='integer', method=True, string='Teachers lack',
                                            store={'school.teacher_data': (_get_iwl_ids_from_td_ids, ['iwl_id', ], 10)},
                                            ),
    }
    
school_impartition_week_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
