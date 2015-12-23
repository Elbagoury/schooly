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
import sys,os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir,"timed_groups")))
from timed_groups import _MAX_DATETIME, _MIN_DATETIME


class school_teacher_change_hours(osv.osv_memory):
    _name = 'school.teacher_change_hours'

    _columns = {
        'teacher_ids': fields.many2many('school.teacher', 'teacher_change_hours_wizard_rel', 'wizard_id', 'teacher_id', string='Teachers', ),
        'max_hours': fields.float('Max Hours', help='Max hours',),
        'min_hours': fields.float('Min Hours', help='Min hours',),
    }

    _defaults = {
        'teacher_ids': lambda self, cr, uid, context = {}: context.get('active_ids', []),
    }

    def act_cancel(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close'}

    def action_change(self, cr, uid, ids, context=None):
        for item in self.browse(cr, uid, ids):
            teacher_ids = [x.id for x in item.teacher_ids]
            self.pool.get('school.teacher').write(cr, uid, teacher_ids, {'max_week_hours': item.max_hours, 'min_week_hours': item.min_hours})
        return {'type': 'ir.actions.act_window_close'}

school_teacher_change_hours()

class school_teacher_suitability_change(osv.osv_memory):
    _name = 'school.teacher_suitability_change'

    _columns = {
        'teacher_ids': fields.many2many('school.teacher', 'teacher_suitability_change_teacher_rel', 'wizard_id', 'teacher_id', string='Teachers', ),
        'course_ids': fields.many2many('school.course', 'teacher_suitability_change_course_rel', 'wizard_id', 'course_id', string='Courses', ),
        'percentage': fields.float('Percentage', ),
        'max_hours': fields.float('Max Hours', help='Max hours',),
        'min_hours': fields.float('Min Hours', help='Min hours',),
    }

    _defaults = {
        'teacher_ids': lambda self, cr, uid, context = {}: context.get('active_ids', []),
    }

    def act_cancel(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close'}

    def action_change(self, cr, uid, ids, context=None):
        obj = self.pool.get('school.teacher_course_suitability')
        for item in self.browse(cr, uid, ids):
            dicci = {'max_week_hours': item.max_hours, 'min_week_hours': item.min_hours, 'percentage': item.percentage,}
            ids_to_write = []
            for teacher in item.teacher_ids:
                for course in item.course_ids:
                    tcs_ids = obj.search(cr, uid, [('teacher_id', '=', teacher.id), ('course_id', '=', course.id)])
                    if tcs_ids:
                        ids_to_write += tcs_ids
                    else:
                        dicci2 = dict(dicci)
                        dicci2.update({'teacher_id': teacher.id, 'course_id': course.id,})
                        obj.create(cr, uid, dicci2, context = context)
            if ids_to_write:
                obj.write(cr, uid, ids_to_write, dicci, context = context)
        return {'type': 'ir.actions.act_window_close'}

school_teacher_suitability_change()

class school_iwl_change_teachers_number_wizard(osv.osv_memory):
    _name = 'school.iwl_change_teachers_wizard'

    _columns = {
        'iwl_ids': fields.many2many('school.impartition_week_line', 'iwl_block_wizard_rel', 'wizard_id', 'iwl_id', string='IWLs', ),
        'teachers_needed': fields.integer('Teachers needed', ),
        'teachers_recommended': fields.integer('Teachers recommended', ),

    }

    _defaults = {
        'iwl_ids': lambda self, cr, uid, context = {}: [(6,0,context.get('active_ids', []))],
        'teachers_needed': lambda * a: 1,
        'teachers_recommended': lambda * a: 1,
    }

    def act_cancel(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close'}

    def action_block(self, cr, uid, ids, context=None):
        for item in self.browse(cr, uid, ids):
            iwl_ids = [x.id for x in item.iwl_ids]
            self.pool.get('school.impartition_week_line').write(cr, uid, iwl_ids, {'teachers_needed': item.teachers_needed, 'teachers_recommended': item.teachers_recommended})

school_iwl_change_teachers_number_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
