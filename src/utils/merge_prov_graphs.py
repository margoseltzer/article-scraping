import os
import json

allDirs = ['real_poli_output', 'kaggle_jsons_output']

types = ['entity', 'agent', 'activity', 'wasAttributedTo', 'wasGeneratedBy', 'wasDerivedFrom']

data = {}
data['root'] = 'All bundles'
data['bundle'] = {}

for d in allDirs:
    for root, dirs, files in os.walk(d):
        for file in files:
            with open(os.path.join(root, file)) as f:
                j = json.load(f)
                j = j['bundle']
                for t in types:
                    if t in j:
                        x = j[t]
                        if t not in data['bundle']:
                            data['bundle'][t] = j[t]
                        else:
                            for y in j[t]:
                                data['bundle'][t][y] = j[t][y]


with open('merged.json', 'w') as f:
  json.dump(data, f, indent=4, sort_keys=True, ensure_ascii=False)
print('merging completed')