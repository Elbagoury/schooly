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
from openerp.tools.translate import _


class school_create_session(osv.osv_memory):
    _name = 'school.create_session'

    _columns = {
        'name' : fields.char('Suffix', size = 200, help="Based in offer name", required=True,),
        'offer_ids' : fields.many2many('school.offer', string='Offers',required=True,help="Offers for the session"),
        'date_from' : fields.date('Date from', required=True,),
        'date_to' : fields.date('Date to', required=True,),
        'lines': fields.integer('Lines', required=True,),
    }

    _defaults = {
        'offer_ids' : lambda self, cr, uid, context={} : context.get('active_ids'),
        'lines': lambda *a: 1,
    }

    def _check_dates(self, cr, uid, ids, context=None):
        return [ x for x in self.browse(cr, uid, ids, context=context) if x.date_to > x.date_from ]

    _constraints = [(_check_dates, _("To date must be greater than From date"), ['date_from','date_to']),]

    def action_cancel(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close'}

    def action_apply(self, cr, uid, ids, context=None):
        g_obj = self.pool.get('groups.group')
        cls_obj = self.pool.get('groups.classification')
        r_obj = self.pool.get('school.room')
        for item in self.browse(cr, uid, ids, context=context):
            for offer in item.offer_ids:
                name = "%s %s" % (offer.name, item.name)
                code = "%s %s" % (offer.code, item.name)
                parent_id = g_obj.create(cr, uid, {'name': code})
                vals = {'name': name, 'offer': offer.id,
                        'code': code, 'group_id': parent_id,
                        'date_from': item.date_from, 'date_to': item.date_to}
                self.pool.get('school.session').create(cr, uid, vals)
                if item.lines > 1:
                    g_l = []
                    vals = {'name': name,}
                    cls_id = cls_obj.create(cr, uid, vals)
                    for line in range(item.lines):
                        vals = {'name': "%s %s" % (name, line),
                                'parent_ids': [(0,0,{'parent_id': parent_id, 'classification': cls_id,})],}
                        g_l.insert(line, g_obj.create(cr, uid, vals))
                conv_g = {}
                for course in offer.course_ids:
                    vals = {'name': "%s CONV %s" % (code, course.code),
                            'parent_ids': [(0,0,{'parent_id': parent_id,})]}
                    conv_g[course.id] = g_obj.create(cr, uid, vals)
                for line in range(item.lines):
                    for course in offer.course_ids:
                        cls_name = "%s-%s" % (course.code, item.name)
                        r_obj.create(cr, uid, {'name': cls_name,})
                        if item.lines > 1:
                            classe_name = "%s-%s %s" % (course.code, item.name, line)
                        else:
                            classe_name = cls_name
                        p_id = item.lines > 1 and g_l[line] or parent_id
                        vals = {'name': classe_name,}
                        cls_id = cls_obj.create(cr, uid, vals)
                        vals = {'name': classe_name,
                                'parent_ids': [(0,0,{'parent_id': p_id, 'classification': cls_id,}),
                                               (0,0,{'parent_id': conv_g[course.id],  'classification': cls_id,}),
                                               ],}
                        child_id = g_obj.create(cr, uid, vals)
                        vals = {'name': classe_name,
                                'course_id': course.id,
                                'date_from': item.date_from,
                                'date_to': item.date_to,
                                'group_id': child_id}
                        self.pool.get('school.classe').create(cr, uid, vals)
        return {'type': 'ir.actions.act_window_close'}

school_create_session()
