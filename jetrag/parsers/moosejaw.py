import json
import logging
import re

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class MoosejawParser:
    def __init__(self):
        pass

    def list_html(self):
        self.db.list()

    def get_html(self):
        self.db.get()

    def parse(self, html):
        product_data = []
        soup = BeautifulSoup(html, 'lxml')
        general_imgs = set(re.findall(r"updateImage\('(https://.+?\.scene7.com/is/image/MoosejawMB/\d+?x\d+?_vAlt\d+?\?\$product700\$)'", html))
        product_specification = {}
        for row in soup.select('.pdp-specifications tr'):
            aux = row.find_all('td')
            product_specification[aux[0].string.strip()] = aux[1].string.strip()
        scripts = soup.find_all('script', {"type": "application/ld+json"})
        data = json.loads(scripts[0].text)
        category = [x['name'] for x in data['itemListElement']]
        data = json.loads(scripts[1].text)
        for row in data['hasVariant']:
            res = {}
            res['category'] = category
            res['item_url'] = data['url']
            res['item_name'] = data['name']
            res['item_code'] = res['item_url'].split('_')[1]
            res['color'] = row['color']
            res['size'] = row['size']
            res['item_no'] = row['sku']
            res['price'] = row['offers']['price']
            res['item_photo'] = [row['image']] + list(general_imgs)
            res['product_specifications'] = json.dumps(product_specification)
            product_data.append(res)
        return product_data