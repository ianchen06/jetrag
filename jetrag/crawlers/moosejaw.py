import time
import logging
import re

from bs4 import BeautifulSoup

from driver import HTTPDriver

logger = logging.getLogger(__name__)

class Moosejaw:
    def __init__(self, cfg, queue, db):
        self.cfg = cfg
        self.base_url = cfg['base_url']
        self.queue = queue
        self.db = db
        self.http = HTTPDriver()

    def __get_page(self, url):
        time.sleep(0.1)
        return self.http.session.get(url, headers=self.cfg['headers'])

    def dispatch(self):
        logger.info('disatching job')
        self.queue.put({'method': 'list_categories'})

    def list_categories(self):
        """Get list of categories from Moosejaw navigation bar

        :return: List of urls
        :rtype: list
        """
        res = self.__get_page(self.base_url)
        soup = BeautifulSoup(res.text, 'html.parser')
        navigation = [self.base_url+x for x in re.findall(r'href="(/navigation.+?)"', res.text)]
        more = [self.base_url+x['href'] for x in soup.select('#DrawerActivity a.list-menu-title')]
        result = set(navigation + more)
        for url in result:
            self.queue.put({'method': 'get_category', 'args': [url]})
        return result

    def get_category(self, url):
        """Get list of urls for all pages of the category

        :param url: url for a category
        :type url: string
        :raises Exception: Page does not have search result, maybe moosejaw side error
        :return: List of URLs of all pages of the category
        :rtype: list
        """
        res = self.__get_page(url)
        data = [url+"?orderBy=9&beginIndex=0&pageSize=48"]
        if not 'searchTotalCount' in res.text:
            raise Exception('page does not contain search results')
        soup = BeautifulSoup(res.text, 'html.parser')
        pagination_links = soup.select('.pagination-page-link')
        if pagination_links:
            last_page = int(soup.select('.pagination-page-link')[-1].text)
            data = [url+"?orderBy=9&beginIndex=%s&pageSize=48"%(48*page) for page in range(last_page)]
        for url in data:
            self.queue.put({'method': 'list_products', 'args': [url]})
        return data

    def list_products(self, url):
        """Get all product links in the category page

        :param url: A category page URL
        :type url: string
        :return: List of product URLs
        :rtype: list
        """
        res = self.__get_page(url)
        data = list(set(re.findall(r'(https://www.moosejaw.com/product/.+?)"', res.text)))
        for url in data:
            self.queue.put({'method': 'get_product', 'args': [url]})

    def get_product(self, url):
        """Get product HTML from the product URL

        :param url: A product URL
        :type url: string
        :raises Exception: Not a valid product page
        """

        res = self.__get_page(url)
        if not 'add2CartBtn' in res.text:
            raise Exception("invalid product page")
        self.store(url, res.text)

    def store(self, url, data):
        self.db.put('moosejaw', data)