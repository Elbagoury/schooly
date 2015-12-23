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

import os
from subprocess import Popen, PIPE
import pickle
import tempfile

from openerp.osv import fields, orm, osv
from openerp.tools.translate import _
from school_assign_teachers_kernel import assigna_classes, assigna_cursos, agrupa_cursos_i_professors
from collections import defaultdict

COMMAND_COMPILED = False

class school_solution_data_by_course(osv.osv_memory):
    _name = 'school.solution.data_by_course'
    
    _columns = {
        'solution_id' : fields.many2one('school.create_solutions','Solution'),
        'course_id' : fields.many2one('school.course','Course',),
        'classes_hours' : fields.float('Classes Hours'),
        'max_hours' : fields.float('Max hours'),
        'min_hours' : fields.float('Min hours'),
    }
    
school_solution_data_by_course()

class school_create_solutions_wizard(osv.osv_memory):
    _name = 'school.create_solutions'
    
    _columns = {
        'number_max_solutions': fields.integer('Max. solutions', help="Maximum number of solutions to return", required=True,),
        'total_classes_hours': fields.float('Total classes hours', readonly=True, ),
        'total_max_hours': fields.float('Max teachers hours', readonly=True, ),
        'total_min_hours': fields.float('Min teachers hours', readonly=True, ),
        'data_by_course' : fields.one2many('school.solution.data_by_course', 'solution_id', readonly=True, ),
        'time_to_compute' : fields.integer('Time (min)', help='Maxixum time to compute in minutes', required=True,),
        'num_proc': fields.integer('Num proc', help='Number of processors will work',required=True,),
        'afina': fields.float('Afina', required=True, help='How many more teachers candidates over needed to compute availability'),
        'deep_only_one': fields.integer('Deep only one', required=True,),
    }

    def _default_total_classes_hours(self, cr, uid, context=None):
        (total_classes_hours, classes_data_by_course) = self.get_classes_data_by_course(cr, uid)
        return total_classes_hours

    def _default_total_max_hours(self, cr, uid, context=None):
        (total_classes_hours, classes_data_by_course) = self.get_classes_data_by_course(cr, uid)
        (total_teachers_hours, data_by_teacher, teachers_data_by_course) = self.get_teachers_data_by_course(cr, uid, classes_data_by_course.keys())
        return total_teachers_hours['pool_max']

    def _default_total_min_hours(self, cr, uid, context=None):
        (total_classes_hours, classes_data_by_course) = self.get_classes_data_by_course(cr, uid)
        (total_teachers_hours, data_by_teacher, teachers_data_by_course) = self.get_teachers_data_by_course(cr, uid, classes_data_by_course.keys())
        return total_teachers_hours['pool_min']

    def _default_data_by_course(self, cr, uid, context=None):
        (total_classes_hours, classes_data_by_course) = self.get_classes_data_by_course(cr, uid)
        (total_teachers_hours, data_by_teacher, teachers_data_by_course) = self.get_teachers_data_by_course(cr, uid, classes_data_by_course.keys())
        ret = []
        for (course_id, classes_data) in classes_data_by_course.items():
            tdc = teachers_data_by_course.get(course_id,{'pool_max': 0, 'pool_min': 0,})
            ret.append({'course_id': course_id,
                        'classes_hours': classes_data['duration'],
                        'max_hours': tdc['pool_max'],
                        'min_hours': tdc['pool_min'],})

        return ret
            
    _defaults = {
        'total_classes_hours': _default_total_classes_hours,
        'total_max_hours': _default_total_max_hours,
        'total_min_hours': _default_total_min_hours,
        'data_by_course' : _default_data_by_course,
        'time_to_compute' : lambda *a: 5,
        'num_proc': lambda *a: 4,
        'afina': lambda *a: 7.0,
        'deep_only_one': lambda *a: 1,
    }

    def get_teachers_hours_blocked(self, cr, uid):
        obj_td = self.pool.get('school.teacher_data')
        total_hours = 0
        hours_by_teacher = defaultdict(int)
        hours_by_course_and_teacher = defaultdict(int)
        
        td_ids = obj_td.search(cr, uid, [('blocked', '=', True)])
        for td in obj_td.browse(cr, uid, td_ids):
            total_hours += td.iwl_id.duration
            hours_by_teacher[td.teacher_id.id] += td.iwl_id.duration
            course_id = td.iwl_id.classe_id.course_id.id
            key = (course_id, td.teacher_id.id)
            hours_by_course_and_teacher[key] += td.iwl_id.duration
        return (total_hours, hours_by_teacher, hours_by_course_and_teacher)
        
    def get_classes_data_by_course(self, cr, uid):
        obj_iwl = self.pool.get('school.impartition_week_line')
        iwl_ids = obj_iwl.search(cr, uid, [('teachers_blocked', '=', False), ])
        total_hours = 0
        ret = {}
        classes = {}
        for iwl in obj_iwl.browse(cr, uid, iwl_ids):
            classe_id = iwl.classe_id.id
            course_id = iwl.classe_id.course_id.id
            classe_key = (classe_id, iwl.iwl_group)
            if not course_id in ret:
                ret[course_id] = {'duration': 0, 'classes': []}
                classes[course_id] = {}
            if (classe_id, iwl.iwl_group) not in classes[course_id]:
                classes[course_id][classe_key] = {'duration': 0, 'iwls': []}
            classes[course_id][classe_key]['duration'] += iwl.duration
            classes[course_id][classe_key]['iwls'].append(iwl.id)
            classes[course_id][classe_key]['id'] = "%s,%s" % classe_key
            ret[course_id]['duration'] += iwl.duration
            total_hours += iwl.duration
        for course_id in ret.keys():
            ret[course_id]['classes'] = list(classes[course_id].values())
        return (total_hours, ret)

    

    def get_teachers_data_by_course(self, cr, uid, courses):
        total_hours = {'pool_max': 0, 'pool_min': 0}
        
        (total_blocked_hours,
        blocked_hours_by_teacher,
        blocked_hours_by_course_and_teacher) = self.get_teachers_hours_blocked(cr, uid)
        
        # recupera de la BD les dades d'idoneitat, hores mínimes i màximes per curs 
        obj_tcs = self.pool.get('school.teacher_course_suitability')
        teachers_suitability_ids = obj_tcs.search(cr, uid, [('course_id', 'in', list(courses))])

        teacher_ids = set()
        teachers_data_by_course = defaultdict(lambda:{'pool_max':0, 'pool_min': 0, 'list': [],})
        
        for item in obj_tcs.browse(cr, uid, teachers_suitability_ids):
            course_id = item.course_id.id
            teacher_ids.add(item.teacher_id.id)
            key = (course_id, item.teacher_id.id)
            max_hours = max(0, item.max_week_hours - blocked_hours_by_course_and_teacher.get(key, 0))
            min_hours = max(0, item.min_week_hours - blocked_hours_by_course_and_teacher.get(key, 0))
            teachers_data_by_course[course_id]['list'].append ({
                                                               'percentage': item.percentage, 
                                                               'id': item.teacher_id.id,
                                                               'pool_max': max_hours,
                                                               'pool_min': min_hours, })
            teachers_data_by_course[course_id]['pool_max'] += max_hours
            teachers_data_by_course[course_id]['pool_min'] += min_hours

        obj_t = self.pool.get('school.teacher')
        data_by_teacher = {}
        for x in obj_t.browse(cr, uid, obj_t.search(cr, uid, [('id','in',list(teacher_ids))])):
            max_hours = max(0, x.max_week_hours - blocked_hours_by_teacher.get(x.id, 0))
            min_hours = max(0, x.min_week_hours - blocked_hours_by_teacher.get(x.id, 0))
            if max_hours > 0:
                data_by_teacher[x.id] = {
                    'pool_max': max_hours,
                    'pool_min': min_hours,
                }
                total_hours['pool_max'] += max_hours
                total_hours['pool_min'] += min_hours
        
        return (total_hours, data_by_teacher, teachers_data_by_course)

    def act_cancel(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close'}
        
    def passa_sols_a_bd(self, cr, uid, llista_de_solucions, 
                        total_classes_hours, classes_data_by_course,
                        teachers_data_by_course, acabat, context=None):
        ts_obj = self.pool.get('school.teachers_solution')
        ret = []
        # Passar solucions a base de dades
        for value, assignacio_by_course in llista_de_solucions:
            vals = {'value': value,
                    'total_hours': total_classes_hours,
                    'acabat': "%s%%" % (acabat * 100),}
            sol_id = ts_obj.create(cr, uid, vals)
            ret.append(sol_id)
            total_assigned = 0
            for (course_id, assignacio) in assignacio_by_course.items():
                for i in range(len(assignacio)):
                    classe = classes_data_by_course[course_id]['classes'][i]
                    total_assigned += classe['duration']
                    for iwl_id in classe['iwls']:
                        value = [  x['percentage']
                                    for x in teachers_data_by_course[course_id]['list']
                                    if x['id'] == assignacio[i]  ][0]
                        self.pool.get('school.teacher_iwl_solution').create(cr, uid,
                                {'solution_id': sol_id, 'iwl_id': iwl_id,
                                 'teacher_id': assignacio[i], 'value': value})
            ts_obj.write(cr, uid, [sol_id], {'total_assigned': total_assigned, })
        return ret
        
    def create_solutions(self, cr, uid, ids, context=None):
        
        sols_from_wizard = []
        create_solutions_wizard = self.browse(cr, uid, ids[0])
        
        time_available = create_solutions_wizard.time_to_compute * 60
        number_max_solutions = create_solutions_wizard.number_max_solutions
        (total_classes_hours, classes_data_by_course) = self.get_classes_data_by_course(cr, uid)
        (total_teachers_hours, data_by_teacher, teachers_data_by_course) = self.get_teachers_data_by_course(cr, uid, classes_data_by_course.keys())
        
        errors = []
        if total_classes_hours > total_teachers_hours['pool_max']:
            errors.append( _('Total hours to assign exceeds teachers disponibility.') )
        for (course_id, classe_data) in classes_data_by_course.items():
            tdc = teachers_data_by_course.get(course_id, {'pool_max': 0, 'pool_min': 0,})
            if classe_data['duration'] > tdc['pool_max']:
                errors.append( _('Total hours to assign exceeds teachers disponibility by course with id %s.') % (course_id,) )
        if errors:
            raise orm.except_orm('Error!', '\n'.join(errors))

        v = {'total_classes_hours' : total_classes_hours,
             'classes_data_by_course': classes_data_by_course,
             'total_teachers_hours': total_teachers_hours,
             'data_by_teacher': data_by_teacher,
             'teachers_data_by_course': dict(teachers_data_by_course),
             'max_solutions': number_max_solutions,
             'num_proc': create_solutions_wizard.num_proc,
             'time_available': time_available,
             'afina': create_solutions_wizard.afina,
             'deep_only_one': create_solutions_wizard.deep_only_one,
             }
        vals = {'input': pickle.dumps(v), # passa parametres
                'number_max_solutions': number_max_solutions,
                'time_to_compute': time_available,
                'num_proc': create_solutions_wizard.num_proc,
                'afina': create_solutions_wizard.afina,
                'deep_only_one': create_solutions_wizard.deep_only_one,
                }
        res_id = self.pool.get('school.creating_solutions').create(cr, uid, vals, context=context)

        return {
            'name': _("Executed solutions"),
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'school.creating_solutions',
            'context': context,
            'res_id': res_id,
            'type': 'ir.actions.act_window',
        }

class school_creating_solutions(osv.osv):
    _name = 'school.creating_solutions'
    
    def _get_value(self, cr, uid, ids, field_name, args, context=None):
        ret = {}
        for item in self.browse(cr, uid, ids, context=context):
            ret[item.id] = {}
            if item.state == 'waiting':
                ret[item.id]['seconds'] = 0
            else:
                dti = datetime.strptime(item.init,'%Y-%m-%d %H:%M:%S')
                if item.state == 'done':
                    dte = datetime.strptime(item.end,'%Y-%m-%d %H:%M:%S')
                    ret[item.id]['seconds'] = (dte-dti).total_seconds()
                else:
                    ret[item.id]['seconds'] = (datetime.now() - dti).total_seconds()
            ret[item.id]['value'] = max([0] + [x.value for x in item.solution_ids])
            ret[item.id]['acabat'] = item.solution_ids and item.solution_ids[0].acabat or 0
        return ret
        
    _columns = {
        'input_file': fields.char('Input file',),
        'input': fields.text('Input'),
        'output_file': fields.char('Output file',),
        'solution_ids': fields.many2many('school.teachers_solution', string='Solutions'),
        'created': fields.datetime('Waiting since',),
        'init': fields.datetime('Initiated'),
        'end': fields.datetime('Ended'),
        'number_max_solutions': fields.integer('Num Max Solutions'),
        'time_to_compute': fields.integer('Time to compute', help="In seconds"),
        'num_proc': fields.integer('Num processors'),
        'afina': fields.float('Afina', help='How many more teachers candidates over needed to compute availability'),
        'deep_only_one': fields.integer('Deep Only One'),
        'value': fields.function(_get_value, type='float', string='Max value', multi='dades'),
        'acabat': fields.function(_get_value, type='char', string='Search completed', multi='dades'),
        'seconds': fields.function(_get_value, type='integer', string='Seconds computing', multi='dades'),      
        'state': fields.selection([('waiting','Waiting'),('running','Running'),('done','Done')], string='State', readonly=True,),
    }
    
    _defaults = {
        'created': lambda *a: datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'),
        'num_proc': lambda *a: 4,
        'state': lambda *a: 'waiting',
    }

    _order = "created"
    
    def activate(self, cr, uid, ids, context=None):
        self.activate_search(cr, uid, context=context)
        return True
        
    def reactivate(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'waiting',}, context=context)
        return True
        
    def teacher_assignation_running(self, cr, uid, ids, context=None):
        for item in self.browse(cr, uid, ids):
            if os.path.isfile(item.output_file) and os.stat(item.output_file).st_size > 0:
                v = pickle.load( open(item.input_file, "rb") )
                acabat, t, llista_de_solucions = pickle.load( open(item.output_file, "rb") )
                
                sols_from_wizard = self.pool.get('school.create_solutions').passa_sols_a_bd(cr, uid,
                                            llista_de_solucions,
                                            v['total_classes_hours'],
                                            v['classes_data_by_course'],
                                            v['teachers_data_by_course'],
                                            acabat,
                                            context=context)
                vals = {'state': 'done',
                        'end': datetime.strftime(t, '%Y-%m-%d %H:%M:%S'),
                        'solution_ids': [(6,0,sols_from_wizard)]}
                self.write(cr, uid, [item.id], vals)
    
    def teacher_assignation_waiting(self, cr, uid, ids, context=None):
        for item in self.browse(cr, uid, ids):
            input_file = tempfile.NamedTemporaryFile(delete=False)
            output_file = tempfile.NamedTemporaryFile(delete=False)
            input_file.write(item.input)
            if COMMAND_COMPILED:
                command = [os.path.dirname(os.path.abspath(__file__))+os.sep+'school_assign_teachers_kernel.exe']
            else:
                command = ['python',os.path.dirname(os.path.abspath(__file__))+os.sep+'school_assign_teachers_kernel.py']
            proc = Popen(command+[
                          input_file.name,
                          output_file.name,],)
            vals = {'state': 'running',
                    'input_file': input_file.name,
                    'output_file': output_file.name,
                    'init': datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
                    }
            self.write(cr, uid, [item.id], vals)

    def activate_search(self, cr, uid, context=None):
        r_ids = self.search(cr, uid, [('state','=','running')], limit=1)
        if r_ids:
            self.teacher_assignation_running(cr, uid, r_ids,context=context)
        else:
            w_ids = self.search(cr, uid, [('state','=','waiting')], limit=1, order='created')
            self.teacher_assignation_waiting(cr, uid, w_ids, context=context)
            
class school_apply_teacher_solution(osv.osv_memory):
    _name = 'school.apply_teacher_solution'

    _columns = {
        'solution_ids': fields.many2many('school.teachers_solution', 'teacher_solution_apply_rel', 'wizard_id', 'solution_id', string='Solutions', ),
    }

    _defaults = {
        'solution_ids': lambda self, cr, uid, context = {}: context.get('active_ids', []),
    }

    def act_cancel(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close'}

    def action_change(self, cr, uid, ids, context=None):
        obj_td = self.pool.get('school.teacher_data')
        ids_td_created = []
        ids_to_unlink = []
        for item in self.browse(cr, uid, ids):
            iwls_cleaned = set()
            for solution in item.solution_ids:
                for teacher_iwl in solution.teacher_iwl_ids:
                    iwl_id = teacher_iwl.iwl_id.id
                    if iwl_id not in iwls_cleaned:
                        iwls_cleaned.add(iwl_id)
                        ids_to_unlink += obj_td.search(cr, uid, [('iwl_id','=',iwl_id),('blocked','=',False)])
                    ids_td_created.append( obj_td.create(cr, uid, {'iwl_id': iwl_id, 'teacher_id': teacher_iwl.teacher_id.id, 'title': 'needed'}) )
        obj_td.unlink(cr, uid, ids_to_unlink)

        return  {
            'domain': [('id','in',ids_td_created),],
            'name': _("Assignations created by the apply solutions wizard"),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'school.teacher_data',
            'context': context,
            'type': 'ir.actions.act_window',
        }
school_apply_teacher_solution()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
