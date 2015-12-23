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


class groups_create_agrupation_wizard(osv.osv_memory):
    _name = 'groups.create_agrupation_wizard'
    
    _columns = {
        'group_ids' : fields.many2many('groups.group','groups_create_agrupation_wizard_rel','wizard_id','group_id',string="Groups",),
        'classification_name' : fields.char('Classification name',size=100,help="If no name, no classification."),
        'parent_group_name' : fields.char('Parent group name',size=200,),
        'parent_id' : fields.many2one('groups.group','Parent group',),
    }
    
    def _default_group_ids(self, cr, uid, context=None):
        if not context: context={}
        return context.get('active_ids',[])
    
    def _default_classification_name(self, cr, uid, context=None):
        if not context: context={}
        return self._default_parent_group_name(cr, uid, context=context)

    def _default_parent_group_name(self, cr, uid, context=None):
        if not context: context={}
        return '+'.join([x.name for x in self.pool.get('groups.group').browse(cr, uid, context.get('active_ids',[]))])

    _defaults = {
        'group_ids' : _default_group_ids,
        'classification_name': _default_classification_name,
        'parent_group_name' : _default_parent_group_name,
    }
    
    def create_agrupation(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids):
            vals={}
            classification_id=False
            if obj.classification_name:
                classification_id=self.pool.get('groups.classification').create(cr, uid, {'name': obj.classification_name,})
            vals['children_ids']=[(0,0,{'child_id': x.id, 'direction': 'up', 'classification': classification_id,}) for x in obj.group_ids]
            vals['name']=obj.parent_group_name
            self.write(cr, uid, [obj.id], {'parent_id': self.pool.get('groups.group').create(cr, uid, vals)})
        return {'type': 'ir.actions.act_window_close'}
    
groups_create_agrupation_wizard()
    
