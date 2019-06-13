import json
import argparse
import networkx as nx

class FeatureExtrator(object):
    '''
    Arguments: provenance output
    Initiaing an instance will extract all the features 
    '''
    def __init__ (self, graph):
        # Private variables
        self.__root          = graph['root']
        self.__wdf_relations = list(graph['bundle']['wasDerivedFrom'].values())
        self.__wat_relations = list(graph['bundle']['wasAttributedTo'].values())
        self.__agents        = list(graph['bundle']['agent'].values())
        self.__entities      = list(graph['bundle']['entity'].values())
        self.__all_relations = self._get_relations()
        self.__all_nodes     = self._get_nodes()
        self.__G             = self._construct_graph()

        # Extrated features

        # Simple features
        self.wdf_relations_count = len(self.__wdf_relations)
        self.wat_relations_count = len(self.__wat_relations)
        self.total_edges_count   = self._count_all_relations()
        
        self.entities_count  = len(self.__entities)
        entities_dict        = self._get_entities_dict() 
        self.article_count   = entities_dict['article']
        self.reference_count = entities_dict['reference']

        self.agents_count    = len(self.__agents)
        agents_dict          = self._get_agents_dict()
        self.person_count    = agents_dict['person'] if 'person' in agents_dict else []
        self.publisher_count = agents_dict['publisher']

        self.total_vertices_count = self._count_all_nodes()

        self.density = self._get_density()

        # More complex features
        self.cycles         = self._get_cycles()
        self.avg_in_degree  = self._get_avg_in_degree()
        self.avg_out_degree = self._get_avg_out_degree()
        self.in_centrality  = self._get_in_centrality()
        self.out_centrality = self._get_out_centrality()
        self.closeness_cent = self._get_closeness_centrality()
        self.leaf_count     = self._get_end_articles()
        self.extract_features()

        self.qutoes_count = 0        
        

    def _count_all_relations(self):
        return self.wdf_relations_count + self.wat_relations_count 

    def _count_all_nodes(self):
        return self.entities_count + self.agents_count + 1
    
    def _get_density(self):
        return self.total_edges_count / (self.total_vertices_count * (self.total_vertices_count - 1))

    def _get_cycles(self):
        return len(list(nx.simple_cycles(self.__G)))
    
    def _get_avg_in_degree(self):
        vertices = list(self.__G.nodes)
        leng     = len(vertices)
        sum_deg  = 0
        for vertex in vertices:
            sum_deg += self.__G.in_degree(vertex)
        return sum_deg / leng

    def _get_avg_out_degree(self):
        vertices = list(self.__G.nodes)
        leng     = len(vertices)
        sum_deg  = 0
        for vertex in vertices:
            sum_deg += self.__G.out_degree(vertex)
        return sum_deg / leng

    def _get_in_centrality(self):
        return nx.in_degree_centrality(self.__G)
    
    def _get_out_centrality(self):
        return nx.out_degree_centrality(self.__G)
        
    def _get_closeness_centrality(self):
        return nx.closeness_centrality(self.__G)

    def _get_end_articles(self):
        out_vertices = nx.out_degree_centrality(self.__G)
        zero_out_deg_vertices = [vtx for vtx, deg in out_vertices.items() if deg == 0]
        # TODO need to get rid of leaf nodes

    def extract_features(self):
        self._get_counts()

    # TODO number of dead ends that are not leaves
    # Get all nodes that have 0 out degree
    # Except for the leave nodes with the max depth, return the number of nodes

    # TODO number of articles that are from root's publisher

    # TODO in_centralized authors

    # TODO number of broccoli

    # TODO word count

    def _get_entities_dict(self):
        res = {}
        for entity in self.__entities:
            for key, val in entity.items():
                if key == 'test:type':
                    res[val] = 1 + res[val] if val in res else 1
        return res

    def _get_agents_dict(self):
        res = {}
        for agent in self.__agents:
            for key, val in agent.items():
                if key == 'test:type':
                    res[val] = 1 + res[val] if val in res else 1        
        return res

    def _get_relations(self):
        wdf = [tuple(reversed(list(rel.values()))) for rel in self.__wdf_relations]
        wat = [tuple(list(rel.values()))           for rel in self.__wat_relations]
        return wdf + wat

    def _get_nodes(self):
        # TODO Do we really need this?? Maybe it would be beneficial to label all nodes.
        res = []
        # self.__entities
        # self.__agents
        return res
    
    def _construct_graph(self):
        G = nx.DiGraph()
        G.add_edges_from(self.__all_relations)
        return G        

    def _get_counts(self):
        # art_refs is a list of all articles and references
        arts_refs = [list(relation.values()) for relation in self.__wdf_relations]
        arts_refs = [num for lst in arts_refs for num in lst]
        # Remove duplicates
        arts_refs = set(arts_refs)
        arts_refs_count = len(arts_refs)
        print("Done")

        


def main():
    arg_parser = argparse.ArgumentParser(
        description="Given a graph json file and extract all features within the graph. File path requried(-p)")
    arg_parser.add_argument('-p', '--path', dest='path',
                            help='A json file path that represents a provenance graph')

    args = arg_parser.parse_args()

    graph_file = args.path

    # with open(graph_file, 'r') as f:
    with open('fake_1_output.json', 'r') as f:
        graph_dict = json.load(f)

    feature_extractor = FeatureExtrator(graph_dict) 
    
main()


# python3 feature_extractor.py -p 'train1_output.json'