import json
import sys


NODE_TYPES_MAP = {
'article': 1,
'publisher': 2,
'person': 3,
'quote': 4,
'reference': 5,
'government': 6
}

id_count = 0
node_id_map = {}

target = 0
edges = []
labels = {}
inverse_labels = {
NODE_TYPES_MAP['article'] : [],
NODE_TYPES_MAP['publisher'] : [],
NODE_TYPES_MAP['person']  : [],
NODE_TYPES_MAP['quote'] : [],
NODE_TYPES_MAP['reference'] : [],
NODE_TYPES_MAP['government'] : []
}

def add_node(node_name):
	global node_id_map
	global id_count
	if node_name not in node_id_map:
		node_id_map[node_name] = id_count
		node_id = id_count
		id_count += 1
	else:
		node_id = node_id_map[node_name]
	return node_id

def transfer(article_id, node_id, node_type):
	global edges
	global labels
	global inverse_labels
	if article_id != node_id:
		edges.append([article_id, node_id])
	labels[node_id] = NODE_TYPES_MAP[node_type]
	inverse_labels[NODE_TYPES_MAP[node_type]].append(node_id)


def main():
	file_name = sys.argv[1]
	print(file_name)

	global node_id_map
	global id_count

	global target
	global edges
	global labels
	global inverse_labels

	if '_1.json' in file_name:
		target = 1

	with open(file_name) as f:
		articles_json = json.load(f)

	root_article = articles_json[0]['url']
	root_article_id = add_node(root_article)

	for article in articles_json:
		article_url = article['url']

		article_id = add_node(article_url)

		transfer(root_article_id, article_id, 'article')

		for author in article['authors']:
			author_name = author['name']

			author_id = add_node(author_name)

			transfer(article_id, author_id, 'person')

		publisher = article['publisher']
		publisher_id = add_node(publisher)

		transfer(article_id, publisher_id, 'publisher')

		for quote in article['quotes']:
			quote_s = quote[0]
			quote_p = quote[1]

			quote_s_id = add_node(quote_s)
			quote_p_id = add_node(quote_p)

			transfer(article_id, quote_s_id, 'quote')
			transfer(quote_s_id, quote_p_id, 'person')

		links = article['links']

		for article_link in links['articles']:
			article_link_id = add_node(article_link)
			transfer(article_id, article_link_id, 'article')

		for gov_link in links['gov_pgs']:
			gov_link_id = add_node(gov_link)
			transfer(article_id, gov_link_id, 'government')

		for reference in links['unsure']:
			reference_id = add_node(reference)
			transfer(article_id, reference_id, 'reference')

	empty_k = []
	for k in inverse_labels:
		if not inverse_labels[k]:
			empty_k.append(k)
	for k in empty_k:
		del inverse_labels[k]

	output_json = {
	'target' : target,
	'edges' : edges,
	'labels' : labels,
	'inverse_labels': inverse_labels
	}

	output = file_name.replace('.json', '_output.json')

	with open(output, 'w') as f:
		json.dump(output_json, f)

	print('finish')

main()