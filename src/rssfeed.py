import feedparser
import pandas as pd
import csv
import time
import scraper
timeout = 7200

RSSFeeds = ['http://feeds.bbci.co.uk/news/world/rss.xml', 'http://feeds.bbci.co.uk/news/rss.xml', 'http://feeds.bbci.co.uk/news/politics/rss.xml'
'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml', 'https://rss.nytimes.com/services/xml/rss/nyt/World.xml',
'http://feeds.reuters.com/Reuters/domesticNews', 'http://feeds.reuters.com/reuters/topNews', 'https://www.motherjones.com/politics/feed/',
'http://feeds.washingtonpost.com/rss/politics', 'http://feeds.washingtonpost.com/rss/world', 
'https://www.theguardian.com/world/rss', 'https://www.theguardian.com/uk/rss', 'https://www.theguardian.com/us/rss',
'http://rss.cnn.com/rss/edition.rss', 'http://rss.cnn.com/rss/edition_world.rss', 'http://rss.cnn.com/rss/edition_us.rss',
'https://feeds.a.dj.com/rss/RSSWorldNews.xml', 'https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml',
'http://feeds.foxnews.com/foxnews/latest', 'http://feeds.foxnews.com/foxnews/national', 'http://feeds.foxnews.com/foxnews/world', 'http://feeds.foxnews.com/foxnews/politics',
'http://feeds.feedburner.com/breitbart', 'https://www.newsbusters.org/blog/feed', 'https://www.thegatewaypundit.com/feed ', 'https://www.infowars.com/feed/custom_feed_rss',
'https://www.nationalreview.com/corner/feed/', 'https://www.dailykos.com/blogs/main.rss', 'https://www.truthdig.com/report/rss', 'http://cnsnews.com/feeds/all',
'https://www.thinkprogress.org/feed', 'http://nypost.com/rss.xml', 'https://sputniknews.com/export/rss2/archive/index.xml', 'https://www.intellihub.com/feed/',
'http://libertywriters.com/feed/']

articlesToVisit = set([])
articleURLS = set([])
s = scraper.Scraper()
idx = 0

def getNewArticles():
    toReturn = set([])
    for url in RSSFeeds:
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]:
            if entry.link not in articleURLS:
                toReturn.add(entry.link)
                articleURLS.add(entry.link)
    print(len(toReturn))
    return toReturn


while True:
    articlesToVisit = articlesToVisit.union(getNewArticles())
    time.sleep(0.5)
    timeout_start = time.time()
    while len(articlesToVisit) > 0 and time.time() < timeout_start + timeout:
        idx = idx + 1
        print(idx)
        url = articlesToVisit.pop()
        scraper.handle_one_url(s, url, 2, 'news_json/' +'article'+str(idx)+'.json')
    time.sleep(0.5)
