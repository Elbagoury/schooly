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
    'name' : 'School Teacher Assignation and FET',
    'version' : '0.0.1',
    'author' : 'Pere Ramon Erro Mas (Tecnoba)',
    'website' : 'http://www.tecnoba.com',
    'description' : """
Compute automaticaly timetable for the assignation solutions.

It need the installation of the FET software, available 
into the 14.04 Ubuntu distributions.
apt-get install fet

Also, FET needs a windows server. 

""",
    "category" : "Generic Modules/Others",
    "depends": ['school_teacher_assignation',
                'school_fet'],
    'data' : [
        'school_tch_assig_and_fet.xml',
        ],
    'active' : False,
    'installable' : True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
