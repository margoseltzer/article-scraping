import json
import argparse

class FeatureExtrator(object):
    '''
    Initiaing an instance will extract all the features 
    '''
    def __init__ (self, graph):
        self.graph = graph
        self.article_count = 0
        self.person_count = 0
        self.publisher_count = 0
        self.qutoes_count = 0
        self.reference_count = 0
        self.vertex_count = 0
        self.edges_count = 0
        self.density = 0
        self.cycle_count = 0

        self.extract_features()


    def extract_features(self):
        self._get_counts()
        self.person_count = 0
        self.publisher_count = 0
        self.qutoes_count = 0
        self.reference_count = 0
        self.vertex_count = 0
        self.edges_count = 0
        self.density = 0
        self.cycle_count = 0

    def _get_article_count():
        with open('train1_output.json', 'r') as f:
            data = json.load(f)

        numbers = data['bundle']['wasDerivedFrom'].keys()

        vals = data['bundle']['wasDerivedFrom'].values()
        vals = [list(obj.values()) for obj in vals]
        vals = [num for lst in vals for num in lst]

        # print(list(numbers))
        print(vals)
        print(len(vals))
        print(len(set(vals)))



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