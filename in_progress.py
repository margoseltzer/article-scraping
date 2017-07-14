import sys
import nltk
import json
import feedparser
import requests
import collections
import re
from lxml import html, etree
from textblob import TextBlob
#from unidecode import unidecode

# CNN one might not always work depending on if author has url or not
# paper : [author tag, body tag, date class]
'''

RUN: python in_progress.py http://www.cnn.com/2017/06/15/us/bill-cosby-jury-six-questions/index.html

'''
trees = {}
paper_tags = {'bbc' : ['N/A', '//div[@class="story-body__inner"]', 'date date--v2'],
              'cnn' : ['//span[@class="metadata__byline__author"]/text()AND//span[@class="metadata__byline__author"]/a/text()', '//section[@id="body-text"]', 'update-time'],
              'reuters' : ['//div[@id="article-byline"]/span/a/text()', '//span[@id="article-text"]', 'timestamp'],
              'nyt' : ['//span[@class="byline-author"]/text()', '//p[@class="story-body-text story-content"]', 'dateline'],
              'washingtonexaminer' : ['//span[@itemprop="name"]/text()', '//section[@class="article-body"]', 'article-date text-muted'],
              'chicagotribune' : ['//span[@itemprop="author"]/text()', '//div[@itemprop="articleBody"]', 'trb_ar_dateline_time'],
              'breitbart' : ['//a[@class="byauthor"]/text()', '//div[@class="entry-content"]', 'bydate'],
              'dailymail' : ['//p/a[@class="author"]/text()', '//div[@id="js-article-text"]', 'article-timestamp article-timestamp published'],
              'newstarget' : ['//div[@class="author-link"]/text()', '//div[@class="entry-content"]', 'entry-date updated'],
              'infowars' : ['//span[@class="author"]/text()', '//div[@class="text"]', 'date']
             }

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
    self.author_links = [] # links to author pages, if applicable
    self.names = []

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
            ',\n\t"date":"'+str(self.date)+
            '",\n\t"quotes":'+json.dumps(self.quotes)+
            ',\n\t"names":'+json.dumps(self.names)+
            ',\n\t"links":'+json.dumps(self.links)+
            ',\n\t"cite_text":'+json.dumps(self.cite_text)+'\n}')

def my_tostring(x):
  return html.tostring(x, encoding = "unicode")

def get_authors(tree, author_tag, paper_type):
  if author_tag == 'N/A':
    return [paper_type]
  authors = []
  for tag in author_tag.split("AND"):
    authors.extend(tree.xpath(tag))
  if paper_type == 'cnn':
    authors = authors[0].replace("By ", "").replace(" and ", ", ").replace(", CNN", "").split(", ")
  return authors

def track_authors(tree, author_tag, paper_type):
  link_ls = []

  if author_tag == 'N/A':
    return [paper_type], linkls

  authors = []
  for tag in author_tag.split("AND"):
    authors.extend(tree.xpath(tag))
    html_auth_tag = tag.replace("/text()", "")
    h = tree.xpath(html_auth_tag)[-1]
    if(h.get('href')):
      link_ls.append(reformat(h.get('href'), paper_type)[0])

  if paper_type == 'cnn':
    authors = authors[0].replace("By ", "").replace(" and ", ", ").replace(", CNN", "").split(", ")
  return authors, link_ls

def get_date(tree, time_tag):
  try:
    return tree.find_class(time_tag)[0].text
    #return html.tostring(tree.find_class(time_tag)[0])
  except:
    return "Error: Could not get date"

def get_body(tree, body_tag):
  body_parts = tree.xpath(body_tag)
  body = ""
  for b in body_parts:
    body = body + str(html.tostring(b))
  return body

def clean_text(text):
  #if paper_type not in ['nyt', 'infowars']:
  ##text = re.sub("\'", "'", text)
  #  return text
  #print("i should be changing things")
  # not sure how the replace/re differ but they seem to...
  text = re.sub(u'\xe2\x80\x9c', '"', text)
  text = re.sub(u'\xe2\x80\x9d', '"', text)
  text = re.sub(u'\xe2\x80\x98', "'", text)
  text = re.sub(u'\xe2\x80\x99', "'", text)
  text = re.sub(u'\xe2\x80\x94', "-", text)

  text = text.replace("“", '"')
  text = text.replace("”", '"')
  text = text.replace("’", "'")

  return text

def get_quotes(tree, body_tag, paper_type):
  text = html.fromstring(get_body(tree, body_tag)).text_content()
  text = clean_text(text)#, paper_type)
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
        #print(found)
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
    if paper_type in url:
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
        #print("i=",l)
        #print("q=", q, "len:", len(q), type(q))
        #print("t=", type(text))
        if q[1:len(q)-1] in text: #text.find(q) >= 0:
          found = True
          matches[q] = l
          break
      except KeyError:
        #pass
        # all I really need to do is check the page html
        text = str(requests.get(reformat(l, paper_type)[0]).content)
        text = re.sub("&#39;", "'", text)
        #if q[1:len(q)-1] in str(text):
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
    text = TextBlob(str(requests.get(reformat(link, paper_type)[0]).content))
  return text.sentiment

def get_names(tree, body_tag):
  names = []
  xa = html.fromstring(get_body(tree, body_tag))
  print("HI")
  body = xa.text_content()
  #text = html.fromstring(get_body(tree, body_tag)).text_content()
  for sent in nltk.sent_tokenize(body):
    for chunk in nltk.ne_chunk(nltk.pos_tag(nltk.word_tokenize(sent))):
      if hasattr(chunk, 'label'):
        names.append((chunk.label(), ' '.join(c[0] for c in chunk.leaves())))
  return names
def get_names2(body):
  names = []
  text = html.fromstring(body).text_content()
  for sent in nltk.sent_tokenize(text):
    for chunk in nltk.ne_chunk(nltk.pos_tag(nltk.word_tokenize(sent))):
      if hasattr(chunk, 'label'):
        names.append((chunk.label(), ' '.join(c[0] for c in chunk.leaves())))
  return names

def main():
  arg = sys.argv
  paper_type = paper(arg[1])
  if not paper_type:
    print("Unable to handle this paper")
    return
  info = paper_tags.get(paper_type)

  t = html.fromstring(requests.get(arg[1]).content)
  authors = get_authors(t, info[0], paper_type)
  #print("NEW FUNCTION:", track_authors(t, info[0], paper_type))
  cites = get_links(get_body(t, info[1]))
  links = cites[0]
  date = get_date(t, info[2])
  title = get_title(t)#t.find_class('title') # (will find html page title, not exactly article title)

  root = Article(arg[1], title, authors, date, get_quotes(t, info[1], paper_type), links, 0)
  root.author_links = track_authors(t, info[0], paper_type)[1]
  print("ROOT QUOTES:", root.quotes)
  root.cite_text = cites[1]

  visited, queue = [arg[1]], collections.deque([root, None]) 

  depth = 1 # started it at 1 since root depth = 0
  depthls = [0]

  trees[arg[1]] = t
  articles = []
  total_links = 1 # starts at 1 bc of root
  num_vertices = 0
  while (depth < 3) and (len(queue) != 0):
    num_vertices += 1
    #print "VISITED: ", visited
    vertex = queue.popleft()
    #print vertex.to_string()
    print("DEPTH = ", depth)
    print("APPENDING "+vertex.url)
    total_links += len(vertex.links)
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
          visited.append(link)#original_link)
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
              b = get_body(t2, new_info[1])
              c2 = get_links(b)
              new_article = Article(link, 
                                  get_title(t2), 
                                  get_authors(t2, new_info[0], new_tag), 
                                  get_date(t2, new_info[2]),
                                  get_quotes(t2, new_info[1],  new_tag),
                                  c2[0],
                                  ext_refs,
                                  depth)
              #print("NEW FUNCTION:", track_authors(t2, new_info[0], new_tag))
              new_article.author_links = track_authors(t2, new_info[0], new_tag)[1]
              new_article.cite_text = c2[1]
              print("new_auth:", new_article.authors)
            except: #requests.exceptions.SSLError
              new_article = Article(link, get_title(html.fromstring(requests.get(link).content)), [], None)
            visited.append(link)
            # not working so far
            #new_article.names = get_names(t2, new_info[1])
            # get author links
            
            articles.append(new_article)
            try:
              trees[original_link] = clean_text(html.fromstring(b).text_content())#, new_tag)
            except:
              # this page would not have a quote anyway
              pass
            depthls.append(depth)
            #print "adding to queue: ", new_article.url
            queue.append(new_article)

    # this is when the next depth is reached
    if (queue[0] == None):
      queue.popleft()
      # only stop if queue is empty
      if len(queue) != 0:
        queue.append(None)
      depth += 1

    #print "TITLE: ", html.tostring(new_article.title)
    #print "QUEUE:"
    #for q in queue:
    #  if q != None:
    #    print q.url
    #  else:
    #    print "None"
  
  print("\nVISITED:")
  for i in range(len(visited)):
    print(visited[i]+": "+str(depthls[i]))
  print("\nNUMBER OF LINKS:", total_links)
  print("NUMBER OF DISTINCT:", len(visited))

  #print root.cite_text
  
  #look for root's quotes/citations
  # getting weird "" as citations, seems to be from images so I will remove those now
  qs0, indices0 = get_quotes(t, info[1], paper_type)
  qs = []
  indices = []
  for i in range(len(qs0)):
    if qs0[i] != "":
      qs.append(qs0[i])
      indices.append(indices0[i])
  print(qs)

  citations_index = []
  text = html.fromstring(get_body(t, info[1])).text_content()
  clean_text(text)#, paper_type)
  for citations in root.cite_text:
    citations_index.append(text.find(citations))
  #matched = match(indices, citations_index)
  matched = match2(qs, root.links, paper_type)
  print("\n")
  for m in matched:
    print(m, matched[m])

  # check what was in the root's neighbors:
  #print "\nOriginal neighbors:"
  #for i in links:
  #  print i
  print(root.jsonify())
  with open("articles.json", "a") as f:
    f.write('[\n')
    for a in articles:
      f.write(a.jsonify())
      if a != articles[-1]:
        f.write(',\n')
    f.write('\n]')

  print("Average links/page", 1.*total_links/num_vertices)
  print(get_names2(get_body(t, info[1])))
main()

