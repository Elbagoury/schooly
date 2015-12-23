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

import bisect
import itertools
import time
import multiprocessing as mp
from datetime import datetime
from copy import copy
from collections import defaultdict

LOG_TIME = 2
LOG_CONDICIONS = 1
LOG_ON = 0
MP = True
RANGE_MAX_SOLS = True
RANGE_AFINA = True


def agrupa_cursos_i_professors(teacher_data_by_course):
    cursos = {}
    professors = {}
    ret = []

    for (curs, _dicci) in teacher_data_by_course.items():
        for _dicci2 in _dicci['list']:
            professor = _dicci2['id']
            if curs not in cursos:
                if professor not in professors:
                    dicci = {'courses': set([curs]), 'professors': set([professor]), }
                    cursos[curs] = len(ret)
                    professors[professor] = len(ret)
                    ret.append(dicci)
                else:
                    dicci = ret[professors[professor]]
                    dicci['courses'].add(curs)
                    cursos[curs] = professors[professor]
            else:
                if professor not in professors:
                    dicci = ret[cursos[curs]]
                    dicci['professors'].add(professor)
                    professors[professor] = cursos[curs]
                else:
                    if cursos[curs] == professors[professor]:
                        continue
                    dicci = ret[cursos[curs]]
                    dicci2 = ret[professors[professor]]
                    dicci['courses'].update(dicci2['courses'])
                    dicci['professors'].update(dicci2['professors'])
                    for curs2 in dicci2['courses']:
                        cursos[curs2] = cursos[curs]
                    for professor2 in dicci2['professors']:
                        professors[professor2] = cursos[curs]
                    dicci2['courses'] = False
                    dicci2['professors'] = False
    return [x for x in ret if x['courses']]

def professors_candidats_ordenats(data_by_teacher,
                                  teacher_course_data_list,
                                  criteri_teachers_suficients):
    tcd_list_ordered = sorted(
        filter(lambda x,dbt=data_by_teacher: x['id'] in dbt,
               teacher_course_data_list),
        key=lambda tcd,dbt=data_by_teacher: (
            tcd['pool_min'],# Minim de temps que necessita el 
                            #   teacher_data en aquest curs
            dbt[tcd['id']]['pool_min'], # Minim de temps que necessita 
                                        #   el teacher_data en total
            tcd['pool_max'], # Total de temps que disposa per al curs
            dbt[tcd['id']]['pool_max'], # Total de temps que disposa
                                        #   en total
            tcd['percentage'], # Percentatge de idonietat
        ), reverse = True)
    new_tcd_list = []
    num_hours = 0
    for tcd in tcd_list_ordered:
        # Reduim la llista de professors: els que necessiten aquest curs
        #   per cumplir el minim d'hores generals i completem amb els
        #   restants fins a tenir un nombre d'hores mes que suficient.
        num_hours += tcd['pool_max']
        new_tcd_list.append(tcd)
        if criteri_teachers_suficients(num_hours, len(new_tcd_list)):
            break
    return new_tcd_list

def insert_and_cut(llista_de_solucions, possible_solucio, max_solutions):
    if len(llista_de_solucions) < max_solutions or\
       llista_de_solucions[max_solutions-1][0] < possible_solucio[0]:
        llista_de_solucions.reverse()
        bisect.insort(llista_de_solucions, possible_solucio)
        llista_de_solucions.reverse()
        if len(llista_de_solucions) > max_solutions:
            del llista_de_solucions[max_solutions:]


def test_conditions(classe_duration,
                            course_data_of_teacher,
                            data_of_teacher,
                            total_hours,
                            total_hours2,
                            total_min_hours,
                            total_min_hours2):
    """
    Condicions:
    1 - Que al teacher li quedi hores per fer aquest curs
    2 - Que al teacher li quedi hores en general
    3 - Que l'assignacio no impedeixi que es cumpleixi el minim 
            d'hores en la resta de teachers per aquest curs
    4 - Que l'assignacio no impedeixi que es cumpleixi el minim 
            d'hores en la resta de teachers en el total de cadascu
    """
    id_teacher = course_data_of_teacher['id']
    # cond 1 
    if not course_data_of_teacher['pool_max'] >= classe_duration:
        if LOG_ON == LOG_CONDICIONS:
            print "Al teacher_data %s no li queden hores. (te %s, cal %s)" % (
                id_teacher, 
                course_data_of_teacher['pool_max'], classe_duration)
        return False
    # cond 2
    if not data_of_teacher['pool_max'] >= classe_duration:
        if LOG_ON == LOG_CONDICIONS:
            print "Al teacher_data %s no li queden hores totals per aquesta. (te %s, cal %s)" % (
                id_teacher,  
                data_of_teacher['pool_max'], 
                classe_duration)
        return False
    # cond 3
    min_h_altres_tch_curs = total_min_hours - course_data_of_teacher['pool_min']
    if not min_h_altres_tch_curs  <= total_hours - classe_duration:
        if LOG_ON == LOG_CONDICIONS:
            tupla = (min_h_altres_tch_curs, total_hours - classe_duration)
            print "L'assignacio de teacher_data %s impedeixi que es cumpleixi el minim d'hores en la resta de teachers per aquest curs %s" % (
                id_teacher, 
                tupla)
        return False
    # cond 4
    min_h_altres_tch = total_min_hours2 - data_of_teacher['pool_min']
    if not min_h_altres_tch <= total_hours2 - classe_duration:
        if LOG_ON == LOG_CONDICIONS:
            tupla = (min_h_altres_tch, total_hours2 - classe_duration)
            print "L'assignacio impedeixi que es cumpleixi el minim d'hores (%s) en la resta de teachers (%s)" % tupla
        return False
    return True
    
    
"""
    classes : llista de duracions
    data_by_teacher : hores maximes i minimes a assignar per teacher
    teacher_course_data_list : hores maximes i minimes a assignar per al
        curs per cada teacher. Dades recuperades se teacher_suitability
    total_hours : hores totals que queden per assignar en aquest curs
    total_hours2 : hores totals que queden per assignar en tots els
        cursos
    total_min_hours : hores minimes totals a omplir per aquest curs
    total_min_hours2 : hores minimes totals a omplir per a tots els
        cursos
    max_solutions : arrosega el numero de solucions que cal
    classe_cursor : cursor que apunta a la classe dins la llista 
        (classes) a la que toca assignar un teacher
    afinament : quoeficient multiplicatiu per saber quants teachers 
        agafarem de la llista ordenada per poder assegurar que omplim
        les assignacions 
"""
def assigna_classes(clss, d_x_tch, l_tch_crs_d,
                    total_hours, total_hours2, 
                    total_min_hours, total_min_hours2,
                    max_sol, p_cls=0, 
                    afina = 7, time_limit=None):

    l_sols_to_ret = []
    cls_dur = clss[p_cls]['duration']

    def criteri_teachers_suficients(num_hours, num_tch,
            h_min=total_hours*afina,
            num_tch_min=(len(clss) - p_cls)):
        return num_hours > h_min and \
               num_tch > num_tch_min

    lo_tch_crs_d = professors_candidats_ordenats(
                            d_x_tch,
                            l_tch_crs_d,
                            criteri_teachers_suficients)
    
    for p_tch in range(len(lo_tch_crs_d)):
        if time.time() > time_limit:
            break # s'ha acabat el temps per fer els calculs
        
        crs_d = lo_tch_crs_d[p_tch]
        tch_id = crs_d['id']
        d = d_x_tch[tch_id]
        
        # comprova condicions assignacio
        if not test_conditions(cls_dur,
                            crs_d,
                            d,
                            total_hours,
                            total_hours2,
                            total_min_hours,
                            total_min_hours2):
            continue

        # TODO : Mirar en FET
        # classes[classe_cursor]['teacher_data'] = id_teacher
        # mira en FET
        
        # Apuntem la solucio actual
        # Si es la darrera classe no cal fer mes recursivitat
        if p_cls + 1 >= len(clss):
            new_sol = (crs_d['percentage'], [tch_id])
            insert_and_cut(l_sols_to_ret, new_sol, max_sol)
            continue

        # calculem el valor a reduir per no baixar de 0
        to_reduce = min(crs_d['pool_min'], cls_dur)
        to_reduce2 = min(d['pool_min'], cls_dur)

        # Preparem les noves llistes        
        new_lo_tch_crs_d = copy(lo_tch_crs_d)
        new_crs_d = copy(crs_d)
        new_crs_d.update({
                    'pool_max': crs_d['pool_max'] - cls_dur,
                    'pool_min': crs_d['pool_min'] - to_reduce})
        new_lo_tch_crs_d[p_tch] = new_crs_d
        new_d_x_tch = copy(d_x_tch)
        new_d = copy(d)
        new_d.update({
                    'pool_max': d['pool_max'] - cls_dur,
                    'pool_min': d['pool_min'] - to_reduce2})
        new_d_x_tch[tch_id] = new_d
    
        # Executem la recursio
        l_v_assig = assigna_classes(
                clss,
                new_d_x_tch,
                new_lo_tch_crs_d,
                total_hours - cls_dur,
                total_hours2 - cls_dur,
                total_min_hours - to_reduce,
                total_min_hours2 - to_reduce2,
                max_sol,
                p_cls = p_cls + 1,
                time_limit = time_limit)
        
        # Apuntem els resultats de la recursio
        for (v, assig) in l_v_assig:
            new_sol = (crs_d['percentage'] + v, [tch_id] + assig)
            insert_and_cut(l_sols_to_ret, new_sol, max_sol)
    return l_sols_to_ret

def _assigna_cursos(courses_punter, cursos_list_orig,
                   total_classes_hours, classes_data_by_course,
                   total_teachers_hours, data_by_teacher,
                   teachers_data_by_course,
                   max_solutions,
                   time_limit=None,
                   afina=7,
                   deep_only_one = 1):

    course_id = cursos_list_orig[courses_punter]
    
    classes = classes_data_by_course[course_id]['classes']
    total_course_duration = classes_data_by_course[course_id]['duration']
    teacher_course_data = teachers_data_by_course[course_id]
    teacher_course_data_list = teacher_course_data['list']

    if LOG_ON:
        tupla = (course_id,
                 total_course_duration,
                 teacher_course_data['pool_min'],
                 teacher_course_data['pool_max'],
                 total_teachers_hours
                 )
        print "Inici assig classes del curs\t%s\t%s\th cla\t(%s,%s)\th tch\t%s\th tt" % tupla
    
    sols = assigna_classes(
            classes,
            data_by_teacher, # dades del teacher
            teacher_course_data_list,
            total_course_duration,
            total_classes_hours,
            teacher_course_data['pool_min'],
            total_teachers_hours['pool_min'],
            max_solutions,
            time_limit=time_limit,
            afina=afina
    )
    """
    sols es una llista de solucions d'assignacio de professors a les classes.
    Cadascuna de les solucions es composa del valor numeric de la solucio i de la llista de professors
    assignats per ordre de les classes que s'han passat com a parametre
    """

    # còpia dels cursos sense el que ja s'ha assignat professors a les classes
    cursos_list = copy(cursos_list_orig)
    cursos_list.pop(courses_punter)

    if not cursos_list:
        llista_de_solucions_a_retornar = [(v,{course_id: l}) for v,l in sols]
        return 1.0, llista_de_solucions_a_retornar

    llista_de_solucions_a_retornar = [(0,{course_id: []})]
    acabat = 0.0        
    for (value, assignacio) in sols:
        
        # Contem les hores per reduir el necessari en l'estructura
        # de dades d'hores maximes que passarem per assignar els seguents cursos
        # TODO: integrar en l'estructura de dades per evitar el càlcul
        hours_by_teacher = defaultdict(int)
        total_hours = 0
        for i in range(len(assignacio)):
            teacher_id = assignacio[i]
            duration = classes[i]['duration']
            hours_by_teacher[teacher_id] += duration
            total_hours += duration

        # Fem recursivitat per
        for cp in range(len(cursos_list)):
            new_data_by_teacher = copy(data_by_teacher)
            new_total_teachers_hours = copy(total_teachers_hours)
            
            # Apliquem la reduccio i contabilitzem les hores minimes
            new_total_teachers_hours['pool_max'] -= total_hours
            for (teacher_id, hours) in hours_by_teacher.items():
                data_of_teacher = copy(data_by_teacher[teacher_id])
                data_of_teacher['pool_max'] -= hours # Apliquem la reduccio d'hores maximes al professor
                to_reduce = min(hours, data_of_teacher['pool_min'])
                data_of_teacher['pool_min'] -= to_reduce
                new_total_teachers_hours['pool_min'] -= to_reduce
                new_data_by_teacher[teacher_id] = data_of_teacher

            _acabat, value_assignacio_list = _assigna_cursos(
                cp,
                cursos_list,
                total_classes_hours - total_hours,
                classes_data_by_course, # passem tota l'estructura de dades
                new_total_teachers_hours,
                new_data_by_teacher,
                teachers_data_by_course, # passem tota l'estructura de dades
                max_solutions, time_limit=time_limit, afina=afina,
                deep_only_one=max(1, deep_only_one - 1)
            )

            acabat += _acabat / len(cursos_list) / len(sols)
            
            # De les solucions dels cursos en la recursio, afegim la solucio trobada del curs apuntat aqui
            # Mantenim la llista de solucions ordenada i ens quedem amb les solucions mes valuoses
            for (value2, assignacio_by_course) in value_assignacio_list:
                assignacio_by_course[course_id] = assignacio
                new_max = (value2 + value, assignacio_by_course)
                insert_and_cut(llista_de_solucions_a_retornar, new_max, max_solutions)

            if LOG_ON == LOG_TIME:
                print time.time(), time_limit
            if time.time() > time_limit:
                break
            if deep_only_one == 1:
                break
    return acabat, llista_de_solucions_a_retornar

def assigna_cursos(cursos_list_orig,
                   total_classes_hours, classes_data_by_course,
                   total_teachers_hours, data_by_teacher,
                   teachers_data_by_course, max_solutions,
                   time_limit=None,num_proc=4,afina=1,deep_only_one=1):

    if time_limit is None:
        time_limit = time.time() + 60

    llista_de_solucions_a_retornar = [(0,{})]
    acabat = 0.0
    
    rg_max_sols = RANGE_MAX_SOLS and range(1,max_solutions) or [max_solutions]
    rg_afina = RANGE_AFINA and range(int(afina),1,-1) or [afina]
    
    for max_sol, afi in itertools.product(rg_max_sols, rg_afina):
        args = [cursos_list_orig,
                total_classes_hours,
                classes_data_by_course,
                total_teachers_hours,
                data_by_teacher,
                teachers_data_by_course,
                max_sol,
                time_limit,
                afi,
                deep_only_one]
        if MP:
            pool = mp.Pool(processes=num_proc)
            results = [pool.apply_async(_assigna_cursos,args=[cp]+args)
                for cp in range(len(cursos_list_orig))]
            res = []
            for p in results:
                if time.time() > time_limit:
                    break
                res.append(p.get())
        else:
            res = [_assigna_cursos(*([cp]+args))
                for courses_punter in range(len(cursos_list_orig))]
        for _acabat, value_assignacio_list in res:
            acabat += _acabat / len(cursos_list_orig) / max_solutions
            for va in value_assignacio_list:
                if all(va[1].values()):
                    insert_and_cut(llista_de_solucions_a_retornar, va, max_solutions)
        if time.time() > time_limit or len(llista_de_solucions_a_retornar) == max_solutions:
            break
    
    if True:
        print "SOLS"
        for value, assig_by_course in llista_de_solucions_a_retornar:
            print "VALOR" , value
            for course_id, ls in assig_by_course.items():
                classes = classes_data_by_course[course_id]['classes']
                cl_tch = [(ls[i],classes[i]['id']) \
                                for i in range(len(ls))]
                assigs = ",".join(map(lambda x: "%s %s" % x, cl_tch))
                print "    course_id: %s, assigs: %s" % (course_id, assigs)

    return acabat, llista_de_solucions_a_retornar


import pickle
import fileinput
import argparse
import sys
import os.path

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Assigna cursos a professors')
    parser.add_argument('input_file')
    parser.add_argument('output_file', help="This file will contain the output")
    parser.add_argument('--error_file', help="Where the program will save the warnings")
    args = parser.parse_args()
    v = pickle.load( open(args.input_file, "rb") )
    
    llista_de_solucions = [(0,{})]
    acabat = 0.0
    
    agrups = agrupa_cursos_i_professors(v['teachers_data_by_course'])
    for agrupacio in agrups:
        agr_time_available = v['time_available'] *  len(agrupacio['courses']) / len(v['teachers_data_by_course'])
        time_limit = time.time() + agr_time_available
        # TODO: fer una llista de cursos ordenada comencant per el mes dificil d'assignar
        #       professors. Es provaran totes pero s'ha de mirar de comencar a
        #       permutar per on hi ha mes probabilitat de solucio

        _acabat, sols = assigna_cursos(
                   list(agrupacio['courses']),
                   v['total_classes_hours'],
                   v['classes_data_by_course'],
                   v['total_teachers_hours'],
                   v['data_by_teacher'],
                   v['teachers_data_by_course'],
                   v['max_solutions'],
                   time_limit=time_limit,
                   num_proc=v.get('num_proc', 4),
                   afina=v.get('afina',1),
                   deep_only_one=v.get('deep_only_one',2),
                   )

        acabat += _acabat / len(agrups)
        new_llista_de_solucions = copy(llista_de_solucions)
        for (value2, assignacio_by_course2) in sols:
            for (value, assignacio_by_course) in llista_de_solucions:
                nova_assignacio_by_course = copy(assignacio_by_course)
                nova_assignacio_by_course.update(assignacio_by_course2)
                nova_sol = (value2+value, nova_assignacio_by_course)
                insert_and_cut(new_llista_de_solucions, nova_sol, v['max_solutions']) 
        llista_de_solucions = new_llista_de_solucions
    solucions = (acabat, datetime.now(), llista_de_solucions)
    pickle.dump(solucions, open(args.output_file, "wb"))
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
