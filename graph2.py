import json
import sys
sys.path.append('/home/ychinlee/prov-cpl/bindings/python/CPL')
import CPL

originator = "root"
c = CPL.cpl_connection()

with open("articles0.json") as f:
  data = json.loads(f.read())

##################
bundle_name = "bundle"
bundle_type = CPL.BUNDLE
bundle = c.create_object(originator, bundle_name, bundle_type)
CPL.p_object(bundle, False)

stuff = []
relations = []
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
    print "Agent:", agent
    print "entity:", entity
    relations.append(entity.relation_to(agent, CPL.WASATTRIBUTEDTO, bundle))

  index = 0
  for quote in article["quotes"][0]:
    q = c.create_object(originator, "QUOTE "+str(quote_counter), CPL.ACTIVITY, bundle)
    quote_counter += 1

    CPL.p_object(q)
    strings.append(quote)
    node_names += 1
    stuff.append(q)
    relations.append(entity.relation_to(q, CPL.WASGENERATEDBY, bundle))

    s = c.create_object(originator, "SENTIMENT "+str(sentiment_counter), CPL.AGENT, bundle)
    sentiment_counter += 1
    strings.append(str(article["sentiments"][index]))
    relations.append(s.relation_to(q, CPL.WASASSOCIATEDWITH, bundle))
    index += 1

for article in articles:
  a = articles[article]
  # find other articles, add relationship to articles
  for link in a[1]["links"]:
    try:
      match = articles[link][0]
    except KeyError:
      match = None
    if match:
      relations.append(a[0].relation_to(match, CPL.WASDERIVEDFROM, bundle))
  
c.export_bundle_json(bundle, "output.json")

c.close()

