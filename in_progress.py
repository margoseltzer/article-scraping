import sys
import feedparser
import requests
import collections
from lxml import html, etree

# CNN one might not always work depending on if author has url or not
# paper : [author_tag, body_tag]
'''

RUN: python in_progress.py http://www.cnn.com/2017/06/15/us/bill-cosby-jury-six-questions/index.html

'''
paper_tags = {'bbc' : ['N/A', '//div[@id=story-body]', 'data date-time'],
              'cnn' : ['//span[@class="metadata__byline__author"]/text()', '//section[@id="body-text"]', 'update-time'],
              'reuters' : ['//div[@id="article-byline"]/span/a/text()', '//span[@id="article-text"]', 'timestamp'],
              'nyt' : ['//span[@class="byline-author"]/text()', '//article[@id="story"]', 'dateline']
             }

'''
  later want to put author extraction etc in this class
'''
class Article:
  def __init__(self, u, t, a, d, q=[], l=[], e=[]):
    self.url = u
    self.title = t
    self.authors = a
    self.date = d
    self.quotes = q
    self.links = l
    self.external = e

  def to_string(self):
    print "\nURL: ", self.url
    print "Title: ", self.title # have to deal with this later
    print "Authors: ", self.authors
    print "Date: ", self.date
    print "Quotes: ", self.quotes
    print "Links: ",  self.links
    print "External references: ", self.external

def get_authors(tree, author_tag):
  return tree.xpath(author_tag)

def get_date(tree, time_tag):
  return tree.find_class(time_tag)

def get_body(tree, body_tag):
  body_parts = tree.xpath(body_tag)
  body = ""
  for b in body_parts:
    body = body + html.tostring(b)
  return body

def get_links(body):
  url_list = []
  try:
    ls = html.fromstring(body).xpath("//a")
    for l in ls:
      # so apparently some 'a' make l.get('href') = None. (I'm guessing it's <a class=...>)
      # also want to avoid adding javascript:void(0) links...
      url = l.get('href')
      if (url != None) and (url.find("javascript:void(0)") < 0):
        url_list.append(url)
  except etree.XMLSyntaxError:
    print "URL had incorrect tag in this body: ", body
  #print "URLS: ",url_list
  return url_list

def get_title(tree):
  try:
    return tree.xpath('//title')[0]
  except IndexError:
    return "No title (could be a PDF)"

# NEEDS TO BE MADE SPECIFIC FOR EACH PAPER. RIGHT NOW APPLIES ONLY TO CNN
def reformat(url, paper_type):
  #print "\nREFORMATING "+url
  if url.find("http") < 0:
    # relative link case
    url = "http://www."+paper_type+".com"+url
  else:
    if (url.find(paper_type) < 0) and (url.find(".com") > 0):
      # basically I want to know whether the url is not from the newspaper
      return "Bad source"
  #print "URL IS "+url+"\n"
  return url

def main():
  arg = sys.argv
  bad = 0 # check whether you have presets for this paper
  for key in paper_tags.keys():
    print key
    if arg[1].find(key) > 0:
      info = paper_tags.get(key)
      paper_type = key
      break
    else:
      bad += 1
  if bad == len(paper_tags):
    print "Unable to handle this paper"
    return
  t = html.fromstring(requests.get(arg[1]).content)
  authors = get_authors(t, info[0])
  links = get_links(get_body(t, info[1]))
  date = get_date(t, info[2])
  title = t.find_class('title') # (will find html page title, not exactly article title)

  visited, queue = [], collections.deque([Article(arg[1], title, authors, date, "", links)]) 

  depth = 0
  original_link = link
  while (depth < 5) and (len(queue) != 0):
    #print "VISITED: ", visited
    vertex = queue.popleft()
    visited.append(vertex.url)
    for link in vertex.links:
      #print "LINK IS ", link
      #print "QUEU LEN ", len(queue)

      link = reformat(link, paper_type)
      if link == "Bad source":
        print "This is not a ", paper_type, " link"
        visited.append(original_link)
      # ELSE BELOW
      if link not in visited:
        #print "URL: ", link
        t2 = html.fromstring(requests.get(link).content)
        new_article = Article(link, 
                            get_title(t2), 
                            get_authors(t2, info[0]), 
                            get_date(t2, info[2]),
                            "",
                            get_links(get_body(t2, info[1])))
        queue.append(new_article)
        #print "\nscraped ", link
        #print "adding ", new_article.links
    #print "TITLE: ", html.tostring(new_article.title)
    print "DEPTH = ", depth
    depth += 1
  
  print visited
main()

