import time
import logging
import re
import datetime
import copy
import random

from bs4 import BeautifulSoup
import requests as r

from http_client import HTTPDriver
from parsers.zappos import ZapposParser
from loaders.zappos import ZapposLoader

logger = logging.getLogger(__name__)

class Zappos:
    def __init__(self, cfg, queue, html_store, sql_alchemy_cfg, notifier):
        self.name = 'zappos'
        self.cfg = cfg
        self.base_url = cfg['base_url']
        self.queue = queue
        self.html_store = html_store
        self.notifier = notifier
        self.dt = datetime.datetime.now().strftime("%Y%m%d")
        self.headers = cfg['headers']
        self.parser = ZapposParser()
        self.loader = ZapposLoader(sql_alchemy_cfg, '', self.dt)

    def __get_page(self, url):
        return r.request('GET', url, headers=self.headers)

    def dispatch(self):
        logger.info('dispatching job')
        self.queue.put({'method': 'list_categories'})

    def list_categories(self):
        """Get list of categories from Moosejaw navigation bar

        :return: List of urls
        :rtype: list
        """
        res = self.__get_page(self.base_url+'/null/.zso?p=0')
        last_page = max([int(x) for x in re.findall(r'href="/null/.zso\?p=(\d+?)"', res.text)])
        for pg in range(last_page+1):
            url = self.base_url + f'/null/.zso?p={pg}'
            self.queue.put({'method': 'list_products', 'args': [url]})

    def list_products(self, url):
        """Get all product links in the category page

        :param url: A category page URL
        :type url: string
        :return: List of product URLs
        :rtype: list
        """
        res = self.__get_page(url)
        products = list(set(re.findall(r'/p/.+?(/product/\d+?)/', res.text)))
        for product_code in products:
            url = self.base_url + product_code
            self.queue.put({'method': 'get_product', 'args': [url]})

    def get_product(self, url):
        """Get product HTML from the product URL

        :param url: A product URL
        :type url: string
        :raises Exception: Not a valid product page
        """

        res = self.__get_page(url)
        if 'Access Denied' in res.text:
            raise Exception("blocked")
        self.store_html({'url': url, 'html': res.text})
        #data = self.parser.parse(res.text)
        #self.store_db(data)

    def get_html_from_html_store(self, filename):
        html = self.html_store.get(filename)
        data = self.parser.parse(html)
        self.store_db(data)

    def store_html(self, data):
        self.html_store.put(f'zappos/{self.dt}', data)

    def store_db(self, data):
        self.loader.load_update(data)