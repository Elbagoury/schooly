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


class school_holidays_calendar(osv.osv):
    _name = 'school.holidays_calendar'
school_holidays_calendar()

class school_holiday_interval(osv.osv):
    _name = 'school.holiday_interval'
    _columns = {
        'name' : fields.char('Name', size=30,),
        'date_from' : fields.date('Date from', select=1, required=True,),
        'date_to' : fields.date('Date to', select=1, required=True,),
        'calendars' : fields.many2many('school.holidays_calendar','school_holidays_calendar_intervals_rel','days_id','cal_id',string="Calendars"),
    }

    def _check_date_from_to(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context=context)
        return obj.date_from <= obj.date_to

    _constraints = [
        (_check_date_from_to, "Please, check the start date !", ['date_from', 'date_to']),
    ]

    _sql_constraints = [
        ('uniq_holiday_interval', 'unique(name)', 'The holiday interval of the year must be unique !'),
    ]

school_holiday_interval()

class school_holidays_calendar(osv.osv):
    _name = 'school.holidays_calendar'
    _columns = {
        'name' : fields.char('Name', size=30,),
        'holidays' : fields.many2many('school.holiday_interval','school_holidays_calendar_intervals_rel','cal_id','days_id',string="Holidays"),
    }
    
    _sql_constraints = [
        ('uniq_holiday_calendar', 'unique(name)', 'The holiday calendar must be unique !'),
    ]

school_holidays_calendar()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
