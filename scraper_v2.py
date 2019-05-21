import argparse
import hashlib
import json
import os
import re
from newspaper import Article

class Author(object):
    def __init__(self, name, link):
        self.name = name
        self.link = link
    
    def jsonify(self):
        return {
            'name': self.name,
            'link': self.link
        }

class NewsArticleException(Exception):
    pass

class NewsArticle(object):
    # news article object
    def __init__(self, article):
        # some useful private properties 
        self.__article = article
        self.__article_html = article.article_html
        self.__html = article.html
        self.__root_html_node = article.clean_doc
        self.__root_article_node = article.clean_top_node

        self.__fulfilled = False

        # news Provenance
        self.url = article.url
        self.title = article.title
        self.authors = []
        self.publication = article.source_url
        self.publish_date = article.publish_date
        self.quotes = []
        self.links = []
        self.key_words = article.keywords
        # self.cite_text = []
        # self.names = []
        # self.sentiments = []
        # self.num_flags = 0

    def find_title(self):
        pass

    def find_auothors(self):
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
    
    def find_publication(self):
        pass

    def find_publish_date(self):
        pass

    def find_quotes(self):
        pass

    def find_links(self):
        pass
    
    def find_all_provenance(self):
        if not self.__fulfilled:
            self.find_title()
            self.find_auothors()
            self.find_publication()
            self.find_publish_date()
            self.find_quotes()
            self.find_links()
            self.__fulfilled = True

    def jsonify(self):
        """ return a dict of news article object
        """
        authors_dicts = []
        for x in self.authors:
            authors_dicts.append(x.jsonify())
        return {
            'url': self.url,
            'title': self.title,
            'authors': authors_dicts,
            'publication': self.publication,
            'publish_date': self.publish_date.strftime("%m/%d/%Y") if self.publish_date else '',
            'quotes': self.quotes,
            'links': self.links,
            'key_words': self.key_words
        }

    @staticmethod
    def build_news_article_from_url(source_url):
        """build new article object from source url, if build fail would raise a NewsArticleException
        """
        try:
            # pre-process news by NewsPaper3k library
            article = Article(source_url, keep_article_html=True)
            article.download();
            article.parse();
            article.nlp();
            
            news_article = NewsArticle(article)
            news_article.find_all_provenance()
            return news_article
        except Exception as e:
            raise e


class Scraper(object):
    def __init__(self):
        self.visited = []
        
    def scrape_news(self, url, depth=0):
        """scrape news article from url, 
            if depth greter than 0, recursively scrape related links in source
        """
        news_article_list = []
        try:
            news_article = NewsArticle.build_news_article_from_url(url)
            news_article_list.append(news_article)
            self.visited.append(url)
        except Exception as e:
            print('fail to scraping from url: ', url)
            print('reason:', e)
        else:
            if depth > 0:
                for link in news_article.links:
                    if link not in self.visited:
                        news_article_list += self.scrape_news(link, (depth - 1))
        finally:
            return news_article_list


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
    print('finish scraping from source url: ', args.url)
    
    # build dict object list
    output_json_list = []
    for news_article in news_article_list:
        output_json_list.append(news_article.jsonify())
    
    # wrote non empty reslut to file
    if news_article_list:
        output = args.output
        if output is None:
            if not os.path.exists('news_json'):
                os.makedirs('news_json')
            url_hash = hash_url(args.url)
            output = 'news_json/' + str(url_hash) + '.json'
        with open(output, 'w') as f:
            json.dump(output_json_list, f, ensure_ascii=False, indent=4)
        print('write scraping result to ' , output)
    else:
        print('scraping result is empyt for source url: ', args.url)


if __name__ == "__main__":
    main()
