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

cite = c.create_object(originator, 'Cite', CPL.ACTIVITY, bundle)
CPL.p_object(bundle)
write = c.create_object(originator, 'Write', CPL.ACTIVITY, bundle)
CPL.p_object(bundle)

articles = {}

for article in data:
  entity_name = str(article["url"])
  entity_type = CPL.ENTITY
  entity = c.create_object(originator, entity_name, entity_type, bundle)
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

for article in articles:
  a = articles[article]
  # find other articles, add relationship to articles
  for link in a[1]["links"]:
    try:
      match = articles[link][0]
    except KeyError:
      match = None
    if match:
      relations.append(a[0].relation_to(match, CPL.WASGENERATEDBY, bundle))
  
c.export_bundle_json(bundle, "output.txt")

c.close()
