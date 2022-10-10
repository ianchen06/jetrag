import json
import logging
import re
from collections import defaultdict

from models.backcountry import *

logger = logging.getLogger(__name__)


class BackcountryParser:
    def __init__(self):
        pass

    def list_html(self):
        self.db.list()

    def get_html(self):
        self.db.get()

    def parse(self, html):
        json_str = re.findall('<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html)[0]
        skus = json.loads(json_str)

        ### basic meta part ###
        meta = {}
        meta['item_url'] = 'https://www.backcountry.com'+skus['props']['pageProps']['product']['url']
        meta['item_name'] = skus['props']['pageProps']['product']['title']
        meta['backcountry_id'] = skus['props']['pageProps']['product']['id']
        meta['brand'] = skus['props']['pageProps']['product']['brand']['name']
        meta['category'] = [x['name'] for x in skus['props']['pageProps']['product']['breadcrumbs']]
        if 'women' in meta['category'][-1].lower():
            meta['gender'] = 'women'
        elif 'men' in meta['category'][-1].lower():
            meta['gender'] = 'men'
        elif 'boys' in meta['category'][-1].lower():
            meta['gender'] = 'boys'
        elif 'girls' in meta['category'][-1].lower():
            meta['gender'] = 'girls'
        else:
            meta['gender'] = 'unisex'

        meta['product_specifications'] = skus['props']['pageProps']['product']['bulletPoints'] if 'bulletPoints' in skus['props']['pageProps']['product'] else []
        meta['tech_specs'] = {x["name"]:x["value"] for x in skus['props']['pageProps']['product']['features']}


        # other detail photos
        sub_item_photos_tmp = [f"https://content.backcountry.com{x['twelveHundredImg']}" for x in skus['props']['pageProps']['product']['detailImages']]

        # save photos in sub_item_photos
        sub_item_photos = []
        for photo_url in sub_item_photos_tmp:
            try:
                sub_item_photos.append(photo_url)
            except:
                logging.info(f"__save_img_byte_to_s3 @ {photo_url}")

        sub_item_photos_dict = defaultdict(list)
        for x in sub_item_photos:
            color_code = x.split("/")[-1].split("_D")[0]
            sub_item_photos_dict[color_code].append(x)

        ### skus part ###
        color_sku = {}
        # accumulate all size info in a single color key
        for prod_id, sku in skus['props']['pageProps']['product']['skusCollection'].items():
            color_name = sku['color']['name']
            color_meta = color_sku.setdefault(color_name, {'price':{}, 'onhand':{}, 'item_photos':set(), 'item_photo_files':set()})

            size = sku['size']['name'] if sku.get('size', None) else 'One Size'
            color_meta['price'].update({size:sku['salePrice']})
            color_meta['onhand'].update({size:sku['inventory']})

            photo_url = f'https://content.backcountry.com{sku["color"]["nineHundredImg"]}'
            color_meta['item_photos'].add(photo_url)
        output_dict = []
        for color_name, sku in color_sku.items():
            color_meta = meta.copy()
            color_meta['color'] = color_name
            color_meta['price'] = sku['price']
            color_meta['onhand'] = sku['onhand']

            color_code = list(sku['item_photos'])[0].split("/")[-1].split(".")[0]

            # if sub_item_photos belongs to this color, then combine sub_item_photos into item_photos
            color_meta['item_photos'] = list(sku['item_photos']) + sub_item_photos_dict.get(color_code, [])
            color_meta['sub_item_photos'] = [v for  k,v in sub_item_photos_dict.items() if k != color_code]
            color_meta['sub_item_photos'] = [item for sublist in color_meta['sub_item_photos'] for item in sublist]

            output_dict.append(color_meta)

        return output_dict