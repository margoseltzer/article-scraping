import json
import sys
#sys.path.append('C:\\Users\\johns\\Documents\\prov-cpl\\bindings\\python')
#sys.path.insert(0, 'C:\\Users\\johns\\Documents\\prov-cpl\\bindings\\python')
import CPL
from CPL import cpl_relation

originator = "demo"
c = CPL.cpl_connection()

# with open("prov.json") as f:
#   data = json.loads(f.read())
# c.import_document_json(data, "testrprov", None, 0)
with open("articles.json") as f:
  data = json.loads(f.read())



##################
bundle_name = str(data[0]["url"]);
bundle_type = CPL.ENTITY
try:
    print("about to look up")
    bundle = c.lookup_bundle(bundle_name, originator)
except Exception as e:
    print("about to create")
    bundle = c.create_bundle(bundle_name, originator)
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
    entity = c.lookup_by_property(originator, "url", str(article["url"]))[0];
    print("this worked");
  except Exception as e:
     print(str(e.message))
     entity = c.create_object(originator, "ARTICLE "+str(article_counter), CPL.ENTITY, bundle)
     entity.add_property(originator, "url", str(article["url"]))

  relations.append(entity.relation_from(bundle, 19, bundle))
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
        agent = c.lookup_by_property(originator, "author", str(author))[0];
    except Exception as e:
        agent = c.create_object(originator, agent_name, agent_type, bundle)
        agent.add_property(originator, "author", str(author))

    relations.append(agent.relation_from(bundle, 19, bundle))

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
        quote
        print("quote was properly defined");
        try:
            q = c.lookup_by_property(originator, "quote", str(quote))[0]
        except Exception as e:
            q = c.create_object(originator, "QUOTE " + str(quote_counter), CPL.ACTIVITY, bundle)
            q.add_property(originator, "quote", str(quote))
        relations.append(q.relation_from(bundle, 19, bundle))
        quote_counter += 1
        # CPL.p_object(q)
        strings.append(quote)
        node_names += 1
        stuff.append(q)
        relations.append(entity.relation_to(q, CPL.WASGENERATEDBY, bundle))
    except Exception as e:
        print ("quote was improperly defined")
    if index < len(article["sentiments"]):
        try:
            s = c.lookup_object(originator, "SENTIMENT "+str(sentiment_counter), CPL.AGENT, bundle)
        except Exception as e:
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

# gathers up all the bundles under this originator for the output file
# if you just want info for one bundle, change this to bundles = [bundle]
# bundles = []
# for o in c.get_all_objects(originator, 0):
#     print(o.name)
#     b = c.lookup_bundle(o.name, originator)
#     bundles.append(b)
bundles = [bundle]

# https://stackoverflow.com/questions/12309269/how-do-i-write-json-data-to-a-file

# TODO need to update export function
outdata = c.export_bundle_json(bundles)
print(str(outdata))
with open('output.json', 'w') as outfile:
    json.dump(outdata, outfile)

print ("finished execution")
c.close()

