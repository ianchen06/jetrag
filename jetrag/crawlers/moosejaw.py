import time
import logging
import re
import datetime
import copy
import random

from bs4 import BeautifulSoup
import requests

from http_client import HTTPDriver
from parsers.moosejaw import MoosejawParser
from loaders.moosejaw import MoosejawLoader

logger = logging.getLogger(__name__)

class Moosejaw:
    def __init__(self, cfg, queue, html_store, sql_alchemy_cfg, notifier):
        self.name = 'moosejaw'
        self.cfg = cfg
        self.base_url = cfg['base_url']
        self.queue = queue
        self.html_store = html_store
        self.notifier = notifier
        self.dt = datetime.datetime.now().strftime("%Y%m%d")
        self.http = HTTPDriver()
        self.headers = cfg['headers']
        self.parser = MoosejawParser()
        self.loader = MoosejawLoader(sql_alchemy_cfg, '', self.dt)

    def __get_page(self, url):
        time.sleep(1)
        clean_headers = self.headers
        headers = copy.deepcopy(clean_headers)
        ua = headers['User-Agent'].replace('88.0', f'88.{random.randint(0,100)}')
        headers['User-Agent'] = ua
        return requests.request('GET', url, headers=headers)

    def dispatch(self):
        logger.info('dispatching job')
        self.queue.put({'method': 'list_categories'})

    def list_categories(self):
        """Get list of categories from Moosejaw navigation bar

        :return: List of urls
        :rtype: list
        """
        res = self.__get_page(self.base_url)
        print(res.text)
        soup = BeautifulSoup(res.text, 'html.parser')
        navigation = [self.base_url+x for x in re.findall(r'href="(/navigation.+?)"', res.text)]
        print(navigation)
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
        if "We're so sorry, but our Fancy Site Protection" in res.text:
            raise Exception("blocked")
        if not 'add2CartBtn' in res.text:
            self.store_html({'url': url+'_invalid', 'html': res.text})
            raise Exception("invalid product page")
        self.store_html({'url': url, 'html': res.text})
        data = self.parser.parse(res.text)
        self.store_db(data)
        return url

    def get_html_from_html_store(self, filename):
        html = self.html_store.get(filename)
        data = self.parser.parse(html)
        self.store_db(data)

    def store_html(self, data):
        self.html_store.put(f'moosejaw/{self.dt}', data)

    def store_db(self, data):
        self.loader.load_update(data)