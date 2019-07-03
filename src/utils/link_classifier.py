from bs4 import BeautifulSoup


class LinkClassifier(object):
    '''
    Link categorizer using an API
    '''

    def __init__(self, links):
        self.links = links
        self.dict = {}
        pass
    """
    The data structure: an object with {news: [Set], sports: [Set]}

    """

    def categorize_links(self, links):
        dict_url_to_categories = {
            link: self._get_categories(link) for link in links}
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
        return self._restructure_dict(dict_url_to_categories)

    def _get_categories(self, link):
        """
        :param link: a link that we want to get categories
        :type a: string
        :return: a single dict that map link to corresponding categories
        :rtype:
        """
        # url = urllib.request.urlopen(
        #     "https://website-categorization-api.whoisxmlapi.com/api/v1?apiKey=at_3GEU4QdYSt8blznjIYKrgId9Y33wR&domainName=" + link)
        # categories = json.loads(url.read().decode()).categories
        categories = ['Reference', 'News and Media']
        return categories

    def _restructure_dict(self, dict_url_to_catgs):
        """
        This method will convert dict_url_to_catgs to dict_catg_to_urls
        :param dict_url_to_catgs: a dictionary that finds categorries of an url, url => catgs
        :return: a dict that find article urls and non-article urls
        :rtype: a dict from string to list of string
        """
        category_dict = {'article': [], 'non-article': []}
        for url, catgs in dict_url_to_catgs.items():
            if 'News and Media' in catgs:
                category_dict['article'].append(url)
            else:
                category_dict['non-article'].append(url)

        self.dict = category_dict
        return category_dict
