import argparse
import hashlib
import json
import subprocess, shlex
import os
import re
import csv
import urllib
import nltk
from urllib.request import urlopen
from bs4 import BeautifulSoup
from newspaper import Article
from newsplease import NewsPlease
from utils.standford_NLP import StanfordNLP
from utils.url_classifier_ml import UrlClassifier
# from utils.url_classifier_ml import UrlClassifier
nltk.download('punkt')

"""
Script for scraping news article provenance from news url

Integrating Python Newspaper3k library and mercury-parser https://mercury.postlight.com/web-parser/
use best effort to extract correct provenance
Using StanfordCoreNLP to extract quotations and attributed speakers. 
Download StanfordCoreNLP from https://stanfordnlp.github.io/CoreNLP/download.html
"""


"""Path to StanfordCoreNLP Library"""
stanfordLibrary = "../stanford-corenlp-full-2018-10-05"

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

    def __init__(self, newspaper_article, mercury_parser_result, news_please, sNLP):
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
        self.__news_please = news_please
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
        # self.q
        #  of bundle of quote: [text, speaker (if known, blank otherwise), number of words in quote, bigger than one sentence?]
############### self.quotes = self.__sNLP.annotate(self.text)
        pass

    def find_links(self):
        """
        Find all a tags and extract urls from href field
        Then, categorize the urls before return
        The result does not include the self reference link.
        """
        url_classifier = UrlClassifier()
        article_html = self.__result_json['content'] or self.__article.article_html
        
        if article_html:
            soup   = BeautifulSoup(article_html, features="lxml")
            a_tags = soup.find_all("a")

            no_duplicate_url_list = list(set([a_tag.get('href') for a_tag in a_tags if url_classifier.is_news_article(a_tag.get('href'))]))
            
            links = {'articles': [link for link in no_duplicate_url_list if url_classifier.is_article(link)],
                     'unsure'  : [link for link in no_duplicate_url_list if url_classifier.is_reference(link)]}

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

            # pre-process by mercury-parser https://mercury.postlight.com/web-parser/
            parser_result = subprocess.run(["mercury-parser", source_url], stdout=subprocess.PIPE)
            result_json = json.loads(parser_result.stdout)
            news_please = NewsPlease.from_url(source_url)
            # if parser fail, set a empty object
            try:
                result_json['domain']
            except Exception as e:
                result_json = {
                    'domain': None,
                    'date_published': None,
                    'content': None
                }

            news_article = NewsArticle(article, result_json, news_please, sNLP)
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
        self.sNLP = {}
############ StanfordNLP()
        self.visited = []
        self.success = []
        self.failed = []

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


def main():
    parser = argparse.ArgumentParser(description='scraping news articles from web, and store result in file')
    parser.add_argument('-u', '--url', dest='url', required=True, help='source news article web url')
    parser.add_argument('-d', '--depth', type=int, dest='depth', default=2, help='the depth of related article would be scraped, defalut is 2')
    parser.add_argument('-o', '--output', dest='output', 
                        help='output file name, if not provided would use url hash as file name' +
                             ' and stored in news_json folder under current path')

    args = parser.parse_args()
    if args.depth < 0:
        print('scraping depth must greater or equal to 0')
        return

    # scrape from url
    # StanfordNLP.startNLPServer()

    scraper = Scraper()
    print('starting scraping from source url: %s, with depth %d' % (args.url, args.depth))
    news_article_list = scraper.scrape_news(args.url, args.depth)
    
    if not news_article_list:
        print('fail scraping from source url: ', args.url)
        return
    
    print('finished scraping all urls')
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
    output = args.output
    if output is None:
        if not os.path.exists('news_json'):
            os.makedirs('news_json')
        url_hash = hash_url(args.url)
        output = 'news_json/' + str(url_hash) + '.json'
    with open(output, 'w') as f:
        json.dump(output_json_list, f, ensure_ascii=False, indent=4)
    print('write scraping result to ', output)

    # StanfordNLP.closeNLPServer()


main()

# scraper = Scraper()
# news_article_list = scraper.scrape_news('https://www.cnn.com/profiles/chris-cillizza', 2)
# news_article_list = scraper.scrape_news('https://mitocopper.com/products/vegansafe-vitamin-b-12-2-oz-bottle?afmc=77&utm_campaign=77&utm_source=leaddyno&utm_medium=affiliate', 2)
# news_article_list = scraper.scrape_news('https://www.deptofnumbers.com/employment/states/', 2)
# news_article_list = scraper.scrape_news('https://www.census.gov/newsroom/press-releases/2018/2013-2017-acs-5year.html', 2)
# news_article_list = scraper.scrape_news('https://www.bbc.com/news/world-us-canada-41419190', 2)
# news_article_list = scraper.scrape_news('https://www.activistpost.com/2017/09/u-s-president-donald-trump-quietly-signs-law-allow-warrant-less-searches-parts-va-dc-md.html', 2)
# news_article_list = scraper.scrape_news('https://www.bbc.com/news/uk-48507244', 2)
# news_article_list = scraper.scrape_news('https://money.cnn.com/2018/05/10/news/companies/alexa-amazon-smart-speakers-voice-shopping/index.html', 2)
# news_article_list = scraper.scrape_news('https://money.cnn.com/quote/quote.html?symb=GIS&source=story_quote_link', 2)
# news_article_list = scraper.scrape_news('https://www.amazon.ca/dp/B07CT3W5R1/ref=ods_gw_d_fday19_lr_xpl3_ca_en?pf_rd_p=e895814e-52b1-4b26-91b5-673e15e7fa1c&pf_rd_r=D70HB6BNTZMSF0D081SZ', 2)
# news_article_list = scraper.scrape_news('https://bloomex.ca/Special-Occasions/Anniversary-Flowers/Anniversary-Designer-Collection-II.html', 2)

# random advertisement: https://mitocopper.com/products/vegansafe-vitamin-b-12-2-oz-bottle?afmc=77&utm_campaign=77&utm_source=leaddyno&utm_medium=affiliate
# stat article: https://www.deptofnumbers.com/employment/states/
# us gov page: https://www.census.gov/newsroom/press-releases/2018/2013-2017-acs-5year.html
# legit page: https://www.bbc.com/news/world-us-canada-41419190
# fake page: https://www.activistpost.com/2017/09/u-s-president-donald-trump-quietly-signs-law-allow-warrant-less-searches-parts-va-dc-md.html
# bbc, data not parsed: https://www.bbc.com/news/uk-48507244
# cnn money but article: https://money.cnn.com/2018/05/10/news/companies/alexa-amazon-smart-speakers-voice-shopping/index.html
# cnn money but not article: https://money.cnn.com/quote/quote.html?symb=GIS&source=story_quote_link
# amazon: https://www.amazon.ca/dp/B07CT3W5R1/ref=ods_gw_d_fday19_lr_xpl3_ca_en?pf_rd_p=e895814e-52b1-4b26-91b5-673e15e7fa1c&pf_rd_r=D70HB6BNTZMSF0D081SZ
# flower advertisement: https://bloomex.ca/Special-Occasions/Anniversary-Flowers/Anniversary-Designer-Collection-II.html