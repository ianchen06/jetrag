import json
import logging
from math import prod
import re

from bs4 import BeautifulSoup

from models.moosejaw import *

logger = logging.getLogger(__name__)


class ZapposParser:
    def __init__(self):
        pass

    def list_html(self):
        self.db.list()

    def get_html(self):
        self.db.get()

    def parse(self, html):
        data = []
        item_url = re.findall(r'<link rel="canonical" href="(.+?)"', html)[0]
        standard = re.findall('<script>window.__INITIAL_STATE__ = (.+?);</script>', html)
        thestyleroom = re.findall('window.tsr.data = (.+?});', html)
        if standard:
            standard_data = json.loads(standard[0])
            data.extend(self.parse_standard(standard_data))
        if thestyleroom:
            thestyleroom_data = json.loads(thestyleroom[0])
            data.extend(self.parse_thestyleroom(thestyleroom_data))
        if not data:
            raise Exception("invalid store type")

        for row in data:
            row['item_url'] = item_url
        return data

    def parse_standard(self, page_data):
        json_array = []  # final output [{one color item}, {}...]
        basic_info = {}

        product = page_data['pixelServer']['data']['product']
        basic_info['zappos_id'] = product['sku']
        basic_info['brand'] = product['brand']
        basic_info['item_name'] = f"{product['brand']} {product['name']}"
        basic_info['category'] = [product['category'], product['subCategory']]
        basic_info['gender'] = product['gender']
        info_list = [self.clean_product_spec(e) for e in page_data['product']['detail']['description']['bulletPoints']]
        basic_info["product specifications"] = info_list            
        
        for color_item in page_data['product']['detail']['styles']:
            item = {}
            item.update(basic_info)

            item['color'] = color_item['color']

            # stock part
            raw_width_dict = {}  # group stocks by width
            for stock in color_item['stocks']:
                raw_width_dict[stock['width']] = raw_width_dict.setdefault(stock['width'], []) + [stock]

            width_dict = {}  # {width:{price:{}, onhand:{}, asin:{}}}
            for width, stocks in raw_width_dict.items():
                unit = {}
                unit['price'] = {stock['size']: color_item['price'][1:] for stock in stocks}
                unit['onhand'] = {stock['size']: stock['onHand'] for stock in stocks}
                unit['asin'] = {stock['size']: stock['asin'] for stock in stocks}
                width_dict[width.lower().replace(" ", "_")] = unit
            item['width'] = width_dict

            # image part
            item['item_photo_files'] = ["{}.jpg".format(p['imageId']) for p in color_item['images']]
            item['item_photo'] = ["https://m.media-amazon.com/images/I/{}._AC_SR700,525_.jpg".format(p['imageId'])
                                  for p in color_item['images']]

            json_array.append(item)
        return json_array

    def parse_thestyleroom(self, target_json):
        json_array = []  # final output [{one color item}, {}...]

        basic_info = {}
        basic_info['zappos_id'] = target_json['productId']
        basic_info['brand'] = target_json['brandName']
        basic_info['item_name'] = f"{target_json['brandName']} {target_json['productName']}"
        basic_info['category'] = [target_json['defaultProductType'], target_json['defaultCategory']]
        basic_info['gender'] = target_json['genders'][0]

        description_str = target_json.get('description', None)
        description_str = description_str.replace("<ul>", "").replace("</ul>", "").replace("<li>", "").replace("</li>", "").split("\n")
        description_list = []
        for x in description_str:
            if x:
                if 'measurements' in x:  # skip measurement
                    break
                else:
                    description_list.append(self.clean_product_spec(x))
        basic_info['product specifications'] = description_list

        ### stock info ###
        for color_item in target_json['styles']:
            item = {}
            item.update(basic_info)

            item['color'] = color_item['color']

            # stock part
            raw_width_dict = {}  # group stocks by width
            for stock in color_item['stocks']:
                raw_width_dict[stock['width']] = raw_width_dict.setdefault(stock['width'], []) + [stock]

            width_dict = {}  # {width:{price:{}, onhand:{}, asin:{}}}
            for width, stocks in raw_width_dict.items():
                unit = {}
                unit['price'] = {stock['size']: color_item['price'][1:] for stock in stocks}
                unit['onhand'] = {stock['size']: stock['onHand'] for stock in stocks}
                unit['asin'] = {stock['size']: stock['asin'] for stock in stocks}
                width_dict[width.lower().replace(" ", "_")] = unit
            item['width'] = width_dict

            # image part
            item['item_photo_files'] = ["{}.jpg".format(p['imageId']) for p in color_item['images']]
            item['item_photo'] = ["https://m.media-amazon.com/images/I/{}._AC_SR700,525_.jpg".format(p['imageId'])
                                  for p in color_item['images']]

            json_array.append(item)

        return json_array
    
    def clean_product_spec(self, s):
        clear_str = ""
        inside_tag = False

        for c in s.rstrip().replace("\n", ""):  # clear <xxx>
            if c == "<":
                inside_tag = True
            elif c == ">":
                inside_tag = False
            else:
                if inside_tag:
                    pass
                else:
                    clear_str += c
        return clear_str