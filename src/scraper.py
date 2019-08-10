import argparse
import csv
import hashlib
import subprocess
import json
import os
import re
import nltk
from bs4 import BeautifulSoup
from threading import Timer
from urllib.parse import urlparse
from boilerpipe.extract import Extractor
from newspaper import Article
from utils.stanford_NLP import StanfordNLP
from utils.url_classifier.url_utils import UrlUtils
nltk.download('punkt')

"""
Script for scraping news article provenance from news url

Integrating Python Newspaper3k library and mercury-parser https://mercury.postlight.com/web-parser/
use best effort to extract correct provenance
Using StanfordCoreNLP to extract quotations and attributed speakers. 
Download StanfordCoreNLP from https://stanfordnlp.github.io/CoreNLP/download.html
"""

class Author(object):
    def __init__(self, name, link):
        self.name = name
        self.link = link

    def jsonify(self):
        """return a dictionary of author object"""
        return {
            'name': self.name,
            'link': self.link
        }

class NewsArticle(object):
    """
    NewsArticle class is mainly to find and store the provance of one news article

    Only two methods should be called outside the class

    One is class static method: 
        build_news_article_from_url(url, sNLP) 
            return an NewsArticle object build from provided url
            use provided sNLP (StanfordNLP class) to extract quotes

    Another method:
        jsonify()
            return a dictionary only contain article provenance
    """

    def __init__(self, newspaper_article, mercury_parser_result, sNLP):
        """
        constructor for NewsArticle object

        NewsArticle constructor based on the parser result return by
        Newspaper3k library and mercury-parser

        Parameters
        ----------
        newspaper_article : Article
            the Article object returned by Newspaper3k library
        mercury_parser_result : dict
            the json format of mercury-parser result
        """
        # some useful private properties
        self.__article = newspaper_article
        self.__result_json = mercury_parser_result 
        self.__fulfilled = False
        self.__sNLP = sNLP

        # news Provenance
        self.url = newspaper_article.url
        self.title = newspaper_article.title
        self.authors = []
        self.publisher = mercury_parser_result['domain'] or newspaper_article.source_url
        self.publish_date = ''
        self.text = newspaper_article.text
        self.quotes = []
        self.links = {'articles':[], 'unsure':[]}
        self.key_words = newspaper_article.keywords

        self.find_all_provenance()

    def find_authors(self):
        print('find author')
        regex = '((For Mailonline)|(.*(Washington Times|Diplomat|Bbc|Abc|Reporter|Correspondent|Editor|Elections|Analyst|Min Read).*))'
        # filter out unexpected word and slice the For Mailonline in dayliymail author's name
        authors_name_segments = [x.replace(' For Mailonline', '') for x in self.__article.authors if not re.match(regex, x)]

        # contact Jr to previous, get full name
        pos = len(authors_name_segments) - 1
        authors_name = []
        while pos >= 0:
            if re.match('(Jr|jr)', authors_name_segments[pos]):
                full_name = authors_name_segments[pos - 1] + ', ' + authors_name_segments[pos]
                authors_name.append(full_name)
                pos -= 2
            else:
                authors_name.append(authors_name_segments[pos])
                pos -= 1

        self.authors = [Author(x, None) for x in authors_name]
        print('find author')
        
        return self.authors

    def find_publish_date(self):
        if self.__article.publish_date:
            self.publish_date = self.__article.publish_date.strftime(
                "%Y-%m-%d")
        else:
            if self.__result_json['date_published']:
                # format would be '%y-%m-%d...'
                self.publish_date = self.__result_json['date_published'][0:10]
            else:
                self.publish_date = ''

        return self.publish_date

    def find_quotes(self):
        print('find quotes')
        # list of bundle of quote: [text, speaker (if known, blank otherwise), number of words in quote, bigger than one sentence?]
        try:
            self.quotes = self.__sNLP.annotate(self.text)
        except Exception as e:
            print('err in find_quotes, ', e)
            self.quotes = []
        print('find quotes')
        
    def find_links(self):
        """
        Find all a tags and extract urls from href field
        Then, categorize the urls before return
        The result does not include the self reference link.
        """
        print('find links')
        parsed_uri = urlparse(self.url)
        domain_name = parsed_uri.scheme + "://" + parsed_uri.netloc
        
        html_new3k   = self.__article.article_html
        html_mercury = self.__result_json['content']
        
        soup_a = BeautifulSoup(html_new3k, features="lxml")
        soup_m = BeautifulSoup(html_mercury, features="lxml")
        
        a_tags_news3k  = soup_a.find_all("a", href=True) or []
        a_tags_mercury = soup_m.find_all("a", href=True) or []

        a_tags_all = a_tags_news3k if len(a_tags_news3k) else a_tags_mercury
        print('Newspaper a tag length is : ', len(a_tags_news3k))
        print('Mercuruparser a tag length is : ', len(a_tags_mercury))
        print('news3k list : ')
        for a_tag in a_tags_news3k: print(a_tag['href'])
        
        print('mercury list : ')
        for a_tag in a_tags_mercury: print(a_tag['href'])
        
        links = { 'articles': [], 'gov_pgs': [], 'unsure': [] }
        if len(a_tags_all):
            url_utils = UrlUtils()
            
            # List of all a-tags in article_html, with added domain name if needed
            a_tags_proc = [url_utils.add_domain(a_tag, domain_name) for a_tag in a_tags_all ]
            
            # Filter out author page URLs, and store them in their respective author objects
            a_tags_no_author = [a_tag for a_tag in a_tags_proc if not url_utils.is_profile(self.authors, a_tag)]
            
            # return_url(a_tag): a_tag is sometimes a string
            urls_no_dup = list(set([url_utils.return_url(a_tag) for a_tag in a_tags_no_author]))
            print(urls_no_dup)
            # Should consider switching the order of unsure and articles
            print('URL IS FOR LOOP')
            for url in urls_no_dup: print(url)
        
            for url in urls_no_dup:
                print(url)
                url = url_utils.return_actual_url(url)
                # if not url_utils.is_valid_url(url) : continue
                # elif url_utils.is_gov_page(url)    : links['gov_pgs'].append(url) 
                # elif url_utils.is_news_article(url): links['articles'].append(url)
                # elif url_utils.is_reference(url)   : links['unsure'].append(url)
                if not url_utils.is_valid_url(url) : 
                    print('NOT VALID ', url)
                    continue
                elif url_utils.is_gov_page(url)    : 
                    print('IS GOV PAGE ', url)
                    links['gov_pgs'].append(url) 
                    continue
                elif url_utils.is_news_article(url):
                    print('IS NEWS ARTICLE ', url) 
                    links['articles'].append(url)
                    continue
                elif url_utils.is_reference(url)   :
                    print('IS REFERENCE ', url) 
                    links['unsure'].append(url)
                    continue
                print('IS NOTHING??? ', url)
            print('gov_pgs  : ', links['gov_pgs'])
            print('articles : ', links['articles'])
            print('unsure   : ', links['unsure'])
            print('find links')
        
        self.links = links

    def find_all_provenance(self):
        if not self.__fulfilled:
            self.find_authors()
            self.find_publish_date()
            self.find_quotes()
            self.find_links()
            self.__fulfilled = True

    def jsonify(self):
        """ return a dictionary only contain article provenance
        """
        authors_dicts = [x.jsonify() for x in self.authors]
        return {
            'url': self.url,
            'title': self.title,
            'authors': authors_dicts,
            'publisher': self.publisher,
            'publish_date': self.publish_date,
            'text': self.text,
            'quotes': self.quotes,
            'links': self.links,
            'key_words': self.key_words
        }

    @staticmethod
    def build_news_article_from_url(source_url, sNLP):
        """build new article object from source url, if build fail would return None
        """
        try:
            print('start to scrape from url: ', source_url)

            # pre-process news by NewsPaper3k library
            article = Article(source_url, keep_article_html=True)
            article.build()
            article.nlp()
            e = Extractor(extractor='DefaultExtractor', html=article.html)
            article.text = e.getText()
            article.article_html = e.getHTML()

            try:
                # pre-process by mercury-parser https://mercury.postlight.com/web-parser/
                parser_result = subprocess.run(["mercury-parser", source_url], stdout=subprocess.PIPE)
                result_json = json.loads(parser_result.stdout)
            except Exception as e:
                result_json = None

            # if parser fail, set a empty object
            try:
                result_json['domain']
            except Exception as e:
                result_json = {
                    'domain': None,
                    'date_published': None,
                    'content': None
                }
            news_article = NewsArticle(article, result_json, sNLP)
            print('success to scrape from url: ', source_url)
            return news_article
        except Exception as e:
            print('fail to scrape from url: ', source_url)
            print('reason:', e)
            return None


class Scraper(object):
    """
    Scraper class, for this class would build a list of NewsArticle objects from source url
    if scraper from multiple source url should initiate different scraper
    """

    def __init__(self):
        self.sNLP = StanfordNLP()
        self.visited = []
        self.success = []
        self.failed = []
    
    def closeNLP(self):
        self.sNLP.close()

    def scrape_news(self, url, depth=0):
        """
        scrape news article from url, 
        if depth greater than 0, scrape related url which is not in black list and not
        be visited yet
        """

        def generate_child_url_list(parent_articles_list):
            """
            generate next leve child url list from previous articles list
            filter out url has been visited
            """
            url_list = [url for article in parent_articles_list for url in article.links['articles']]
            url_list_unvisited = [url for url in url_list if url not in self.visited]
            return url_list_unvisited

        news_article_list = []

        news_article = NewsArticle.build_news_article_from_url(url, self.sNLP)
        if not news_article:
            self.failed.append(url)
            return news_article_list

        news_article_list.append(news_article)

        self.visited.append(url)
        self.success.append(url)

        # Steps for scraping links find in article.
        # parent_articles_list would be only current level, from this list generates url list for next level
        parent_articles_list = [news_article]
        while depth > 0:
            child_url_list = generate_child_url_list(parent_articles_list)
            child_articles_list = self.scrape_news_list(child_url_list)
            news_article_list += child_articles_list
            parent_articles_list = child_articles_list
            self.visited += child_url_list
            depth -= 1

        return news_article_list

    def scrape_news_list(self, url_list):
        """
        scrape news article from url list
        """
        news_article_list = []
        for url in url_list:
            article = NewsArticle.build_news_article_from_url(url, self.sNLP)
            if article: 
                news_article_list.append(article)
                self.success.append(url)
            else:
                self.failed.append(url)

        return news_article_list


def hash_url(url):
    md5Hash = hashlib.md5()
    md5Hash.update(url.encode())
    return md5Hash.hexdigest()

def handle_single_url(url, depth, output=None):
    # scrape from url
    scraper = Scraper()
    print('starting scraping from source url: %s, with depth %d' % (url, depth))
    news_article_list = scraper.scrape_news(url, depth)
    
    if not news_article_list:
        print('fail scraping from source url: ', url)
        return False
    
    scraper.closeNLP()
    print('finished scraping urls from source: ', url)
    print('total scraped %d pages:' %(len(scraper.visited)))
    print('total successful %d pages:' %(len(scraper.success)))
    print('success url list :')
    print(*scraper.success, sep='\n')
    
    if scraper.failed:
        print('failed url list :')
        print(*scraper.failed, sep='\n')

    # build dict object list
    output_json_list = []
    for news_article in news_article_list:
        output_json_list.append(news_article.jsonify())

    # write reslut to file
    if output is None:
        if not os.path.exists('news_json'):
            os.makedirs('news_json')
        url_hash = hash_url(url)
        output = 'news_json/' + str(url_hash) + '.json'
    with open(output, 'w') as f:
        json.dump(output_json_list, f, ensure_ascii=False, indent=4)
    print('write scraping result to ', output)
    return True

def handle_one_url(scraper, url, depth, output=None):
    # scrape from url
    print('starting scraping from source url: %s, with depth %d' % (url, depth))
    news_article_list = scraper.scrape_news(url, depth)
    
    if not news_article_list:
        print('fail scraping from source url: ', url)
        return False
    
    print('finished scraping urls from source: ', url)
    print('total scraped %d pages:' %(len(scraper.visited)))
    print('total successful %d pages:' %(len(scraper.success)))
    print('success url list :')
    print(*scraper.success, sep='\n')
    
    if scraper.failed:
        print('failed url list :')
        print(*scraper.failed, sep='\n')

    # build dict object list
    output_json_list = []
    for news_article in news_article_list:
        output_json_list.append(news_article.jsonify())

    # write reslut to file
    if output is None:
        if not os.path.exists('news_json'):
            os.makedirs('news_json')
        url_hash = hash_url(url)
        output = 'news_json/' + str(url_hash) + '.json'
    with open(output, 'w') as f:
        json.dump(output_json_list, f, ensure_ascii=False, indent=4)
    print('write scraping result to ', output)
    return True

def handle_url_list_file(file_name, depth):
    scraper = Scraper()
    with open(file_name, 'r') as f:
            csv_reader = csv.DictReader(f)
            line_count = 0
            fail_list = []
            idx = 0
            url_utils = UrlUtils()
            for row in csv_reader:
                if idx <= 1821:
                    print(idx)
                    idx += 1
                    continue
                if line_count == 0:
                    header = list(row.keys())
                url = row['url']
                print('url in the dataset ', url)
                print('index is ', idx)
                label = row['label']
                if not url_utils.is_news_article(url) or url_utils.is_gov_page(url) or not url_utils.is_valid_url(url): 
                    idx += 1
                    continue
                rsp = handle_one_url(scraper, url, depth, 'article'+str(idx)+'_'+label+'.json')
                if not rsp:
                    fail_list.append(row)
                line_count += 1
                idx += 1
            if fail_list:
                with open('fail_list.csv', 'w') as fail_csv:
                    writer = csv.DictWriter(fail_csv, fieldnames=header)
                    writer.writeheader()
                    for row in fail_list:
                        writer.writerow(row)
            print('finish process urls in ', file_name)
            print('success on %d urls, failed on %d urls ' % (line_count - len(fail_list), len(fail_list)))
            print('any failed case could be found in fail_list.csv')
            scraper.closeNLP()

def main():
    parser = argparse.ArgumentParser(description='scraping news articles from web, and store result in file')
    parser.add_argument('-u', '--url', dest='url', help='source news article web url')
    parser.add_argument('-f', '--file', dest='file', help='file contain list of url')
    parser.add_argument('-d', '--depth', type=int, dest='depth', default=2, help='the depth of related article would be scraped, defalut is 2')
    parser.add_argument('-o', '--output', dest='output', 
                        help='specify output file for url feed by -u option')

    args = parser.parse_args()
    if args.depth < 0:
        print('scraping depth must greater or equal to 0')
        return

    if not args.url and not args.file:
        print('must provide at least one url or file contain url')
        return

    if args.url:
        handle_single_url(args.url, args.depth, args.output)
    if args.file:
        handle_url_list_file(args.file, args.depth)

main()



# def timeout():
#     Exception('Something is taking Too long')

# t = Timer(60, timeout)
# t.start()
# print('timer starts')
# print('timer is cancelled')
