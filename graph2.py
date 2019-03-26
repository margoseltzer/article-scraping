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
bundle_name = str(data[0]["url"]);
bundle_type = CPL.ENTITY
try:
    print("about to look up")
    bundle = c.lookup_bundle(bundle_name)
except Exception, e:
    print("about to create")
    bundle = c.create_bundle(bundle_name)
# CPL.p_bundle(bundle, False)

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

  try:
    entity = c.lookup_object(originator, "ARTICLE "+str(article_counter), CPL.ENTITY, bundle)
  except Exception, e:
     print(str(e.message))
     entity = c.create_object(originator, "ARTICLE "+str(article_counter), CPL.ENTITY, bundle)
  relations.append(entity.relation_from(bundle, 19, bundle))
  #s = article["title"].decode('ascii', 'ignore')
  #entity.add_property(originator, "title", s)
  entity.add_property(originator, "url", str(article["url"]))
  article_counter += 1
  strings.append(str(article["url"]))


  # CPL.p_object(entity)
  node_names += 1
  stuff.append(entity)
  articles[article["url"]] = (entity, article)

  for author in article["authors"]:
    agent_type = CPL.AGENT
    agent_name = "AUTHOR "+str(author_counter)
    author_counter += 1

    strings.append(str(author))
    try:
        agent = c.lookup_object(originator, agent_name, agent_type, bundle)
    except Exception, e:
        agent = c.create_object(originator, agent_name, agent_type, bundle)

    relations.append(agent.relation_from(bundle, 19, bundle))
    agent.add_property(originator, "author", str(author))

   # CPL.p_object(agent)
    node_names += 1
    stuff.append(agent)
    print ("Agent:", agent)
    print ("entity:", entity)
    print("about to add relation")
    relations.append(entity.relation_to(agent, CPL.WASATTRIBUTEDTO, bundle))


  index = 0
  for unit in article["quotes"]:
    for x in unit:
      if (x == 'quote'):
        quote = unit[x];
    try:
        q = c.lookup_object(originator, "QUOTE "+str(quote_counter), CPL.ACTIVITY, bundle)
    except Exception, e:
        q = c.create_object(originator, "QUOTE "+str(quote_counter), CPL.ACTIVITY, bundle)
    relations.append(q.relation_from(bundle, 19, bundle))
    q.add_property(originator, "quote", str(quote))
    quote_counter += 1
    #print(quote)
    # CPL.p_object(q)
    strings.append(quote)
    node_names += 1
    stuff.append(q)
    relations.append(entity.relation_to(q, CPL.WASGENERATEDBY, bundle))
    if index < len(article["sentiments"]):
        try:
            s = c.lookup_object(originator, "SENTIMENT "+str(sentiment_counter), CPL.AGENT, bundle)
        except Exception, e:
            s = c.create_object(originator, "SENTIMENT " + str(sentiment_counter), CPL.AGENT, bundle)
        relations.append(s.relation_from(bundle, 19, bundle))
        sentiment_counter += 1
        # print ("doodlye doo:",str(article["sentiments"][index]))
        # print ("doodley doo:",str(article["quotes"][index]))
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

# TODO need to update export function
print ("finished execution")
# outdata = c.export_bundle_json(bundles)
# with open('output.json', 'w') as outfile:
#     json.dump(outdata, outfile)
c.close()

