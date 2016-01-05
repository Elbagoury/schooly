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
import collections
import time
from openerp.osv import fields ,orm, osv
from openerp.tools.translate import _
import glob
import os
import tempfile
import base64
from subprocess import Popen, PIPE
from lxml import etree


class school_teachers_solution(osv.osv):
    _inherit = 'school.teachers_solution'
    
    _columns = {
        'fet_state': fields.selection([('none','None'),('waiting','Waiting'),('running','Running'),('done','Done'),], string='FET state',),
        'output_dir': fields.char('Output dir'),
        'fet_file': fields.char('FET input file'),
        'fet_result': fields.text('Fet result'),
    }
    
    _defaults = {
        'fet_state': lambda *a: 'none',
    }
    
class school_create_solutions_wizard(osv.osv_memory):
    _inherit = 'school.create_solutions'
    
    _columns = {
        'fet_computing': fields.boolean('Timetabling computing',),
    }
    
    _defaults = {
        'fet_computing': lambda *a: True,
    }

    def passa_sols_a_bd(self, cr, uid, llista_de_solucions, 
                        total_classes_hours, classes_data_by_course,
                        teachers_data_by_course, acabat, context=None):
        if not context:
            context = {}
        ts_obj = self.pool.get('school.teachers_solution')
        lsup = super(school_create_solutions_wizard, self)
        ret = lsup.passa_sols_a_bd(cr, uid, llista_de_solucions, 
                        total_classes_hours, classes_data_by_course,
                        teachers_data_by_course, acabat, context=context)
        if context.get('fet_computing'):
            ts_obj.write(cr, uid, ret, {'fet_state': 'waiting',})
        return ret

    def create_solutions(self, cr, uid, ids, context=None):
        ret = super(school_create_solutions_wizard, self).create_solutions(cr, uid, ids, context=context)
        creating_id = ret['res_id']
        item = self.browse(cr, uid, ids[0])
        if item.fet_computing:
            self.pool.get('school.creating_solutions').write(cr, uid, [creating_id], {'fet_computing': True,})
        return ret

class school_creating_solutions(osv.osv):
    _inherit = 'school.creating_solutions'
    
    def teacher_assignation_running(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        item = self.browse(cr, uid, ids[0])
        context2 = dict(context)
        if item.fet_computing:
            context2.update({'fet_computing': True,})
        super(school_creating_solutions, self).teacher_assignation_running(cr, uid, ids, context=context2)
        
    _columns = {
        'fet_computing': fields.boolean('Timetabling computing',),
    }

    def activate_search(self, cr, uid, context=None):
        if not context:
            context = {}
        ts_obj = self.pool.get('school.teachers_solution')
        fe_obj = self.pool.get('school.fet.export')
        r_ids = ts_obj.search(cr, uid, [('fet_state','=','running')], limit=1)
        if r_ids:
            ts = ts_obj.browse(cr, uid, r_ids[0])
            file_pattern = ts.output_dir + os.sep + "timetables" + os.sep + \
                            os.path.basename(ts.fet_file) + os.sep + "*.fet"
            fns = glob.glob(file_pattern)
            if fns:
                d = etree.parse(fns[0])
                ts_obj.write(cr, uid, r_ids, {'fet_result': etree.tostring(d), 'fet_state': 'done',})
        else:
            w_ids = ts_obj.search(cr, uid, [('fet_state','=','waiting')], limit=1)
            if w_ids:
                ts = ts_obj.browse(cr, uid, w_ids[0])
                iwl_ids = list(set(iwl_sol.iwl_id.id for iwl_sol in ts.teacher_iwl_ids))
                vals = {
                    'iwl_ids': [(6,0,iwl_ids)],
                }
                wiz_id = self.pool.get('school.fet.export').create(cr, uid, vals, context=context)
                context2 = context.copy()
                context2['tch_assig_id'] = ts.id
                fe_obj.generate_file(cr, uid, [wiz_id], context=context2)
                fe = fe_obj.browse(cr, uid, wiz_id, context=context)
                f = tempfile.NamedTemporaryFile(delete=False)
                f.write(base64.decodestring(fe.file))
                output_dir = tempfile.mkdtemp()
                ts_obj.write(cr, uid, w_ids, {'output_dir': output_dir,
                                              'fet_file': f.name,
                                              'fet_state': 'running'})
                command = ['/usr/bin/xvfb-run','/usr/bin/fet',]
                params = ['--inputfile=%s' % f.name,
                                      '--outputdir=%s' % output_dir,]
                print " ".join(command + params)
                proc = Popen(command + params)
        return super(school_creating_solutions, self).activate_search(
                                    cr, uid, context=context)

class school_fet_export(osv.osv_memory):
    _inherit = 'school.fet.export'
    
    def prepara_activitats(self, cr, uid, fex, context=None):
        if not context:
            context = {}
        
        tch_by_iwl = collections.defaultdict(list)
        if 'tch_assig_id' in context:
            tch_assig = self.pool.get('school.teachers_solution').browse(cr, uid, context['tch_assig_id'])
            for ia in tch_assig.teacher_iwl_ids:
                tch_by_iwl[ia.iwl_id.id].append((ia.teacher_id.id, ia.teacher_id.name))
            
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
            #### Afegit
            if tch_by_iwl:
                for tch_id, tch_name in tch_by_iwl[iwl.id]:
                    teacher_key="%s,%s" % (tch_id, tch_name)
                    teacher_ids.add(tch_id)
                    teachers.add(teacher_key)
                    activity['teachers'].add(teacher_key)                    
            else:
            #### Fi afegit
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

class school_apply_teacher_solution(osv.osv_memory):
    _inherit = 'school.apply_teacher_solution'

    def action_change(self, cr, uid, ids, context=None):
        ret = super(school_apply_teacher_solution, self).action_change(cr, uid, ids, context=context)
        
        wiz = self.browse(cr, uid, ids[0], context=None)
        cadna = wiz.solution_ids[0].fet_result

        vals = {'file':base64.encodestring(cadna),}
        wiz2_id = self.pool.get('school.fet.import').create(cr, uid, vals, context=context)
        self.pool.get('school.fet.import').import_file(cr, uid, [wiz2_id], context=context)
        
        return ret

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
