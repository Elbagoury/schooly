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

import sys,os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir)))

from timed_groups import selection_methods

class groups_create_classification_wizard(osv.osv_memory):
    _name = 'groups.create_classification_wizard'

    _columns = {
        'parent_id' : fields.many2one('groups.group','Parent group',require=True,),
        'classification_name' : fields.char('Classification name',size=100,require=True,),
        'classification_method' : fields.selection(selection_methods, string="Method",),
        'groups_number' : fields.integer('Children groups number',require=True,),
        'group_ids' : fields.many2many('groups.group','groups_create_classification_wizard_rel','wizard_id','group_id',string="Groups",),
    }
    
    def _default_parent_id(self, cr, uid, context=None):
        if not context: context={}
        return context.get('active_id',False)
    
    _defaults = {
        'parent_id' : _default_parent_id,
    }
    
    def create_classification(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids):
            vals={'children_ids': []}
            classification_id=self.pool.get('groups.classification').create(cr, uid, {'name': obj.classification_name, 'method': obj.classification_method,})
            group_ids=[]
            for c in range(obj.groups_number):
                child_id=self.pool.get('groups.group').create(cr, uid, {'name': obj.classification_name+'#'+str(c+1),})
                group_ids.append( child_id )
                vals['children_ids'].append( (0,0,{'child_id': child_id, 'direction': 'down', 'classification': classification_id, }) )
            self.pool.get('groups.group').write(cr, uid, [obj.parent_id.id], vals)
            self.write(cr, uid, [obj.id], {'group_ids': [(6,0,group_ids)],})
            self.pool.get('groups.classification').run_classify(cr, uid, [classification_id], context = context)
        return True
    
groups_create_classification_wizard()
    
