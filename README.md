# Provenance Graphs for News Articles

## Table of Contents 
1. Introduction<br/>
2. Installation <br/>
3. Database Schema <br/>
4. How to Run <br/>
5. Summary: Files <br/>
6. Summary: How to Run <br/>
7. Vaccine Case Study<br/>

## Introduction
The original code was written by Ying-Ke Chin-Lee in 2017.
Jeanette worked on forks of this repo and https://github.com/jeanettejohnson/prov-cpl during a directed studies at UBC in Winter 2019.  
For more information on the concept of data provenance, check out [A Primer on Provenance](https://dl.acm.org/citation.cfm?id=2602651). The purpose of this module is to extract provenance from online news articles and to store and visualize it in a meaningful way. It attempts this by taking an article and generating a graph or matrix representing a collection of the authors, quotes, and linked articles related to the base article mapping the relationships between them. The ultimate goal is to address the question of whether provenance can be used to distinguish "Fake News" from real news. 

## Installation
In order to run the end-to-end pipeline to generate a provenance graph for an article, there are a few dependencies that need to be installed first. Here is a step-by-step guide to installing everything you'll need to run this project.

1. Clone this repository: `git clone https://github.com/margoseltzer/article-scraping.git`

2. Open in your text editor or IDE and begin to resolve dependencies in `src/scraper.py`,`graphing/graph_builder.py` and `graphing/interactive_graph.py`. **Do not attempt to resolve `provgenerator.py` dependencies yet**. You will need to install quite a few packages, including but not necessarily limited to:
	* ``src/scraper.py`` requires a stanford_NLP library. This can be downloaded from https://stanfordnlp.github.io/CoreNLP/download.html  
	    * In ``src/scraper.py``, modify the ``stanfordLibrary`` variable definition so that it points towards your downloaded library
	
3. Download and install the Prov-CPL library and Python bindings, as well as their dependencies. My fork of library and the original installation instructions can be found here: https://github.com/jeanettejohnson/prov-cpl
	#### A few slight changes to the installation process
	* When configuring the database, run the command `sudo psql -U postgres postgres < scripts/postgresql-setup-article-prov.sql` rather than the default option. The database schema is slightly different for this project than is assumed by the original.
	* If you are having linking issues during compilation (and you are on unix), run `set LD_LIBRARY_PATH="/usr/local/lib"`. If this does not work, try setting it [like this](https://stackoverflow.com/questions/13428910/how-to-set-the-environmental-variable-ld-library-path-in-linux)
	
4. Start the PostgreSQL server you installed in step 3: `sudo /etc/init.d/postgresql start`. Verify that it says [OK] and accepts connections on port 5432 (or whichever port you configured it to listen on). 

5. (Optional) Download and install a PostgreSQL Database Visualizer. I like pgAdmin: https://www.pgadmin.org/. Connect to the running DB with username postgres and verify that the DB has been set up correctly and you can navigate between tables. There won't be anything there yet as you are running it locally.

6. `src/provgeneration/prov_generator.py` needs to be run using python 2, while the rest of the project depends on python 3/Anaconda. This is because provgenerator is the file with dependencies to prov-cpl, and the cpl python bindings strictly support 2.7. You will need to figure out a way to switch easily between the two Python builds. You can do this via command line with the python command linking to python 2.7 and the python3 command linking to python 3.7. My solution to this was to use PyCharm with WSL support, and run python 2 in a WSL interpreter and python 3 in the command line. This is definitely *not* the best approach and I don't recommend it, but it's a slightly easier way to get the CPL bindings to work.

## Database Schema
You will notice that cpl_bundles has no direct relationship to `cpl_objects`. In previous prov-cpl versions, each object belonged to a bundle. However, for this specific application where a "bundle" is an article and an "object" can be an author, quote, or link to another article, it did not make sense for objects to uniquely belong to one bundle (e.g. if Alice authored two InfoWars articles, there should be one "author: Alice" object in the database that belongs to the bundles "infowars article 1" and "infowars article 2"). To deal with this, bundles have become a special type of object and the relationship from bundle to objects is stored in the `cpl_relations` table. 
![CPL PostgreSQL Schema](screenshots/cplschema.png)

## How to Run
Here is a walk through of how to generate a prov graph, using [this InfoWars anti-vaccine article](https://www.infowars.com/mmr-vaccine-after-puberty-reduces-testosterone-sperm-counts-report/). A short summary of the relevant commands and files can be found below this section.
First, run the web scraper module to look at the article HTML and pull out relevant items such as authors, quotes, and links to other articles.  
The scraper takes in various arguments:  
 ``-u`` to specify a single url  
 ``-f`` to pass in a file containing a list of urls. The file should be a csv with format ???  
 ``-d`` to specify the depth to scrape to (referenced articles are scraped recursively). This defaults to depth 2.  
 ``-o`` to specify the output file  
 **TODO: specify csv file format**
```
python3 src/scraper.py -u https://www.infowars.com/mmr-vaccine-after-puberty-reduces-testosterone-sperm-counts-report/ -o fileName.json
```

The information will be written in JSON format to the output file, and will have the following fields:
```json
[
    {
        "url": "",
        "title": "",
        "authors": [],
        "publisher": "",
        "publish_date": "",
        "text": "",
        "quotes": [],
        "links": {
            "articles": [],
            "unsure": []
        },
        "key_words": []
    }
]
```
Next, run the provenance generator using python 2.7. 
The prov_generator script takes in various arguments:  
 ``-f`` to specify the name of file to process. The result is stored in result stored in file_name_output.json.  
 ``-d`` process all files in a directory, the result is stored in a directory called directory_name_output.   
 ``-o`` to specify the originator. This defaults to ``test``  
 ``-a`` ???  
 **TODO: describe -a**
 
 ```
python src/provgeneration/prov_generator.py -f fileName.json
``` 
This module uses the prov-cpl library to create provenance entities and map relationships between them.
The information written to the output file follows the Prov-JSON syntax, documentation for which can be found here: https://www.w3.org/Submission/2013/SUBM-prov-json-20130424/. 
The output file will have a list of provenance objects followed by an enumeration of the relationships between them, and will look something like this:

```json
"{\"activity\":
	{\"demo:QUOTE 0\":
		{\"demo:quote\":\"\\\"Well, I\\\\'ll tell you, I pray that it doesn\\\\'t get to that. I pray it doesn\\\\'t get to that.\\\"\"}},
\"agent\":
	{\"demo:AUTHOR 0\":
		{\"demo:author\":\"Children's Health Defense\"}
\"entity\":
	{\"demo:ARTICLE 0\":
		{\"demo:url\":\"https://www.infowars.com/mmr-vaccine-after-puberty-reduces-testosterone-sperm-counts-report/\"},
	\"demo:ARTICLE 1\":
		{\"demo:url\":\"http://www.infowars.com/watch/?video=5c2fe1fbf6d3eb27147154a5\"}
\"inBundle\":
	{\"78758\":
		{\"prov:bundle\":\"https://www.infowars.com/mmr-vaccine-after-puberty-reduces-testosterone-sperm-counts-report/\",
		 \"prov:object\":\"demo:ARTICLE 0\"},
	\"78760\":
		{\"prov:bundle\":\"https://www.infowars.com/mmr-vaccine-after-puberty-reduces-testosterone-sperm-counts-report/\",
		\"prov:object\":\"demo:AUTHOR 0\"},
	\"78764\":
		{\"prov:bundle\":\"https://www.infowars.com/mmr-vaccine-after-puberty-reduces-testosterone-sperm-counts-report/\",
		\"prov:object\":\"demo:ARTICLE 1\"},
	\"78770\":
		{\"prov:bundle\":\"https://www.infowars.com/mmr-vaccine-after-puberty-reduces-testosterone-sperm-counts-report/\",
		\"prov:object\":\"demo:QUOTE 0\"},
\"wasAttributedTo\":
	{\"78762\":
		{\"prov:agent\":\"demo:AUTHOR 0\",
		\"prov:entity\":\"demo:ARTICLE 0\"}},
\"wasDerivedFrom\":
	{\"78834\":
		{\"prov:generatedEntity\":\"demo:ARTICLE 0\",
		\"prov:usedEntity\":\"demo:ARTICLE 1\"}},
\"wasGeneratedBy\":{
	\"78772\":
		{\"prov:activity\":\"demo:QUOTE 0\",
		\"prov:entity\":\"demo:ARTICLE 1\"}}}"
```

**TODO: add instructions for the interactive graph**  
Finally, visualize the graph: **`python graphbuilder.py`**
The graph builder will read the prov-JSON from `output.json` and display an undirected network graph where nodes represent quotes, articles, and authors and edges between them represent provenance relationships. Here is the graph for the infowars vaccine article:


**TODO: update the key**  
**Key:**
- blue: quote
- green: author
- red: article
- purple: sentiment

**TODO: update the screenshots**
![InfoWars Vaccine Graph](screenshots/demograph.png)

The graphbuilder can also generate NumPy matrices. Here is the matrix representation of this article:
![InfoWars Vaccine Matrix](screenshots/demomatrix.png)

## Summary: File list
* ```src/scraper.py```
  * program that does the scraping
  * uses Python 3
* ```src/provgeneration/prov_generator.py```
  * since cpl-prov uses Python 2, uses python 2 as well
* **TODO: add the graphing files**
