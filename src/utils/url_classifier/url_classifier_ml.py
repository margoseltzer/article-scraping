import re
from utils.url_classifier.article_classifier_model import UrlFeatureProcessor
from urllib.request import urlopen, Request
from pandas import pd

class UrlClassifier(object):
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
        '(/(your-account|send|privacy-policy|terms|pages/todayspaper)/)|'
        # check key word
        '(category=subscribers)|'
        # check end
        '(.pdf$|.jpg$|.png$|.jpeg$|.index.html)).*'))
    
    # link is a government website
    govList = pd.read_csv("govList.csv")
    GOV_LIST = re.compile((".*("
        "([\.//]("+'|'.join(govList) + "))).*"))

    # link is a reference link but not an article
    UNSURE_LIST = re.compile(('.*('
        # check domain 
        '([\.//](youtube|youtu.be|youtu|reddit|twitter|facebook|invokedapps)\.)|'
        # check sub page
        '(cnn.com/quote|/wiki|/newsletter./|/subscription|/subscribe)/).*'))

    def __init__(self):
        pass
    
    def is_news_article(self, url):
        return self._is_valid_url(url) and self._is_news(url)

    def _is_valid_url(self, url):
        # for sitiuation get('href') return None
        if not url:
            return False
        return UrlClassifier.URL_REGEX.search(liurlnk) and not UrlClassifier.BLACK_LIST.search(url)
    
    def _is_news(self, url):
        feature_processor = UrlFeatureProcessor(url)
        return True
        
    def is_gov_page(self, url):
        pass

    def is_article(self, url):
        return not UrlClassifier.UNSURE_LIST.search(url)
    
    def is_reference(self, url):
        return not not UrlClassifier.UNSURE_LIST.search(url)

    def return_actual_url(self, url):
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
    