import json
import argparse

class FeatureExtrator(object):
    '''
    Initiaing an instance will extract all the features 
    '''
    def __init__ (self, graph):
        # Private variables
        self.__root = graph['root']
        self.__wdf_relations = list(graph['bundle']['wasDerivedFrom'].values())
        self.__wat_relations = list(graph['bundle']['wasAttributedTo'].values())
        self.__agents        = list(graph['bundle']['agent'].values())
        self.__entities      = list(graph['bundle']['entity'].values())

        # Extrated features

        # Simple features
        self.wdf_relations_count = len(self.__wdf_relations)
        self.wat_relations_count = len(self.__wat_relations)
        self.total_edges_count   = self._count_all_relations()
        
        self.entities_count  = len(self.__entities)
        entities_counts      = self._get_entities_counts() 
        self.article_count   = entities_counts['article']
        self.reference_count = entities_counts['reference']

        self.agents_count    = len(self.__agents)
        agents_counts        = self._get_agents_counts()
        self.person_count    = agents_counts['person']
        self.publisher_count = agents_counts['publisher']

        self.total_vertices_count = self._count_all_nodes()

        self.density = self._get_dentist()
        self.cycle_count = 0
        self.extract_features()

        self.qutoes_count = 0        
        

    def _count_all_relations(self):
        return self.wdf_relations_count + self.wat_relations_count 

    def _count_all_nodes(self):
        return self.entities_count + self.agents_count + 1
    
    def _get_dentist(self):
        return self.total_edges_count / (self.total_vertices_count * (self.total_vertices_count - 1))

    def extract_features(self):
        self._get_counts()

    def _get_entities_counts(self):
        res = {}
        for entity in self.__entities:
            for key, val in entity.items():
                if key == 'test:type':
                    res[val] = 1 + res[val] if val in res else 1
                
        return res

    def _get_agents_counts(self):
        res = {}
        for agent in self.__agents:
            for key, val in agent.items():
                if key == 'test:type':
                    res[val] = 1 + res[val] if val in res else 1
                
        return res

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
    with open('train1_output.json', 'r') as f:
        graph_dict = json.load(f)

    feature_extractor = FeatureExtrator(graph_dict) 
    
main()


# python3 feature_extractor.py -p 'train1_output.json'