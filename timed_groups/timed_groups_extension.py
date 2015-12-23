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

import collections
import math

from openerp.osv import osv, orm, fields
from datetime import datetime
from timed_groups import _inclou_interval_en_llista,_complementa_llista,_MIN_DATETIME,_MAX_DATETIME
from bisect import bisect_left
from openerp.tools.translate import _


def num_max_coincidences(llista, diahora_inici, diahora_fi, context = None):
    ranges = [(diahora_inici,0)]
    for dtf0,dtt0 in llista:
        dtf0 = max(dtf0, diahora_inici)
        dtt0 = min(dtt0, diahora_fi)
        if dtt0 > dtf0:
            ind = bisect_left(ranges, (dtf0,0))
            if len(ranges) == ind:
                ranges.insert(ind, (dtf0, 1))
            elif ranges[ind][0] < dtf0:
                ranges.insert(ind, (dtf0, ranges[ind][1]))
                ind += 1
            ind2 = bisect_left(ranges, (dtt0, 0))
            while ind < ind2:
                ranges[ind] = (ranges[ind][0], ranges[ind][1] + 1)
                ind += 1
            if dtt0 < diahora_fi:
                if ind==len(ranges):
                    ranges.insert(ind, (dtt0, 0))
                elif ranges[ind][0] != dtt0:
                    ranges.insert(ind, (dtt0, ranges[ind-1][1] - 1))
    return max(x[1] for x in ranges)


#class groups_group(osv.osv):
#    _name = 'groups.group'
#
#groups_group()
#
#class groups_participation(osv.osv):
#    _name = 'groups.participation'
#
#groups_participation()

_CHANGE_ASSIGNATION_GROUP_IDS_KEY='change_assignation_group_ids'
_CLASSIFYING_KEY='classifying'
_DEEP_MARK = 'deep_mark'

def diff_time(title = 'Group assignation' ,group_name = None, participation_id = None, datetime_from = None, datetime_to = None, classifying = None, time_ant = None, context = None):
    now = datetime.today()
    time_now = now.minute *60000000 + now.second * 1000000 + now.microsecond
    if time_ant:
#        print "%s - %s%s : (%s, %s, %s-%s c:%s) :: %s" % (context[_DEEP_MARK], ''.join(map(lambda *a: "\t",range(context[_DEEP_MARK]))) ,title, group_name, participation_id, datetime_from, datetime_to, classifying, time_now - time_ant)
        context[_DEEP_MARK] -= 1
    else:
        context[_DEEP_MARK] = context.get(_DEEP_MARK, 0) + 1    
    return time_now
            
class groups_group_assignation(osv.osv):
    _name = 'groups.group_assignation'
    _inherit = 'groups.group_assignation'
    
    def _get_gas_from_contact(self, cr, uid, ids, context = None):
        return self.pool.get('groups.group_assignation').search(cr, uid, [('participation_id.participant','in',ids)])
        
    def _get_gas_from_participation(self, cr, uid, ids, context = None):
        return self.pool.get('groups.participation').search(cr, uid, [('participation_id','in',ids)])

    def _get_part_name(self, cr, uid, ids, field_name, arg, context = None):
        ret = {}
        for item in self.browse(cr, uid, ids):
            ret[item.id] = '%s' % (item.participation_id.participant.name,)
        return ret
        
    _columns = {
        'part_name' : fields.function(_get_part_name, type='char', size=150, string = 'Name', method = True, store = {
            'res.partner': (_get_gas_from_contact, ['name'], 30),
            'group.participation' : (_get_gas_from_participation, ['participant'], 20),
            'group.group_assignation' : (lambda self,cr,uid,ids,context={}: ids, ['participation_id'], 10)}),
    }

    _order = 'part_name'
    
    def be_right(self, cr, uid, ids, context = None):
        cont = True
        while cont:
            query = """
                SELECT ga.participation_id,ga.group_id,ga.datetime_from,ga.datetime_to,ga2.group_id,ga2.datetime_from,ga2.datetime_to FROM groups_group_assignation AS ga
                    INNER JOIN groups_groups_rel AS gr ON ga.group_id=gr.child_id
                    INNER JOIN groups_groups_rel AS gr2 ON gr.classification=gr2.classification AND gr2.id<>gr.id
                    INNER JOIN groups_group_assignation AS ga2 ON gr2.child_id=ga2.group_id AND ga.participation_id=ga2.participation_id
                WHERE (ga.datetime_from,ga.datetime_to) OVERLAPS (ga2.datetime_from,ga2.datetime_to) ORDER BY participation_id
                LIMIT 1        
            """
            cr.execute(query)
            cont = False
            for (part_id,g1_id,dtf1,dtt1,g2_id,dtf2,dtt2) in cr.fetchall():
                self.remove_assignation(cr, uid, part_id, g1_id, classifying = False, datetime_from=max(dtf1,dtf2), datetime_to=min(dtt1,dtt2), context = context)
                cont = True
            
    def add_assignation(self, cr, uid, participation_id, group, classifying = False, datetime_from=_MIN_DATETIME, datetime_to=_MAX_DATETIME, context=None):
        if not context:
            context={}
        time_intro = diff_time(context = context)
        ret=None
        datetime_from=max(_MIN_DATETIME,datetime_from or _MIN_DATETIME)
        datetime_to=min(_MAX_DATETIME,datetime_to or _MAX_DATETIME)
        if type(group) in (int,long):
            group=self.pool.get('groups.group').browse(cr, uid, group, context={'withoutBlank': False })

        # Don't repeat group
        if not _CHANGE_ASSIGNATION_GROUP_IDS_KEY in context:
            context[_CHANGE_ASSIGNATION_GROUP_IDS_KEY]=[]
        if group.id in context[_CHANGE_ASSIGNATION_GROUP_IDS_KEY]:
            diff_time(title='Add to group', group_name = group.name, participation_id = participation_id, datetime_from = datetime_from, datetime_to = datetime_to, classifying = classifying, time_ant = time_intro, context = context)
            return
        context[_CHANGE_ASSIGNATION_GROUP_IDS_KEY].append(group.id)

        # Els pares que baixen domini cap el grup resulten amb un domini interseccio
        unio_dels_dominis_complementaris=[]
        for parent_rel in group.parent_ids:
            if parent_rel.direction=='down':
                ga_ids=self.pool.get('groups.group_assignation').search(cr, uid, [('group_id','=',parent_rel.parent_id.id),('participation_id','=',participation_id),('datetime_from','>',datetime_to),('datetime_to','<',datetime_from)])
                for ga in self.browse(cr, uid, ga_ids, context={'withoutBlank': False,}):
                    if ga.datetime_from>datetime_from:
                        _inclou_interval_en_llista(unio_dels_dominis_complementaris,(datetime_from,ga.datetime_from))
                    if ga.datetime_from<datetime_from:
                        _inclou_interval_en_llista(unio_dels_dominis_complementaris,(ga.datetime_to,datetime_to))

        # De la interseccio potser surten mes d'un interval
        for (dt_from,dt_to) in _complementa_llista(unio_dels_dominis_complementaris,(datetime_from,datetime_to)):
            # Amplia assignacions dels grups superiors per la participacio
            # Si hi ha un pare sense classificacio ha de ser pare unic perque en cas contrari no sabem a quin pare hem d'ampliar l'assignacio

            # Fusiona assignacions dins de l'interval respectant els limits de les ja incloses
            ga_ids=self.search(cr, uid, [('group_id','=',group.id),('participation_id','=',participation_id),('datetime_from','<=',dt_to),('datetime_to','>=',dt_from)])
            ret = 'ga_id' in context and context['ga_id'] in ga_ids and context['ga_id'] or 0

            datetime_from_min=dt_from
            datetime_to_max=dt_to
            
            unio_dins = []
            for item in self.browse(cr, uid, ga_ids, context={'withoutBlank': False,}):
                datetime_from_min=min(item.datetime_from or _MIN_DATETIME,datetime_from_min)
                datetime_to_max=max(item.datetime_to or _MAX_DATETIME,datetime_to_max)
                _inclou_interval_en_llista(unio_dins, (max(item.datetime_from,datetime_from,_MIN_DATETIME),min(item.datetime_to,datetime_to,_MAX_DATETIME) ) )
            for (dt_from2,dt_to2) in _complementa_llista(unio_dins,(datetime_from,datetime_to)):
                for parent_rel in group.parent_ids:
                    if parent_rel.direction=='up':
                        self.add_assignation(cr, uid, participation_id, parent_rel.parent_id.id, datetime_from=dt_from2, datetime_to=dt_to2, context=context)
                    if parent_rel.classification:
                        for group_rel in parent_rel.classification.groups_rel_ids:
                            if group_rel.child_id.id!=group.id:
                                self.remove_assignation(cr, uid, participation_id, group_rel.child_id.id, classifying = True, datetime_from=dt_from2, datetime_to=dt_to2, context=context)
            vals={'participation_id': participation_id, 'group_id': group.id, 'datetime_from': datetime_from_min, 'datetime_to': datetime_to_max,}
            if ret:
                super(groups_group_assignation, self).write(cr, uid, [ret], vals)
                ga_ids.remove(ret)
            else:
                if 'ga_id' in context and context['ga_id']:
                    vals['id'] = context['ga_id']
                ret=super(groups_group_assignation, self).create(cr, uid, vals)
            super(groups_group_assignation, self).unlink(cr, uid, ga_ids)

            # Decidim a quin grup de les divisions afegim l'assignacio
            for classification in set(child_rel.classification for child_rel in group.children_ids if child_rel.direction=='down' and child_rel.classification):
                self.pool.get('groups.classification').add_assignation(cr, uid, participation_id, classification,datetime_from=dt_from, datetime_to=dt_to, context=context)
        diff_time(title = 'Add to group', group_name = group.name, participation_id = participation_id, datetime_from = datetime_from, datetime_to = datetime_to, classifying = classifying, time_ant = time_intro, context = context)
        return ret


    def remove_assignation(self, cr, uid, participation_id, group, classifying = False, datetime_from=_MIN_DATETIME, datetime_to=_MAX_DATETIME, context=None):
        if not context:
            context={}
        time_intro = diff_time(context = context)
        datetime_from=max(_MIN_DATETIME,datetime_from or _MIN_DATETIME)
        datetime_to=min(_MAX_DATETIME,datetime_to or _MAX_DATETIME)
        
        if type(group) in (int,long):
            group=self.pool.get('groups.group').browse(cr, uid, group, context={'withoutBlank': False,})
        if not _CHANGE_ASSIGNATION_GROUP_IDS_KEY in context:
            context[_CHANGE_ASSIGNATION_GROUP_IDS_KEY]=[]
        if group.id in context[_CHANGE_ASSIGNATION_GROUP_IDS_KEY]:
            diff_time(title = 'Remove from group', group_name = group.name, participation_id = participation_id, datetime_from = datetime_from, datetime_to = datetime_to, classifying = classifying, time_ant = time_intro, context = context)
            return
        context[_CHANGE_ASSIGNATION_GROUP_IDS_KEY].append(group.id)
        
        ga_ids=self.search(cr, uid, [('group_id','=',group.id),('participation_id','=',participation_id),('datetime_from','<',datetime_to),('datetime_to','>',datetime_from)])

        datetime_from_min=datetime_from
        datetime_to_max=datetime_to
        ints = []
        for data in self.read(cr, uid, ga_ids, ['datetime_from','datetime_to'], context={'withoutBlank': False,}):
            # Treu l'assignacio a tots  els grups inferiors
            for child_rel in group.children_ids:
                if child_rel.direction=='down':
                    self.remove_assignation(cr, uid, participation_id, child_rel.child_id,
                                            datetime_from=max(datetime_from,data['datetime_from']),
                                            datetime_to=min(datetime_to,data['datetime_to']) , context=context)
                else:
                    children_ids = self.search(cr, uid, [('participation_id','=',participation_id),
                                          ('group_id','=',child_rel.child_id.id),
                                          ('datetime_from','<',min(datetime_to,data['datetime_to'])),
                                          ('datetime_to','>',max(datetime_from,data['datetime_from'])), ])
                    if children_ids:
                        raise orm.except_orm('Problem',"Domini del fill amb ids %s massa gran." % (children_ids,))

            ints.append( (max(datetime_from,data['datetime_from']), min(datetime_to,data['datetime_to'])) )
            datetime_from_min=min(data['datetime_from'],datetime_from_min)
            datetime_to_max=max(data['datetime_to'],datetime_to_max)
        if datetime_from_min<datetime_from:
            super(groups_group_assignation, self).create(cr, uid, {'participation_id': participation_id, 'group_id': group.id, 'datetime_from': datetime_from_min, 'datetime_to': datetime_from,})
        if datetime_to_max>datetime_to:
            super(groups_group_assignation, self).create(cr, uid, {'participation_id': participation_id, 'group_id': group.id, 'datetime_from': datetime_to, 'datetime_to': datetime_to_max,})
        super(groups_group_assignation, self).unlink(cr, uid, ga_ids)
        
        # Treiem l'assignacio de tots els pares del qual aquest es un grup de la classificacio
        for parent_rel in group.parent_ids:
            if parent_rel.classification and not classifying and parent_rel.direction=='up':
                for (dtf,dtt) in ints:
                    llista = []
                    for data in self.read(cr, uid, self.search(cr, uid, [
                        ('participation_id','=',participation_id),
                        ('group_id.parent_ids','in',[brother.id for brother in parent_rel.classification.groups_rel_ids if brother.id != parent_rel.id]),
                        ]), ['datetime_from','datetime_to'], context={'withoutBlank': False,}):
                        llista = _inclou_interval_en_llista(llista, (data['datetime_from'],data['datetime_to']))
                    for (dtf1, dtt1) in _complementa_llista(llista, (dtf,dtt)):
                        self.remove_assignation(cr, uid, participation_id, parent_rel.parent_id, datetime_from=dtf1, datetime_to=dtt1, context=context)
        diff_time(title = 'Remove from group', group_name = group.name, participation_id = participation_id, datetime_from = datetime_from, datetime_to = datetime_to, classifying = classifying, time_ant = time_intro, context = context)
        
            
    def read(self, cr, uid, ids, fields, context=None, load='_classic_write'):
        if not fields: fields=[]
        if not context: context={}
        ret=super(groups_group_assignation, self).read(cr, uid, ids, fields, context=context, load=load)
        # @type context dict
        if context.get('withoutBlank', True):
            # @type ret list
            for item in ret:
                if 'datetime_from' in item:
                    if item['datetime_from']==_MIN_DATETIME: item['datetime_from']=''
                if 'datetime_to' in item:
                    if item['datetime_to']==_MAX_DATETIME: item['datetime_to']=''
        return ret
        
    def create(self, cr, uid, vals, context=None):
        return self.add_assignation(cr, uid, vals['participation_id'], vals['group_id'],
            datetime_from=vals.get('datetime_from',_MIN_DATETIME),
            datetime_to=vals.get('datetime_to',_MAX_DATETIME), context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if not context:
            context = {}
        for item in self.browse(cr, uid, ids, {'withoutBlank': False,}):
            to_remove = []
            to_add = []
            if ( vals.get('datetime_to',_MAX_DATETIME) < item.datetime_from or 
                 vals.get('datetime_from',_MIN_DATETIME) > item.datetime_to ):
                to_remove.append( (item.datetime_from, item.datetime_to) )
                to_add.append( (vals.get('datetime_from',item.datetime_from),
                                     vals.get('datetime_to',item.datetime_to) ) )
            elif ( vals.get('datetime_from',_MIN_DATETIME) > item.datetime_from and 
                 vals.get('datetime_to',_MAX_DATETIME) < item.datetime_to ):
                to_remove.append( (item.datetime_from, vals.get('datetime_from',_MIN_DATETIME)) )
                to_remove.append( (vals.get('datetime_to',_MIN_DATETIME), item.datetime_to) )
            elif ( vals.get('datetime_from',_MIN_DATETIME) < item.datetime_from and 
                 vals.get('datetime_to',_MAX_DATETIME) > item.datetime_to ):
                to_add.append( (vals.get('datetime_from',_MIN_DATETIME), item.datetime_from) )
                to_add.append( (item.datetime_to, vals.get('datetime_to',_MIN_DATETIME)) )
            else:
                if vals.get('datetime_from',_MIN_DATETIME) < item.datetime_from:
                    to_add.append( (vals.get('datetime_from',_MIN_DATETIME), item.datetime_from) )
                else:
                    to_remove.append( (item.datetime_from, vals.get('datetime_from',_MIN_DATETIME)) )
                if vals.get('datetime_to',_MAX_DATETIME) > item.datetime_to:
                    to_add.append( (item.datetime_to, vals.get('datetime_to',_MAX_DATETIME) ) )
                else:
                    to_remove.append( (vals.get('datetime_to',_MAX_DATETIME), item.datetime_to) )
                    
            for (datetime_from,datetime_to) in to_remove:
                context2 = dict(context)
                context2[_CHANGE_ASSIGNATION_GROUP_IDS_KEY] = []
                self.remove_assignation(cr, uid, item.participation_id.id, item.group_id, datetime_from=datetime_from, datetime_to=datetime_to, context=context2)
            for (datetime_from,datetime_to) in to_add:                
                context2 = dict(context)
                context2[_CHANGE_ASSIGNATION_GROUP_IDS_KEY] = []
                self.add_assignation(cr, uid, vals.get('participation_id',item.participation_id.id),
                                     vals.get('group_id',item.group_id.id),
                                     datetime_from=datetime_from,
                                     datetime_to=datetime_to, context=context2)
        return True


    def unlink(self, cr, uid, ids, context=None):
        context[_CHANGE_ASSIGNATION_GROUP_IDS_KEY]=[]
        for item in self.browse(cr, uid, ids, {'withoutBlank': False,}):
            self.remove_assignation(cr, uid, item.participation_id.id, item.group_id, datetime_from=item.datetime_from, datetime_to=item.datetime_to, context=context)
        return True

groups_group_assignation()

class groups_participation(osv.osv):
    _name = 'groups.participation'
    _inherit = 'groups.participation'


    def _get_groups(self, cr, uid, ids, field_name, arg, context=None):
        ret={}
        for obj in self.browse(cr, uid, ids):
            reti=set()
            retxt=[]
            for obj2 in sorted(obj.assignation_ids, key=lambda assig: assig.group_id.name):
                reti.add(obj2.group_id.id)
                retxt.append(obj2.group_id.name)
            ret[obj.id]={'group_ids': list(reti), 'group_txt': ','.join(retxt)}
        return ret

    def _search_by_group(self, cr, uid, obj, name, args, context=None):
        ga_obj=self.pool.get('groups.group_assignation')
        ga_ids=ga_obj.search(cr, uid, [('group_id.name',op,value) for (namex,op,value) in args if namex==name])
        return [('id','in',[x['participation_id'] for x in ga_obj.read(cr, uid, ga_ids, ['participation_id'])])]

    def _get_part_name(self, cr, uid, ids, field_name, arg, context = None):
        ret = {}
        for item in self.browse(cr, uid, ids):
            session_name = ''
            if item.session_id:
                session_name = item.session_id.name
            ret[item.id] = '%s - %s, %s (%s)' % (session_name, item.participant.name, item.participant.first_name, item.name)
        return ret
    
    def _get_part_ids_from_parts(self, cr, uid, ids, context = None):
        return ids
    
    _columns = {
        'group_ids' : fields.function(_get_groups, fnct_search=_search_by_group, arg=None, type='many2many', obj='groups.group', method=True, string="Groups", multi='groups',),
        'group_txt' : fields.function(_get_groups, arg=None, type='char', method=True, string="Groups with assignation", multi='groups',),
        'part_name' : fields.function(_get_part_name, type='char', size=150, string = 'Name', method = True, store = {
            'res.partner': (lambda self,cr,uid,ids,context={}: self.pool.get('groups.participation').search(cr, uid, [('participant','in',ids)]), ['name',], 10),
            'groups.participation' : (_get_part_ids_from_parts, ['participant'], 20)}),
    }

    def groups_in_interval(self, cr, uid, ids, date_from=_MIN_DATETIME, date_to=_MAX_DATETIME, context=None):
        """
        Retorna un diccionari amb claus els identificadors de les participacions
        contingudes en la llista del parametre ids. Els valors son una llista de
        diccionaris amb dades sobre els grups amb assignacions per la participacio
        identificada amb la clau dins el periode determinat pels parametres
        date_from i date_to. La llista de grups es troba ordenada per prioritat
        essent el grup amb prioritat mes alta el quin es primer.
        """
        res={}
        if ids:
            for part_id in ids:
                res[part_id] = []
            cr.execute("""
            SELECT ga.participation_id,
                ga.datetime_from,ga.datetime_to,
                g.id AS gid,g.priority
            FROM groups_group_assignation AS ga
                INNER JOIN groups_group AS g ON ga.group_id=g.id
            WHERE ga.participation_id in %(part_ids)s
                AND ga.limit_from < %(date_to)s
                AND ga.limit_to > %(date_from)s
            ORDER BY g.priority,ga.datetime_from DESC
            """, {'part_ids': tuple(ids+[0]),'date_from': date_from, 'date_to': date_to, } )
            for (part_id,datetime_from,datetime_to,group_id,priority) in cr.fetchall():
                res[part_id] += [  {'group_id': group_id,
                                    'datetime_from': datetime_from,
                                    'datetime_to': datetime_to,
                                    'priority':priority,}  ]
        return res

    def _domain_by_participation(self, cr, uid, group_id, participation_id, datetime_from = _MIN_DATETIME, datetime_to = _MAX_DATETIME, context = None):
        obj = self.pool.get('groups.groups_rel')
        obj_ga = self.pool.get('groups.group_assignation')
        datetime_from = max(datetime_from, _MIN_DATETIME)
        datetime_to = min(datetime_to, _MAX_DATETIME) 
        llista = []
        for groups_rel in obj.browse(cr, uid, obj.search(cr, uid, [('child_id','=',group_id),('direction','=','down')])):
            for dicci in obj_ga.read(cr, uid, obj_ga.search(cr, uid, [('group_id','=',groups_rel.parent_id.id),('participation_id','=',participation_id)]), ['datetime_from','datetime_to'], context ={'withoutBlank': False}):
                for dtf,dtt in _complementa_llista([(dicci['datetime_from'],dicci['datetime_to'])]):
                    llista = _inclou_interval_en_llista(llista, (dtf,dtt))
        return [(max(dtf,datetime_from),min(dtt,datetime_to)) for dtf,dtt in _complementa_llista(llista) if dtt > datetime_from and dtf < datetime_to]
                
groups_participation()

class groups_preference(osv.osv):
    _name = 'groups.preference'
    
    _columns = {
        'participation_id' : fields.many2one('groups.participation', string='Participation', ondelete='cascade',),
        'classification_id' : fields.many2one('groups.classification', string='Classification', ondelete='cascade',),
        'group_id' : fields.many2one('groups.group', string='Group', ondelete='cascade',),
        'sequence' : fields.integer('Sequence'),
    }
    
    _sql_constraints = [('_pref_unique1','UNIQUE (participation_id,classification_id,group_id)','Unicity for the record violated.'),
        ('_pref_unique2','UNIQUE (participation_id,classification_id,sequence)','Unicity for the record violated.')]

    _order = 'sequence'
groups_preference()

class groups_classification(osv.osv):
    _name = 'groups.classification'
    _inherit = 'groups.classification'

    def _get_parts_and_children(self, cr, uid, classification, order = lambda x: x.participant.name, datetime_from=_MIN_DATETIME, datetime_to=_MAX_DATETIME, context=None ):
        participations={}
        child_groups=set()
        part_ids = None
        for groups_rel in classification.groups_rel_ids:
            part_ids2 = set()
            group_domain=groups_rel.direction=='up' and groups_rel.child_id or groups_rel.parent_id
            group_child=groups_rel.direction=='down' and groups_rel.child_id or groups_rel.parent_id
            child_groups.add((group_child.id,group_child.name))
            for ga in group_domain.assignation_ids:
                key=(ga.participation_id.id,order(ga.participation_id))
                part_ids2.add(key)
                if key not in participations:
                    participations[key]= groups_rel.direction == 'down' and [(datetime_from,datetime_to)] or []
                unitats_a_afegir = [(max(datetime_from,ga.datetime_from),min(datetime_to,ga.datetime_to))]
                if groups_rel.direction == 'down':
                    participations[key] = _complementa_llista(participations[key])
                    unitats_a_afegir = _complementa_llista(unitats_a_afegir)
                for interval in unitats_a_afegir:
                    participations[key] = _inclou_interval_en_llista(participations[key], interval)
                if groups_rel.direction == 'down':
                    participations[key] = _complementa_llista(participations[key])
            if part_ids is None:
                part_ids = set(part_ids2)
            else:
                if groups_rel.direction=='down':
                    part_ids.intersection_update(part_ids2)
                else:
                    part_ids.update(part_ids2)
        participations = dict( (key,value) for (key,value) in participations.items() if key in part_ids)
        return participations, child_groups

    def _assigna_a_grups(self, cr, uid, participations_sorted, child_groups_sorted, participations_data, context=None):
        c=0
        for (part_id,contact_name) in participations_sorted:
            grup_ind = int( c * len(child_groups_sorted) / len(participations_sorted) )
            c+=1
            for (dtf,dtt) in participations_data[(part_id,contact_name)]:
                context[_CHANGE_ASSIGNATION_GROUP_IDS_KEY]=[]
                self.pool.get('groups.group_assignation').add_assignation(cr, uid, part_id, child_groups_sorted[grup_ind][0], classifying = True, datetime_from=dtf, datetime_to=dtt, context=context)

    def alfabetical_classification_method(self, cr, uid, classification, datetime_from=_MIN_DATETIME, datetime_to=_MAX_DATETIME, context=None):
        if not context: context={}
        datetime_from = max(_MIN_DATETIME,datetime_from)
        datetime_to = min(_MAX_DATETIME,datetime_to)
        # Escollim el grup que li toca dividint segons ordre alfabetic
        participations, child_groups = self._get_parts_and_children(cr, uid, classification, datetime_from=datetime_from, datetime_to=datetime_to, context = context)
        participations_sorted=sorted(participations.keys(),key=lambda x: x[1])
        child_groups_sorted=sorted(child_groups,key=lambda x: x[1])
        self._assigna_a_grups(cr, uid, participations_sorted, child_groups_sorted, participations, context=context)

    def order_id_classification_method(self, cr, uid, classification, datetime_from=_MIN_DATETIME, datetime_to=_MAX_DATETIME, context=None):
        if not context: context={}
        datetime_from = max(_MIN_DATETIME,datetime_from)
        datetime_to = min(_MAX_DATETIME,datetime_to)
        # Escollim el grup que li toca dividint segons ordre alfabetic
        participations, child_groups = self._get_parts_and_children(cr, uid, classification, order= lambda x: x.id, datetime_from=datetime_from, datetime_to=datetime_to, context = context)
        participations_sorted=sorted(participations.keys(),key=lambda x: x[1])
        child_groups_sorted=sorted(child_groups,key=lambda x: x[1])
        self._assigna_a_grups(cr, uid, participations_sorted, child_groups_sorted, participations, context=context)

    def by_preferences_classification_method(self, cr, uid, classification, datetime_from=_MIN_DATETIME, datetime_to=_MAX_DATETIME, context=None):
        if not context: context={}
        datetime_from = max(_MIN_DATETIME,datetime_from)
        datetime_to = min(_MAX_DATETIME,datetime_to)
        # Escollim el grup que li toca dividint segons ordre alfabetic
        participations, child_groups = self._get_parts_and_children(cr, uid, classification, order= lambda x: x.id, datetime_from=datetime_from, datetime_to=datetime_to, context = context)
#        participations_sorted=sorted(participations.keys(),key=lambda x: x[1])
        child_group_ids=[x[0] for x in child_groups]
        
        n_parts_by_group = dict.fromkeys(child_group_ids, 0)
        nmax_by_group = dict([(x.id,x.max_assignations) for x in self.pool.get('groups.group').browse(cr, uid, child_group_ids)])
        
        # First the preferences
        pref_ids = self.pool.get('groups.preference').search(cr, uid, [('group_id','in',child_group_ids),
                    ('classification_id','=',classification.id),
                    ('participation_id','in',[x[0] for x in participations.keys()])],order='sequence')        
        for item in self.pool.get('groups.preference').browse(cr, uid, pref_ids):
            if not child_group_ids:
                break
            if item.participation_id.id in participations and item.group_id.id in child_group_ids:
                if n_parts_by_group[item.group_id.id] < nmax_by_group[item.group_id.id]:
                    for (dtf,dtt) in participations[(item.participation_id.id,item.participation_id.participant.name)]:
                        context[_CHANGE_ASSIGNATION_GROUP_IDS_KEY]=[]
                        self.pool.get('groups.group_assignation').add_assignation(cr, uid, item.participation_id, item.group_id.id, classifying = True, datetime_from=dtf, datetime_to=dtt, context=context)
                    n_parts_by_group[item.group_id.id] += 1
                    del participations[item.participation_id.id]
                else:
                    child_group_ids.remove(item.group_id.id)
        # Other participations without preferences
        for (part_id,part_name) in participations.keys():
            if not child_group_ids:
                break
            group_id = False
            if classification.method_one == 'complete':
                group_id = child_group_ids[0]
            if classification.method_one == 'first':
                tuples = [(n_parts_by_group[g_id], g_id) for g_id in child_group_ids if n_parts_by_group[g_id] < nmax_by_group[g_id]]
                if tuples:
                    group_id = min( tuples )[1]
            if group_id:
                for (dtf,dtt) in participations[(part_id,part_name)]:
                    context[_CHANGE_ASSIGNATION_GROUP_IDS_KEY]=[]
                    self.pool.get('groups.group_assignation').add_assignation(cr, uid, part_id, group_id, classifying = True, datetime_from=dtf, datetime_to=dtt, context=context)
                n_parts_by_group[group_id] += 1
                if n_parts_by_group[group_id] == nmax_by_group[group_id]:
                    child_group_ids.remove[group_id]

    def add_assignation(self, cr, uid, participation_id, classification, datetime_from=_MIN_DATETIME, datetime_to=_MAX_DATETIME, context=None):
        if not context:
            context = {}
        time_intro = diff_time(context = context)
        if type(classification) in (int,long):
            classification = self.browse(cr, uid, classification, context={'withoutBlank': False })
        if classification.auto_active and classification.groups_rel_ids:
            groups_rel = classification.groups_rel_ids[0]
            target_group=groups_rel.direction=='up' and groups_rel.parent_id or groups_rel.child_id
            self.pool.get('groups.group_assignation').add_assignation(cr, uid, participation_id, target_group, datetime_from=datetime_from, datetime_to=datetime_to, context=context)
            self.classify(cr, uid, classification, context=context)
        else:
            target_group = None
            last_group = (None, _MIN_DATETIME)
            if classification.method_one == 'first':
                num_max0 = -1
                for groups_rel in classification.groups_rel_ids:
                    group_child=groups_rel.direction=='down' and groups_rel.child_id or groups_rel.parent_id
                    llista = []
                    for ga in group_child.assignation_ids:
                        llista.append((ga.datetime_from,ga.datetime_to))
                        if ga.participation_id.id == participation_id and ga.datetime_to > last_group[1]:
                            last_group = (group_child, ga.datetime_to)
                    nmax = num_max_coincidences(llista, datetime_from, datetime_to, context = context)
                    if num_max0 < nmax:
                        target_group = group_child
            elif classification.method_one == 'complete':
                for groups_rel in classification.groups_rel_ids:
                    group_child=groups_rel.direction=='down' and groups_rel.child_id or groups_rel.parent_id
                    llista = []
                    for ga in group_child.assignation_ids:
                        llista.append((ga.datetime_from,ga.datetime_to))
                        if ga.participation_id.id == participation_id and ga.datetime_to > last_group[1]:
                            last_group = (group_child, ga.datetime_to)
                    if target_group is None:
                        nmax = num_max_coincidences(llista, datetime_from, datetime_to, context = context)
                        if group_child.max_assignations > nmax:
                            target_group = (group_child, nmax)
            self.pool.get('groups.group_assignation').add_assignation(cr, uid, participation_id, target_group, datetime_from=datetime_from, datetime_to=datetime_to, context=context)
        diff_time(title = 'Add on classification', group_name = classification.name, participation_id = participation_id, datetime_from = datetime_from, datetime_to = datetime_to, time_ant = time_intro, context = context)
        
            
    def classify(self, cr, uid, classification, datetime_from=_MIN_DATETIME, datetime_to=_MAX_DATETIME, context=None):
        for groups_rel in classification.groups_rel_ids:
            target_group=groups_rel.direction=='up' and groups_rel.parent_id or groups_rel.child_id
            for ga in target_group.assignation_ids:
                context[_CHANGE_ASSIGNATION_GROUP_IDS_KEY]=[]
                self.pool.get('groups.group_assignation').remove_assignation(cr, uid, ga.participation_id.id, target_group, classifying = True, datetime_from=datetime_from, datetime_to=datetime_to, context=context)
        if classification.method=='alfa_classi':
            self.alfabetical_classification_method(cr, uid, classification, datetime_from=datetime_from, datetime_to=datetime_to, context=context)
        if classification.method=='order_id':
            self.order_id_classification_method(cr, uid, classification, datetime_from=datetime_from, datetime_to=datetime_to, context=context)
        if classification.method=='preferences':
            self.by_preferences_classification_method(cr, uid, classification, datetime_from=datetime_from, datetime_to=datetime_to, context=context)

    def run_classify(self, cr, uid, ids, context = None):
        for item in self.browse(cr, uid, ids, context={'withoutBlank': False }):
            self.classify(cr, uid, item, context = context)
        return True

groups_classification()

class groups_groups_rel(osv.osv):
    _name = 'groups.groups_rel'
    _inherit = 'groups.groups_rel'

    def create(self, cr, uid, vals, context=None):
        if not context: context={}
        ret=super(groups_groups_rel, self).create(cr, uid, vals, context=context)
        item=self.browse(cr, uid, ret, context={'withoutBlank': False,})
        if item.classification and item.classification.auto_active:
            self.pool.get('groups.classification').classify(cr, uid, item.classification, context=context)
        if item.direction=='up':
            for ga in item.child_id.assignation_ids:
                context[_CHANGE_ASSIGNATION_GROUP_IDS_KEY]=[item.child_id.id]
                self.pool.get('groups.group_assignation').add_assignation(cr, uid, ga.participation_id.id, item.parent_id, datetime_from=ga.datetime_from, datetime_to=ga.datetime_to, context=context)
        if not self.pool.get('groups.group_assignation')._assignation_in_domain(cr, uid, [ga.id for ga in item.child_id.assignation_ids]):
            raise orm.except_orm('Problem',"El domini del pare no inclou el domini del fill.")

    def write(self, cr, uid, ids, vals, context=None):
        return super(groups_groups_rel, self).write(cr, uid, ids, dict((k,v) for (k,v) in vals.items() if k in ('sequence','classification')))
#        raise orm.except_orm('Problem',"You could only create or remove group relationship.")

    def unlink(self, cr, uid, ids, context=None):
        for item in self.browse(cr, uid, ids, context={'withoutBlank': False,}):
            source_group=item.direction=='down' and item.parent_id or item.child_id
            target_group=item.direction=='up' and item.parent_id or item.child_id
            for ga in source_group.assignation_ids:
                context[_CHANGE_ASSIGNATION_GROUP_IDS_KEY]=[]
                self.pool.get('groups.group_assignation').remove_assignation(cr, uid, ga.participation_id.id, target_group, ga.datetime_from, ga.datetime_to, context=context)
        return super(groups_groups_rel, self).unlink(cr, uid, ids, context = context)
            
groups_groups_rel()
