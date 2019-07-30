import codecs
import argparse
import json
import os
import itertools
import CPL
from CPL import ENTITY, AGENT, WASATTRIBUTEDTO, WASGENERATEDBY, WASDERIVEDFROM, BUNDLERELATION
import string


# relations type 20 represents a relation between two bundles
# get_all_objects gives only bundle objects
# get_bundle_objects gives objects in the bundle
# get_bundle_relations gives all relations in the bundle
# use 'test' for object and bundles

def process_db():
    db_connection = CPL.cpl_connection()
    # bundles = 145
    # total nodes = 2620
    roots = db_connection.get_all_objects('test')
    bundles = [r.object for r in roots]
    obj_props = []
    rel_lists = [db_connection.get_bundle_relations(b) for b in bundles]
    rel_list = list(itertools.chain.from_iterable(rel_lists))
    
    obj_dict = {}
    for b in bundles:
        if type(b) == list: continue
        b_objs = db_connection.get_bundle_objects(b)

        for obj in b_objs:
            if not obj.id in obj_dict:
                valid_props = get_valid_props(obj.string_properties())
                obj_dict[obj.id] = {}
                obj_dict[obj.id]['type'] = valid_props[0]
                obj_dict[obj.id]['val'] = valid_props[1]
        
    # Get all relations and construct dicts {article_id:[ids]}
    ent_adj_dict = {}
    agn_adj_dict = {}
    qot_adj_dict = {}
    for r in rel_list:
        # type 8 = entity to entity, 'wasDerivedFrom'
        if r.type == 8: 
            ent_adj_dict[r.base.id]  = ent_adj_dict[r.base.id] + [r.other.id] if r.base.id  in ent_adj_dict else [r.other.id]
            if obj_dict[r.other.id]['type'] == 'article':
                ent_adj_dict[r.other.id] = ent_adj_dict[r.other.id] + [r.base.id] if r.other.id in ent_adj_dict else [r.base.id]
            # if obj_dict[r.other.id]['type'] == 'government':
            #     print(obj_dict[r.other.id])
        # type 11 = entity to agent, or activity to agent 'wasAttributedTo'
        elif r.type == 11 and obj_dict[r.base.id]['type'] == 'article':
            agn_adj_dict[r.base.id] = agn_adj_dict[r.base.id] + [r.other.id] if r.base.id in agn_adj_dict else [r.other.id]
        
        # type 9 = entity to quote, 'wasGeneratedBy'
        elif r.type == 9:
            qot_adj_dict[r.base.id] = qot_adj_dict[r.base.id] + [r.other.id] if r.base.id in qot_adj_dict else [r.other.id]
            
    # Check if all object is 
  
    # Remove all duplicates
    ent_adj_dict = {k_id: list(set(v_ids)) for (k_id, v_ids) in ent_adj_dict.items()}
    agn_adj_dict = {k_id: list(set(v_ids)) for (k_id, v_ids) in agn_adj_dict.items()}
    qot_adj_dict = {k_id: list(set(v_ids)) for (k_id, v_ids) in qot_adj_dict.items()}
    
    print('Processing db finished')

    db_connection.close()

    return obj_dict, ent_adj_dict, agn_adj_dict, qot_adj_dict

def get_valid_props(props_lists):
    ''' Extract only useful and valid props from props_lists
        return [type, value]
    '''
    props_list = sum(props_lists, [])
    prefix = props_list[0]
    typ = ''
    val = ''
    for i, prop in enumerate(props_list, start=0):
        if prop == 'type':
            typ = props_list[i+1]
            break

    if typ == 'article' or typ == 'reference' or typ == 'government':
        for i, prop in enumerate(props_list, start=0):
            if prop == 'url':
                val = props_list[i+1]
                break

    elif typ == 'person':
        for i, prop in enumerate(props_list, start=0):
            if prop == 'name':
                val = props_list[i+1]
                break

    else:
        for i, prop in enumerate(props_list, start=0):
            if prop == typ:
                tmp_val = props_list[i+1]
                if tmp_val != prefix:
                    val = tmp_val
                    break

    return [typ, val]
    

    
process_db()