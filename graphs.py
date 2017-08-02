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

cite = c.create_object(originator, 'Cite', CPL.ACTIVITY, bundle)
CPL.p_object(bundle)
write = c.create_object(originator, 'Write', CPL.ACTIVITY, bundle)
CPL.p_object(bundle)

for article in data:
  entity_name = article  # not sure I can do this but I'd like to in order to retain the info
  entity_type = CPL.ENTITY
  entity = c.create_object(originator, entity_name, entity_type, bundle)
  CPL.p_object(entity)
  stuff.append(entity)

  for author in article["authors"]:
    agent_name = "Author"
    agent_type = CPL.AGENT
    agent_name = author
    agent = c.create_object(originator, agent_name, agent_type, bundle)
    CPL.p_object(agent)
    stuff.append(agent)
    articles[article['link']] = agent
    relations.append(entity.relation_to(agent, CPL.WASATTRIBUTEDTO, bundle))

for a in articles:
  article = articles[a]
  # find other articles, add relationship to articles
  for link in article["links"]:
    try:
      match = articles[link]
    except KeyError:
      match = None
    if not match:
      relations.append(article.relation_to(articles, CPL.WASGENERATEDBY, bundle))
  
c.close()
