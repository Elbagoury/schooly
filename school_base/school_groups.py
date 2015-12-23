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

from openerp.osv import osv, fields, orm
from datetime import datetime, date, timedelta
from openerp.tools.translate import _


class groups_participation(osv.osv):
    _name = 'groups.participation'
    _inherit = 'groups.participation'

    def name_get(self, cr, uid, ids, context = None):
        res = []
        for item in self.browse(cr, uid, ids):
            session_name = item.session_id and item.session_id.name or ''
            res.append((item['id'],'%s - %s' % (session_name, item.participant.name)))
        return res

    _columns = {
        'session_id' : fields.many2one('school.session', 'Session', ondelete = 'cascade', select=1,),
    }

groups_participation()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
