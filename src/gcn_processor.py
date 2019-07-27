import json
import os
import numpy as np
import pandas as pd
import csv
import sys
import execnet
from scipy.sparse import csr_matrix
from utils.url_classifier.url_utils import UrlUtils

dirpath = os.path.dirname(os.path.realpath(__file__))
dirpath = os.path.dirname(dirpath) + '/data/datasets/'

def store_labeled_articles(f_list):
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
    '''
    return article_url(str) to label(0 or 1) dictionary 
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

def link_articles(ent_adj_dict, dict_list):
    ''' 
    Links articles that are two hops away from each other by quote or agent
    return new article_id to [article_ids] dictionary
    '''
    res_dict = ent_adj_dict
    for dic in dict_list: 
        for k_1, v_1 in dic.items():
            adj_entities = {i: 1 for i in v_1}

            for k_2, v_2 in dic.items():
                if k_1 == k_2: continue

                for i in v_2:
                    if i in adj_entities:
                        res_dict[k_1] = res_dict[k_1] + [k_2] if k_1 in res_dict else [k_2]
    return res_dict

def get_ids_idx_dict(obj_dict):
    '''
    return obj_id to idx dictionary
    '''
    id_idx_dict = {}
    idx = 0
    for k, v in obj_dict.items():
        id_idx_dict[k] = idx
        idx += 1
    return id_idx_dict

def convert_ids_to_idx(id_idx_dict, dicts_to_convert):
    '''
    Modify all the dictionaries' keys and values in place from article_id to index  
    '''
    def convert_value(v):
        '''
        Simply comvert a list of ids into a list of idx
        '''
        if type(v) == list: 
            v = [id_idx_dict[i] for i in v]
        return v

    res_dicts = [{}, {}, {}, {}]
    i = 0
    for dic in dicts_to_convert:
        new_dict = res_dicts[i]
        for k, v in dic.items():
            new_key = id_idx_dict[k]
            new_dict[new_key] = convert_value(v)
        i += 1
    return res_dicts[0], res_dicts[1], res_dicts[2], res_dicts[3] 


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

# Get article_id to idx dict of only article 
id_idx_dict = get_ids_idx_dict(obj_dict)

# Convert all ids in dicts to idx
dicts_to_convert = [obj_dict, ent_adj_dict, agn_adj_dict, qot_adj_dict]
obj_dict, ent_adj_dict, agn_adj_dict, qot_adj_dict = convert_ids_to_idx(id_idx_dict, dicts_to_convert)

# Process dict_list so articles connected via one hop are in their adj_lists each other 
dict_list = [agn_adj_dict, qot_adj_dict]
art_adj_dict = link_articles(ent_adj_dict, dict_list)

print(art_adj_dict.keys())
print(len(art_adj_dict.keys()))
print(obj_dict)
print(len(obj_dict))
print('DONE')