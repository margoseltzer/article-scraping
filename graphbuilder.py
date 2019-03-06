# libraries
import json
from typing import List, Any

import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from pandas.io.json import json_normalize

# https://python-graph-gallery.com/323-directed-or-undirected-network/

def extractname(str):
    return str.split(":")[1]

with open("output.json") as f:
  data = json.loads(f.read())
print("im here")
data = json.loads(data)
print(data)
# nodenames: List[Any] = list(data["wasAssociatedWith"])+list(data["wasAttributedTo"])\
#             +list(data["wasDerivedFrom"])+list(data["wasGeneratedBy"])
nodenames: List[Any] = list(data["wasAttributedTo"])\
            +list(data["wasDerivedFrom"])+list(data["wasGeneratedBy"])
#nodenames: List[Any] = list(data["wasAttributedTo"])+list(data["wasDerivedFrom"])

fromlist = [];
tolist = [];
# for item in data["wasAssociatedWith"]:
#     fromlist.append(extractname(list(data["wasAssociatedWith"][item].values())[0]))
#     tolist.append(extractname(list(data["wasAssociatedWith"][item].values())[1]))
for item in data["wasAttributedTo"]:
    fromlist.append(extractname(list(data["wasAttributedTo"][item].values())[0]))
    tolist.append(extractname(list(data["wasAttributedTo"][item].values())[1]))
for item in data["wasDerivedFrom"]:
    fromlist.append(extractname(list(data["wasDerivedFrom"][item].values())[0]))
    tolist.append(extractname(list(data["wasDerivedFrom"][item].values())[1]))
for item in data["wasGeneratedBy"]:
    fromlist.append(extractname(list(data["wasGeneratedBy"][item].values())[0]))
    tolist.append(extractname(list(data["wasGeneratedBy"][item].values())[1]))
nodelist = []

df = pd.DataFrame({'from': fromlist, 'to': tolist})
print("got here")
#df = pd.DataFrame({'from': ['D', 'A', 'B', 'C', 'A'], 'to': ['A', 'D', 'A', 'E', 'C']})
df
# Build your graph. Note that we use the DiGraph function to create the graph!
G = nx.from_pandas_edgelist(df, 'from', 'to', create_using=nx.Graph())
# https://stackoverflow.com/questions/27030473/how-to-set-colors-for-nodes-in-networkx-python
color_map = []
for node in G:
    if node.startswith('QUOTE'):
        color_map.append('blue')
    elif node.startswith('AUTHOR'):
        color_map.append('green')
    elif node.startswith('ARTICLE'):
        color_map.append('red')
    else: color_map.append('black')

# Make the graph
nx.draw(G, node_color = color_map, with_labels=False, node_size=500, alpha=0.5, arrows=True)

plt.title("UN-Directed")
plt.show()
