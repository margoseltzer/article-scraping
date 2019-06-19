import argparse
import pandas as pd
import csv
import time
import os.path
import urllib
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup


'''
Expected Error List
1. index out of range: 
  1.1. Facebook denies requesting too many times. Try again later
  1.2. Facebok post has been removed
  1.3. When url directs to video
3. 404: The news on the orininal site has been removed
4. 403 (Should not appear anymore): means trying to open shoten url
5. 503 Service Unavailable: temporary error. Try again.
'''


class FbLinkParser(object):
    '''
    This parser will store the url archived from an old fb post and parse it to the url for the real news
    '''

    def __init__(self, url=None):
        self.url_fb = url
        self.url_real = ''

    def set_link(self, url):
        self.url_fb = url
        self.url_real = ''

    def parse_url_fb(self):
        try:
            # Header is to let Fb knows where the requests are come from
            headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3723.0 Safari/537.36'}
            req = Request(url=self.url_fb, headers=headers)

            page_fb = urlopen(req)
            soup = BeautifulSoup(page_fb, 'html.parser')

            # Get all hidden elements
            hidden_elem_soups = soup.find_all('div', class_='hidden_elem')

            # Get all <Code></Code> from hidden elements
            code_soups = [hidden_elem_soup.find('code') for hidden_elem_soup in hidden_elem_soups 
                            if hidden_elem_soup.find('code')]

            # Get all the hidden post html in string
            hidden_strs = [code_soup.contents[0] for code_soup in code_soups 
                            if code_soup.contents[0]]

            # Convert the strings into soups
            hidden_soups = [BeautifulSoup(html, 'html.parser') for html in hidden_strs]

            # Get all a tags from the hidden soups
            a_tags_lists = [hidden_soup.find_all('a') for hidden_soup in hidden_soups]

            # Join all the lists of <a/>
            a_tags = [a_tag for a_tags_list in a_tags_lists for a_tag in a_tags_list]

            # Get all href from <a/> that includes reference link starts with l.facebook.com
            # All the links in hrefs direct to a same page
            hrefs = [a_tag.get('href') for a_tag in a_tags
                     if a_tag.get('href') and a_tag.get('href').find('l.facebook.com') > -1]

            # Free all the unnecessary variables
            hidden_elem_soups = code_soups = hidden_strs = hidden_soups = a_tags_lists = a_tags = None

            # Parse the href to find the shoten link
            req = Request(url=hrefs[0], headers=headers)
            page = urlopen(req)
            soup = BeautifulSoup(page, 'html.parser')
            body = soup.find('body')

            # Get the first <script></script> where the shortened url resides
            # Assume the first script has the link and it seems to
            script_elems = body.find('script').contents[0]

            http_index = script_elems.find('http')
            end_index = script_elems.find(');')

            # Substring with the indices and remove \\ in the url
            url_short = script_elems[http_index: end_index - 1].replace('\\', '')

            # execute if http_index is -1 meaning the whole body is parsed and link is hidden in a <span/>
            if url_short is '':
                spans = soup.find_all('span')
                span_contents = [span.contents[0] for span in spans 
                                    if len(span.contents)]

                for content in span_contents:
                    if content.find('http') is 0:
                        url_short = content
                        break

            # TODO might need loop
            req = Request(url=url_short, headers=headers)
            page_real = urlopen(req)

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


def main():
    arg_parser = argparse.ArgumentParser(description="Parse news article url on a Facebook post. Requires either url or csv file path")
    arg_parser.add_argument('-u', '--url',  dest='url',  help='an url archievd from Facebook in the form of http://www.facebook....')
    arg_parser.add_argument('-p', '--path', dest='path', help='A csv file path of facebook where the first column is urls and the second is labels')

    args = arg_parser.parse_args()

    url_fb = args.url
    file_path = args.path

    if url_fb:
        print('Facebook url : ', url_fb)
        fb_link_parser = FbLinkParser(url=url_fb)
        print('Original url : ', fb_link_parser.parse_url_fb())

    if file_path:
        my_path = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(my_path, file_path)
        data = pd.read_csv(path)

        fb_link_parser = FbLinkParser()

        with open('parsed_fb_urls.csv', mode='w') as csv_file:
            fieldnames = ['fb_URL', 'URL', 'label']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            idx = 0
            for row in data.itertuples():
                fb_link_parser.set_link(url=row[3])
                
                tmp_url_real = fb_link_parser.parse_url_fb()

                writer.writerow({'fb_URL': row[3], 'URL': tmp_url_real, 'label': row[5]})

                print('Index is     : ', idx)
                print('Facebook url : ', row[3])
                print('Original url : ', tmp_url_real)

                idx = idx + 1


main()
