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
from datetime import datetime, date
import pytz
import math

# Utility function for convert a database format date string to python date object
def str_to_date(dt):
    return date(int(dt[0:4]),int(dt[5:7]),int(dt[8:10]))

# Utility function for convert a database format datetime string to python datetime object
def str_to_datetime(dt):
    return datetime(int(dt[0:4]),int(dt[5:7]),int(dt[8:10]),int(dt[11:13]),int(dt[14:16]))

week_day_selection = [('1','monday'),('2','tuesday'),('3','wednesday'),('4','thursday'),('5','friday'),('6','saturday'),('7','sunday')]

def _tz_get(self,cr,uid, context=None):
    return [(x, x) for x in pytz.all_timezones]

class util_periodicity(osv.osv):
    _name = 'util.periodicity'
    _description = 'A room to impartition a week hour for a seance class'


    def _get_filled(self, cr, uid, ids, field_name, arg, context=None):
        ret = {}
        for item in self.browse(cr, uid, ids, context=context):
            ret[item.id] = item.week_day and item.date_from and item.date_to
        return ret
    
    _columns = {
        'week_day' : fields.selection(week_day_selection,"Week day",),
        'hour_from' : fields.float('Hour from',),
        'tz' : fields.selection(_tz_get,  'Timezone', size=64,
            help="The user's timezone, used to create proper date and time values inside seances. "),
        'date_from' : fields.date('Date from',),
        'date_to' : fields.date('Date to'),
        'weeks_to_pass' : fields.integer('Week to pass',help="Weeks to pass until next week"),
        'week_to_init' : fields.integer('Week to init',help="Weeks to pass until first week"),
        'filled' : fields.function(_get_filled, type='boolean', method=True, string='Filled', store={
            'util.periodicity' : (lambda self,cr,uid,ids,context={}: ids, ['week_day','date_from','date_to'], 10),
        })
    }
    _order ='week_day, hour_from, date_from desc'

    _defaults = {
        'weeks_to_pass' : lambda *a: 0,
        'week_to_init' : lambda *a: 0,
        'tz' : lambda self,cr,uid,context={}: context.get('tz','UTC'),
    }

    # Module function returning a list of datetimes conditioned by seance properties values
    def periodicity_datetimes(cls,**vals):
        ret=[]
        if vals.get('hour_from',False):
            local_timezone = pytz.timezone(vals.get('tz','Europe/Madrid'))
            utc_timezone = pytz.timezone('UTC')
            for data in cls.periodicity_dates(**vals):
                (frac_hour,int_hour)=math.modf(vals['hour_from'])
                ud= datetime(data.year,data.month,data.day,int(int_hour),
                    int(math.floor(frac_hour*60)),0,0)
                ud = local_timezone.localize(ud, is_dst=False).astimezone(utc_timezone)
                ret.append(ud)
        return ret

    # Module function returning a list of datetimes conditioned by seance properties values
    def periodicity_dates(cls,week_to_init=0,weeks_to_pass=0,week_day=False,days_no_work=[],date_from=False,date_to=False,**other):
        if not date_from or not date_to or not week_day: return []
        ret=[]
        ldate=str_to_date(date_from)
        sk=week_to_init
    # TODO: Pending quality code up
        while (ldate<=str_to_date(date_to)):
            if str(ldate.weekday()+1)==str(week_day):
                sk=sk-1
                if sk<0:
                    if ldate.strftime('%Y-%m-%d') not in days_no_work:
                        ud=date(ldate.year,ldate.month,ldate.day)
                        ret.append(ud)
                    sk=weeks_to_pass
            ldate=ldate+ldate.resolution
        return ret

    # Module function returning a list of datetimes conditioned by seance properties values
    def periodicity_dates_str(cls,**vals):
        ret=[]
        for a_date in cls.periodicity_dates(**vals):
            ret.append(a_date.strftime('%Y-%m-%d'))
        return ret

    # Module function returning a list of datetimes conditioned by seance properties values
    def periodicity_datetimes_str(cls,**vals):
        ret=[]
        for a_datetime in cls.periodicity_datetimes(**vals):
            ret.append(a_datetime.strftime('%Y-%m-%d %H:%M:%S'))
        return ret

    def rb_periodicity_datetimes_str(cls, rb,days_no_work):
        return cls.periodicity_datetimes_str(
                    date_from=rb.date_from,
                    date_to=rb.date_to,
                    hour_from=rb.hour_from,
                    tz=rb.tz,
                    week_day=rb.week_day,
                    weeks_to_pass=rb.weeks_to_pass,
                    week_to_init=rb.week_to_init,
                    days_no_work=days_no_work)

util_periodicity()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
