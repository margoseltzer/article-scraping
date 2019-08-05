import re
import os
import csv
import pandas as pd
from urllib.request import urlopen, Request
from urllib.parse import urlparse
from newspaper import Article
global count
count = 0
my_path = os.path.abspath(os.path.dirname(__file__))
path = os.path.join(my_path, 'all_lists.csv')
all_lists =  pd.read_csv(path)
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
    '([\.//(www.)?](' + '|'.join(map(re.escape,all_lists['BL_DOMAIN'].dropna())) + ')\.)|'
    '(/(' + '|'.join(map(re.escape,all_lists['BL_SUB'].dropna())) + ')/)|'
    '(' + '|'.join(map(re.escape, all_lists['BL_KEYWORD'].dropna())) + ')|'
    '(' + '|'.join(map(re.escape,all_lists['BL_END'].dropna())) + ')).*'))

# link is a government website
GOV_LIST = re.compile(('|'.join(map(re.escape,all_lists['GOV_PAGE'].dropna()))))

# link is a reference link but not an article
UNSURE_LIST = re.compile(('.*(' 
    '([\.//www.](' + '|'.join(map(re.escape,all_lists['REF_DOMAIN'].dropna())) + ')\.)|'
    '(' + '|'.join(map(re.escape,all_lists['REF_SUB'].dropna())) + ')/).*'))


def get_actual_url(x):
    global count 
    count = count + 1
    print(count)
    try:
        a = Article(x)
        a.build()
    except:
        return x
    else:
        if a.meta_data['url']:
            return a.meta_data['url']
        else:
            try:
                return a.meta_data['og']['url']
            except:
                return x


data = pd.read_csv('classifier_model_training.csv')
url_or = data['urls']
urls = [get_actual_url(i) for i in url_or]
toUse = [i for i in urls if not (BLACK_LIST.search(i) or UNSURE_LIST.search(i) or GOV_LIST.search(i))]
df = pd.DataFrame(columns={'url'})
for i in range(len(toUse)):
    df.loc[i] = toUse[i]

df.to_csv('final_url_list.csv')