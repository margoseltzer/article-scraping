from bs4 import BeautifulSoup
from urllib.request import urlopen, Request


class LinkClassifier(object):
    '''
    !!! DOES NOT WORK BECAUSE THE API IS NOT ACCURATE AND DENIES MANY REQUESTS 
    Call categorize_links will return restructured dictionary
    '''

    def __init__(self, links):
        self.links = links
        self.dict = {}

    def categorize_links(self):
        dict_url_to_categories = {link: self._get_categories(link) for link in self.links}

        return self._restructure_dict(dict_url_to_categories)

    def _get_categories(self, link):
        '''
        :param link: a link that we want to get categories
        :type a: string
        :return: a single category that map link to corresponding category
        '''
        # url = urllib.request.urlopen(
        #     "https://website-categorization-api.whoisxmlapi.com/api/v1?apiKey=at_3GEU4QdYSt8blznjIYKrgId9Y33wR&domainName=" + link)
        # categories = json.loads(url.read().decode()).categories
        # eg. categories = ['Reference', 'News and Media']
        url = 'https://fortiguard.com/webfilter?q=' + link
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3723.0 Safari/537.36'}
        req = Request(url=url, headers=headers)

        page = urlopen(req)
        soup = BeautifulSoup(page, 'html.parser')
        meta_tags = soup.find_all('meta')
        
        for tag in meta_tags:
            attrs = tag.attrs
            if 'content' in attrs and attrs['content'].find('Category') > -1:
                start = attrs['content'].find('y: ') + 3
                category = attrs['content'][start:]
                break
        return category

    def _restructure_dict(self, dict_url_to_catgs):
        '''
        This method will convert dict_url_to_catgs to dict_catg_to_urls
        :param dict_url_to_catgs: a dictionary that finds categorries of an url, url => catgs
        :return: a dict that find article urls and non-article urls
        '''
        category_dict = {'government': [], 'non-gov': []}
        for url, catgs in dict_url_to_catgs.items():
            # 'News and Media' for news
            if 'Government and Legal Organizations' in catgs:
                category_dict['government'].append(url)
            else:
                category_dict['non-gov'].append(url)

        self.dict = category_dict
        return category_dict

''' 
Test set: in order to test, uncomment the below two lines and run debuger on the current file.
'''
        # dict_url_to_categories = {
        #     'https://money.cnn.com/2018/09/22/technology/alexa-everywhere/index.html': ['Reference', 'News and Media'],
        #     'https://invokedapps.com/sleepsounds': ['Health', 'People and Society', 'Arts and Entertainment'],
        #     'https://developer.amazon.com/alexa-skills-kit/rewards': ['Internet and Telecom', 'Computer and electronics'],
        #     'https://developer.amazon.com/blogs/post/Tx205N9U1UD338H/Introducing-the-Alexa-Skills-Kit-Enabling-Developers-to-Create-Entirely-New-Voic': ['Internet and Telecom', 'Computer and electronics'],
        #     'https://www.cnn.com/20s18/09/28/tech/amazon-echo-event/index.html': ['People and Society', 'Reference', 'News and Media'],
        #     'https://money.cnn.com/quote/quote.html?symb=AMZN&source=story_quote_link': ['Reference', 'News and Media'],
        #     'https://money.cnn.com/2018/04/21/technology/alexa-blueprints/index.html': ['Reference', 'News and Media'],
        #     'https://blueprints.amazon.com/share?policy=eyJza2lsbElkIjoiYW16bjEuYXNrLnNraWxsLjQ1YjhkZDYzLWEwZWEtNDBkNy05OWIyLWU1OGU3NTUyODc4MCIsInBvbGljeUlkIjoiMmU5ZDhiYzAtNmZhZi00NzBmLWJkZGItMTEwOTZlYTg1ZmYzIiwiZXhwaXJhdGlvblRpbWUiOiIyMDIwLTAzLTA4VDE3OjU2OjUxLjU0MVoifQ&signature=qgRacLGFoHLAr8U1V3A6GH4VO68UTvwYOnp6VhokBGg%3D': ['Internet and Telecom', 'Health', 'Pets and Animals'],
        #     'https://www.amazon.com/Easy-Meditation-guided-Madeleine-Shaw/dp/B077M72Y8S/ref=sr_1_43?qid=1555971730&s=alexa-skills&sr=1-43': ['Internet and Telecom', 'Health', 'Pets and Animals'],
        #     'https://money.cnn.com/2018/05/10/news/companies/alexa-amazon-smart-speakers-voice-shopping/index.html': ['Reference', 'News and Media']
        # }
# urls = ['https://www.nytimes.com/by/jonathan-martin', 'https://www.rcaanc-cirnac.gc.ca/eng/1559226684295/1559226709198']
# urls2 = [
#             'https://money.cnn.com/2018/09/22/technology/alexa-everywhere/index.html', 
#             'https://invokedapps.com/sleepsounds',
#             'https://developer.amazon.com/alexa-skills-kit/rewards',
#             'https://developer.amazon.com/blogs/post/Tx205N9U1UD338H/Introducing-the-Alexa-Skills-Kit-Enabling-Developers-to-Create-Entirely-New-Voic',
#             'https://www.cnn.com/2018/09/28/tech/amazon-echo-event/index.html',
#             'https://money.cnn.com/quote/quote.html?symb=AMZN&source=story_quote_link',
#             'https://money.cnn.com/2018/04/21/technology/alexa-blueprints/index.html',
#             'https://blueprints.amazon.com/share?policy=eyJza2lsbElkIjoiYW16bjEuYXNrLnNraWxsLjQ1YjhkZDYzLWEwZWEtNDBkNy05OWIyLWU1OGU3NTUyODc4MCIsInBvbGljeUlkIjoiMmU5ZDhiYzAtNmZhZi00NzBmLWJkZGItMTEwOTZlYTg1ZmYzIiwiZXhwaXJhdGlvblRpbWUiOiIyMDIwLTAzLTA4VDE3OjU2OjUxLjU0MVoifQ&signature=qgRacLGFoHLAr8U1V3A6GH4VO68UTvwYOnp6VhokBGg%3D',
#             'https://www.amazon.com/Easy-Meditation-guided-Madeleine-Shaw/dp/B077M72Y8S/ref=sr_1_43?qid=1555971730&s=alexa-skills&sr=1-43',
#             'https://money.cnn.com/2018/05/10/news/companies/alexa-amazon-smart-speakers-voice-shopping/index.html'
#         ]
# link_classifier = LinkClassifier(urls)
# link_classifier.categorize_links()
# print(link_classifier.dict)