import argparse
import hashlib
import json
import subprocess
import os
import re
from newspaper import Article

"""
Script for scraping news article provenance from news url

Integrating Pyhton Newspaper3k library and mercury-parser https://mercury.postlight.com/web-parser/
use best effort to extract correct provenance
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
    NewsArticle class mainly for find and store the provance of one news article

    Only two methods should be called outside the class

    One is class static method: 
        build_news_article_from_url(url) 
            return an NewsArticle object build from provided url
    
    Anohter method:
        jsonify()
            return a dictionary only contain article provenance
    """

    def __init__(self, newspaper_article, mercury_parser_result):
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

        # news Provenance
        self.url = newspaper_article.url
        self.title = newspaper_article.title
        self.authors = []
        self.publication = mercury_parser_result['domain'] or newspaper_article.source_url
        self.publish_date = ''
        self.text = newspaper_article.text
        self.quotes = []
        self.links = []
        self.key_words = newspaper_article.keywords
        
        self.find_all_provenance()

    def find_authors(self):
        regex = '((For Mailonline)|(.*(Washington Times|Diplomat|Bbc|Abc|Reporter|Correspondent|Editor|Elections|Analyst|Min Read).*))'
        authors_name_segments = []
        for x in self.__article.authors:
            # filter out unexpected word
            if not re.match(regex, x):
                # slice the For Mailonline in dayliymail author's name
                if 'For Mailonline' in x:
                    authors_name_segments.append(x.replace(' For Mailonline', ''))
                else:
                    authors_name_segments.append(x)

        # contact Jr to previous, get full name
        pos = len(authors_name_segments) - 1
        authors_name = []
        while pos >= 0:
            if re.match('(Jr|jr)', authors_name_segments[pos]):
                full_name = authors_name_segments[pos-1] + ', ' + authors_name_segments[pos]
                authors_name.append(full_name)
                pos -= 2
            else:
                authors_name.append(authors_name_segments[pos])
                pos -= 1
        
        authors = []
        for x in authors_name:
            authors.append(Author(x, None))
        self.authors = authors
        
        return authors

    def find_publish_date(self):
        if self.__article.publish_date:
            self.publish_date = self.__article.publish_date.strftime("%Y-%m-%d")
        else:
            if self.__result_json['date_published']:
                # format would be '%y-%m-%d...'
                self.publish_date = self.__result_json['date_published'][0:10]
            else:
                self.publish_date = ''
        
        return self.publish_date


    def find_quotes(self):
        pass

    def find_links(self):
        pass
    
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
        authors_dicts = []
        for x in self.authors:
            authors_dicts.append(x.jsonify())
        return {
            'url': self.url,
            'title': self.title,
            'authors': authors_dicts,
            'publication': self.publication,
            'publish_date': self.publish_date,
            'text': self.text,
            'quotes': self.quotes,
            'links': self.links,
            'key_words': self.key_words
        }

    @staticmethod
    def build_news_article_from_url(source_url):
        """build new article object from source url, if build fail would return None
        """
        try:
            # pre-process news by NewsPaper3k library
            article = Article(source_url, keep_article_html=True)
            article.build()

            # pre-process by mercury-parser https://mercury.postlight.com/web-parser/
            parser_result = subprocess.run(["mercury-parser", source_url], stdout=subprocess.PIPE)
            result_json = json.loads(parser_result.stdout)
            
            news_article = NewsArticle(article, result_json)
            return news_article
        except Exception as e:
            print('fail to scraping from url: ', source_url)
            print('reason:', e)
            return None


class Scraper(object):
    """
    Scraper class, for this class would build a list of NewsArticle objects from source url
    if scraper from multiple source url should initiate different scraper
    """
    def __init__(self):
        self.visited = []
        
    def scrape_news(self, url, depth=0):
        """
        scrape news article from url, 
        if depth greter than 0, scrape related child articles
        """
        news_article_list = []

        news_article = NewsArticle.build_news_article_from_url(url)
        if not news_article:
            return news_article_list

        news_article = NewsArticle.build_news_article_from_url(url)
        news_article_list.append(news_article)
        
        self.visited.append(url)
        parent_articles_list = [news_article]
        while depth > 0:
            child_url_list = [url for article in parent_articles_list for url in article.links]
            child_articles_list = self.scrape_news_list(child_url_list)
            news_article_list += child_articles_list
            parent_articles_list = child_articles_list 
            depth -= 1

        return news_article_list

    def scrape_news_list(self, url_list):
        """
        scrape news article from url list, if url has been visited skip that one
        """
        url_list_filtered = [url for url in url_list if url not in self.visited]
        news_article_list = [NewsArticle.build_news_article_from_url(url) for url in url_list_filtered]
        self.visited += url_list_filtered
        return [article for article in news_article_list if article]


def hash_url(url):
    md5Hash = hashlib.md5()
    md5Hash.update(url.encode())
    return md5Hash.hexdigest()

def main():
    parser = argparse.ArgumentParser(description='scraping news articles from web, and store result in file')
    parser.add_argument('-u', '--url', dest='url', required=True, help='source news article web url')
    parser.add_argument('-d', '--depth', type=int, dest='depth', default=2,
                        help='the depth of related article would be scraped, defalut is 2')
    parser.add_argument('-o', '--output', dest='output',
                        help='output file name, if not provided would use url hash as file name' + 
                        ' and stored in news_json folder under current path')
    
    args = parser.parse_args()

    if args.depth < 0:
        print('scraping depth must greater or equal to 0')
        return

    # scrape from url
    scraper = Scraper()
    print('starting scraping from source url: %s, with depth %d' %(args.url, args.depth))
    news_article_list = scraper.scrape_news(args.url, args.depth)
    if not news_article_list:
        print('fail scraping from source url: ', args.url)
        return

    print('finish scraping from source url: ', args.url)
    
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
    print('write scraping result to ' , output)

main()
