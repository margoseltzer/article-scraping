import json

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


with open('train1_output.json', 'r') as f:
    data = json.load(f)

numbers = data['bundle']['wasDerivedFrom'].keys()

vals = data['bundle']['wasDerivedFrom'].values()
# vals = [a_row.values() for a_row in vals]

# print(list(numbers))
# print(list(vals))
print(set(vals))
print(set(([1,1,2,3])))