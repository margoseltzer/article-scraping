import json
import sys
sys.path.append('/home/ychinlee/prov-cpl/bindings/python/CPL')
import CPL

originator = "root"
c = CPL.cpl_connection()

with open("articles.json") as f:
  data = json.loads(f.read())

##################
bundle_name = "bundle"
bundle_type = CPL.BUNDLE
bundle = c.create_object(originator, bundle_name, bundle_type)
CPL.p_object(bundle, False)

stuff = []
relations = []

articles = {}

for article in data:
  entity = c.create_object(originator, str(article["url"]), CPL.ENTITY, bundle)
  CPL.p_object(entity)
  stuff.append(entity)
  articles[article['url']] = (entity, article)

  for author in article["authors"]:
    agent_type = CPL.AGENT
    agent_name = str(author)
    agent = c.create_object(originator, agent_name, agent_type, bundle)
    CPL.p_object(agent)
    stuff.append(agent)
    print "Agent:", agent
    print "entity:", entity
    relations.append(entity.relation_to(agent, CPL.WASATTRIBUTEDTO, bundle))

  index = 0
  for quote in article["quotes"][0]:
    q = c.create_object(originator, str(quote), CPL.ACTIVITY, bundle)
    CPL.p_object(q)
    stuff.append(q)
    relations.append(entity.relation_to(q, CPL.WASGENERATEDBY, bundle))
'''

    s = article["sentiments"][index]
    relations.append(q.relation_to(s, CPL.WASASSOCIATEDWITH, bundle))
    index += 1
'''

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
  
c.export_bundle_json(bundle, "output.txt")

c.close()

