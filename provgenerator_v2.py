import codecs
import argparse
import json
import os
import sys
import CPL
from CPL import ENTITY, ACTIVITY, AGENT, WASATTRIBUTEDTO, WASGENERATEDBY, WASDERIVEDFROM, BUNDLE_RELATION

# Global Varialbes
originator = 'test'
db_connection = CPL.cpl_connection()

def add_article(article, bundle):
    article_url = article['url'].encode('utf-8')
    article_title = article['title'].encode('utf-8')
    article_authors = article['authors']
    article_publisher = article['publisher'].encode('utf-8')
    article_publish_date = article['publish_date'].encode('utf-8')
    article_quotes = article['quotes']

    # add article object
    short_aricle_url = article_url[:250] if len(article_url) > 250 else article_url
    try:
        article_object = db_connection.lookup_by_property(originator, 'url', article_url)[0]
    except Exception as e:
        print(str(e.message))
        article_object = db_connection.create_object(originator, short_aricle_url, ENTITY, bundle)
    article_object.add_property(originator, 'type', 'article')
    article_object.add_property(originator, 'url', article_url)
    article_object.add_property(originator, 'title', article_title)

    # add date, text to article_object property
    article_object.add_property(originator, 'date', article_publish_date)

    try:
        publisher_object = db_connection.lookup_by_property(originator, 'publisher', article_publisher)[0]
    except Exception as e:
        publisher_object = db_connection.create_object(originator, article_publisher, AGENT, bundle)
        publisher_object.add_property(originator, 'publisher', article_publisher)
        publisher_object.add_property(originator, 'type', 'publisher')
    
    # add relation between publisher and article
    try:
        article_publiser_relation = db_connection.lookup_relation(article_object.id, publisher_object.id, WASATTRIBUTEDTO)
    except Exception as e:
        article_publiser_relation = db_connection.create_relation(article_object.id, publisher_object.id, WASATTRIBUTEDTO)

    # include article and publisher relation in bundle
    db_connection.create_relation(bundle.id, article_publiser_relation.id, BUNDLE_RELATION)


    # add author object
    for author in article_authors:
        author_name = author['name'].encode('utf-8')
        try:
           author_object = db_connection.lookup_by_property(originator, 'name', author_name)[0]
        except Exception as e:
            author_object = db_connection.create_object(originator, author_name, AGENT, bundle)
            author_object.add_property(originator, 'name', author_name)
            author_object.add_property(originator, 'type', 'person')
    
        # add relation between author and article
        try:
            article_author_relation = db_connection.lookup_relation(article_object.id, author_object.id, WASATTRIBUTEDTO)
        except Exception as e:
            article_author_relation = db_connection.create_relation(article_object.id, author_object.id, WASATTRIBUTEDTO)

        # include article and author relation in bundle
        db_connection.create_relation(bundle.id, article_author_relation.id, BUNDLE_RELATION)

    # add quotes object
    # TODO: add quotes

    return article_object

def add_relation_between_article(article, articles_object_map, bundle):
    article_url = article['url']
    article_links = article['links']
    article_object = articles_object_map[article_url]
    for url in article_links:
        url_str = url.encode('utf-8')
        short_url_str = url_str[:250] if len(url_str) > 250 else url_str
        try:
            reference_object = articles_object_map[url]  
        except Exception as e:
            try:
                reference_object = db_connection.lookup_by_property(originator, 'url', url_str)[0]
            except Exception as e:
                reference_object = db_connection.create_object(originator, short_url_str, ENTITY, bundle)
            reference_object.add_property(originator, 'url', url_str)
            reference_object.add_property(originator, 'type', 'article')
        
        try:
            reference_relation = db_connection.lookup_relation(article_object.id, reference_object.id, WASDERIVEDFROM)
        except Exception as e:
            reference_relation = db_connection.create_relation(article_object.id, reference_object.id, WASDERIVEDFROM)

        db_connection.create_relation(bundle.id, reference_relation.id, BUNDLE_RELATION)

def add_bundle(articles_json):
    root_article  = articles_json[0]
    bundle_name = root_article['url'].encode('utf-8')
    try:
        print("try to find bundle %s" % (bundle_name))
        bundle = db_connection.lookup_bundle(bundle_name, originator)
    except Exception as e:
        print("bundle not exsist create new one")
        bundle = db_connection.create_bundle(bundle_name, originator)

    articles_object_map = {}

    for article in articles_json:
        articles_object_map[article['url']] = add_article(article, bundle)

    for article in articles_json:
        add_relation_between_article(article, articles_object_map, bundle)
    
    return bundle

def write_output(output_file_name, bundles):
    try:
        output_json = json.loads(db_connection.export_bundle_json(bundles))
        with codecs.open(output_file_name, 'w', encoding='utf-8') as f:
            json.dump(output_json, f, ensure_ascii=False, indent=4, encoding='utf-8')
        print('wrote output to ' + output_file_name)
    except Exception as e:
        print(e)

def process_file(file_name, output_file = None):
    '''
    process json file, write output to file_name_output.json, return bundle object
    '''
    print('start processing ' + file_name)
    with open(file_name) as f:
        articles_json = json.load(f)
        
    bundle = add_bundle(articles_json)
    print('finished process ' + file_name)

    # write to ouput
    output_file_name = file_name[:-5] + '_output.json' if not output_file else output_file
    write_output(output_file_name, [bundle])
    
    return bundle

def process_directory(directory_name):
    '''
    process all json file in dirctory, write output to dirctory_name_output/file_name_output.json,
    return list of bundle objects
    '''
    def build_output_directory(directory_path):
        return directory_path[:-1] + '_output' if directory_path.endswith('/') else directory_path + '_output'

    # build output directory
    for r, d, f in os.walk(directory_name):
        output_directory = build_output_directory(r)
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

    input_output_list = [(os.path.join(r, file), os.path.join(build_output_directory(r), file[:-5] + '_output.json')) 
        for r, d, f in os.walk(directory_name) for file in f if '.json' in file]
    return [process_file(i, o) for i, o in input_output_list]

def main():
    global originator
    parser = argparse.ArgumentParser(
        description='store all provenance in file to database, and output new file for graph analysis')
    parser.add_argument('-f', '--file', dest='file_name', 
                        help='name of file need to be process, result stored in file_name_output.json')
    parser.add_argument('-d', '--directory', dest='directory_name', 
                        help='name of directory need to be process, result stored in directory_name_output directory')
    parser.add_argument('-o', '--originator', type=str, dest='originator', default='test',
                        help='the originator name, default is test')
    parser.add_argument('-a', '--all', dest='all', action='store_true',
                        help='output all bundles processed by this time in output.json')

    args = parser.parse_args()

    if args.originator:
        originator = args.originator

    # if no both file or directory, terminamte
    if not args.file_name and not args.directory_name:
        print("you must provide at least one of file name or directory name")
    
    bundles = []
    if args.file_name:
        bundles.append(process_file(args.file_name))

    if args.directory_name:
        bundles += process_directory(args.directory_name)

    if args.all:
        #show all bundles in database
        print("output all the bundles processed by this time")
        write_output('output.json', bundles)

    print("finished process all files")

main()
db_connection.close()
