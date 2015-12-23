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

import bisect
from datetime import datetime

import time
from openerp.osv import fields ,orm, osv
from openerp.tools.translate import _

class school_impartition_week_line(osv.osv):
    _name = 'school.impartition_week_line'
    _inherit = 'school.impartition_week_line'

    def _compute_blocked(self, cr, uid, ids, field_name, arg, context=None):
        ret = {}
        for iwl in self.browse(cr, uid, ids):
            blocked = (len(iwl.teachers) > 0)
            ret[iwl.id] = {'teachers_lack': max(0, iwl.teachers_needed - len(iwl.teachers)), }
            for td in iwl.teachers:
                blocked &= td.blocked
                if not blocked: break
            ret[iwl.id]['teachers_blocked'] = blocked
        return ret

    def _get_iwl_ids_from_td_ids(self, cr, uid, ids, context=None):
        ret = set()
        for td in self.browse(cr, uid, ids):
            ret.add(td.iwl_id.id)
        return list(ret)


    _columns = {
        'teachers_blocked': fields.function(_compute_blocked, type='boolean', method=True, string='Blocked', multi='teachers', help='No teachers changes allowed',
                                            store={'school.teacher_data': (_get_iwl_ids_from_td_ids, ['blocked'], 10)},
                                            ),
        'iwl_group': fields.char('IWL group', size=30, help="Group name for IWL's with same teacher", ),
        'teachers_needed': fields.integer('Teachers needed', ),
        'teachers_recommended': fields.integer('Teachers recommended', ),
        'teachers_lack': fields.function(_compute_blocked, type='integer', method=True, string='Teachers lack', multi='teachers',
                                            store={'school.teacher_data': (_get_iwl_ids_from_td_ids, ['iwl_id', ], 10)},
                                            ),
    }

    _defaults = {
        'teachers_needed': lambda * a: 1,
        'teachers_recommended': lambda * a: 1,
    }

    _sql_constraints = [
        ('needed_and_recommended_check', 'CHECK (teachers_needed <= teachers_recommended)', "The number required should be smaller than the recommended"),
        ('needed_not_negative', 'CHECK (teachers_needed >= 0)', "The number required should be not negative"),
        ]

school_impartition_week_line()

class school_teacher_data(osv.osv):
    _name = 'school.teacher_data'
    _inherit = 'school.teacher_data'

    _columns = {
        'blocked': fields.boolean('Blocked', help='No teachers changes allowed',),
    }

school_teacher_data()

class school_teachers_solution(osv.osv):
    _name = 'school.teachers_solution'

school_teachers_solution()

class school_teacher_iwl_solution(osv.osv):
    _name = 'school.teacher_iwl_solution'
    
    _columns = {
        'solution_id': fields.many2one('school.teachers_solution', 'Solution', ondelete='cascade', required=True, ),
        'iwl_id': fields.many2one('school.impartition_week_line', 'IWL', ondelete='cascade', required=True, ),
        'teacher_id': fields.many2one('school.teacher', 'Teacher', ondelete='cascade', required=True, ),
        'value': fields.float('Value', ),
    }
    
school_teacher_iwl_solution()

class school_teachers_solution(osv.osv):
    _name = 'school.teachers_solution'
    
    def _compute(self, cr, uid, ids, field_name, arg, context=None):
        return sum([x.percentage for x in self.browse(cr, uid, ids, context=context)]) / len(ids)
        
    _columns = {
        'name': fields.char('Name', size=100, ),
        'created': fields.datetime('Created', ),
        'total_hours': fields.float('Total hours', ),
        'total_assigned': fields.float('Total assigned', ),
        'teacher_iwl_ids': fields.one2many('school.teacher_iwl_solution', 'solution_id', 'Solution', ),
        'value': fields.float('Value', ),
        'acabat': fields.char('Acabat', help='Percentage of search'),
    }
    
    _defaults = {
        'created': lambda * a: datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
    }
school_teachers_solution()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
