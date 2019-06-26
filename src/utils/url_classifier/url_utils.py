import re
from utils.url_classifier.article_classifier_model import UrlFeatureProcessor
from urllib.request import urlopen, Request
import pandas as pd

class UrlUtils(object):
    # regex used to validate url
    # refer to https://gist.github.com/dperini/729294
    URL_REGEX = re.compile(
        u"^"
        # protocol identifier
        u"(?:(?:https?|ftp)://)"
        # user:pass authentication
        u"(?:\S+(?::\S*)?@)?"
        u"(?:"
        # IP address exclusion
        # private & local networks
        u"(?!(?:10|127)(?:\.\d{1,3}){3})"
        u"(?!(?:169\.254|192\.168)(?:\.\d{1,3}){2})"
        u"(?!172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})"
        # IP address dotted notation octets
        # excludes loopback network 0.0.0.0
        # excludes reserved space >= 224.0.0.0
        # excludes network & broadcast addresses
        # (first & last IP address of each class)
        u"(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])"
        u"(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}"
        u"(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))"
        u"|"
        # host name
        u"(?:(?:[a-z\u00a1-\uffff0-9]-?)*[a-z\u00a1-\uffff0-9]+)"
        # domain name
        u"(?:\.(?:[a-z\u00a1-\uffff0-9]-?)*[a-z\u00a1-\uffff0-9]+)*"
        # TLD identifier
        u"(?:\.(?:[a-z\u00a1-\uffff]{2,}))"
        u")"
        # port number
        u"(?::\d{2,5})?"
        # resource path
        u"(?:/\S*)?"
        u"$", re.UNICODE)

    # link should not in reference link
    BLACK_LIST = re.compile(('.*('
        # check domain
        '([\.//](get.adobe|downloads.bbc|support|policies|aboutcookies|amzn|amazon|itunes)\.)|'
        # check sub page
        '(/(your-account|send|privacy-policy|subscription|subscriptions|people|profiles|terms|pages/todayspaper)/)|'
        # check key word
        '(category=subscribers)|'
        # check end
        '(.pdf$|.jpg$|.png$|.jpeg$|.index.html)).*'))
    
    # link is a government website
    # govList = pd.read_csv("govList.csv")
    # GOV_LIST = re.compile((".*("
    #     "([\.//]("+'|'.join(govList) + "))).*"))

    # link is a reference link but not an article
    UNSURE_LIST = re.compile(('.*('
        # check domain 
        '([\.//wwww.](youtube|youtu.be|youtu|reddit|twitter|facebook|invokedapps)\.)|'
        # check sub page
        '(cnn.com/quote|/wiki|/newsletter./|/video/|fast-facts/|/subscribe)/).*'))

    def __init__(self):
        pass
    
    def is_news_article(self, url):
        already_news = '/article/' in url
        if already_news:
            return True
        return self._is_valid_url(url) and self._is_article(url) and self._is_news(url)

    def _is_valid_url(self, url):
        # for sitiuation get('href') return None
        if not url:
            return False
        return UrlUtils.URL_REGEX.search(url) and not UrlUtils.BLACK_LIST.search(url)
    
    def _is_news(self, url):
        url = self._return_actual_url(url)
        feature_processor = UrlFeatureProcessor(url)
        return True

    def _return_actual_url(self, url):
        ''' This method replace a shorten or rediecting url to actual url'''
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3723.0 Safari/537.36'}

        url_real = url
        req = Request(url=url, headers=headers)
        page_real = urlopen(req)

        if hasattr(page_real, 'getcode'):
            if page_real.getcode() is 200:
                url_real = page_real.url
            else:
                print('Unable page code is not 200')
        
        return url_real

    def _is_article(self, url):
        return not UrlUtils.UNSURE_LIST.search(url)

    def is_gov_page(self, url):
        pass
    
    def is_reference(self, url):
        return not not UrlUtils.UNSURE_LIST.search(url)
    
    def add_domain(self, a_tag, domain):
        if a_tag['href'][0] == '/':
            a_tag = domain + a_tag['href']
        return a_tag 
    
    def is_profile(self, authors, a_tag):
        '''
        authors is list of author objects  
        '''
        for auth in authors:
            if self._only_name(auth.name) in self._only_name(str(a_tag)):
                return True
        return False

    def _only_name(self, st):
        only_alphabets = re.split('[^a-zA-Z]+', st)
        return ''.join(only_alphabets).lower()
    
    def return_url(self, a_tag):
        if type(a_tag) == str:
            return a_tag
        return a_tag['href']


# u = UrlUtils().return_actual_url('http://www.politico.com/news/stories/0308/9214.html')
# print(u)