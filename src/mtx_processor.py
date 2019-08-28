# TODO SEE how many have labels and not

import json
import os
import csv
import sys
import copy
import execnet
import itertools
import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from gcn import train
from collections import defaultdict
from scipy.sparse import csr_matrix
from utils.url_classifier.url_utils import UrlUtils

path = os.path.dirname(os.path.realpath(__file__))
dirpath = os.path.dirname(path) + '/data/datasets/'

class MtxProcessor(object):
    def __init__(self):
        # Paths for labeled data files from data dir
        self.file_list = ['fakeNewsNet_data/politifact_real.csv', 
                        'fakeNewsNet_data/politifact_fake.csv', 
                        'fakeNewsNet_data/gossipcop_real.csv', 
                        'fakeNewsNet_data/gossipcop_fake.csv', 
                        'dataset_from_Kaggle.csv',
                        'facebook-fact-check_parsed.csv']

        ''' For showing graph '''
        self.adj_dict = {}
        self.y = {}
        
        ''' All matrices '''
        self.adj_mtx = {}
        self.full_ft_mtx = {}
        self.bin_ft_mtx = {}

        self.n = 0
        self.d = 0

        self.get_all_mtx()

    def get_all_mtx(self):
        # Process all article urls and create a csv file and a dict obj
        '''saved_file_name   = self.store_labeled_articles(self.file_list)'''
        article_label_dic = self.get_article_dict('labeled_articles.csv')

        # obj_dict: obj_id to {type, val}
        # ent/agn/qot_adj_dict: id to [ids] 
        obj_dict, ent_adj_dict, agn_adj_dict, qot_adj_dict, qot_per_dict = self.call_python_version('2.7', 'db_processor', 'process_db', [])

        with open(dirpath + 'obj_dict.csv', mode='w') as f:
            headers = ['id', 'type', 'val'] 
            writer = csv.DictWriter(f, fieldnames=headers)
            for i, dic in obj_dict.items():
                typ = dic['type']
                val = dic['val']
                writer.writerow({'id': i, 'type': typ, 'val': val}) 

        # Get article_id to idx dict of only article 
        art_id_idx_dict, ft_id_idx_dict = self.get_ids_idx_dicts(obj_dict)

        # Filter articles which is not labeled
        # ent_adj_dict = self.filter_unlabeled_articles(ent_adj_dict, obj_dict, article_label_dic)

        # Convert all ids in dicts to idx
        dicts_to_convert = [obj_dict, ent_adj_dict, agn_adj_dict, qot_adj_dict, qot_per_dict]
        obj_dict, ent_adj_dict, agn_adj_dict, qot_adj_dict, qot_per_dict = self.convert_ids_to_idx(art_id_idx_dict, ft_id_idx_dict, dicts_to_convert)
        # print('len(ent_adj_dict)')
        # print(len(ent_adj_dict))
        print('len(art_id_idx_dict)')
        print(len(art_id_idx_dict))
        # print(art_id_idx_dict.values())
        # Separate ent_adj into two pre reuslt dictionaries
        tmp_aid_adj_dict, tmp_aid_fid_dict = self.separate_arts(ent_adj_dict)
        # print('tmp_aid_adj_dict.values()')
        # print(tmp_aid_adj_dict.keys())
        # print(tmp_aid_adj_dict.values())

        # Process dict_list so articles connected via one hop are in their adj_lists each other
        dict_list = {'non-art': tmp_aid_fid_dict, 'agent': agn_adj_dict, 'quote': qot_adj_dict}
        aid_adj_dict, aid_fid_dict = self.link_articles(tmp_aid_adj_dict, tmp_aid_fid_dict, obj_dict, dict_list)
        print(len(aid_adj_dict))
        print(len(aid_fid_dict))
        # Handle special case: add persons who are indirectly connected to articles.
        # ex) if art1--q1--p1--q2--art2, then p1 is the feature of art1 and art2 but art1 and art2 are not connected
        aid_fid_dict = self.handle_indirect_persons(aid_fid_dict, obj_dict, qot_per_dict)
        print(len(aid_fid_dict))
        # self.save_articles(obj_dict, aid_fid_dict, article_label_dic)

        # get n and d dimension
        self.n, self.d = self.get_n_d(aid_adj_dict, aid_fid_dict)
        # Add label vector on obj_dict  
        self.y = self.get_y(aid_adj_dict, article_label_dic, obj_dict)

        # Get all mtx
        self.bin_ft_mtx  = self.return_bin_ft_mtx(tmp_aid_adj_dict, aid_fid_dict, obj_dict, self.n)
        print(len(aid_adj_dict))
        print(len(aid_fid_dict))
        self.adj_dict, ft_dict = self.remove_prefix(aid_adj_dict, aid_fid_dict)
        print(self.n) 
        print(len(self.adj_dict))
        print(len(ft_dict))
        # print(1+'1')

        self.adj_mtx, self.full_ft_mtx = self.convert_dict_to_mtx(self.adj_dict, ft_dict, self.n, self.d)

    def return_bin_ft_mtx(self, tmp_aid_adj_dict, aid_fid_dict, obj_dict, n):
        # get binned feature matrix
        ft_bin_dict = self.get_bin_ft_dict(tmp_aid_adj_dict, aid_fid_dict, obj_dict, n)
        ft_bin_dict = self.remove_only_prefix(ft_bin_dict)

        len_r, len_q, len_a = self.get_len_of_features(ft_bin_dict)
        dict_without_q, d_bin = self.get_no_q_dict(ft_bin_dict)

        ft_bin_dict = self.convert_bin_ft_toidx(ft_bin_dict, dict_without_q)

        return self.convert_bin_dict_to_mtx(ft_bin_dict, n, d_bin, len_r, len_q, len_a)

    def show_adj_graph(self):
        G = nx.Graph()
        true_nodes = []
        fake_nodes = []
        unlabeled_nodes = []
        G.add_nodes_from(list(self.adj_dict.keys()))
        for k, v in self.adj_dict.items():
            for f in v: G.add_edge(k, f)
            y_k = self.y[k]
            if y_k == -1 : unlabeled_nodes.append(k)
            if y_k == 1  : true_nodes.append(k)
            elif y_k == 0: fake_nodes.append(k)
            
        pos = nx.spring_layout(G)
        nx.draw_networkx_nodes(G,pos, nodelist=true_nodes, node_color='b', node_size=50, alpha=0.6)
        nx.draw_networkx_nodes(G,pos, nodelist=fake_nodes, node_color='r', node_size=50, alpha=0.6)
        nx.draw_networkx_nodes(G,pos, nodelist=unlabeled_nodes, node_color='g', node_size=50, alpha=0.6)
        nx.draw_networkx_edges(G,pos, width=1.0, alpha=0.2)
        
        plt.show()

    def save_articles(self, obj_dict, aid_fid_dict, article_label_dic):
        with open(dirpath + 'articles.csv', mode='w') as f:
            headers = ['url', 'label'] 
            writer = csv.DictWriter(f, fieldnames=headers)
            labeled_n = 0
            unlabeled_n = 0
            for art, _ in aid_fid_dict.items():
                # print(obj_dict[art])
                url = obj_dict[art]['val']
                y_i = article_label_dic[url] if url in article_label_dic else -1
                if url in article_label_dic: labeled_n += 1
                else: unlabeled_n += 1 
                writer.writerow({ 'url': url, 'label': y_i})
            print('labeled_n :' + labeled_n)
            print('unlabeled_n :' + unlabeled_n)
        # print('1'+1)


    ''' The rest of functions below are helpers for above functions. Do not call them individually '''
    
    def store_labeled_articles(self, f_list):
        ''' From the file list, extract only url and label
            return the saved file name
        '''
        def valid(url):
            if url[0:4] != 'http': return 'http://' + url
            return url

        res = np.array([['url', 'label']])
        url_util = UrlUtils()
        saved_file_name = 'labeled_articles.csv'
        with open(dirpath + saved_file_name, mode='w') as csv_w:
            writer = csv.writer(csv_w)
            for f_name in f_list:
                print(dirpath + f_name)
                with open(dirpath + f_name, mode='r') as csv_f:
                    reader = csv.DictReader(csv_f)
                    tmp = [[valid(row['url']), row['label']] for row in reader if url_util.is_valid_url(valid(row['url']))]
                    res = np.append(res, tmp, axis=0)
            idxes = list(range(res.shape[0]))[:-1]
            idx_row = np.array(['idx'] + idxes)
            res = np.c_[res, idx_row]
            writer.writerows(res)
        return saved_file_name

    def get_article_dict(self, file_name):
        ''' return article_url(str) to label(0 or 1) dictionary 
        '''
        reader = csv.reader(open(dirpath + file_name, mode='r'))
        # reader = csv.reader(open('/home/gckim93' +  file_name, mode='r'))
        next(reader)
        article_label_dic = {r[0]: r[1] for r in reader}
        return article_label_dic

    def call_python_version(self, Version, Module, Function, ArgumentList):
        gw      = execnet.makegateway("popen//python=python%s" % Version)
        channel = gw.remote_exec("""
            from %s import %s as the_function
            channel.send(the_function(*channel.receive()))
        """ % (Module, Function))
        channel.send(ArgumentList)
        return channel.receive()

    def separate_arts(self, ent_adj_dict):
        ''' return dict that only includes aid : [aids] and dict that only includes aid: [fids]
        '''
        art_adj_dict = {}
        art_ft_dict = {}
        for k, v in ent_adj_dict.items():
            tmp_as = [] 
            tmp_fs = []
            for e in v:
                if e[0] == 'a': tmp_as.append(e)
                else          : tmp_fs.append(e)
            art_adj_dict[k] = tmp_as
            art_ft_dict[k] = tmp_fs

        return art_adj_dict, art_ft_dict

    def filter_unlabeled_articles(self, ent_adj_dict, obj_dict, article_label_dic):
        return dict((id, ids) for id, ids in ent_adj_dict.items() if not(obj_dict[id]['type'] == 'article' and obj_dict[id]['val'] not in article_label_dic))
        
    def link_articles(self, adj_dict, ft_dict, obj_dict, dict_list):
        ''' Links articles that are two hops away from each other by quote or agent
            return new article_id to [article_ids] dictionary and a feature dictionary that keeps 
            track of which agents or quotes are attributed to articles
        '''
        alert = 0
        for typ, dic in dict_list.items(): 
            # Process on adj_dict
            for k_1, v_1 in dic.items():
                adj_entities = v_1
#                 print(alert)
                for k_2, v_2 in dic.items():
                    if k_1 == k_2: continue
                        # adj_dict[k_1] = adj_dict[k_1] + [k_1] if k_1 in adj_dict else [k_1]
                    for i in v_2:
                        alert += 1
                        if i in adj_entities:
                            adj_dict[k_1] = adj_dict[k_1] + [k_2] if k_1 in adj_dict else [k_2]
                        else:
                            adj_dict[k_1] = adj_dict[k_1] if k_1 in adj_dict else []
            # Process on ft_dict
            for k, v in dic.items():
                for f in v:
                    ft_dict[k] = ft_dict[k] + [f] if k in ft_dict else [f]

        return adj_dict, ft_dict

    def handle_indirect_persons(self, aid_fid_dict, obj_dict, qot_per_dict):
        ''' Link persons who are indirectly connencted to articles
        '''
        for k, adj_quotes in aid_fid_dict.items():
            for q_id, p_id_lst in qot_per_dict.items():
                if q_id in adj_quotes: 
                    for p_id in p_id_lst:
                        adj_quotes.append(p_id)
            adj_quotes = list(set(adj_quotes))
        return aid_fid_dict

    def get_ids_idx_dicts(self, obj_dict):
        ''' return art_id to idx dict and non_art_id to idx dict
        '''
        art_id_idx_dict = {}
        ft_id_idx_dict = {}
        
        art_idx = 0
        ft_idx = 0
        for k, v in obj_dict.items():
            if v['type'] == 'article':
                art_id_idx_dict[k] = 'a' +  str(art_idx)
                art_idx += 1
            else:
                ft_id_idx_dict[k] = 'f' + str(ft_idx)
                ft_idx += 1
        return art_id_idx_dict, ft_id_idx_dict

    def convert_ids_to_idx(self, art_id_idx_dict, ft_id_idx_dict, dicts_to_convert):
        ''' Modify all the dictionaries' keys and values in place from article_id to index  
        '''
        def convert_value(v):
            ''' Simply comvert a list of ids into a list of idx
            '''
            if type(v) == list: 
                v = [ft_id_idx_dict[i] if i in ft_id_idx_dict else art_id_idx_dict[i] for i in v]
            return v

        res_dicts = [{}, {}, {}, {}, {}]
        i = 0
        for dic in dicts_to_convert:
            new_dict = res_dicts[i]
            for k, v in dic.items():
                new_key = art_id_idx_dict[k] if k in art_id_idx_dict else ft_id_idx_dict[k]
                new_dict[new_key] = convert_value(v)
            i += 1
        return res_dicts[0], res_dicts[1], res_dicts[2], res_dicts[3], res_dicts[4]

    def get_y(self, aid_fid_dict, article_label_dic, obj_dict):
        y = []
        for k, v in aid_fid_dict.items():
            typ = obj_dict[k]['type']
            if typ == 'article':
                url = obj_dict[k]['val']
                if url in article_label_dic:
                    y_i = article_label_dic[url] 
                    y.append(int(y_i))
                else: 
                    # TODO assume this
                    # print(url)
                    y.append(-1)
        return y

    def remove_prefix(self, adj_dict, ft_dict):
        ''' Remove all 'a' and 'f' in front of ids
        '''
        def remove_prefix_val(v):
            return list(set([int(fid[1:]) for fid in v]))
        # for k, v in adj_dict.items():
            # if k == 'f3' or k == 'a3':
            #     print(k)
            #     print(len(v))
        adj_dict = dict((int(k[1:]), remove_prefix_val(v)) for (k, v) in adj_dict.items())
        ft_dict = dict((int(k[1:]), remove_prefix_val(v)) for (k, v) in ft_dict.items())
        # print(len(adj_dict))
        # print(len(ft_dict))
        return adj_dict, ft_dict

    def remove_only_prefix(self, ft_dict):
        ''' Remove all 'a' and 'f' in front of ids
        '''
        def remove_prefix_val(v):
            return list([int(ft[1:]) if type(ft) == str else ft for ft in v])

        ft_dict = dict((int(k[1:]), remove_prefix_val(v)) for (k, v) in ft_dict.items())
        return ft_dict

    def get_n_d(self, aid_adj_dict, aid_fid_dict):
        n = len(aid_adj_dict)
        d = len(set(list(itertools.chain.from_iterable(aid_fid_dict.values()))))
        return n, d

    def convert_dict_to_mtx(self, adj_dict, ft_dict, n, d):
        adj_mtx = np.zeros((n, n))
        ft_mtx = np.zeros((n, d+1))
        fids = []
        
        for i in range(n):
            adj_row = adj_dict[i]
            ft_row = ft_dict[i]
            for a_id in adj_row:
                adj_mtx[i][a_id] = 1
            for f_id in ft_row:
                fids.append(f_id)
                ft_mtx[i][f_id] = 1
        ft_mtx[:, d] = 1
        
        return adj_mtx, ft_mtx
        
    def get_bin_ft_dict(self, aid_adj_dict, aid_fid_dict, obj_dict, n):
        ''' return feature matrix but last three features are:
            # of reference, quotes, and articles
        '''
        bin_dict = dict()
        for aid, fids in aid_fid_dict.items():
            n_q = 0
            n_r = 0
            for fid in fids:
                if obj_dict[fid]['type'] == 'reference': n_r += 1
                elif obj_dict[fid]['type'] == 'quote'  : n_q += 1
                else: bin_dict[aid] = bin_dict[aid] + [fid] if aid in bin_dict else [fid]
            
            bin_dict[aid] = list(set(bin_dict[aid])) + [n_r, n_q] if aid in bin_dict else [n_r, n_q]
        
        for aid, aids in aid_adj_dict.items():
            bin_dict[aid] = bin_dict[aid] + [len(set(aids))] if aid in bin_dict else [0, 0, len(set(aids))]
    
        return bin_dict

    def get_len_of_features(self, ft_bin_dict):
        n_r = n_q = n_a = 0
        for _, fts in ft_bin_dict.items():
            numbers = fts[-3:]
            # print(numbers)
            tmp_r = numbers[0]
            tmp_q = numbers[1]
            tmp_a = numbers[2]
            n_r = tmp_r if tmp_r > n_r else n_r
            n_q = tmp_q if tmp_q > n_q else n_q
            n_a = tmp_a if tmp_a > n_a else n_a

        return n_r, n_q, n_a

    def get_no_q_dict(self, ft_bin_dict):
        only_fts = set()
        for aid, fts in ft_bin_dict.items():
            for ft in fts[:-3]:
                only_fts.add(ft)
        
        d = len(only_fts) + 3
        dic = dict((key, val) for val, key in enumerate(only_fts))
        return dic, d
        
    def convert_bin_ft_toidx(self, ft_bin_dict, dict_without_q):
        new_dict = dict()
        for aid, fts in ft_bin_dict.items():
            for ft in fts[:-3]:
                new_fts = dict_without_q[ft]
                new_dict[aid] = new_dict[aid] + [new_fts] if aid in new_dict else [new_fts]
            new_dict[aid] = new_dict[aid] + fts[-3:] if aid in new_dict else fts[-3:]
        return new_dict

    def convert_bin_dict_to_mtx(self, ft_bin_dict, n, d_bin, len_r, len_q, len_a):
        # mtx dimension is n x total length of features and binned features
        mtx = np.zeros((n, d_bin + len_r + len_q + len_a + 1))
        # print(d_bin + len_r + len_q + len_a + 1)
        # print(n)
        # print(len(ft_bin_dict))
        for i, fts in ft_bin_dict.items():
            # print((i, fts))
            for j in fts[:-3]:
                mtx[i][j] = 1
            mtx[i][d_bin + fts[-3]] = 1
            mtx[i][d_bin + len_r + fts[-2]] = 1
            mtx[i][d_bin + len_r + len_q + fts[-1]] = 1
        return mtx




# # Testing
# # print(set(aid_adj_dict.keys()))
# # print(set(aid_fid_dict.keys()))
# print('    adj  n :', len(aid_adj_dict.keys()))
# print('    ft  n :', len(aid_fid_dict.keys()))
# a = set(list(itertools.chain.from_iterable(aid_adj_dict.values())))
# b = set(list(itertools.chain.from_iterable(aid_fid_dict.values())))
# print('nonempty n :', len(a))
# print('         d :', len(b))

# l = 0
# for lst in aid_adj_dict.values():
#     if len(lst) == 0: l += 1
# print('   empty n :', l)

# print('         n :', str(l+len(a)))

# c = 0
# d = []
# e = []
# f = []
# g = []
# h = []
# i = []
# j = []
# l = []
# for k, v in obj_dict.items():
#     if k[0] == 'a': 
#         c += 1
#         d.append(k)
#     if v['type'] == 'article':
#         f.append(k)

#     elif v['type'] == 'reference':
#         g.append(k)
    
#     elif v['type'] == 'government':
#         j.append(k)
    
#     elif v['type'] == 'publisher':
#         h.append(k)
    
#     elif v['type'] == 'quote':
#         e.append(k)
    
#     elif v['type'] == 'person':
#         if 'to' in v:
#             print(v['to'])
#         l.append(k)
    
#     else: 
#         print(v['type'])
#         i.append(k)
# print('         n :', c)

# print('         n :', len(set(d)))
# print('         d :', len(set(g + j + h + e + l )))
# print('       ref :', len(set(g)))
# print('       gov :', len(set(j)))
# print(' publisher :', len(set(h)))
# print('     quote :', len(set(e)))
# print('    person :', len(set(l)))
# print('     trash :', len(set(i)))
# print('         n :', len(set(f)))


# e = []
# f = []
# g = []
# h = []
# i = []
# j = []
# l = []
# for k in b:
#     if obj_dict[k]['type'] == 'article':
#         f.append(k)

#     elif obj_dict[k]['type'] == 'reference':
#         g.append(k)
    
#     elif obj_dict[k]['type'] == 'government':
#         j.append(k)
    
#     elif obj_dict[k]['type'] == 'publisher':
#         h.append(k)
    
#     elif obj_dict[k]['type'] == 'quote':
#         e.append(k)
    
#     elif obj_dict[k]['type'] == 'person':
#         l.append(k)
    
#     else: 
#         print(obj_dict(k))
#         i.append(k)

# print('BBBBBBBBBBB')
# print('         n :', len(set(d)))
# print('         d :', len(set(g + j + h + e + l )))
# print('       ref :', len(set(g)))
# print('       gov :', len(set(j)))
# print(' publisher :', len(set(h)))
# print('     quote :', len(set(e)))
# print('    person :', len(set(l)))
# print('     trash :', len(set(i)))
# print('         n :', len(set(f)))


# # print('         y :', y)
# print('     y len :', len(y))

# print('DONE')
