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

from openerp.osv import fields,osv
from lxml import etree

def _get_id(item):
    return "exp_test_%s_%s" % (item._name.replace(".","_"),item.id)
def _get_model(item):
    return item._name
def _get_ref(obj, cr, uid, item):
    ids = obj.search(cr, uid, [('model','=',item._name),('res_id','=',item.id)])
    if ids:
        return obj.browse(cr, uid, ids[0]).complete_name
    return _get_id(item)
def _get_type(self, model, field):
    obj = self.pool.get(model)
    if field in obj._columns:
        return obj._columns[field]
    ret = filter(None,[_get_type(self, mod, field) for mod in obj._inherits])
    return ret and ret[0]
def _get_record_node(data, item):
    return etree.SubElement(data, "record", id=_get_id(item), model=_get_model(item))
    
class school_export_test_data(osv.osv_memory):
    _name = 'school.export_test_data'

    _columns = {
        'xml_data': fields.text('XML Data', ),
    }

    def export_xml(self, cr, uid, ids, context=None):
        obj_data = self.pool.get('ir.model.data')
        root = etree.Element("openerp")
        data = etree.SubElement(root, "data")
        
        planning = [
            ('school.teacher', ('name','teacher_code','login','max_week_hours','min_week_hours')),
            ('school.course', ('name','code')),
            ('school.offer', ('name',)),
            ('school.course.line',('course_id','offer_id','needly','weekly_hours')),
            ('school.session',('name','date_from','date_to','offer','school_id')),
            ('res.partner',('name',)),
            ('groups.participation',('participant',)),
            ('groups.group',('name',)),
            ('groups.classification',('name','method')),
            ('groups.group_assignation',('participation_id','group_id')),
            ('school.classe',('name','group_id','group_id','course_id','date_from','date_to')),
            ('school.building',('name',)),
            ('school.room',('name','capacity','building_id')),
            ('school.impartition_week_line',('classe_id','week_day','hour_from','duration')),
            ('school.teacher_course_suitability',('teacher_id','course_id','percentatge','max_week_hours','min_week_hours')),
            ]
            
        for model, camps in planning:    
            obj = self.pool.get(model)
            for item in obj.browse(cr, uid, obj.search(cr, uid, [])):
                val = _get_ref(obj_data, cr, uid, item)
                if not '.' in val:
                    node = _get_record_node(data, item)
                    for field in camps:
                        ftype = _get_type(self, model, field)._type
                        value = getattr(item, field)
                        if ftype in ('char','text'):
                            etree.SubElement(node, "field", name=field).text = value
                        elif ftype == 'many2one':
                            etree.SubElement(node, "field", name=field, ref= _get_ref(obj_data, cr, uid, value))
        
        self.write(cr, uid, ids, {'xml_data': etree.tostring(root, pretty_print = True),})
        act_id = obj_data.xmlid_to_res_id(cr, uid, 'school_export_test_data.school_export_test_data_act_1')
        ret= self.pool.get('ir.actions.act_window').read(cr, uid, [act_id], [])[0]
        ret['res_id'] = ids[0]
        return ret
            
school_export_test_data()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
