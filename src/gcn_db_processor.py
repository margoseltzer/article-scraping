import codecs
import argparse
import json
import os
import itertools
import CPL
from CPL import ENTITY, AGENT, WASATTRIBUTEDTO, WASGENERATEDBY, WASDERIVEDFROM, BUNDLE_RELATION
import string


# relations type 20 represents a relation between two bundles
# get_all_objects gives only bundle objects
# get_bundle_objects gives objects in the bundle
# get_bundle_relations gives all relations in the bundle
# use 'test' for object and bundles

def main():
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
                valid_props = obj.properties()[0][1:]
                obj_dict[obj.id] = {}
                obj_dict[obj.id]['type'] = valid_props[0]
                obj_dict[obj.id]['val'] = valid_props[1]
        
    print(len(obj_dict.values()))
    print(obj_dict)    

    # Get all relations and construct dicts {article_id:[ids]}
    ent_adj_dict = {}
    agn_adj_dict = {}
    qot_adj_dict = {}
    for r in rel_list:

        # type 8 = entity to entity, 'wasDerivedFrom'
        if r.type == 8: 
            ent_adj_dict[r.base.id]  = ent_adj_dict[r.base.id] + [r.other.id] if r.base.id  in ent_adj_dict else [r.other.id]
            ent_adj_dict[r.other.id] = ent_adj_dict[r.other.id] + [r.base.id] if r.other.id in ent_adj_dict else [r.base.id]

        # type 11 = entity to agent, or activity to agent 'wasAttributedTo'
        elif r.type == 11 :
            # and check of base is type 'article'
            agn_adj_dict[r.base.id] = agn_adj_dict[r.base.id] + [r.other.id] if r.base.id in agn_adj_dict else [r.other.id]
        
        # type 9 = entity to quote, 'wasGeneratedBy'
        elif r.type == 9:
            qot_adj_dict[r.base.id] = qot_adj_dict[r.base.id] + [r.other.id] if r.base.id in qot_adj_dict else [r.other.id]
            
    # Check if all object is 
  
    # Remove all duplicates
    ent_adj_dict = {k_id: list(set(v_ids)) for (k_id, v_ids) in ent_adj_dict.items()}
    agn_adj_dict = {k_id: list(set(v_ids)) for (k_id, v_ids) in agn_adj_dict.items()}
    qot_adj_dict = {k_id: list(set(v_ids)) for (k_id, v_ids) in qot_adj_dict.items()}
    
    print('DONE')

    db_connection.close()

    return obj_dict, ent_adj_dict, agn_adj_dict, qot_adj_dict

main()

