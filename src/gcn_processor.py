import json
import os
import numpy as np
import pandas as pd
import csv
import sys
import copy
import execnet
import itertools
from scipy.sparse import csr_matrix
from utils.url_classifier.url_utils import UrlUtils

# import time
# start = time.time()

# end = time.time()
# print(end - start)

dirpath = os.path.dirname(os.path.realpath(__file__))
dirpath = os.path.dirname(dirpath) + '/data/datasets/'

def store_labeled_articles(f_list):
    ''' From the file list, extract only url and label
        return the saved file name
    '''
    res = np.array([['url', 'label']])
    url_util = UrlUtils()
    saved_file_name = 'labeled_articles.csv'
    with open(dirpath + saved_file_name, mode='w') as csv_w:
        writer = csv.writer(csv_w)
        for f_name in f_list:
            print(dirpath + f_name)
            with open(dirpath + f_name, mode='r') as csv_f:
                reader = csv.DictReader(csv_f)
                tmp = [[row['url'], row['label']] for row in reader if url_util.is_valid_url(row['url'])]
                res = np.append(res, tmp, axis=0)
        idxes = list(range(res.shape[0]))[:-1]
        idx_row = np.array(['idx'] + idxes)
        res = np.c_[res, idx_row]
        writer.writerows(res)
    return saved_file_name

def get_article_dict(file_name):
    ''' return article_url(str) to label(0 or 1) dictionary 
    '''
    reader = csv.reader(open(dirpath + file_name, mode='r'))
    next(reader)
    article_label_dic = {r[0]: r[1] for r in reader}
    return article_label_dic

def call_python_version(Version, Module, Function, ArgumentList):
    gw      = execnet.makegateway("popen//python=python%s" % Version)
    channel = gw.remote_exec("""
        from %s import %s as the_function
        channel.send(the_function(*channel.receive()))
    """ % (Module, Function))
    channel.send(ArgumentList)
    return channel.receive()

def separate_arts(ent_adj_dict):
        ''' return dict that only includes aid : [aids] and dict that only includes aid: [fids]
        '''
        art_adj_dict = {}
        art_fts_dict = {}
        for k, v in ent_adj_dict.items():
            tmp_as = [] 
            tmp_fs = []
            for e in v:
                if e[0] == 'a': tmp_as.append(e)
                else          : tmp_fs.append(e)
            art_adj_dict[k] = tmp_as
            art_fts_dict[k] = tmp_fs

        return art_adj_dict, art_fts_dict

def link_articles(adj_dict, fts_dict, obj_dict, dict_list):
    ''' Links articles that are two hops away from each other by quote or agent
        return new article_id to [article_ids] dictionary and a feature dictionary that keeps 
        track of which agents or quotes are attributed to articles
    '''
    for typ, dic in dict_list.items(): 
        # Process on adj_dict
        for k_1, v_1 in dic.items():
            adj_entities = v_1

            for k_2, v_2 in dic.items():
                if k_1 == k_2: continue

                for i in v_2:
                    if i in adj_entities and obj_dict[i]['type'] != 'publisher':
                        adj_dict[k_1] = adj_dict[k_1] + [k_2] if k_1 in adj_dict else [k_2]
                    else:
                        adj_dict[k_1] = adj_dict[k_1] if k_1 in adj_dict else []

        # Process on fts_dict
        if typ == 'non-art': continue
        for k_1, v_1 in dic.items():
            for f in v_1:
                fts_dict[k_1] = fts_dict[k_1] + [f] if k_1 in fts_dict else [f]

    return adj_dict, fts_dict

def get_ids_idx_dicts(obj_dict):
    ''' return art_id to idx dict and non_art_id to idx dict
    '''
    art_id_idx_dict = {}
    fts_id_idx_dict = {}
    
    art_idx = 0
    fts_idx = 0
    for k, v in obj_dict.items():
        if v['type'] == 'article':
            art_id_idx_dict[k] = 'a' +  str(art_idx)
            art_idx += 1
        else:
            fts_id_idx_dict[k] = 'f' + str(fts_idx)
            fts_idx += 1
    return art_id_idx_dict, fts_id_idx_dict

def convert_ids_to_idx(art_id_idx_dict, fts_id_idx_dict, dicts_to_convert):
    ''' Modify all the dictionaries' keys and values in place from article_id to index  
    '''
    def convert_value(v):
        ''' Simply comvert a list of ids into a list of idx
        '''
        if type(v) == list: 
            v = [fts_id_idx_dict[i] if i in fts_id_idx_dict else art_id_idx_dict[i] for i in v]
        return v

    res_dicts = [{}, {}, {}, {}]
    i = 0
    for dic in dicts_to_convert:
        new_dict = res_dicts[i]
        for k, v in dic.items():
            new_key = art_id_idx_dict[k] if k in art_id_idx_dict else fts_id_idx_dict[k]
            new_dict[new_key] = convert_value(v)
        i += 1
    return res_dicts[0], res_dicts[1], res_dicts[2], res_dicts[3] 

def get_y(obj_dict, article_label_dic):
    for i, r in obj_dict.items():
        if r['type'] == 'article':
            y_i = article_label_dic[r['val']] if r['val'] in article_label_dic else -1
            r['label'] = y_i


# Paths for labeled data files from data dir
file_list = ['BuzzFeed_fb_urls_parsed.csv', 
             'data_from_Kaggle.csv',
             'fakeNewsNet_data/politifact_real.csv', 
             'fakeNewsNet_data/politifact_fake.csv',]

# Process all article urls and create a csv file and a dict obj
saved_file_name = store_labeled_articles(file_list)

article_label_dic = get_article_dict(saved_file_name)

# obj_dict: obj_id to {type, val}
# ent/agn/qot_adj_dict: id to [ids] 
obj_dict, ent_adj_dict, agn_adj_dict, qot_adj_dict = call_python_version('2.7', 'src.gcn_db_processor', 'process_db', [])
# print(len( set(list(ent_adj_dict.keys()) + list(agn_adj_dict.keys()) + list(qot_adj_dict.keys())) ))

# Get article_id to idx dict of only article 
art_id_idx_dict, fts_id_idx_dict = get_ids_idx_dicts(obj_dict)
# print(len(list(art_id_idx_dict.keys())))
# print(fts_id_idx_dict)

# Convert all ids in dicts to idx
dicts_to_convert = [obj_dict, ent_adj_dict, agn_adj_dict, qot_adj_dict]
obj_dict, ent_adj_dict, agn_adj_dict, qot_adj_dict = convert_ids_to_idx(art_id_idx_dict, fts_id_idx_dict, dicts_to_convert)

# Separate ent_adj into two pre reuslt dictionaries
tmp_aid_adj_dict, tmp_aid_fid_dict = separate_arts(ent_adj_dict)
# print(len(tmp_aid_adj_dict))
# print(len(tmp_aid_fid_dict))

# Process dict_list so articles connected via one hop are in their adj_lists each other
dict_list = {'non-art': tmp_aid_fid_dict, 'agent': agn_adj_dict, 'quote':qot_adj_dict}

aid_adj_dict, aid_fid_dict = link_articles(tmp_aid_adj_dict, tmp_aid_fid_dict, obj_dict, dict_list)
# print(set(aid_adj_dict.keys()))
# print(set(aid_fid_dict.keys()))
print('  adj  n :', len(aid_adj_dict.keys()))
print('  fts  n :', len(aid_fid_dict.keys()))
a = set(list(itertools.chain.from_iterable(aid_adj_dict.values())))
b = set(list(itertools.chain.from_iterable(aid_fid_dict.values())))
print('       a :', len(a))
print('       b :', len(b))

l = 0
for lst in aid_adj_dict.values():
    if len(lst) == 0: l += 1
print('empty ns :', l)

print('       n :', str(l+len(a)))

c = 0
d = []
for k, v in obj_dict.items():
    if k[0] == 'a': 
        c += 1
        d.append(k)
    # if v['type'] == 'government':
    #     print(v)
print('  real n :', c)

print('  real n :', len(set(d + list(aid_fid_dict.keys()))))

# Add label vector on obj_dict  
get_y(obj_dict, article_label_dic)

print('DONE')
