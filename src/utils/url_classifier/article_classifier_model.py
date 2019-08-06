import argparse
import json
import subprocess
import pandas as pd
import numpy as np
import csv
import os
import time
import urllib
import os.path
from numpy import genfromtxt
from numpy import linalg as LA
from sklearn.cluster import KMeans
from sklearn import svm
from sklearn.semi_supervised import LabelSpreading
from sklearn.model_selection import train_test_split
from newspaper import Article
from newsplease import NewsPlease
from bs4 import BeautifulSoup

dirpath = os.path.dirname(os.path.realpath(__file__))

class Article_Classifier(object):
    def __init__(self, url=None, news3k=None):
        self.url = url
        self.news3k = news3k
        self.newspl = None
        self.features = None
        self.bin_f = None
        self.stats = {}
        self.clf = self.train()
    
    def reset_url(self, url, news3k=None):
        self.url = url
        self.news3k = news3k
        self.newspl = None
        self.features = None
        self.bin_f = None

    def _run_libraries(self):
        # news3k is more significant than newpls so failure raises e
        try:
            if not self.news3k:
                news3k  = Article(self.url)
                self.news3k = news3k
            print('run_libs1')
            self.news3k.build()
            print('run_libs2')
            self.news3k.download()
            print('run_libs3')
            self.news3k.parse()
            print('run_libs4')
            return
        except Exception as e:
            print('Err occured from news3k : ', e)
            raise e
            
        try:
            self.newspl = NewsPlease.from_url(self.url)
        except Exception as e:
            print('Err occured from newspl but it is fine : ', e)
            self.newspl = None

    def extract_features(self):
        self._run_libraries()
        print('extract_features1')
        if self.news3k:
            meta           = self.news3k.meta_data if self.news3k.meta_data else {}
            meta_kwords    =  self.news3k.meta_keywords
            sub_domain     = self.url[self.url[8:].index('/') + 8 :] 
            sub_domain_arr = self.url.split('/') if sub_domain[len(sub_domain)-1] != '/' else self.url.split('/')[:-1]
            meta_tag_arr   = BeautifulSoup(self.news3k.html, features='lxml').find_all('meta')
            print('extract_features2')
            res = [ self.newspl.authors[0]        if self.newspl and len(self.newspl.authors)           else self.news3k.authors      or  None,
                    self.newspl.date_publish      if self.newspl and self.newspl.date_publish           else self.news3k.publish_date or  None,
                    meta['og']['price']['amount'] if 'og'      in meta and 'price'   in meta['og']      else None,
                    meta['og']['type']            if 'og'      in meta and 'type'    in meta['og']      else None,
                    meta['article']['section']    if 'article' in meta and 'section' in meta['article'] else None,
                    meta['section']               if 'section' in meta                                  else None,
                    mata['type']                  if 'type'    in meta                                  else None,
                    self.news3k.meta_keywords     if len(meta_kwords) and meta_kwords[0] != ''          else None,
                    self.news3k.keywords          if len(self.news3k.keywords)                          else None,
                    sub_domain                                                                                   ,
                    sub_domain_arr                                                                               ,
                    meta_tag_arr                                                                                 ,
                    self.news3k.text ]
            print('extract_features3')
        else:
            res = None
        
        self.features = res
        return res

    def convert_into_bin(self):
        ''' 
        Features: type
        auth     : bin,
        p_date   : bin,
        price    : bin,
        m.og.ty  : if article or website then 1, else 0
        m.at.sec : bin,
        m.sect   : bin,
        m.type   : bin,
        kwords   : if statistics or government, 1 else 0,
        m.kwords : if statistics or government, 1 else 0,
        length of subdomain,	
        number of subdomains,
        number of meta_tags,
        word_count
        '''
        res = []
        if self.features:
            res = [ 
                1 if self.features[0]                     else 0,
                1 if self.features[1]                     else 0,
                1 if self.features[2]                     else 0,
                1 if self._is_art_web(self.features[3])   else 0,
                1 if self.features[4]                     else 0,
                1 if self.features[5]                     else 0,
                1 if self.features[6]                     else 0,
                1 if self._has_stat_gov(self.features[7]) else 0,
                1 if self._has_stat_gov(self.features[8]) else 0,
                len(self.features[9]),
                len(self.features[10]),
                len(self.features[11]),
                len(self.features[12].split())
            ]
        self.bin_f = res
        return res

    def _is_art_web(self, tyype):
        if tyype != None:
            return tyype == 'article' or tyype == 'website'

    def _has_stat_gov(self, kwords):
        if kwords != None:
            for word in kwords:
                low_w = word.lower()
                if low_w == 'government' or low_w == 'statistics':
                    return True
        return False
    
    def predict(self):
        print('predict1')
        self.extract_features()
        print('predict2')
        self.convert_into_bin()
        print('predict3')
        self.bin_f[9]  = (self.bin_f[9]  - self.stats['mu_9'])  / self.stats['sd_9']
        self.bin_f[10] = (self.bin_f[10] - self.stats['mu_10']) / self.stats['sd_10']
        self.bin_f[11] = (self.bin_f[11] - self.stats['mu_11']) / self.stats['sd_11']
        self.bin_f[12] = (self.bin_f[12] - self.stats['mu_12']) / self.stats['sd_12']
        print('The Features of the url is : ')
        print(self.bin_f)

        np_bin = np.array(self.bin_f)
        return self.clf.predict(np_bin.reshape(1, -1))

    def train(self):
        # dataset musht have features from column 1 to the one before the last column and the last column is y
        # TODO training set is based on not actual urls meaning some urls are redirecting url
        data = genfromtxt(dirpath + '/train_xy.csv', delimiter=',')
        print('training 1')
        n, d = data.shape

        x_train = data[:, 1:d-5]
        y_train = data[:, d-1:]

        mu_9  = np.mean(data[:, d-5])
        mu_10 = np.mean(data[:, d-4])
        mu_11 = np.mean(data[:, d-3])
        mu_12 = np.mean(data[:, d-2])
        
        sd_9  = np.std(data[:, d-5])
        sd_10 = np.std(data[:, d-4])
        sd_11 = np.std(data[:, d-3])
        sd_12 = np.std(data[:, d-2])
        
        x_train[:, 9]  = (data[:, d-5] - mu_9)  / sd_9
        x_train[:, 10] = (data[:, d-4] - mu_10) / sd_10
        x_train[:, 11] = (data[:, d-3] - mu_11) / sd_11
        x_train[:, 12] = (data[:, d-2] - mu_12) / sd_12

        self.stats['mu_9']  = mu_9
        self.stats['sd_9']  = sd_9
        self.stats['mu_10'] = mu_10
        self.stats['sd_10'] = sd_10
        self.stats['mu_11'] = mu_11
        self.stats['sd_11'] = sd_11
        self.stats['mu_12'] = mu_12
        self.stats['sd_12'] = sd_12

        np.savetxt(dirpath + '/recent_train_x.csv', x_train, delimiter=",")
        print('training 2')
        clf = svm.SVC(gamma='scale', kernel='rbf', degree=7)
        clf.fit(x_train, y_train.ravel()) 
        return clf


def extract_features(output_name, file_path):
    if file_path:
        my_path = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(my_path, file_path)
        data = pd.read_csv(path)
        
        url_feature_processor = Article_Classifier('None')
        
        with open(output_name + '.csv', mode='a') as csv_file, \
             open(output_name + '_failed.csv', mode='a') as csv_file_failed, \
             open(output_name + '_features.csv', mode='a') as csv_file_features:
            
            fieldnames        = ['idx', 
                                'original_URL', 
                                'author', 
                                'publish_date', 
                                'price', 
                                'meta_og_type', 
                                'meta_art_sect', 
                                'meta_sect',
                                'meta_type' 
                                'meta_keywords', 
                                'keywords',
                                'meta_tags',
                                'sub_w_count', 
                                'sub_count',
                                'word_count']

            fieldnames_features = ['idx', 
                                'original_URL', 
                                'author', 
                                'publish_date', 
                                'price', 
                                'meta_og_type', 
                                'meta_art_sect',
                                'meta_type' 
                                'meta_sect', 
                                'meta_keywords', 
                                'keywords',
                                'meta_tags',
                                'subdomain',
                                'text']
            
            fieldnames_failed = ['original_URL', 
                                'error']

            writer        = csv.DictWriter(csv_file,          fieldnames=fieldnames)
            writer_fts    = csv.DictWriter(csv_file_features, fieldnames=fieldnames_features)
            writer_failed = csv.DictWriter(csv_file_failed,   fieldnames=fieldnames_failed)
            
            idx = 0
            for row in data.itertuples():
                url = row[1]
                try:
                    url_feature_processor.reset_url(url)

                    print(idx, ' ', url)
                    start = time.time()
                    features = url_feature_processor.extract_features()
                    end = time.time()
                    time_taken = end - start
                    print('Time on extracting: ',time_taken)
                    
                    start_bins = time.time()
                    bins = url_feature_processor.convert_into_bin()
                    end_bins = time.time()
                    time_taken_bins = end_bins - start_bins
                    print('Time on converting: ',time_taken_bins)

                    writer.writerow({
                        'idx'          : idx,
                        'original_URL' : row[1], 
                        'author'       : bins[0],
                        'publish_date' : bins[1], 
                        'price'        : bins[2], 
                        'meta_og_type' : bins[3], 
                        'meta_art_sect': bins[4], 
                        'meta_sect'    : bins[5],
                        'meta_type'    : bins[6],
                        'meta_keywords': bins[7], 
                        'keywords'     : bins[8], 
                        'meta_tags'    : bins[9],
                        'sub_w_count'  : bins[10],
                        'sub_count'    : bins[11],
                        'word_count'   : bins[12]
                    })

                    writer_fts.writerow({
                        'idx'          : idx,
                        'original_URL' : row[1], 
                        'author'       : features[0],
                        'publish_date' : features[1], 
                        'price'        : features[2], 
                        'meta_og_type' : features[3], 
                        'meta_art_sect': features[4], 
                        'meta_sect'    : features[5],
                        'meta_type'    : features[6], 
                        'meta_keywords': features[7], 
                        'keywords'     : features[8],
                        'meta_tags'    : features[9],
                        'subdomain'    : features[10],
                        'text'         : features[12]
                    })

                    idx += 1  

                except Exception as e:
                    print(e, url)
                    writer_failed.writerow({
                        'original_URL': row[1],
                        'error': e
                    })

def main():
    arg_parser = argparse.ArgumentParser(
        description="Process and extract features of urls and train a model to identify news urls")
    
    # Must specify the name of output file for any purpose
    arg_parser.add_argument('-o', '--output', dest='output', help='Name of the result file.')
    
    # The argument below is for extracting features before running any learning algorithm
    arg_parser.add_argument('-p', '--path', dest='path', help='A training file path of urls. The first column is url and the second is label.')

    args = arg_parser.parse_args()

    output_name  = args.output
    file_path    = args.path
    train_path   = args.path
    test_path    = args.test

    if fle_path:
        print('Executing feature extraction')
        extract_features(output_name, file_path)

    else:
        print('No matching arguments skip main.')

# main()

# used to test the accuracy of traning set using SVM
def main3():
    print(0)
    X = genfromtxt('src/utils/url_classifier/train_xy.csv', delimiter=',')
    print(123)
    x_1, x_2 = train_test_split(X, test_size=200/1958)
    n, d = x_1.shape

    x_train = x_1[:, 1:d-5]
    print(x_train[0])
    y_train = x_1[:, d-1:]
    
    x_test = x_2[:, 1:d-5]
    y_test = x_2[:, d-1:]
    print(x_train.shape)
    print(y_train.shape)
    clf = svm.SVC(gamma='scale', kernel='rbf', degree=7)
    clf.fit(x_train, y_train.ravel()) 

    y_pred = clf.predict(x_test)
    diff = np.array(y_test.T - y_pred.T)
    
    print('The accuracy is : ', (200 - np.count_nonzero(diff)) / 200)

    # np.savetxt("svm_pred.csv", y_pred, delimiter=",")
    # np.savetxt("svm_real.csv", y_test, delimiter=",")

# main3()
