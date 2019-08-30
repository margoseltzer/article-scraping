import pandas as pd
from urllib.parse import urlparse

# Path for cpl_relations csv
cpl_relations = ''

# Path for cpl_objects csv
cpl_objects = ''

# Path for cpl_object_properties csv
cpl_properties = ''

relations = pd.read_csv(cpl_relations, index_col='id')
objects = pd.read_csv(cpl_objects)
properties = pd.read_csv(cpl_properties)

# Create new dataframe with node id, value, and type
properties = properties[properties.name == 'type']
nodes = pd.merge(objects, properties, on='id')

unique = {}
def get_newValue(row):
    if row.value in ['reference','government']:
        parsed = urlparse(row.name_x)
        if parsed.netloc:
            unique[parsed.netloc] = row.id
            return parsed.netloc
        else:
            unique[row.name_x] = row.id
            return row.name_x
    else:
        unique[row.name_x] = row.id
        return row.name_x


# Get just domain names for reference and government pages
nodes['new_value'] = nodes.apply(lambda x: get_newValue(x), axis=1)
nodes.set_index('id')

# Eliminate bundle edges
relations = relations[relations.type != 20]

def get_new_target(row):
    try:
        return unique[nodes.loc[row.to_id]['new value']]
    except:
        return row.to_id

# Get new target node based on renamed reference and government pages
relations['new_target'] = relations.apply(lambda x: get_new_target(x), axis=1)
nodes = nodes[['name_x','value','new_value']]
relations = relations[['from_id','to_id','type','new_target']]

nodes.rename(columns={'name_x': 'value', 'value': 'type'}, inplace=True)
relations.rename(columns={'from_id': 'Source', 'to_id': 'old_target', 'new_target':'Target'}, inplace=True)