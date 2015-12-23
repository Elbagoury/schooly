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
{
    'name' : 'School Management Extension',
    'version' : '0.0.1',
    'author' : 'Pere Ramon Erro Mas (Tecnoba)',
    'website' : 'http://www.tecnoba.com',
    'description' : """
Base module for extends school base module. I adds classes and seances.
""",
    "category" : "Generic Modules/Others",
    "depends": [
        'school_base',
    ],
    'data' : [
        'school_extension_view.xml',
        'school_create_session_view.xml',
        'security/ir.model.access.csv',
    ],
    'demo' : [
        'school_extension_demo.xml',
    ],
    'active' : False,
    'installable' : True,
}

