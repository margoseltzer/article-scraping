import sys
import feedparser
import requests
import collections
import re
from lxml import html, etree
from unidecode import unidecode

# CNN one might not always work depending on if author has url or not
# paper : [author tag, body tag, date class]
'''

RUN: python in_progress.py http://www.cnn.com/2017/06/15/us/bill-cosby-jury-six-questions/index.html

'''
trees = {}
paper_tags = {'bbc' : ['N/A', '//div[@class="story-body__inner"]', 'data date-time'],
              'cnn' : ['//span[@class="metadata__byline__author"]/text()AND//span[@class="metadata__byline__author"]/a/text()', '//section[@id="body-text"]', 'update-time'],
              'reuters' : ['//div[@id="article-byline"]/span/a/text()', '//span[@id="article-text"]', 'timestamp'],
              'nyt' : ['//span[@class="byline-author"]/text()', '//p[@class="story-body-text story-content"]', 'dateline'],
              'washingtonexaminer' : ['//span[@itemprop="name"]/text()', '//section[@class="article-body"]', 'article-date text-muted'],
              'chicagotribune' : ['//span[@itemprop="author"]/text()', '//div[@itemprop="articleBody"]', 'trb_ar_dateline_time'],
              'breitbart' : ['//a[@class="byauthor"]/text()', '//div[@class="entry-content"]', 'bydate'],
              'dailymail' : ['//p/a[@class="author"]/text()', '//div[@id="js-article-text"]', 'article-timestamp article-timestamp published'],
              'newstarget' : ['//div[@class="author-link"]/text()', '//div[@class="entry-content"]', 'entry-date updated']
             }

'''
  later want to put author extraction etc in this class
  also want to add ways to differentiate additional media (video/picture links, refs to other papers)
I shouldn't need this but here it is just in case:
class Citation:
  def __init__(self, u, t):
    self.url = u
    self.text = t
'''

class Article:
  def __init__(self, u, t, a, d, q=[], l=[], e=[], d2=0):
    self.url = u
    self.title = t
    self.authors = a
    self.date = d
    self.quotes = q
    self.links = l
    self.external = e
    self.depth = d2
    self.cite_text = []

  def to_string(self):
    print "\nURL: ", self.url
    print "Title: ", self.title
    print "Authors: ", self.authors
    print "Date: ", self.date
    print "Quotes: ", self.quotes
    print "Links: ",  self.links
    print "External references: ", self.external
    print "Depth: ", self.depth

def get_authors(tree, author_tag, paper_type):
  if author_tag == 'N/A':
    return paper_type
  authors = []
  for tag in author_tag.split("AND"):
    authors.extend(tree.xpath(tag))
  return authors

def get_date(tree, time_tag):
  try:
    return html.tostring(tree.find_class(time_tag)[0])
  except:
    return "Error: Could not get date"

def get_body(tree, body_tag):
  body_parts = tree.xpath(body_tag)
  body = ""
  for b in body_parts:
    body = body + html.tostring(b)
  return body

def get_quotes(tree, body_tag):
  text = html.fromstring(get_body(tree, body_tag)).text_content()
  text = re.sub(u'\xe2\x80\x9c', '"', text)
  text = re.sub(u'\xe2\x80\x9d', '"', text)
  text = re.sub(u'\xe2\x80\x98', "'", text)
  text = re.sub(u'\xe2\x80\x99', "'", text)
  text = re.sub(u'\xe2\x80\x94', "-", text)
  #text = unidecode(text)
  print text
  rx = r'\{[^}]+\}\\?'
  text = re.sub(rx, '', text)
  found = ""
  quotes_index = []
  quotes = []
  counter = 0
  for c in text:
    if len(found) != 0:
      found = found + c
      if c == '"':
        quotes.append(found)
        found = ""
    else:
      if c == '"':
        found = found + c
        quotes_index.append(counter)
    counter += 1
  return quotes, quotes_index

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
    return tree.xpath('//title')[0]
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
  if not url.startswith("http"):
    # relative link case
    url = "http://www."+paper_type+".com"+url
  else:
    if (url.find(paper_type) < 0):
      # identify if it is a paper program can handle
      link_type = paper(url)
      if not link_type:
        new_type = None
      else:
        new_type = link_type
  return [url, new_type]

def match2(quotes, links):
  matches = {}
  found = False
  for q in quotes:
    for l in links:
      t = trees[l]
      if html.tostring(t).find(q) >= 0:
        found = True
        matches[q] = l
        continue
    if not found:
      matches[q] = False
  return matches

'''
def match(quotes_index, citations_index):
  citations_index.append(sys.maxint)
  c_curr = 0
  matches = []
  # catch the beginning in case of no quotes but links
  while citations_index[c_curr] < quotes_index[0]:
    matches.append((citations_index[c_curr], []))
    c_curr += 1
  for i in range(len(quotes_index)):
    if citations_index[c_curr-1] <= quotes_index[i] and quotes_index[i] < citations_index[c_curr]:
      matches[-1][1].append(quotes_index[i])
    else:
      matches.append((citations_index[c_curr], [quotes_index[i]]))
      c_curr += 1
  return matches
'''

def main():
  arg = sys.argv
  paper_type = paper(arg[1])
  if not paper_type:
    print "Unable to handle this paper"
    return
  info = paper_tags.get(paper_type)

  t = html.fromstring(requests.get(arg[1]).content)
  authors = get_authors(t, info[0], paper_type)
  cites = get_links(get_body(t, info[1]))
  links = cites[0]
  date = get_date(t, info[2])
  title = t.find_class('title') # (will find html page title, not exactly article title)

  root = Article(arg[1], title, authors, date, "", links, 0)
  root.cite_text = cites[1]

  visited, queue = [arg[1]], collections.deque([root, None]) 

  depth = 1 # started it at 1 since root depth = 0
  depthls = [0]

  trees[arg[1]] = t
  run = 0
  while (depth < 2) and (len(queue) != 0):
    #print "VISITED: ", visited
    vertex = queue.popleft()
    #print vertex.to_string()
    print "DEPTH = ", depth
    print "APPENDING "+vertex.url
    for link in vertex.links:
      ext_refs = []
      original_link = link
      formatted = reformat(link, paper_type)
      link = formatted[0]
      new_tag = formatted[1]
      new_info = paper_tags.get(new_tag)
      #print "formatted is ",formatted
      if not new_tag:
        ext_refs.append(original_link)
        if link not in visited:
          visited.append(original_link)
          depthls.append(depth)
      else:
        if link not in visited:
          # check whether this is already queued
          in_queue = False
          for q in queue:
            if (q != None) and (q.url == link):
              in_queue = True
          
          if not in_queue:
            #print "getting "+link
            try:
              #citations = get_links(get_body(t2, new_info[1]))
              #for c in citations:
              #  # get the text inside, I guess
              t2 = html.fromstring(requests.get(link).content)
              trees[original_link] = t2
              c2 = get_links(get_body(t2, new_info[1]))
              new_article = Article(link, 
                                  get_title(t2), 
                                  get_authors(t2, new_info[0], new_tag), 
                                  get_date(t2, new_info[2]),
                                  "",
                                  c2[0],
                                  ext_refs,
                                  depth)
              new_article.cite_text = c2[1]
            except: #requests.exceptions.SSLError
              new_article = Article(link, None, None, None, "", None, depth)
            visited.append(link)
            depthls.append(depth)
            #print "adding to queue: ", new_article.url
            queue.append(new_article)

    # this is when the next depth is reached
    if (queue[0] == None):
      queue.popleft()
      # only stop if queue is empty
      if len(queue) != 0:
        queue.append(None)
        #print "hey "+str(run)
      depth += 1

    #print "TITLE: ", html.tostring(new_article.title)
    #print "QUEUE:"
    #for q in queue:
    #  if q != None:
    #    print q.url
    #  else:
    #    print "None"
  
    run += 1
  print "\nVISITED:"
  for i in range(len(visited)):
    print visited[i]+": "+str(depthls[i])

  #print root.cite_text
  
  #look for root's quotes/citations
  # getting weird "" as citations, seems to be from images so I will remove those now
  qs0, indices0 = get_quotes(t, info[1])
  qs = []
  indices = []
  for i in range(len(qs0)):
    if qs0[i] != "":
      qs.append(qs0[i])
      indices.append(indices0[i])

  citations_index = []
  text = html.fromstring(get_body(t, info[1])).text_content()
  for citations in root.cite_text:
    citations_index.append(text.find(citations))
  #matched = match(indices, citations_index)
  matched = match2(qs, root.links)
  for m in matched:
    print m, matched[m]
    #print "LINK:", root.links[citations_index.index(m[0])], ":", root.cite_text[citations_index.index(m[0])]
    #for i in m[1]:
    #  print "QUOTE: ", qs[indices.index(i)]

  #for i in range(len(q)):
  #  if indices[i] <

  # check what was in the root's neighbors:
  #print "\nOriginal neighbors:"
  #for i in links:
  #  print i
main()

