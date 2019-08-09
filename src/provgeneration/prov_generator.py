import codecs
import argparse
import json
import os
import CPL
from CPL import ENTITY, AGENT, WASATTRIBUTEDTO, WASGENERATEDBY, WASDERIVEDFROM, BUNDLERELATION
from google_quote import get_full_quote
import string

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
        article_object = db_connection.lookup_by_string_property(originator, 'url', article_url)[0]
    except Exception as e:
        print(str(e.message))
        article_object = db_connection.create_object(originator, short_aricle_url, ENTITY)
    article_object.add_string_property(originator, 'type', 'article')
    article_object.add_string_property(originator, 'url', article_url)
    article_object.add_string_property(originator, 'title', article_title)

    # add date, text to article_object property
    article_object.add_string_property(originator, 'date', article_publish_date)

    try:
        publisher_object = db_connection.lookup_by_string_property(originator, 'publisher', article_publisher)[0]
    except Exception as e:
        publisher_object = db_connection.create_object(originator, article_publisher, AGENT)
        publisher_object.add_string_property(originator, 'publisher', article_publisher)
        publisher_object.add_string_property(originator, 'type', 'publisher')
    
    # add relation between publisher and article
    try:
        article_publiser_relation = article_object.lookup_to_relation(publisher_object, WASATTRIBUTEDTO)
    except Exception as e:
        article_publiser_relation = article_object.relation_to(publisher_object, WASATTRIBUTEDTO)

    # include article and publisher relation in bundle
    bundle.relation_to(article_publiser_relation, BUNDLERELATION)


    # add author object
    for author in article_authors:
        author_name = author['name'].encode('utf-8')
        try:
           author_object = db_connection.lookup_by_string_property(originator, 'name', author_name)[0]
        except Exception as e:
            author_object = db_connection.create_object(originator, author_name, AGENT)
            author_object.add_string_property(originator, 'name', author_name)
            author_object.add_string_property(originator, 'type', 'person')
    
        # add relation between author and article
        try:
            article_author_relation = article_object.lookup_to_relation(author_object, WASATTRIBUTEDTO)
        except Exception as e:
            article_author_relation = article_object.relation_to(author_object, WASATTRIBUTEDTO)

        # include article and author relation in bundle
        bundle.relation_to(article_author_relation, BUNDLERELATION)

    # Add the quotes
    for quote in article_quotes:
        quote_str = convert_quote_str(quote[0])
        quote_object = None

        # If the quote is not a full sentence, check if the full quote is already in the database.
        # If it is not already in the database, search google for the full quote
        if not quote[2]:
            try:
                quote_object = db_connection.lookup_object_property_wildcard('%' + quote_str + '%')
                add_quote_relation(article_object, quote_object, bundle)
            except Exception as e:
                try:
                    quote_str = get_full_quote(quote[0])
                    if quote_str:
                        quote_object = add_quote(article_object, convert_quote_str(quote_str), bundle)
                except Exception as e:
                    pass
        else:
             quote_object = add_quote(article_object, quote_str, bundle)

        if quote_object and quote[1]:
            speaker_string = quote[1].encode('utf-8')
            try:
                speaker_object = db_connection.lookup_by_string_property(originator, 'name', speaker_string)[0]
            except Exception as e:
                speaker_object = db_connection.create_object(originator, speaker_string, AGENT)
                speaker_object.add_string_property(originator, 'name', speaker_string)
                speaker_object.add_string_property(originator, 'type', 'person')

            try:
                quote_speaker_relation = quote_object.lookup_to_relation(speaker_object, WASATTRIBUTEDTO)
            except Exception as e:
                quote_speaker_relation = quote_object.relation_to(speaker_object, WASATTRIBUTEDTO)

            # include quote and speaker relation in bundle
            bundle.relation_to(quote_speaker_relation, BUNDLERELATION)

    return article_object


def convert_quote_str(quote_str):
    return quote_str.encode('utf-8').translate(None, string.punctuation).lower()


def add_quote(article, quote_str, bundle):
    try:
        quote_object = db_connection.lookup_by_string_property(originator, 'quote', quote_str)[0]
    except Exception as e:
        quote_object = db_connection.create_object(originator, quote_str[0:255], CPL.ACTIVITY)
        quote_object.add_string_property(originator, 'quote', quote_str)
        quote_object.add_string_property(originator, 'type', 'quote')
    add_quote_relation(article, quote_object, bundle)
    return quote_object


def add_quote_relation(article, quote_object, bundle):
    try:
        article_quote_relation = article.lookup_to_relation(quote_object, WASGENERATEDBY)
    except Exception as e:
        article_quote_relation = article.relation_to( quote_object, WASGENERATEDBY)
    bundle.relation_to(article_quote_relation, BUNDLERELATION)

def add_reference_relation(article, articles_object_map, bundle):
    def add_relation(url, url_type, articles_object_map, article_object, bundle):
        url_str = url.encode('utf-8')
        short_url_str = url_str[:250] if len(url_str) > 250 else url_str
        try:
            reference_object = articles_object_map[url]  
        except Exception as e:
            try:
                reference_object = db_connection.lookup_by_string_property(originator, 'url', url_str)[0]
            except Exception as e:
                reference_object = db_connection.create_object(originator, short_url_str, ENTITY)
            reference_object.add_string_property(originator, 'url', url_str)
            reference_object.add_string_property(originator, 'type', url_type)
        try:
            reference_relation = article_object.lookup_to_relation(reference_object, WASDERIVEDFROM)
        except Exception as e:
            reference_relation = article_object.relation_to(reference_object, WASDERIVEDFROM)

        bundle.relation_to(reference_relation, BUNDLERELATION)

    article_url = article['url']
    article_links = article['links']['articles']
    article_unsure_links = article['links']['unsure']
    article_gov_links = article['links']['gov_pgs']
    article_object = articles_object_map[article_url]
    for url in article_links:
        add_relation(url, 'article', articles_object_map, article_object, bundle)
    
    for url in article_unsure_links:
        add_relation(url, 'reference', articles_object_map, article_object, bundle)

    for url in article_gov_links:
        add_relation(url, 'government', articles_object_map, article_object, bundle)

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
        add_reference_relation(article, articles_object_map, bundle)
    
    return bundle

def write_output(output_file_name, bundles, root_url=None):
    try:
        bundle_json = json.loads(db_connection.export_bundle_json(bundles))
        output_json = {
            'root': root_url,
            'bundle': bundle_json }
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
        
    root_url = articles_json[0]['url']
    bundle = add_bundle(articles_json)
    print('finished process ' + file_name)

    # write to output
    output_file_name = file_name[:-5] + '_output.json' if not output_file else output_file
    write_output(output_file_name, [bundle], root_url)
    
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
