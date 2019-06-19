import argparse
import json
import subprocess
import pandas as pd
import numpy as np
import csv
import time
import urllib
import os.path
from numpy import genfromtxt
from sklearn.cluster import KMeans
from newspaper import Article
from newsplease import NewsPlease

class ArticleClassifier(object):
    def __init__(self):
        pass
    
class UrlFeatureProcessor(object):
    def __init__(self, url, news3k = None):
        self.url = url
        self.news3k = news3k
        self.newspl = None
        self.features = None
        self.bin_f = None
    
    def reset_url(self, url):
        self.url = url
        self.news3k = None
        self.newspl = None
        self.features = None
        self.bin_f = None

    def _run_libraries(self):
        if not self.news3k:
            try:
                news3k  = Article(self.url)
                self.news3k = news3k
                self.news3k.build()
            except Exception as e:
                raise e
                # print('news3k error', e)
                # print(type(e))

        try:
            self.newspl = NewsPlease.from_url(self.url)
        except Exception as e:
            print(type(e))
            print('newspl error', e)
            self.newspl = None

    def extract_features(self):
        ''' Features: 
        author, publish_date, price, metadata.og.type, metadata.article.section, metadata.type, metadata.section, 
        keywords (may find statistics), metadata.keywords (may find statistics), metadata.wallet (if 1 then advertisement?), metadata.section
        '''
        start = time.time()
        self._run_libraries()
        end = time.time()
        time_taken = end - start
        print('Time on extracting: ',time_taken)
        
        if self.news3k:
            # print(str(f_2.year) + str(f_2.month) + str(f_2.day))
            meta = self.news3k.meta_data if self.news3k.meta_data else {}
            meta_kwords =  self.news3k.meta_keywords
            
            res = [
                self.newspl.authors[0]        if self.newspl and len(self.newspl.authors)           else self.news3k.authors      or  None,
                self.newspl.date_publish      if self.newspl and self.newspl.date_publish           else self.news3k.publish_date and None,
                meta['og']['price']['amount'] if 'og'      in meta and 'price'   in meta['og']      else None,
                meta['og']['type']            if 'og'      in meta and 'type'    in meta['og']      else None,
                meta['article']['section']    if 'article' in meta and 'section' in meta['article'] else None,
                meta['type']                  if 'type'    in meta                                  else None,
                meta['section']               if 'section' in meta                                  else None,
                self.news3k.meta_keywords     if len(meta_kwords) and meta_kwords[0] != ''          else None,
                self.news3k.keywords          if len(self.news3k.keywords)                          else None
            ]

        else:
            res = None
        
        self.features = res
        return res

    def convert_into_bin(self):
        ''' Features: 
        auth     : bin,
        p_date   : bin,
        pri      : bin,
        m.og.ty  : if article or website then 1, else 0
        m.at.sec : bin,
        m.ty     : bin
        m.sect   : bin,
        kwords   : if statistics or government, 0 else 1
        m.kwords : 
        '''
        res = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        if self.features:
            res = [ 
                1 if self.features[0] else 0,
                1 if self.features[1] else 0,
                1 if self.features[2] else 0,
                1 if self._is_type_art_web(self.features[3]) else 0,
                1 if self.features[4] else 0,
                1 if self.features[5] else 0,
                1 if self.features[6] else 0,
                1 if self._contains_stat_gov(self.features[7]) else 0,
                1 if self._contains_stat_gov(self.features[8]) else 0,
            ]

        self.bin_f = res
        return res

    def _is_type_art_web(self, tyype):
        if tyype != None:
            return tyype == 'article' or tyype == 'website'

    def _contains_stat_gov(self, kwords):
        if kwords != None:
            for word in kwords:
                low_w = word.lower()
                if low_w == 'government' or low_w == 'statistics':
                    return True
        return False

def countdown(t):
    while t:
        mins, secs = divmod(t, 60)
        timeformat = '{:02d}:{:02d}'.format(mins, secs)
        print(timeformat, end='\r')
        time.sleep(1)
        t -= 1
    print('Goodbye!\n\n\n\n\n')
    
def main():

    arg_parser = argparse.ArgumentParser(description="Process and extract features of urls and train a model to identify news urls")
    arg_parser.add_argument('-p', '--path', dest='path', help='A training file path of urls. The first column is url and the second is label.')

    args = arg_parser.parse_args()

    file_path = args.path

    if file_path:
        my_path = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(my_path, file_path)
        data = pd.read_csv(path)
        # print(data)
        
        url_feature_processor = UrlFeatureProcessor('None')
        
        with open('binary_features.csv', mode='a') as csv_file, open('binary_features_failed.csv', mode='a') as csv_file_failed, open('features_mat.csv', mode='a') as csv_file_features:
            
            fieldnames = ['original_URL', 'author', 'publish_date', 'price', 'meta_og_type', 'meta_art_sect', 'meta_type', 'meta_sect', 'meta_keywords', 'keywords', 'sub_w_count', 'sub_count', 'label']
            fieldnames_failed = ['original_URL', 'error', 'idx']
            fieldnames_fields = ['original_URL', 'author', 'publish_date', 'price', 'meta_og_type', 'meta_art_sect', 'meta_type', 'meta_sect', 'meta_keywords', 'keywords']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer_f = csv.DictWriter(csv_file_features, fieldnames=fieldnames)
            writer_failed = csv.DictWriter(csv_file_failed, fieldnames=fieldnames_failed)
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
                        'original_URL' : row[1], 
                        'author'       : bins[0],
                        'publish_date' : bins[1], 
                        'price'        : bins[2], 
                        'meta_og_type' : bins[3], 
                        'meta_art_sect': bins[4], 
                        'meta_type'    : bins[5],
                        'meta_sect'    : bins[6], 
                        'meta_keywords': bins[7], 
                        'keywords'     : bins[8], 
                        'sub_w_count'  : len(row[1][row[1][8:].index('/') + 8 :]) or 0 ,
                        'sub_count'    : len(row[1].split('/')) - 3,
                        'label'        : 0
                    })

                    writer_f.writerow({
                        'original_URL' : row[1], 
                        'author'       : features[0],
                        'publish_date' : features[1], 
                        'price'        : features[2], 
                        'meta_og_type' : features[3], 
                        'meta_art_sect': features[4], 
                        'meta_type'    : features[5],
                        'meta_sect'    : features[6], 
                        'meta_keywords': features[7], 
                        'keywords'     : features[8]
                    })
                        # 'label': row[2]})
                    
                except Exception as e:
                    print(e) 
                    print(idx, ' ', url)
                    writer_failed.writerow({
                        'original_URL': row[1],
                        'error': e,
                        'idx': idx
                    })
                idx += 1

    # url_feature_processor = UrlFeatureProcessor()
    # url_feature_processor.process()

main()

# python3 article_classifier_model.py -p ../data/sample_data_article_classification.csv

#p = UrlFeatureProcessor(
    # url = 'https://www.deptofnumbers.com/employment/states/'
    # )
# p.extract_features()