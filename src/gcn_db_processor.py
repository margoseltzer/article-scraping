import codecs
import argparse
import json
import os
import CPL
from CPL import ENTITY, AGENT, WASATTRIBUTEDTO, WASGENERATEDBY, WASDERIVEDFROM, BUNDLE_RELATION
import string

db_connection = CPL.cpl_connection()
# relations type 20 represents a relation between two bundles
# get_all_objects gives only bundle objects
# get_bundle_objects gives objects in the bundle
# get_bundle_relations gives all relations in the bundle
# use 'test' for object and bundles

def main():
    roots = db_connection.get_all_objects('test')
    bundles = [r.object for r in roots]
    objects = []
    relations = []
    
    b_obj_ids = []
    for b in bundles:
        if type(b) == list: continue
        #b_objs is list of {id: int}
        id_objs = db_connection.get_bundle_objects(b)
        ids = [obj.id for obj in id_objs]
        print(ids)
        b_obj_ids += ids
    print(len(b_obj_ids))
    print(len(set(b_obj_ids)))
    print(len(roots))
    print('DONE')
main()

db_connection.close()
