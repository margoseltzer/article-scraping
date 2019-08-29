import pandas as pd
import scraper

dataset = pd.read_csv('dataset.csv', index_col='url')
s = scraper.Scraper()
urlList = pd.read_csv('urlList.csv')
urlList = urlList[['url', 'type']]
toVisit = list(urlList.values)
visited = set()
while len(visited) < 5000:
    urlToVisit = urlList.pop()
    if urlToVisit[1] in ['rumor', 'hate', 'unreliable', 'conspiracy', 'fake', 'junksci', 'clickbait', 'satire', 'bias']:
        furtherURLs = scraper.handle_one_url_return_urls(s, url, 0, 'dataset_json/' +'0_article'+str(idx)+'.json')
    elif urlToVisit[1] in ['reliable', 'political']:
        furtherURLs = scraper.handle_one_url_return_urls(s, url, 0, 'dataset_json/' +'1_article'+str(idx)+'.json')
    else:
        furtherURLs = []
    
    visited.add(urlToVisit)
    else
    for i in furtherURLs:
        try:
            result = dataset.loc[i]
            toVisit.append([result.url, result.type])
        except:
            print('Not in dataset')

s.closeNLP()