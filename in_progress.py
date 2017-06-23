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
paper_tags = {'bbc' : ['N/A', '//div[@class=story-body]', 'data date-time'],
              'cnn' : ['//span[@class="metadata__byline__author"]/text()', '//section[@id="body-text"]', 'update-time'],
              'reuters' : ['//div[@id="article-byline"]/span/a/text()', '//span[@id="article-text"]', 'timestamp'],
              'nyt' : ['//span[@class="byline-author"]/text()', '//p[@class="story-body-text story-content"]', 'dateline'],
              'breitbart' : ['//a[@class="byauthor"]/text()', '//div[@class="entry-content"]', 'bydate'],
              'dailymail' : ['//p/a[@class="author"]/text()', '//div[@id="js-article-text"]', 'article-timestamp article-timestamp published']
             }

'''
  later want to put author extraction etc in this class
  also want to add ways to differentiate additional media (video/picture links, refs to other papers)
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
    self.neighbors = [] # to hold other articles

  def to_string(self):
    print "\nURL: ", self.url
    print "Title: ", self.title
    print "Authors: ", self.authors
    print "Date: ", self.date
    print "Quotes: ", self.quotes
    print "Links: ",  self.links
    print "External references: ", self.external
    print "Depth: ", self.depth

  def print_connections(self):
    print self.url+": "+str(self.depth)
    for i in self.neighbors:
      i.print_connections()

def get_authors(tree, author_tag, paper_type):
  if author_tag == 'N/A':
    return paper_type
  return tree.xpath(author_tag)

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

def get_links(body):
  url_list = []
  try:
    ls = html.fromstring(body).xpath("//a")
    for l in ls:
      # some 'a' make l.get('href') = None. (I'm guessing it's <a class=...>)
      # also want to avoid adding javascript:void(0) links
      url = l.get('href')
      if (url != None) and (url.find("javascript:")) < 0 and (url.find("mailto:") < 0):
        url_list.append(url)
  except etree.XMLSyntaxError:
    return []
  return url_list

def get_title(tree):
  try:
    return tree.xpath('//title')[0]
  except IndexError:
    return "No title (sometimes occurs in PDFs)"

def reformat(url, paper_type):
  if url.find("http") < 0:
    # relative link case
    url = "http://www."+paper_type+".com"+url
  else:
    if (url.find(paper_type) < 0) and (url.find(".com") >= 0):
      # basically I want to know whether the url is not from the newspaper
      return "Bad source: "+url
  return url

def main():
  arg = sys.argv
  bad = 0 # check whether you have presets for this paper
  for key in paper_tags.keys():
    print key
    if arg[1].find(key) >= 0:
      info = paper_tags.get(key)
      paper_type = key
      break
    else:
      bad += 1
  if bad == len(paper_tags):
    print "Unable to handle this paper"
    return
  t = html.fromstring(requests.get(arg[1]).content)
  authors = get_authors(t, info[0], paper_type)
  links = get_links(get_body(t, info[1]))
  date = get_date(t, info[2])
  title = t.find_class('title') # (will find html page title, not exactly article title)

  root = Article(arg[1], title, authors, date, "", links, 0)
  visited, queue = [arg[1]], collections.deque([root, None]) 
  print root.to_string()

  depth = 1 # started it at 1 since root depth = 0
  depthls = [0]

  run = 0
  while (depth < 5) and (len(queue) != 0):
    #print "VISITED: ", visited
    vertex = queue.popleft()
    print "DEPTH = ", depth
    #print "!!!! APPENDING!! "+vertex.url
    for link in vertex.links:
      ext_refs = []
      original_link = link
      link = reformat(link, paper_type)
      #print "link is "+link
      if link.find("Bad source") >= 0:
        #print "This is not a ", paper_type, " link"
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
              t2 = html.fromstring(requests.get(link).content)
              new_article = Article(link, 
                                  get_title(t2), 
                                  get_authors(t2, info[0], paper_type), 
                                  get_date(t2, info[2]),
                                  "",
                                  get_links(get_body(t2, info[1])),
                                  ext_refs,
                                  depth)
            except: #requests.exceptions.SSLError
              new_article = Article(link, None, None, None, "", None, depth)
            visited.append(link)
            depthls.append(depth)
            #print "adding to queue: ", new_article.url
            queue.append(new_article)

    # this is when the next depth is reached
    if (queue[0] == None):
      queue.popleft()
      queue.append(None)
      print "hey "+str(run)
      depth += 1

    #print "TITLE: ", html.tostring(new_article.title)
    print "QUEUE:"
    for q in queue:
      if q != None:
        print q.url
      else:
        print "None"
  
    run += 1
  print "\nVISITED:"
  for i in range(len(visited)):
    print visited[i]+": "+str(depthls[i])

  # check what was in the root's neighbors:
  #print "\nOriginal neighbors:"
  #for i in links:
  #  print i
main()

