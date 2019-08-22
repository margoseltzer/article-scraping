# GAM
This folder provides the data which can be applied on [this GAM model implementation](https://github.com/benedekrozemberczki/GAM)

## Model

### Graph Attention Model (GAM)

This is an RNN model proposed in paper [Graph Classification using Structural Attention. John Boaz Lee, Ryan Rossi, and Xiangnan Kong KDD, 2018](http://ryanrossi.com/pubs/KDD18-graph-attention-model.pdf)

#### ABSTRACT
Graph classification is a problem with practical applications in many different domains. To solve this problem, one usually calculates certain graph statistics (i.e., graph features) that help discriminate between graphs of different classes. When calculating such features, most existing approaches process the entire graph. In a graphlet-based approach, for instance, the entire graph is processed to get the total count of different graphlets or subgraphs. In many real-world applications, however, graphs can be noisy with discriminative patterns confined to certain regions in the graph only. In this work, we study the problem of attention-based graph classification . The use of attention allows us to focus on small but informative parts of the graph, avoiding noise in the rest of the graph. We present a novel RNN model, called the Graph Attention Model (GAM), that processes only a portion of the graph by adaptively selecting a sequence of “informative” nodes. Experimental results on multiple real-world datasets show that the proposed method is competitive against various well-known methods in graph classification even though our method is limited to only a portion of the graph.

### Data structure

This implementation takes json file and follow data structure as graph representation.

For example these JSON files have the following key-value structure:

```javascript
{"target": 1,
 "edges": [[0, 1], [0, 4], [1, 3], [1, 4], [2, 3], [2, 4], [3, 4]],
 "labels": {"0": 2, "1": 3, "2": 2, "3": 3, "4": 4},
 "inverse_labels": {"2": [0, 2], "3": [1, 3], "4": [4]}}
```
The **target key** has an integer value, which is the ID of the target class (e.g. Carcinogenicity). The **edges key** has an edge list value for the graph of interest. The **labels key** has a dictonary value for each node, these labels are stored as key-value pairs (e.g. node - atom pair). The **inverse_labels key** has a key for each node label and the values are lists containing the nodes that have a specific node label.

## File

### Parser.py

A small parser takes output from scraper.py and coverts it to the proper json file which could be used for GAM model.

### Data

This folder contains all data from `scraped_data/data_d0`, and using parser.py convert to proper format. File name end with 0 means data comes from fake news, 1 means comes from real news.

#### Node type:
``` json
article: 1,
publisher: 2,
person: 3,
quote: 4,
reference: 5,
government: 6
```

## Steps

Fisrt build training and test dataset, using 80% fake and real news data to build training dataset, rest would be test dataset.

After setup GAM moldel, use command
```
python src/main.py --train-graph-folder folder_path --test-graph-folder folder_path --prediction-path output_csv_file_path --log-path output_json_file_path
```

Using different hyper-parameters combination.

## Conclusion

The reason using this model is it would performance well even is limited to only a portion of the graph. Since the largest scrapered dataset we have is depth zero. It can be assummed that we only explore a portion of the whole provenance graph of that news.

Tried different hyper-parameters combination, the accuracy is around 72%, whcih can support the hypothesis the news provenance can used to detect fake news.