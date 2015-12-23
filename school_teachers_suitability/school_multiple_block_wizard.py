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

from openerp.osv import fields, orm, osv
from openerp.tools.translate import _


class school_block_iwl_wizard(osv.osv_memory):
    _name = 'school.block_iwl_wizard'

    _columns = {
        'iwl_ids': fields.many2many('school.impartition_week_line', 'iwl_block_wizard_rel', 'wizard_id', 'iwl_id', string='IWLs', ),
        'block': fields.boolean('Block', help='Block, yes or no',),

    }

    _defaults = {
        'iwl_ids': lambda self, cr, uid, context = {}: [(6,0,context.get('active_ids', []))],
    }

    def act_cancel(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close'}

    def action_block(self, cr, uid, ids, context=None):
        for item in self.browse(cr, uid, ids):
            iwl_ids = [x.id for x in item.iwl_ids]
            td_ids = self.pool.get('school.teacher_data').search(cr, uid, [('iwl_id', 'in', iwl_ids)])
            self.pool.get('school.teacher_data').write(cr, uid, td_ids, {'blocked': item.block, })
        return True

school_block_iwl_wizard()

class school_block_td_wizard(osv.osv_memory):
    _name = 'school.block_td_wizard'

    _columns = {
        'td_ids': fields.many2many('school.teacher_data', 'td_block_wizard_rel', 'wizard_id', 'td_id', string='Teacher Data', ),
        'block': fields.boolean('Block', help='Block, yes or no',),

    }

    _defaults = {
        'td_ids': lambda self, cr, uid, context = {}: [(6,0,context.get('active_ids', []))],
    }

    def act_cancel(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close'}

    def action_block(self, cr, uid, ids, context=None):
        for item in self.browse(cr, uid, ids):
            td_ids = [x.id for x in item.td_ids]
            self.pool.get('school.teacher_data').write(cr, uid, td_ids, {'blocked': item.block, })

school_block_td_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
