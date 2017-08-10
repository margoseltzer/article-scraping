# article-scraping
for summer 2017 news article scraping

## File list
* ```in_progress.py```
  * could be named better :P
  * program that does the scraping
  * outputs "articles.json"
* ```graph2.py```
  * up-to-date version of ```graph.py```
  * input is "articles.json"
  * outputs "output.json"

## How to run
* Uses Python 3
* ```python3 in_progress.py [url of article]```
* ```python graph2.py```

## Current issues
* it's not showing relationships like wasgeneratedby and wasassociatedwith although those relationships are shown in output.json
  * it's the backslashes, rename nodes
* working on comparing sentiment of paragraph to quote

good articles:
https://www.nytimes.com/2017/07/19/us/politics/john-mccain-brain-cancer.html
http://www.washingtonexaminer.com/senate-judiciary-committee-approves-fbi-nominee-christopher-wray/article/2629199

bad articles:


retracted articles:
* https://web.archive.org/web/20170622210615/http://www.cnn.com/2017/06/22/politics/russian-investment-fund-under-investigation/index.html
