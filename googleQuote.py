from bs4 import BeautifulSoup
from bs4.element import Comment
from googlesearch import search
import nltk
import re
from urllib2 import urlopen


def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True


def text_from_html(body):
    soup = BeautifulSoup(body, 'html.parser')
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)
    return u" ".join(t.strip() for t in visible_texts)


def get_full_quote(quote):
    toReturn = ""
    for j in search('"' + quote + '"', num=10, stop=10):
        print(j)
        try:
            html = urlopen(j).read()

        except Exception as e:
            print(e)
            print("Can't open URL")

        else:
            alltext = text_from_html(html)
            charmap = {0x201c: u'"',
                       0x201d: u'"',
                       0x2018: u"'",
                       0x2019: u"'"}

            alltext = alltext.translate(charmap)
            final = re.findall(r'"([^"]*)"', alltext)
            splitFinal = [nltk.tokenize.sent_tokenize(s) for s in final]

            #TODO: doing s[0] throws an exception if element of splitFinal is an empty array
            match = [s[0] for s in splitFinal if quote in s[0]]
            if match:
                if match[0].endswith(('?', '!', '.', ',')) and match[0][0].isupper():
                    toReturn = match[0]
                    break
                elif len(match[0]) > len(quote):
                    toReturn = match[0]
    return toReturn
