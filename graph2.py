import json
import sys
#sys.path.append('C:\\Users\\johns\\Documents\\prov-cpl\\bindings\\python')
#sys.path.insert(0, 'C:\\Users\\johns\\Documents\\prov-cpl\\bindings\\python')
import CPL
from CPL import cpl_relation

originator = "root"
c = CPL.cpl_connection()

with open("articles.json") as f:
  data = json.loads(f.read())

##################
bundle_name = "bundle"
bundle_type = CPL.ENTITY
bundle = c.create_bundle(bundle_name)
CPL.p_bundle(bundle, False)

stuff = []
relations = []  # type: List[cpl_relation]
strings = []
node_names = 0 # counter
article_counter = 0
author_counter = 0
quote_counter = 0
sentiment_counter = 0

articles = {}
for article in data:
  
  entity = c.create_object(originator, "ARTICLE "+str(article_counter), CPL.ENTITY, bundle)
  article_counter += 1
  strings.append(str(article["url"]))

  CPL.p_object(entity)
  node_names += 1
  stuff.append(entity)
  articles[article["url"]] = (entity, article)

  for author in article["authors"]:
    agent_type = CPL.AGENT
    agent_name = "AUTHOR "+str(author_counter)
    author_counter += 1

    strings.append(str(author))
    agent = c.create_object(originator, agent_name, agent_type, bundle)
    CPL.p_object(agent)
    node_names += 1
    stuff.append(agent)
    print ("Agent:", agent)
    print ("entity:", entity)
    relations.append(entity.relation_to(agent, CPL.WASATTRIBUTEDTO, bundle))

  index = 0
  for unit in article["quotes"]:
    for x in unit:
      if (x == 'quote'):
        quote = unit[x];
    q = c.create_object(originator, "QUOTE "+str(quote_counter), CPL.ACTIVITY, bundle)
    quote_counter += 1
    #print(quote)
    CPL.p_object(q)
    strings.append(quote)
    node_names += 1
    stuff.append(q)
    relations.append(entity.relation_to(q, CPL.WASGENERATEDBY, bundle))
    if index < len(article["sentiments"]):
        s = c.create_object(originator, "SENTIMENT "+str(sentiment_counter), CPL.AGENT, bundle)
        sentiment_counter += 1
        print ("doodlye doo:",str(article["sentiments"][index]))
        print ("doodley doo:",str(article["quotes"][index]))
        strings.append(str(article["sentiments"][index]))
        relations.append(s.relation_to(q, CPL.WASASSOCIATEDWITH, bundle))
    index += 1

for article in articles:
  a = articles[article]
  # find other articles, add relationship to articles
  for link in a[1]["links"]:
    if "http://" in link:
      alt = link.replace("http://", "https://")
    else:
      alt = link.replace("https://", "http://")
    match = None
    try:
      match1 = articles[link][0]
      match = match1
    except KeyError:
      match1 = None
    try:
      match2 = articles[alt][0]
      match = match2
    except KeyError:
      match2 = None
    if match1 or match2:
      relations.append(a[0].relation_to(match, CPL.WASDERIVEDFROM, bundle))

bundles = [bundle]
# https://stackoverflow.com/questions/12309269/how-do-i-write-json-data-to-a-file
outdata = c.export_bundle_json(bundles)
with open('output.json', 'w') as outfile:
    json.dump(outdata, outfile)
c.close()

