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

import copy
from lxml import etree
from openerp.osv import orm, osv, fields
import base64
from math import floor
from wizard.school_fet_wizard import floats_to_school_fet_hour

class school_fet_hour(osv.osv):
    _name = 'school.fet.hour'

    def name_get(self, cr, uid, ids):
        ret=[]
        for item in self.browse(cr, uid, ids):
            ret.append( (item.id, floats_to_school_fet_hour(item.hour_from,item.hour_to) ) )
        return ret

    _columns = {
        'sequence' : fields.integer('Sequence',select=1,),
        'hour_from' : fields.float('Hour from',),
        'hour_to' : fields.float('Hour to',),
    }

    def _constraint_no_overlap_hours(self, cr, uid, ids):
        sql="""
        SELECT fh1.id
        FROM school_fet_hour AS fh1 INNER JOIN school_fet_hour AS fh2 ON fh1.id<>fh2.id AND fh1.hour_to>fh2.hour_from AND fh1.hour_from<fh2.hour_to
        WHERE fh1.id IN %s
        """
        cr.execute(sql,(tuple(ids),))
        return len(cr.fetchall())==0

    _constraints = [
        (_constraint_no_overlap_hours, 'Overlaping', ['hour_from','hour_to']),
    ]
    _sql_constraints = [
        ('hour_from_ok','CHECK (hour_from BETWEEN 0 AND 24)','Hour incorrect'),
        ('hour_to_ok','CHECK (hour_to BETWEEN 0 AND 24)','Hour incorrect'),
        ('hours_ok','CHECK (hour_to>hour_from)','Hours incorrect'),
    ]

school_fet_hour()

class school_fet_day(osv.osv):
    _name = 'school.fet.day'

    _columns = {
        'name' : fields.selection([('monday','monday'),('tuesday','tuesday'),('wednesday','wednesday'),('thursday','thursday'),('friday','friday'),('saturday','saturday'),('sunday','sunday')],"Week day",),
    }

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'The day name must be unique !')
    ]
school_fet_day()

class school_fet_aules_propies(osv.osv):
    _name = 'school.fet.aules_propies'

    _columns = {
        'group_id' : fields.many2one('groups.group',string="Group",ondelete="cascade",),
        'room_id' : fields.many2one('school.room',string="Room",ondelete="cascade",),
        'percentatge' : fields.integer('Percentatge',),
    }
school_fet_aules_propies()

class school_fet_tag(osv.osv):
    _name = 'school.fet.tag'

    _columns = {
        'name' : fields.char('Activity Tag', size = 50, help = "Activity Tag for restrictions on FET"),
        'iwl_ids' : fields.many2many('school.impartition_week_line', 'school_iwl_tag_rel', 'tag_id', 'iwl_id', string = 'IWLs',),
    }
school_fet_tag()

class school_impartition_week_line(osv.osv):
    _name = 'school.impartition_week_line'
    _inherit = 'school.impartition_week_line'

    _columns = {
        'tag_ids' : fields.many2many('school.fet.tag', 'school_iwl_tag_rel', 'iwl_id', 'tag_id', string = 'Tags',),
    }
school_impartition_week_line()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
