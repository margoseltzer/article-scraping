import argparse
import urllib
import numpy as np
import pandas as pd
import csv
import sys 
import time
import os.path
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup

class FbLinkParser(object):
    '''
    This parser will store the url archived from an old fb post and parse it to the url for the real news
    '''

    def __init__(self, url=''):
        self.url_fb = url
        self.url_real = ''

    def ser_link(self, url):
        self.url_fb = url
        self.url_real = ''
    
    def parse_url_fb(self):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3723.0 Safari/537.36'}
            reg_url = self.url_fb
            req = Request(url=reg_url, headers=headers)
            #print('WHERE IS TYPE CHECKING 0')
            page_fb = urlopen(req)
            soup = BeautifulSoup(page_fb, 'html.parser')
            # print(soup)
            # Get all hidden elements
            hidden_elem_soups = soup.find_all('div', class_='hidden_elem')
            # print('WHERE IS TYPE CHECKING 1')
            # Get all <Code></Code> from hidden elements 
            code_soups = [hidden_elem_soup.find('code') 
                            for hidden_elem_soup in hidden_elem_soups 
                                if hidden_elem_soup.find('code')]
            print('WHERE IS TYPE CHECKING 2')
            # Get all the hidden post html in string
            hidden_strs = [code_soup.contents[0] 
                            for code_soup in code_soups 
                                if code_soup.contents[0]]
            # print('WHERE IS TYPE CHECKING 3')
            # Convert the strings into soups
            hidden_soups = [BeautifulSoup(html, 'html.parser') 
                                for html in hidden_strs]
            # print('WHERE IS TYPE CHECKING 4')
            # Get all a tags from the hidden soups
            a_tags_lists = [hidden_soup.find_all('a') 
                                for hidden_soup in hidden_soups]
            # print('WHERE IS TYPE CHECKING 5')
            # Join all the lists of <a/>
            a_tags = [a_tag for a_tags_list in a_tags_lists for a_tag in a_tags_list]

            # Get all href from <a/> that includes reference link starts with l.facebook.com
            # All the links in hrefs direct to a same page
            hrefs = [a_tag.get('href') 
                        for a_tag in a_tags 
                            if a_tag.get('href') and a_tag.get('href').find('l.facebook.com') > -1]
            # print('WHERE IS TYPE CHECKING 6')
            # Free all the unnecessary variables
            # hidden_elem_soups = code_soups = hidden_strs = hidden_soups = a_tags_lists = a_tags = None
            # print('WHERE IS TYPE CHECKING 7')            
            # Parse the href to find the shoten link
            req = Request(url=hrefs[0], headers=headers)
            page = urlopen(req)
            soup = BeautifulSoup(page, 'html.parser')
            body = soup.find('body')
            # print('WHERE IS TYPE CHECKING 8')
            # Get the first <script></script> where the shortened url resides
            # Assum the first script has the link and it seems to
            script_elems = body.find('script').contents[0]
            http_index = script_elems.find('http')
            end_index = script_elems.find(');')

            # Substring with the indices and remove \\ in the url
            url_short = script_elems[http_index : end_index - 1].replace('\\', '')
            # print('WHERE IS TYPE CHECKING 9')
            # TODO might need loop
            req = Request(url=url_short, headers=headers)
            page_real = urlopen(req)
            # print(type(page_real))
            # print(type(page_real.read()))
            # print(hasattr(page_real, 'getcode'))
            # print(page_real.getcode())
            if hasattr(page_real, 'getcode'):
                if page_real.getcode() is 200:
                    url_real = page_real.url
                else: 
                    return 'Unable page code is not 200'
            # url_short is the real url
            else:
                url_real = url_short

            self.url_real = url_real
            return url_real

        except Exception as e:
            print('Unable to parse the url, Error : ', e)
            return 


# 403 forbidden:https://www.facebook.com/OccupyDemocrats/posts/1253171768109208
def main():
    arg_parser = argparse.ArgumentParser(description = "Parse news article url on a Facebook post")
    arg_parser.add_argument('-u', '--url', dest = 'url', required = True, 
                                help = 'an url archievd from Facebook in the form of http://www.facebook....')
    arg_parser.add_argument('-l', '--label', dest = 'label', help = 'The label that indicates if the given url is legit or fake')

    args = arg_parser.parse_args()

    url_fb = args.url
    url_label = args.label
    print('Facebook url : ', url_fb)    
    fb_link_parser = FbLinkParser(url_fb)
    print('Original news article url : ', fb_link_parser.parse_url_fb())
    

def main_csv():
    arg_parser = argparse.ArgumentParser(description = 'Parse csv file that contains fb urls')
    arg_parser.add_argument('-p', '--path', dest = 'path', required = True, 
                                help = 'A csv file path of facebook where the first column is urls and the second is labels')
    
    args = arg_parser.parse_args()
    file_path = args.path

    my_path = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(my_path, file_path)
    data = pd.read_csv(path)
    
    # res_array contains [[url, label]s]
    res_array = []
    fb_link_parser = FbLinkParser()

    # url resides at idx = 3 and label at 5
    # This should vary between files so automate this later

    with open('parsed_fb_urls.csv', mode='w') as csv_file:
        fieldnames = ['fb_URL', 'URL', 'label']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        idx = 0
        for row in data.itertuples():
            fb_link_parser.ser_link(row[3])
            time.sleep(3)
            tmp_url_real = fb_link_parser.parse_url_fb()

            writer.writerow({'fb_URL': row[3], 'URL': tmp_url_real, 'label': row[5]})

            print(idx)
            print(row[3])
            # print('Original news article url : ', tmp_url_real)
            idx = idx + 1

main_csv()
# main()

# # f= open("facebook.html","w+")
# # f.write(str(a_tags))
# # f.close()

# fb_link_parser = FbLinkParser('https://www.facebook.com/cnnpolitics/posts/1281724775202686')
# print('Original news article url : ', fb_link_parser.parse_url_fb())

# https://www.facebook.com/AddictingInfoOrg/posts/1447486135291854
# WHERE IS TYPE CHECKING 2
# Unable to parse the url, Error :  HTTP Error 479: Unknown HTTP Status