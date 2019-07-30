import argparse
import csv
import hashlib
import subprocess
import json
import os
import re
import nltk
from bs4 import BeautifulSoup
from threading import Timer
from urllib.parse import urlparse

print('there')
parser_result = subprocess.run(["mercury-parser", 'https://www.nytimes.com/2019/07/22/us/politics/budget-deal.html?action=click&module=Top%20Stories&pgtype=Homepage'], stdout=subprocess.PIPE)
result_json = json.loads(parser_result.stdout)
print()