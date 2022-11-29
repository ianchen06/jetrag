import time
import logging
import re
import datetime

import requests

from http_client import HTTPDriver
from parsers.backcountry import BackcountryParser
from loaders.backcountry import BackcountryLoader

logger = logging.getLogger(__name__)

class Backcountry:
    def __init__(self, cfg, queue, html_store, sql_alchemy_cfg, notifier):
        self.name = 'backcountry'
        self.cfg = cfg
        self.base_url = cfg['base_url']
        self.queue = queue
        self.html_store = html_store
        self.notifier = notifier
        self.dt = datetime.datetime.now().strftime("%Y%m%d")
        self.http = HTTPDriver()
        self.headers = cfg['headers']
        self.max_retry_cnt = 3
        self.http_timeout_seconds = 10
        self.parser = BackcountryParser()
        self.loader = BackcountryLoader(sql_alchemy_cfg, '', self.dt)

    def __get_page(self, url):
        cnt = 0
        errors = []
        while True:
            try:
                return requests.request('GET', url, headers=self.headers, timeout=self.http_timeout_seconds)
            except requests.exceptions.ReadTimeout as e:
                logger.info(e)
                errors.append(e)
            except requests.exceptions.ConnectionError as e:
                logger.info(e)
                errors.append(e)
            cnt += 1
            if cnt > self.max_retry_cnt:
                raise Exception(f"Retry exceeded {self.max_retry_cnt} times, url: {url}, reasons: {errors}")
            time.sleep(1)

    def dispatch(self):
        logger.info('dispatching job')
        self.queue.put({"method": "list_categories"})

    def list_categories(self):
        """Get list of categories from Backcountry navigation bar

        :return: List of urls
        :rtype: list
        """
        res = self.__get_page(self.base_url)
        urls = re.findall(r'<a class="chakra-link css-\w+?" href="(/[\w-]+?)">\w+?</a><ul role="list" class="css-', res.text)
        all_activities = re.findall(r'All Activities</.+?</ul>', res.text)[0]
        activities_urls = re.findall(r'<a class="chakra-link css-\w+?" href="(/[\w-]+?)">.+?</a>', all_activities)
        category_urls = urls+activities_urls
        logger.info(category_urls)
        for url in category_urls:
            self.queue.put({'method': 'get_category', 'args': [self.base_url+url+'?show=all']})
        return category_urls

    def get_category(self, url):
        """Get list of urls for all pages of the category

        :param url: url for a category
        :type url: string
        :raises Exception: Page does not have search result, maybe moosejaw side error
        :return: List of URLs of all pages of the category
        :rtype: list
        """
        res = self.__get_page(url)
        try:
            total_page = int(re.findall(r'Page 1 of (.+?)<', res.text)[0])
        except IndexError:
            logger.info(f"{url} has no total_page")
            return
        print(f"{url}: total_page: {total_page}")
        for np in range(1, total_page+1):
            self.queue.put({'method': 'list_products', 'args': [url+f"&page={np}"]})
        return f"{url}, total_page: {total_page}"

    def list_products(self, url):
        """Get all product links in the category page

        :param url: A category page URL
        :type url: string
        :return: List of product URLs
        :rtype: list
        """
        res = self.__get_page(url)
        data = re.findall(r'<a href="(/[\w-]+?)" variant="text" class="chakra-linkbox__overlay css-\w+?">', res.text)
        with open(f"/tmp/data/{url.replace('/', '-').replace(':', '-')}.txt", 'w') as f:
            for url in data:
                f.write(url + '\n')
        for url in data:
            self.queue.put({'method': 'get_product', 'args': [self.base_url + url]})
        return data

    def get_product(self, url):
        """Get product HTML from the product URL

        :param url: A product URL
        :type url: string
        :raises Exception: Not a valid product page
        """

        res = self.__get_page(url)
        # Check if blocked
        if "We're so sorry, but our Fancy Site Protection" in res.text:
            raise Exception("blocked")

        # If some other weird page
        
        self.store_html({'url': url, 'html': res.text})
        data = self.parser.parse(res.text)
        self.store_db(data)
        return url

    def get_html_from_html_store(self, filename):
        html = self.html_store.get(filename)
        data = self.parser.parse(html)
        self.store_db(data)

    def store_html(self, data):
        self.html_store.put(f'backcountry/{self.dt}', data)

    def store_db(self, data):
        self.loader.load_update(data)