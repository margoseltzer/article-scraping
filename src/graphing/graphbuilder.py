import argparse
import networkx as nx
import json
from bokeh.io import show, output_file
from bokeh.models import Plot, Range1d, MultiLine, Circle, HoverTool, BoxZoomTool, ResetTool
from bokeh.models.graphs import from_networkx

originator = "test"
NODE_TYPES = ['entity','agent','activity']

def find_originator(data):
    for node_type in NODE_TYPES:
        try:
            nodes = data[node_type]
            for node_name in nodes:
                index = node_name.find(":")
                # print(node_name[:index])
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
        return ('blue', 'quote')
    elif  node_type == 'person':
        return ('green', 'name')
    elif node_type == 'article':
        return ('red', 'url')
    elif node_type == 'reference':
        return ('yellow', 'url')
    elif node_type == 'publisher':
        return ('purple', 'publisher')
    else:
        print ("UNKNOWN TYPE: " + node_type)
        return ('gray', None)

def main():
    global originator
    parser = argparse.ArgumentParser(
        description='based on prov json generate graph')
    parser.add_argument('-f', '--file', dest='file_name',required=True, help='name of file need to be process')

    args = parser.parse_args()

    with open(args.file_name) as f:
        data = json.load(f)
    root_url = data['root']
    bundle_data = data['bundle']
    
    originator = find_originator(bundle_data)

    #initial empty graph:
    G = nx.Graph()

    # add all nodes
    node_types = [item for item in bundle_data if item in NODE_TYPES]
    for node_type in node_types:
        print("add all " + node_type + " nodes")
        nodes = bundle_data[node_type]
        for node_name in nodes:
            node = nodes[node_name]
            n_type = node[add_prefix_to_name('type')]
            n_color, n_name = assign_color(n_type) 
            n_value = node[add_prefix_to_name(n_name)] if n_name else None
            n_color = 'black' if n_value == root_url else n_color
            G.add_node(extract_name(node_name), type=n_type, color=n_color, value=n_value)

    # add all edges
    edge_types = [item for item in bundle_data if item not in NODE_TYPES]
    for edge_type in edge_types:
        print("add all " + edge_type + " edges")
        edges = bundle_data[edge_type]
        for edge_name in edges:
            edge = edges[edge_name]
            values = list(edge.values())
            from_node = extract_name(values[0])
            to_node = extract_name(values[1])
            G.add_edge(from_node, to_node)

    # Show with Bokeh
    plot = Plot(plot_width=1200, plot_height=750,
                x_range=Range1d(-1.1, 1.1), y_range=Range1d(-1.1, 1.1))
    plot.title.text = "Provenance graph"

    node_hover_tool = HoverTool(tooltips=[("type", "@type"), ("value", "@value")])
    plot.add_tools(node_hover_tool, BoxZoomTool(), ResetTool())

    graph_renderer = from_networkx(G, nx.spring_layout, scale=1, center=(0, 0))

    graph_renderer.node_renderer.glyph = Circle(size=15, fill_color='color')
    graph_renderer.edge_renderer.glyph = MultiLine(line_alpha=0.8, line_width=1)
    plot.renderers.append(graph_renderer)

    output_file("provenance_graphs.html")

    show(plot)

main()
