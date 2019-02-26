# libraries
import json
from typing import List, Any

import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from pandas.io.json import json_normalize

# https://python-graph-gallery.com/323-directed-or-undirected-network/

# Build a dataframe with your connections
# This time a pair can appear 2 times, in one side or in the other!
with open("output.json") as f:
  data = json.loads(f.read())
print("im here")
data = json.loads(data)
nodenames: List[Any] = list(data["wasAssociatedWith"])+list(data["wasAttributedTo"])\
            +list(data["wasDerivedFrom"])+list(data["wasGeneratedBy"])

vallist = [];
for item in data["wasAssociatedWith"]:
    vallist.append(list(data["wasAssociatedWith"][item].values())[0])
    vallist.append(list(data["wasAssociatedWith"][item].values())[1])
for item in data["wasAttributedTo"]:
    vallist.append(list(data["wasAttributedTo"][item].values())[0])
    vallist.append(list(data["wasAttributedTo"][item].values())[1])
for item in data["wasDerivedFrom"]:
    vallist.append(list(data["wasDerivedFrom"][item].values())[0])
    vallist.append(list(data["wasDerivedFrom"][item].values())[1])
for item in data["wasGeneratedBy"]:
    vallist.append(list(data["wasGeneratedBy"][item].values())[0])
    vallist.append(list(data["wasGeneratedBy"][item].values())[1])
nodelist = []
for node in nodenames:
    nodelist.append(node)
    nodelist.append(node)
print(vallist)
print(nodenames)
#pdjson = pd.read_json(data);
df = pd.DataFrame({'from': nodelist, 'to': vallist})
print("got here")
#df = pd.DataFrame({'from': ['D', 'A', 'B', 'C', 'A'], 'to': ['A', 'D', 'A', 'E', 'C']})
df
# Build your graph. Note that we use the DiGraph function to create the graph!
G = nx.from_pandas_edgelist(df, 'from', 'to', create_using=nx.Graph())

# Make the graph
nx.draw(G, with_labels=True, node_size=500, alpha=0.5, arrows=True)

plt.title("UN-Directed")
plt.show()
