import json
import os
import numpy as np
import pandas as pd 
import csv
import sys
import copy
import execnet
import itertools
from gcn import train
from collections import defaultdict
from scipy.sparse import csr_matrix
from utils.url_classifier.url_utils import UrlUtils

path = os.path.dirname(os.path.realpath(__file__))
dirpath = os.path.dirname(path) + '/data/datasets/'
gcn_path = path + '../../gcn/gcn'

# from gcn_path import gcn

# import time
# start = time.time()

# end = time.time()
# print(end - start)

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
                if k_1 == k_2:
                    adj_dict[k_1] = adj_dict[k_1] + [k_1] if k_1 in adj_dict else [k_1]
                for i in v_2:
                    if i in adj_entities and obj_dict[i]['type'] != 'publisher':
                        adj_dict[k_1] = adj_dict[k_1] + [k_2] if k_1 in adj_dict else [k_2]
                    else:
                        adj_dict[k_1] = adj_dict[k_1] if k_1 in adj_dict else []
        # Process on fts_dict
        for k, v in dic.items():
            for f in v:
                fts_dict[k] = fts_dict[k] + [f] if k in fts_dict else [f]

    return adj_dict, fts_dict

def handle_indirect_persons(aid_fid_dict, obj_dict, qot_per_dict):
    ''' Link persons who are indirectly connencted to articles
    '''
    for k, adj_quotes in aid_fid_dict.items():
        for q_id, p_id_lst in qot_per_dict.items():
            if q_id in adj_quotes: 
                for p_id in p_id_lst:
                    adj_quotes.append(p_id)
        adj_quotes = list(set(adj_quotes))
    return aid_fid_dict

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

    res_dicts = [{}, {}, {}, {}, {}]
    i = 0
    for dic in dicts_to_convert:
        new_dict = res_dicts[i]
        for k, v in dic.items():
            new_key = art_id_idx_dict[k] if k in art_id_idx_dict else fts_id_idx_dict[k]
            new_dict[new_key] = convert_value(v)
        i += 1
    return res_dicts[0], res_dicts[1], res_dicts[2], res_dicts[3], res_dicts[4]

def get_y(aid_fid_dict, article_label_dic, obj_dict):
    y = []
    for k, v in aid_fid_dict.items():
        typ = obj_dict[k]['type']
        if typ == 'article':
            url = obj_dict[k]['val']
            y_i = article_label_dic[url] if url in article_label_dic else -1
            y.append(int(y_i))
        else: 
            print(typ)
    return y

def remove_prefix(adj_mat, fts_mat):
    ''' Remove all 'a' and 'f' in front of ids
    '''
    def remove_prefix_val(v):
        return [int(fid[1:]) for fid in v]

    adj_mat = dict((int(k[1:]), remove_prefix_val(v)) for (k, v) in adj_mat.items())
    fts_mat = dict((int(k[1:]), remove_prefix_val(v)) for (k, v) in fts_mat.items())
    return adj_mat, fts_mat

def get_n_d(aid_adj_dict, aid_fid_dict):
    n = len(aid_adj_dict)
    d = len(set(list(itertools.chain.from_iterable(aid_fid_dict.values()))))
    return n, d

def convert_dict_to_mat(adj_dict, fts_dict, n, d):
    adj_mat = np.zeros((n, n))
    fts_mat = np.zeros((n, d+1))
    fids = []
    for i in range(n):
        adj_row = adj_dict[i]
        fts_row = fts_dict[i]
        for a_id in adj_row:
            adj_mat[i][a_id] = 1
        for f_id in fts_row:
            fids.append(f_id)
            fts_mat[i][f_id] = 1
    fts_mat[:, d] = 1
    print(adj_mat)
    print(np.sum(adj_mat, axis=1))
    return adj_mat, fts_mat
    
def get_data_for_gcn(adj_dict, fts_mat, y, n, d):
    graph = defaultdict(int, adj_dict)
    ally = np.zeros((n, 2))
    for i, yi in enumerate(y, start=0):
        #if   yi == -1: ally[i][2] = 1
        #el
        if yi ==  0: ally[i][1] = 1
        elif yi ==  1: ally[i][0] = 1

    allx = csr_matrix(np.array(fts_mat))
    
    return allx[:20], ally[:20], allx[:120], ally[:120], allx[120:], ally[120:], graph
    # return x, y, tx, ty, allx, ally, graph


# Paths for labeled data files from data dir
file_list = ['BuzzFeed_fb_urls_parsed.csv', 
             'data_from_Kaggle.csv',
             'fakeNewsNet_data/politifact_real.csv', 
             'fakeNewsNet_data/politifact_fake.csv',]

# Process all article urls and create a csv file and a dict obj
saved_file_name = store_labeled_articles(file_list)

article_label_dic = get_article_dict(saved_file_name)

# obj_dict: obj_id to {type, val}
# !!! Special case: there are some persons with 'to' attributes. they are connected to only quotes
# ent/agn/qot_adj_dict: id to [ids] 
obj_dict, ent_adj_dict, agn_adj_dict, qot_adj_dict, qot_per_dict = call_python_version('2.7', 'src.gcn_db_processor', 'process_db', [])

# Get article_id to idx dict of only article 
art_id_idx_dict, fts_id_idx_dict = get_ids_idx_dicts(obj_dict)

# Convert all ids in dicts to idx
dicts_to_convert = [obj_dict, ent_adj_dict, agn_adj_dict, qot_adj_dict, qot_per_dict]
obj_dict, ent_adj_dict, agn_adj_dict, qot_adj_dict, qot_per_dict = convert_ids_to_idx(art_id_idx_dict, fts_id_idx_dict, dicts_to_convert)

# Separate ent_adj into two pre reuslt dictionaries
tmp_aid_adj_dict, tmp_aid_fid_dict = separate_arts(ent_adj_dict)

# Process dict_list so articles connected via one hop are in their adj_lists each other
dict_list = {'non-art': tmp_aid_fid_dict, 'agent': agn_adj_dict, 'quote': qot_adj_dict}
aid_adj_dict, aid_fid_dict = link_articles(tmp_aid_adj_dict, tmp_aid_fid_dict, obj_dict, dict_list)

# Handle special case: add persons who are indirectly connected to articles.
# ex) if art1--q1--p1--q2--art2, then p1 is the feature of art1 and art2 but art1 and art2 are not connected
aid_fid_dict = handle_indirect_persons(aid_fid_dict, obj_dict, qot_per_dict)

# Add label vector on obj_dict  
y = get_y(aid_adj_dict, article_label_dic, obj_dict)

n, d = get_n_d(aid_adj_dict, aid_fid_dict)

adj_dict, fts_dict = remove_prefix(aid_adj_dict, aid_fid_dict)
adj_mat, fts_mat   = convert_dict_to_mat(adj_dict, fts_dict, n, d)

x, y, tx, ty, allx, ally, graph = get_data_for_gcn(adj_dict, fts_mat, y, n, d)



# Testing
# print(set(aid_adj_dict.keys()))
# print(set(aid_fid_dict.keys()))
print('    adj  n :', len(aid_adj_dict.keys()))
print('    fts  n :', len(aid_fid_dict.keys()))
a = set(list(itertools.chain.from_iterable(aid_adj_dict.values())))
b = set(list(itertools.chain.from_iterable(aid_fid_dict.values())))
print('nonempty n :', len(a))
print('         d :', len(b))

l = 0
for lst in aid_adj_dict.values():
    if len(lst) == 0: l += 1
print('   empty n :', l)

print('         n :', str(l+len(a)))

c = 0
d = []
e = []
f = []
g = []
h = []
i = []
j = []
l = []
for k, v in obj_dict.items():
    if k[0] == 'a': 
        c += 1
        d.append(k)
    if v['type'] == 'article':
        f.append(k)

    elif v['type'] == 'reference':
        g.append(k)
    
    elif v['type'] == 'government':
        j.append(k)
    
    elif v['type'] == 'publisher':
        h.append(k)
    
    elif v['type'] == 'quote':
        e.append(k)
    
    elif v['type'] == 'person':
        if 'to' in v:
            print(v['to'])
        l.append(k)
    
    else: 
        print(v['type'])
        i.append(k)
print('         n :', c)

print('         n :', len(set(d)))
print('         d :', len(set(g + j + h + e + l )))
print('       ref :', len(set(g)))
print('       gov :', len(set(j)))
print(' publisher :', len(set(h)))
print('     quote :', len(set(e)))
print('    person :', len(set(l)))
print('     trash :', len(set(i)))
print('         n :', len(set(f)))



e = []
f = []
g = []
h = []
i = []
j = []
l = []
for k in b:
    if obj_dict[k]['type'] == 'article':
        f.append(k)

    elif obj_dict[k]['type'] == 'reference':
        g.append(k)
    
    elif obj_dict[k]['type'] == 'government':
        j.append(k)
    
    elif obj_dict[k]['type'] == 'publisher':
        h.append(k)
    
    elif obj_dict[k]['type'] == 'quote':
        e.append(k)
    
    elif obj_dict[k]['type'] == 'person':
        l.append(k)
    
    else: 
        print(obj_dict(k))
        i.append(k)

print('BBBBBBBBBBB')
print('         n :', len(set(d)))
print('         d :', len(set(g + j + h + e + l )))
print('       ref :', len(set(g)))
print('       gov :', len(set(j)))
print(' publisher :', len(set(h)))
print('     quote :', len(set(e)))
print('    person :', len(set(l)))
print('     trash :', len(set(i)))
print('         n :', len(set(f)))


# print('         y :', y)
print('     y len :', len(y))

print('DONE')

train.train(x, y, tx, ty, allx, ally, graph)
