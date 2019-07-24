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

def call_python_version(Version, Module, Function, ArgumentList):
    gw      = execnet.makegateway("popen//python=python%s" % Version)
    channel = gw.remote_exec("""
        from %s import %s as the_function
        channel.send(the_function(*channel.receive()))
    """ % (Module, Function))
    channel.send(ArgumentList)
    return channel.receive()

# Process all article urls and create a csv file and a dict obj
# store_labeled_articles(file_list)

idx_art_dic, url_idx_dic = get_article_dict()

# dictionries {article_id: ...}
obj_dict, ent_adj_dict, agn_adj_dict, qot_adj_dict = call_python_version('2.7', 'src.gcn_db_processor', 'main', [])

# Process the bundle into a adjacency matrix

print('donE')
