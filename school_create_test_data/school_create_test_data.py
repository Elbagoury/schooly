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

import random
from collections import defaultdict
from openerp.osv import fields,osv

class school_create_test_data(osv.osv_memory):
    _name = 'school.create_test_data'

    _columns = {
        'complexity': fields.selection([('high','High'),('low','Low')], string='Complexity',),
        'num_week_hours_per_teacher': fields.integer('Num Week Hours per Teacher',),
        'lack': fields.integer('Margin total hours',),
        'lack2': fields.integer('Margin course hours',),
    }

    def create_test_data(self, cr, uid, ids, context=None):
        iwl_obj = self.pool.get('school.impartition_week_line')
        t_obj = self.pool.get('school.teacher')
        tcs_obj = self.pool.get('school.teacher_course_suitability')
        r_obj = self.pool.get('school.room')
        for wiz in self.browse(cr, uid, ids):
            lack_by_course = defaultdict(int)
            total_lack = 0
            for iwl in iwl_obj.browse(cr, uid, iwl_obj.search(cr, uid, [('teachers_lack','>',0)])):
                lack_by_course[iwl.classe_id.course_id.id] += iwl.teachers_lack
                total_lack += iwl.teachers_lack
            num_teachers = float(total_lack) / wiz.num_week_hours_per_teacher
            t_ids = []
            for i in range(int(num_teachers)):
                name = 'Teacher Test %s' % i
                login = 'TT%02d' % i
                u_ids = self.pool.get('res.users').search(cr, uid, [('login','=',login)])
                vals = {'teacher_code': 'TT%02d' % i,
                        'max_week_hours': wiz.num_week_hours_per_teacher + wiz.lack,
                        'min_week_hours': max(0, wiz.num_week_hours_per_teacher - wiz.lack),
                        }
                if u_ids:
                    vals.update({'user_id': u_ids[0]})
                else:
                    vals.update({'name': name, 'login': login})
                t_ids += [t_obj.create(cr, uid, vals)]
            tcs_ids = []
            for c_id, lack in lack_by_course.items():
                rl = [random.random() for i in range(len(t_ids))]
                s = sum(rl)
                rl = [ x*lack/s for x in rl ]
                for i in range(len(t_ids)):
                    t_id = t_ids[i]
                    tcs_ids += [tcs_obj.create(cr, uid, {'teacher_id': t_id,
                                             'course_id': c_id,
                                             'percentage': random.randint(0,100),
                                             'max_week_hours': int(rl[i] + wiz.lack2),
                                             'min_week_hours': max(0, int(rl[i] - wiz.lack2)),
                                             })]
            for t_id in t_ids:
                vals = {'name': 'school_demo_tch_%03d' % t_id,
                        'model': 'school.teacher',
                        'module': 'school_create_test_data',
                        'noupdate': True,
                        'res_id': t_id,}
                self.pool.get('ir.model.data').create(cr, uid, vals)
            for tcs_id in tcs_ids:
                vals = {'name': 'school_demo_tcs_%03d' % tcs_id,
                        'model': 'school.teacher_course_suitability',
                        'module': 'school_create_test_data',
                        'noupdate': True,
                        'res_id': tcs_id,}
                self.pool.get('ir.model.data').create(cr, uid, vals)
                
        return True
        

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
