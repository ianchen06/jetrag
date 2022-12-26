import time
import logging
import re
import datetime
import certifi
from io import BytesIO

import pycurl
from bs4 import BeautifulSoup

from http_client import HTTPDriver
from parsers.sierra import SierraParser
from loaders.sierra import SierraLoader

logger = logging.getLogger(__name__)

class HTTPResponse:
    def __init__(self, text):
        self.text = text

class Sierra:
    def __init__(self, cfg, queue, html_store, sql_alchemy_cfg, notifier):
        self.name = 'sierra'
        self.cfg = cfg
        self.base_url = cfg['base_url']
        self.queue = queue
        self.html_store = html_store
        self.notifier = notifier
        self.dt = datetime.datetime.now().strftime("%Y%m%d")
        self.http = HTTPDriver()
        self.headers = cfg['headers']
        self.max_retry_cnt = 3
        self.http_timeout_seconds = 30
        self.parser = SierraParser()
        self.loader = SierraLoader(sql_alchemy_cfg, '', self.dt)

    def __get_page(self, url):
        cnt = 0
        errors = []
        while True:
            try:
                buffer = BytesIO()
                c = pycurl.Curl()
                c.setopt(pycurl.HTTPHEADER, [f"{k}: {v}" for k,v in self.headers.items()])
                c.setopt(pycurl.URL, url)
                c.setopt(pycurl.ENCODING, 'gzip')
                c.setopt(pycurl.WRITEDATA, buffer)
                c.setopt(pycurl.CAINFO, certifi.where())
                c.perform()
                status_code = c.getinfo(pycurl.HTTP_CODE)
                c.close()

                if status_code > 300:
                    raise Exception(f"Fetch url error: {url}-{status_code}")

                body = buffer.getvalue()
                # Body is a byte string.
                # We have to know the encoding in order to print it to a text file
                # such as standard output.
                return HTTPResponse(body.decode('utf-8'))
            except:
                cnt += 1
                if cnt > self.max_retry_cnt:
                    raise Exception(f"Retry exceeded {self.max_retry_cnt} times, url: {url}, reasons: {errors}")
                time.sleep(1)

    def dispatch(self):
        logger.info('dispatching job')
        self.queue.put({"method": "list_categories"})

    def list_categories(self):
        """Get list of categories from navigation bar

        :return: List of urls
        :rtype: list
        """
        res = self.__get_page(self.base_url)
        soup = BeautifulSoup(res.text)
        urls = [x['href'].split('?')[0] for x in soup.select('#navigation > div > div > div > div.nav-item.dropdown.navigation-dropdown.backdrop-toggle.pos-s.drawer-item > a')]
        logger.info(urls)
        for url in urls:
            self.queue.put({'method': 'get_category', 'args': [self.base_url+url]})
        return urls

    def get_category(self, url):
        """Get list of urls for all pages of the category

        :param url: url for a category
        :type url: string
        :raises Exception: Page does not have search result, maybe moosejaw side error
        :return: List of URLs of all pages of the category
        :rtype: list
        """
        url96 = url + '?perPage=96'
        res = self.__get_page(url96)
        last_page = re.findall(r'<a class="pageLink lastPage" href="/.+?~\d+?/(\d+?)/" aria-label="Go to Last Page">page \d+?</a>', res.text)[0]       
        total_page = int(last_page)
        print(f"{url}: total_page: {total_page}")
        for np in range(1, total_page+1):
            self.queue.put({'method': 'list_products', 'args': [url+f"{np}/?perPage=96"]})
        return f"{url}, total_page: {total_page}"

    def list_products(self, url):
        """Get all product links in the category page

        :param url: A category page URL
        :type url: string
        :return: List of product URLs
        :rtype: list
        """
        res = self.__get_page(url)
        product_detail_regex = '<a id="productLink.+?" title=".+?" href="(.+?)" class="js-productThumbnail">'        # with open(f"/tmp/data/{url.replace('/', '-').replace(':', '-')}.txt", 'w') as f:
        data = re.findall(product_detail_regex, res.text)
        logger.info(f"Found {len(data)} products on {url}")
        for url in data:
            url = url.split('?')[0]
            self.queue.put({'method': 'get_product', 'args': [self.base_url + url]})
        return data

    def get_product(self, url):
        """Get product HTML from the product URL

        :param url: A product URL
        :type url: string
        :raises Exception: Not a valid product page
        """

        res = self.__get_page(url)    
        self.store_html({'url': url, 'html': res.text})
        data = self.parser.parse(res.text)
        self.store_db(data)
        return url

    def get_html_from_html_store(self, filename):
        html = self.html_store.get(filename)
        data = self.parser.parse(html)
        self.store_db(data)

    def store_html(self, data):
        self.html_store.put(f'sierra/{self.dt}', data)

    def store_db(self, data):
        self.loader.load_update(data)