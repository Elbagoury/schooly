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


class groups_change_assignation_dates_wizard(osv.osv_memory):
    _name = 'groups.change_assignation_dates.wizard'
    
    _columns = {
        'ga_ids' : fields.many2many('groups.group_assignation','groups_change_assignation_dates_wizard_rel','wizard_id','ga_id',string="Assignations",),
        'datetime_from' : fields.datetime('Date and Time from',),
        'change_from' : fields.boolean('Change from',), 
        'datetime_to' : fields.datetime('Date and Time to',),
        'change_to' : fields.boolean('Change to',), 
    }
    
    def _get_ga_ids_default(self, cr, uid, context = None):
        return context.get('active_ids',[])
    
    _defaults = {
        'ga_ids' : _get_ga_ids_default,
    }
    
    def change_dates(self, cr, uid, ids, context=None):
        for wizard in self.browse(cr, uid, ids):
            ga_obj = self.pool.get('groups.group_assignation')
            dicci = {}
            if wizard.change_from:
                dicci['datetime_from'] = wizard.datetime_from
            if wizard.change_to:
                dicci['datetime_to'] = wizard.datetime_to
            if dicci:
                ga_obj.write(cr, uid, [x.id for x in wizard.ga_ids], dicci, context = context)
        return {'type': 'ir.actions.act_window_close'}
    
groups_change_assignation_dates_wizard()
    
