import sys
import nltk
import json
import feedparser
import requests
import collections
import re
from lxml import html, etree
from textblob import TextBlob
from random import *
import os.path
#from unidecode import unidecode

# CNN one might not always work depending on if author has url or not
# paper : [author tag, body tag, date class]
'''

RUN: python scraper.py http://www.cnn.com/2017/06/15/us/bill-cosby-jury-six-questions/index.html

'''
trees = {}

paper_tags = {'bbc' : {'author' : 'N/A', 
                       'body' : '//div[@class="story-body__inner"]', 
                       'paragraph' : '//p',
                       'date' : 'date date--v2',
                       'href' : 'N/A'},
              'cnn' : {'author' : '//span[@class="metadata__byline__author"]/text()AND//span[@class="metadata__byline__author"]/a/text()AND//span[@class="metadata__byline__author"]/strong/text()', 
                       'body' : '//div[@class="l-container"]',# '//section[@id="body-text"]', 
                       'paragraph' : '//div[@class="zn-body__paragraph"]',
                       'date' : 'update-time',
                       'href' : '//h3[@class=cd__headline"]'},
              'reuters' : {'author' : '//div[@id="article-byline"]/span/a/text()', 
                       'body' : '//span[@id="article-text"]', 
                       'paragraph' : '//p',
                       'date' : 'timestamp',
                       'href' : '//div[@class="feature"]'},
              'nytimes' : {'author' : '//span[@class="byline-author"]/text()', 
                       'body' : '//p[@class="story-body-text story-content"]', 
                       'paragraph' : '//p[@class="story-body-text story-content"]',
                       'date' : 'dateline',
                       'href' : '//div[@class="story-body"]'},
              'washingtonexaminer' : {'author' : '//span[@itemprop="name"]/text()', 
                       'body' : '//section[@class="article-body"]', 
                       'paragraph' : '//p',
                       'date' : 'article-date text-muted',
                       'href' : '//div[@class="align-top"]'},
              'chicagotribune' : {'author' : '//span[@itemprop="author"]/text()', 
                       'body' : '//div[@itemprop="articleBody"]', 
                       'paragraph' : '//p',
                       'date' : 'trb_ar_dateline_time',
                       'href' : '//li[@class="trb_outfit_group_list_item"]'},
              'breitbart' : {'author' : '//a[@class="byauthor"]/text()', 
                       'body' : '//div[@class="entry-content"]', 
                       'paragraph' : '//p',
                       'date' : 'bydate',
                       'href' : '//div[@class="grp-content"]'},
              'dailymail' : {'author' : '//p/a[@class="author"]/text()', 
                       'body' : '//div[@id="js-article-text"]', 
                       'paragraph' : '//p[@class="mol-para-with-font"]',
                       'date' : 'article-timestamp article-timestamp published',
                       'href' : '//h3[@class="sch-res-title"]'},
              'newstarget' : {'author' : '//div[@class="author-link"]/text()', 
                       'body' : '//div[@class="entry-content"]', 
                       'paragraph' : '//p',
                       'date' : 'entry-date updated',
                       'href' : '//div[@class="f-tabbed-list-content"]'},
              'latimes' : {'author' : '//a[@class="trb_ar_by_nm_au_a"]/text()', 
                       'body' : '//div[@class="trb_ar_main"]', 
                       'paragraph' : '//p',
                       'date' : 'trb_ar_dateline_time',
                       'href' : '//a[@class="trb_outfit_relatedListTitle_a"]'},
              'infowars' : {'author' : '//span[@class="author"]/a/text()', 
                       'body' : '//div[@class="text"]', 
                       'paragraph' : '//p',
                       'date' : 'date',
                       'href' : '//article'}
             }

recognized_pgs = {'t.co' : "twitter"}

class Article:
  def __init__(self, u, t, a, d, q=[[],[]], l=[], e=[], d2=0):
    self.url = u
    self.title = t
    self.authors = a
    self.date = d
    self.quotes = q
    self.links = l
    self.external = e
    self.depth = d2
    self.cite_text = []
    self.author_links = [] # links to author pages, if applicable
    self.names = []
    self.sentiments = []
    self.num_flags = 0

  def to_string(self):
    print("\nURL:", self.url)
    print("Title:", self.title)
    print("Authors:", self.authors)
    print("Date:", self.date)
    print("Quotes:", self.quotes)
    print("Names:", self.names) 
    print("Links:",  self.links)
    print("External references:", self.external)

  def jsonify(self):
    #return '{\n\t"url":"'+self.url+'",\n\t "title":"'+json.dumps(self.title)+'",\n\t"authors":'+json.dumps(self.authors)+',\n\t"date":"'+str(self.date)+'",\n\t"quotes":'+json.dumps(self.quotes)+',\n\t"links":'+json.dumps(self.links)+',\n\t"cite_text":'+json.dumps(self.cite_text)+'\n}'
    return ('{\n\t"url":"'+self.url+
            '",\n\t "title":'+json.dumps(self.title)+
            ',\n\t"authors":'+json.dumps(self.authors)+
            ',\n\t"author_links":'+json.dumps(self.author_links)+
            ',\n\t"date":"'+str(self.date)+
            '",\n\t"quotes":'+json.dumps(self.quotes)+
            ',\n\t"names":'+json.dumps(self.names)+
            ',\n\t"links":'+json.dumps(self.links)+
            ',\n\t"sentiments":'+json.dumps(self.sentiments)+
            ',\n\t"num_flags":'+json.dumps(self.num_flags)+
            ',\n\t"cite_text":'+json.dumps(self.cite_text)+'\n}')

def my_tostring(x):
  return html.tostring(x, encoding = "unicode")

def track_authors(tree, author_tag, paper_type, link):
  link_ls = []

  if author_tag == 'N/A':
    return [paper_type], link_ls

  authors = []
  for tag in author_tag.split("AND"):
    authors.extend(tree.xpath(tag))
    html_auth_tag = tag.replace("/text()", "")
    h = tree.xpath(html_auth_tag)
    if h != []:
      h = tree.xpath(html_auth_tag)[-1]
      if(h.get('href')):
        link_ls.append(reformat(h.get('href'), paper_type)[0])
  new_auths =  []
  if paper_type == 'cnn':
    for a in authors:
      to_add =  a.replace("By ", "").replace(" and ", ", ").replace(", CNN", "").split(", ")
      new_auths.extend(to_add)
    authors = [x for x in new_auths if x != ""]

  if authors == []:
    n = "unknown"
    for recognized in recognized_pgs.keys():
      if recognized in link:
        n = recognized_pgs[recognized]
    authors = [n]
    #authors = [paper_type]
  return authors, link_ls

def get_date(tree, time_tag):
  try:
    return tree.find_class(time_tag)[0].text
  except:
    return "Error: Could not get date"

def get_body(tree, body_tag):
  # below applies to CNN:
  for bad in tree.xpath('//div[@class="el__storyhighlights"]'):
    bad.getparent().remove(bad)

  body_parts = tree.xpath(body_tag)
  body = ""
  for b in body_parts:
    body = body + str(html.tostring(b))
  return body

def clean_text(text):
  # not sure how the replace/re differ but they seem to...
  text = re.sub(u'\xe2\x80\x9c', '"', text)
  text = re.sub(u'\xe2\x80\x9d', '"', text)
  text = re.sub(u'\xe2\x80\x98', "'", text)
  text = re.sub(u'\xe2\x80\x99', "'", text)
  text = re.sub(u'\xe2\x80\x94', "-", text)

  text = text.replace("“", '"')
  text = text.replace("”", '"')
  text = text.replace("’", "'")

  cleanr = re.compile('<.*?>')
  cleanr2 = re.compile('{.*?}')
  text = re.sub(cleanr, '', text)
  text = re.sub(cleanr2, '', text)

  return text

def get_quotes(tree, para_tag, paper_type):
  paragraphs = tree.xpath(para_tag)
  quotes = []
  for p in paragraphs:
    unit = {}
    p_text = clean_text(str(html.tostring(p)))
    unit['paragraph'] = p_text
    found = ""
    for c in str(p_text):
      if len(found) != 0:
        found = found + c
        if c == '"':
          unit['quote'] = found
          quotes.append(unit)
          found = ""
      else:
        if c == '"':
          found = found + c
  return quotes

def get_links(body):
  url_list = []
  citations_list = []
  try:
    ls = html.fromstring(body).xpath("//a")
    for l in ls:
      # some 'a' make l.get('href') = None. (I'm guessing it's <a class=...>)
      # also want to avoid adding javascript:void(0) links
      url = l.get('href')
      if (url != None) and (url.find("javascript:")) < 0 and (url.find("mailto:") < 0):
        url_list.append(url)
        citations_list.append(l.text_content())
  except etree.XMLSyntaxError:
    return [], []
  return url_list, citations_list

def get_title(tree):
  try:
    return clean_text(tree.xpath('//title/text()')[0])
  except IndexError:
    return "No title found (sometimes occurs in PDFs)"

def paper(link):
  bad = 0
  for key in paper_tags.keys():
    if link.find(key) >= 0:
      info = paper_tags.get(key)
      return key
    else:
      bad += 1
  if bad == len(paper_tags):
    return None

def reformat(url, paper_type):
  new_type = paper_type
  if url.startswith("/"):
    # relative link case
    url = "http://www."+paper_type+".com"+url
  else:
    url = url.replace("https:", "http:")
    if not url.startswith("http"):
      url = "http://"+url
    if paper_type not in url:
      # identify if it is a paper program can handle
      link_type = paper(url)
      if not link_type:
        new_type = None
      else:
        new_type = link_type
  return [url, new_type]

def match2(quotes, links, paper_type):
  matches = {}
  for q in quotes:
    found = False
    for l in links:
      try:
        text = trees[l]
        if q[1:len(q)-1] in text:
          found = True
          matches[q] = l
          break
      except KeyError:
        # all I really need to do is check the page html
        text = str(requests.get(reformat(l, paper_type)[0], verify=False).content)
        text = re.sub("&#39;", "'", text)
        if q[1:len(q)-1] in text:
          found = True
          matches[q] = l
          break
        trees[l] = text
    if not found:
      print (q, "not found")
      matches[q] = False
  return matches

def analyze(link):
  try:
    text = trees[link]
  except KeyError:
    text = TextBlob(str(requests.get(reformat(link, paper_type)[0], verify=False).content))
  return text.sentiment

# count mismatches between quote and paragraph sentiment
def count_flags(tree, para_tag, quotes):
  paragraphs = tree.xpath(para_tag)
  diff_counter = 0
  for p in paragraphs:
    for q in quotes:
      s = p.text_content()
      if q in s:
        if TextBlob(s).sentiment.polarity * TextBlob(q).sentiment.polarity < 0:
          diff_counter += 1
  return diff_counter

# analyze just the paragraph containing the quote
def analyze2(tree, paragraph, quote):
  if quote in paragraph:
    text = TextBlob(paragraph)
    return str(text.sentiment)
  return str(None) #if error

def get_names2(body):
  names = []
  try:
    text = html.fromstring(body).text_content()
    for sent in nltk.sent_tokenize(text):
      for chunk in nltk.ne_chunk(nltk.pos_tag(nltk.word_tokenize(sent))):
        if hasattr(chunk, 'label'):
          names.append((chunk.label(), ' '.join(c[0] for c in chunk.leaves())))
  except:
    pass
  return names

# adding from author links into queue (need to test)
def add_same_authors(tree, queue, paper_type):
  articles_urls = get_links(tree.xpath(paper_tags[paper_type]['href']))
  for url in articles_urls:
    t2 = html.fromstring(requests.get(url, verify=False).content)
    b = get_body(t2, new_info['body'])
    c2 = get_links(b)
    new_authors, new_auth_ls = track_authors(t2, new_info['author'], new_tag, link)
    new_article = Article(link, 
                          get_title(t2), 
                          new_authors, 
                          get_date(t2, new_info['date']),
                          get_quotes(t2, new_info['paragraph'],  new_tag),
                          c2[0],
                          ext_refs,
                          0)
    if new_article.quotes != []:
      for q in new_article.quotes[0]:
        new_article.sentiments.append(analyze2(tree, paper_tags[paper_type]['paragraph'], q))
    new_article.author_links = new_auth_ls
    new_article.cite_text = c2[1]

def main():
  arg = sys.argv
  paper_type = paper(arg[1])
  print(arg[1])
  if not paper_type:
    print("Unable to handle this paper")
    return
  info = paper_tags.get(paper_type)

  t = html.fromstring(requests.get(arg[1], verify=False).content)
  authors, auth_ls = track_authors(t, info['author'], paper_type, arg[1])
  cites = get_links(get_body(t, info['body']))
  links = cites[0]
  date = get_date(t, info['date'])
  title = get_title(t) # (will find html page title, not exactly article title)

  root = Article(arg[1], title, authors, date, get_quotes(t, info['paragraph'], paper_type), links, 0)
  root.author_links = auth_ls
  print("ROOT QUOTES:", root.quotes)
  if root.quotes != []:
    for q in root.quotes[0]:
      root.sentiments.append(analyze2(t, info['paragraph'], q))
  root.cite_text = cites[1]

  visited, queue = [arg[1]], collections.deque([root, None]) 

  depth = 1 # started it at 1 since root depth = 0
  depthls = [0]

  trees[arg[1]] = t
  articles = [root]
  total_links = 1 # starts at 1 bc of root
  num_vertices = 0
  while (depth < 3) and (len(queue) != 0):
    num_vertices += 1
    vertex = queue.popleft()
    print("APPENDING "+vertex.url)
    total_links += len(vertex.links)
    for link in vertex.links:
      ext_refs = []
      original_link = link
      formatted = reformat(link, paper_type)
      link = formatted[0]
      new_tag = formatted[1]
      new_info = paper_tags.get(new_tag)
      if not new_tag:
        ext_refs.append(original_link)
        if link not in visited:
          visited.append(link)
          depthls.append(depth)
      else:
        if (link not in visited) and ('//#' not in link):
          # check whether this is already queued
          in_queue = False
          for q in queue:
            if (q != None) and (q.url == link):
              in_queue = True
          
          if not in_queue:
            try:
              t2 = html.fromstring(requests.get(link, verify=False).content)
              b = get_body(t2, new_info['body'])
              c2 = get_links(b)
              new_authors, new_auth_ls = track_authors(t2, new_info['author'], new_tag, link)
              new_article = Article(link, 
                                  get_title(t2), 
                                  new_authors, 
                                  get_date(t2, new_info['date']),
                                  get_quotes(t2, new_info['paragraph'],  new_tag),
                                  c2[0],
                                  ext_refs,
                                  depth)
              new_article.author_links = new_auth_ls
              new_article.cite_text = c2[1]
            except:
              n = "unknown"
              for recognized in recognized_pgs.keys():
                if recognized in link:
                  n = recognized_pgs[recognized]
              new_article = Article(link, get_title(html.fromstring(requests.get(link, verify=False).content)), [n], None)
              b = ""
            visited.append(link)
            new_article.names = get_names2(b)
            print(new_info['paragraph'])
            print(new_article.quotes)
            # TODO resolve and uncomment this.. not sure how
            # if new_article.quotes != []:
            #   for q in new_article.quotes:
            #     print("q is ", q['quote'])
            #     new_article.sentiments.append(analyze2(t2, q['paragraph'], q['quote']))
            # get author links
            
            articles.append(new_article)
            try:
              trees[original_link] = clean_text(html.fromstring(b).text_content())#, new_tag)
            except:
              # this page would not have a quote anyway
              pass
            depthls.append(depth)
            queue.append(new_article)

    # this is when the next depth is reached
    if (queue[0] == None):
      queue.popleft()
      # only stop if queue is empty
      if len(queue) != 0:
        queue.append(None)
      depth += 1

  print("\nVISITED:")
  for i in range(len(visited)):
    print(visited[i]+": "+str(depthls[i]))
  print("\nNUMBER OF LINKS:", total_links)
  print("NUMBER OF DISTINCT:", len(visited))

  qs0 = get_quotes(t, info['paragraph'], paper_type)
  qs = []
  for i in qs0:
    qs.append(i['quote'])
  print(qs)

  citations_index = []
  text = html.fromstring(get_body(t, info['body'])).text_content()
  clean_text(text)
  for citations in root.cite_text:
    citations_index.append(text.find(citations))
  matched = match2(qs, root.links, paper_type)
  print("\n")
  for m in matched:
    print(m, matched[m])

  # check what was in the root's neighbors:
  #print "\nOriginal neighbors:"
  #for i in links:
  #  print i
  print(root.jsonify())
  # I think we don't actually want to append to the existing file...?
  if os.path.isfile("articles.json"):
    rand = randint(1, 10000)
    os.rename("articles.json", "articles"+str(rand)+".json")
  with open("articles.json", "a") as f:
    f.write('[\n')
    for a in articles:
      f.write(a.jsonify())
      if a != articles[-1]:
        f.write(',\n')
    f.write('\n]')

  print("Average links/page", 1.*total_links/num_vertices)
  print(get_names2(get_body(t, info['body'])))
main()

