import sys
import json


'''
lable diferent node using number start from 0
represent graph as edge list
each line would be one edge
format:
src_node_lable  dst_node_lable  src_node_type:dst_node_type:edge_typt
'''

originator = "test"
NODE_TYPES = ['entity','agent','activity']
NODE_TYPES_MAP = {
    'article': 1,
    'publisher': 2,
    'person': 3,
    'quote': 4,
    'reference': 5
}

EDGE_TYPES_MAP = {
    'wasDerivedFrom': 1,
    'wasAttributedTo': 2,
}
# helper to pull out the "root:" prefix from prov-json objects
def extract_name(name_with_prefix):
    start_index = len(originator) + 1
    return name_with_prefix[start_index:]

def add_prefix_to_name(name):
    return originator + ':' + name

def find_originator(data):
    for node_type in NODE_TYPES:
        try:
            nodes = data[node_type]
            for node_name in nodes:
                index = node_name.find(":")
                return node_name[:index]
        except Exception as e:
            pass
    raise Exception('can not found originator')

def main():
    global originator
    file_name = sys.argv[1]
    output_name = sys.argv[2]

    with open(file_name) as f:
        json_data = json.load(f)

    root_url = json_data['root']
    bundle_data = json_data['bundle']

    originator = find_originator(bundle_data)

    i = 0
    node_map = {}

    node_types = [item for item in bundle_data if item in NODE_TYPES]
    for node_type in node_types:
        nodes = bundle_data[node_type]
        for node_name in nodes:
            node = nodes[node_name]
            n_type = NODE_TYPES_MAP[node[add_prefix_to_name('type')]]
            node_map[node_name] = (i, n_type)
            i += 1
        print("add all " + node_type + " nodes to node lable map")
    
    with open(output_name, 'w') as f:
        edge_types = [item for item in bundle_data if item not in NODE_TYPES]
        for edge_type in edge_types:
            edges = bundle_data[edge_type]
            for edge_name in edges:
                edge = edges[edge_name]
                values = list(edge.values())
                from_node = values[0]
                to_node = values[1]
                from_node_id, from_node_type = node_map[from_node]
                to_node_id, to_node_type = node_map[to_node]
                edge_type_number = EDGE_TYPES_MAP[edge_type]
                edge_str = str(from_node_id) + '\t' + str(to_node_id) + '\t' + str(from_node_type) + ':' + str(to_node_type) + ':' + str(edge_type_number) + '\n'
                f.write(edge_str)
            print("write all " + edge_type + " edges to " + output_name)
    
main()


    

    