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

from openerp.osv import fields,osv

class school_teacher(osv.osv):
    _name = 'school.teacher'
    _inherit = 'school.teacher'

    _columns = {
        'max_week_hours': fields.float('Max hours', help="Max. week hours to help assign "),
        'min_week_hours': fields.float('Min hours', help="Min. week hours to help assign "),
    }

    _sql_constraints = [
        ('max_greater_or_equal_than_min', 'CHECK (max_week_hours >= min_week_hours)', "Max hours should be greater or equal than min hours"),
        ('min_hours_not_negative', 'CHECK (min_week_hours >= 0)', "Max hours should be not negative"),
        ]

school_teacher()

class school_teacher_course_suitability(osv.osv):
    _name = 'school.teacher_course_suitability'
        
    _columns = {
        'teacher_id': fields.many2one('school.teacher', 'Teacher', ondelete='cascade', ),
        'course_id': fields.many2one('school.course', 'Course', ondelete='cascade', ),
        'percentage': fields.float('Percentage', help='Percentage suitability', ),
        'max_week_hours': fields.float('Max hours', help="Max. week hours for this course"),
        'min_week_hours': fields.float('Min hours', help="Min. week hours for this course"),
        'total_max_hours': fields.related('teacher_id', 'max_week_hours', type='float', string="Total max for all week", ),
        'total_min_hours': fields.related('teacher_id', 'min_week_hours', type='float', string="Total min for all week", ),
    }

    _sql_constraints = [
        ('teacher_course_unique', 'UNIQUE(teacher_id,course_id)', 'Only one register for the same teacher and course'),
        ('max_greater_or_equal_than_min', 'CHECK(max_week_hours >= min_week_hours)', "Max hours should be greater or equal than min hours"),
        ('min_hours_not_negative', 'CHECK(min_week_hours >= 0)', "Max hours should be not negative"),
        ('percentage_between_0_and_100', 'CHECK(percentage BETWEEN 0 AND 100)', "Percentage should be between 0 and 100"),
        ]

school_teacher_course_suitability()

class school_impartition_week_line(osv.osv):
    _name = 'school.impartition_week_line'
    _inherit = 'school.impartition_week_line'
    
    _columns = {
        'teachers_needed': fields.integer('Teachers needed', ),
        'teachers_recommended': fields.integer('Teachers recommended', ),
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

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
