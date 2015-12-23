# -*- coding: utf-8 -*-
##############################################################################
#
#    school module for OpenERP
#    Copyright (C) 2010 Tecnoba S.L. (http://www.tecnoba.com)
#      Pere Ramon Erro Mas <pereerro@tecnoba.com> All Rights Reserved.
#    Copyright (C) 2011 Zikzakmedia S.L. (http://www.zikzakmedia.com)
#      Jesús Martín Jiménez <jmargin@zikzakmedia.com> All Rights Reserved.
#
#    This file is a part of school module
#
#    school OpenERP module is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    school OpenERP module is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from openerp.osv import osv, fields, orm
from datetime import datetime, date, timedelta
from openerp.tools.translate import _

class school_school(osv.osv):
    _name = 'school.school'
school_school()

class school_teacher(osv.osv):
    _name = "school.teacher"
    _inherits = {'res.users' : 'user_id',}

    _columns = {
        'teacher_code': fields.char('Code',size=30,required=True,),
        'user_id': fields.many2one('res.users', string='User', required=True, ondelete='cascade'),
    }
    
    def create(self, cr, uid, vals, context=None):
        ret = super(school_teacher, self).create(cr, uid, vals, context=context)

        # afegir usuari al grup de professors
        md_obj = self.pool.get('ir.model.data')
        user = self.browse(cr, uid, ret, context=context).user_id
        group_ids = [x.id for x in user.groups_id]
        criteria = [('module','=','school_base'),
                    ('name','=','res_groups_school_professor_group'),]
        md_ids = md_obj.search(cr, uid, criteria)
        for md in md_obj.browse(cr, uid, md_ids):
            if md.res_id not in group_ids:
                self.write(cr, uid, [ret], {'groups_id': [(4,md.res_id)]})
            
        return ret
    
school_teacher()

class school_offer(osv.osv):
    _name = 'school.offer'
school_offer()

class school_course(osv.osv):
    _name  =  'school.course'
    
    def name_search(self, cr, uid, name='',args=None, operator='ilike',context=None, limit=80):
        criteria = ['|',('name','ilike',name),('code','ilike',name)]
        ids = self.search(cr, uid, criteria, limit = limit, context = context)
        return self.name_get(cr, uid, ids, context = context)

    _columns  =  {
        'name' : fields.char('Name', size=200,),
        'code' : fields.char('Code', size = 10, select = 1, help = "The course code."),
        'min_hours' : fields.integer('Total hours'),
        'offer_id': fields.many2one('school.offer', 'Offer', ondelete = 'restrict', select = 1, help = "The offer.", change_default=True,),
        'parent_id' : fields.many2one('school.course', string='Part of', ondelete = 'restrict', change_default=True),
        'needly' : fields.selection([('required','Required'),('optional','Optional')], string='Needly',),
        'active': fields.boolean('Active'),
    }

    _defaults  =  {
        'active' : lambda *a: 1,
        'min_hours' : 1,
    }

    _order  =  'name'

    def create(self, cr, uid, vals, context=None):
        if not all(x in vals for x in ('name','code')):
            o_obj = self.pool.get('school.offer')
            if vals.get('parent_id') and vals.get('offer_id'):
                parent = self.browse(cr, uid, vals['parent_id'])
                offer = o_obj.browse(cr, uid, vals['offer_id'])
                if not vals.get('name'):
                    vals['name'] = "%s %s" % (parent.name, offer.name)
                if not vals.get('code'):
                    vals['code'] = "%s %s" % (parent.code, offer.code)
        ret = super(school_course, self).create(cr, uid, vals, context=context)
        return ret
        
school_course()

class school_offer(osv.osv):
    _name = 'school.offer'

    _columns = {
        'name' : fields.char('Name', size=32, required=True, select=1, help="The offer name"),
        'code' : fields.char('Code', size=5, required=True, select=1, help="The offer code"),
        'course_ids' : fields.one2many('school.course','offer_id','Courses',help='List of the courses in the offer'),
        'active' : fields.boolean('Active', select=2,),
        'session_ids' : fields.one2many('school.session','offer',string='Sessions',),
    }

    _defaults = {
        'active' : lambda *a: 1,
    }

    _order = 'name'

school_offer()


class school_session(osv.osv):
    _name = 'school.session'

    
    _columns = {
        'name' : fields.char('Name', size=32, required=True, select=1, help="The session name"),
        'code' : fields.char('Code', size=10, required=True, select=1, help="The session code"),
        'offer' : fields.many2one('school.offer','Offer',select=1,help="The offer relationed with the item",),
        'date_from' : fields.date('Date from', required=True,),
        'date_to' : fields.date('Date to', required=True,),
        'group_id': fields.many2one('groups.group', string='Group', required=True,),
        'active' : fields.boolean('Active', select=2,),
        'school_id': fields.many2one('school.school', 'School', select = 1, help = 'School that is related to the current session.'),
    }

    _defaults = {
        'active' : lambda *a: 1,
    }

    _sql_constraints = [
        ('dates_ok','CHECK (date_to>=date_from)','Date to minor than date from'),
        ('name_uniq', 'unique (name)', 'The Name of the Session must be unique !')
    ]

    _order = 'name'

    def copy(self, cr, uid, id, default = {}, context = None):
        session_name = self.read(cr, uid, [id], ['name'])[0]['name']
        default.update({
            'name': _('%s (copy)') % session_name,
        })
        return super(school_session, self).copy(cr, uid, id, default, context)

    def create(self, cr, uid, vals, context=None):
        if 'code' not in vals and vals.get('offer'):
            num = 0
            offer = self.pool.get('school.offer').browse(cr, uid, vals['offer'])
            n = len(offer.code)
            cr.execute("SELECT code FROM school_session WHERE code LIKE %s", (offer.code+'%',))
            for (code,) in cr.fetchall():
                m = re.match(" (\d\d\d)", code[n:])
                if m:
                    num = max(num, int(m.group(1)))
            vals['code'] = "%s %s" % (offer.code, num + 1)
        return super(school_session, self).create(cr, uid, vals, context=context)
                
school_session()

class school_holidays(osv.osv):
    _name = 'school.holidays_calendar'
    _inherit = 'school.holidays_calendar'

    _columns = {
        'school_id': fields.many2one('school.school', string='School', select=1,),
    }
school_holidays()

class school_school(osv.osv):
    _name = 'school.school'
    _columns = {
        'name': fields.char('Name', size = 30, required = True, select = 1),
        'calendar_ids': fields.one2many('school.holidays_calendar', 'school_id', string = 'Calendars', help = 'Calendars of this school.'),
        'session_ids': fields.one2many('school.session', 'school_id', string = 'Sessions', help = 'Sessions of this school.'),
    }

school_school()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
