import json
import os
import numpy as np
import pandas as pd
import csv
import sys
from scipy.sparse import csr_matrix
from utils.url_classifier.url_utils import UrlUtils

dirpath = os.path.dirname(os.path.realpath(__file__))
dirpath = os.path.dirname(dirpath) + '/data/'

# Paths for labeled data files from data dir
file_list = ['BuzzFeed_fb_urls_parsed.csv', 
             'data_from_Kaggle.csv',
             'fakeNewsNet_data/politifact_real.csv', 
             'fakeNewsNet_data/politifact_fake.csv',]

def store_labeled_articles(f_list):
    res = np.array([['url', 'label']])
    url_util = UrlUtils()
    with open(dirpath + 'labeled_articles.csv', mode='w') as csv_w:
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

def get_article_dict():
    reader = csv.reader(open(dirpath+'labeled_articles.csv', mode='r'))
    next(reader)

    idx_art_dic = {}
    url_idx_dic = {}

    for row in reader:
        url    = row[0]
        label  = row[1]
        art_id = row[2]
        
        idx_art_dic[art_id] = {'url': url, 'label': label}
        url_idx_dic[url]    = art_id

    return idx_art_dic, url_idx_dic


def get_adj_matrix(b, idx_art_dic, url_idx_dic):
    adj_mat = {}
    all_ent = process_entity(b['entity'], idx_art_dic, url_idx_dic)
    set_adj_articles(b['wasDerivedFrom'], all_ent)
    return all_ent

# returns a dict with all article urls with labels in merged.json
def process_entity(entity, idx_art_dic, url_idx_dic):
    dict_obj = next(iter(entity.values()))
    orig = get_orig(dict_obj)
    res = {}
    for key, ent in entity.items():
        if ent[orig+'type'] == 'article':
            url      = ent[orig+'url']
            url_idx  = url_idx_dic[url]     if url in url_idx_dic else -1
            art_obj  = idx_art_dic[url_idx] if url_idx != -1      else {'label': -1}
            res[url] = int(art_obj['label'])
    return res

def get_orig(dic):
    k = list(dic.keys())[0]
    i = k.find(':')
    return k[: i+1]

def set_adj_articles(rels, entity_dic):

    for key, rel in rels.items():
        # print(rel)
        from_n = remove_originator(list(rel.values())[1]) 
        to_n   = remove_originator(list(rel.values())[0])
        # print(from_n)
        # print(to_n)

def remove_originator(url):
    return url[url.find(':')+1 :]

# Process all article urls and create a csv file and a dict obj
'''store_labeled_articles(file_list)
'''
idx_art_dic, url_idx_dic = get_article_dict()

# Process a merged bundle file from merge_prov_graphs into a dict obj
my_path = os.path.abspath(os.path.dirname(__file__))
path = os.path.join(my_path, 'merged.json')

json_f = open(path, mode='r')
json_str = json_f.read()
bundle = json.loads(json_str)['bundle']

# Process the bundle into a adjacency matrix
adj = get_adj_matrix(bundle, idx_art_dic, url_idx_dic)
print('donE')
