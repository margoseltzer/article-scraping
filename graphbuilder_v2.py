import argparse
import json
import networkx as nx
import matplotlib.pyplot as plt

originator = "test"
NODE_TYPES = ['entity','agent','activity']

def find_originator(data):
    for node_type in NODE_TYPES:
        try:
            nodes = data[node_type]
            for node_name in nodes:
                index = node_name.find(":")
                print(node_name[:index])
                return node_name[:index]
        except Exception as e:
            pass
    raise Exception('can not found originator')
            
# helper to pull out the "root:" prefix from prov-json objects
def extract_name(name_with_prefix):
    start_index = len(originator) + 1
    return name_with_prefix[start_index:]

def add_prefix_to_name(name):
    return originator + ':' + name

def assign_color(node_type):
    if node_type == 'quote':
        return 'blue'
    elif  node_type == 'person':
        return 'green'
    elif node_type =='article':
        return 'red'
    elif node_type == 'publisher':
        return 'purple'
    else:
        print ("UNKNOWN TYPE: " + node_type)
        return 'black'

def main():
    global originator
    parser = argparse.ArgumentParser(
        description='based on prov json generate graph')
    parser.add_argument('-f', '--file', dest='file_name',required=True, help='name of file need to be process')
    parser.add_argument('-l', '--lable', dest='lable', action='store_true',
                        help='show graph with node lable')

    args = parser.parse_args()

    with open(args.file_name) as f:
        data = json.load(f)
    
    originator = find_originator(data)

    #initial empty graph:
    G = nx.Graph()

    # add all nodes
    node_types = [item for item in data if item in NODE_TYPES]
    for node_type in node_types:
        print("add all " + node_type + " nodes")
        nodes = data[node_type]
        for node_name in nodes:
            node = nodes[node_name]
            n_type = node[add_prefix_to_name('type')]
            n_color = assign_color(n_type)
            G.add_node(extract_name(node_name), type=n_type, color=n_color)

    # add all edges
    edge_types = [item for item in data if item not in NODE_TYPES]
    for edge_type in edge_types:
        print("add all " + edge_type + " edges")
        edges = data[edge_type]
        for edge_name in edges:
            edge = edges[edge_name]
            values = list(edge.values())
            from_node = extract_name(values[0])
            to_node = extract_name(values[1])
            G.add_edge(from_node, to_node)

    colors = [node[1] for node in G.nodes(data='color')]
    nx.draw(G, node_color = colors, with_labels=(args.lable if args.lable else False), alpha=0.5)
    plt.show()

main()
    