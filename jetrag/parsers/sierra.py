import logging
import re
from collections import defaultdict
from html.parser import HTMLParser

from bs4 import BeautifulSoup

from models.sierra import *

logger = logging.getLogger(__name__)


class MyHTMLParser(HTMLParser):
    def __init__(self, *args, **kwargs):
        super(MyHTMLParser, self).__init__(*args, **kwargs)
        self.data_list = []

    def handle_starttag(self, tag, attrs):
        # print("Encountered a start tag:", tag)
        pass

    def handle_endtag(self, tag):
        # print("Encountered an end tag :", tag)
        pass

    def handle_data(self, data):
        # print("Encountered some data  :", data)
        self.data_list.append(data)

class SierraParser:
    def __init__(self):
        pass

    def list_html(self):
        self.db.list()

    def get_html(self):
        self.db.get()

    def str_processing(self, txt):
        return txt.rstrip().replace("\n", "").replace("\r", "")[::-1].rstrip()[::-1]

    def parse(self, html):
        soup = BeautifulSoup(html, 'html.parser', from_encoding='utf-8')

        """
        # scan Factory seconds(瑕疵貨) in all text -> item.unavailable()
        for discard_word in ["Factory seconds", "Factory_seconds", "Factory-seconds", "Factory 2nds"]:
            if discard_word.lower() in html_text.lower():
                logging.info(f"{url} is Factory seconds")
                return "Factory seconds"
        """
        ### basic info ###
        info = {}
        info['item_name'] = self.str_processing(soup.title.text)

        for x in soup.find_all('h3', class_='m-b-lg'):
            if 'About' in x.text:
                info['brand'] = x.text.replace("About ", "")
        canonical_url = re.findall('<link rel="canonical" href="(https://www.sierra.com/.+?~p~.+?/)"', html, re.DOTALL)[0]
        info['item_url'] = canonical_url
        info['sierra_id'] = re.findall('~p~(.*?)/', canonical_url)[0] if re.findall('~p~(.*?)/', canonical_url) else canonical_url[canonical_url.index("~p~")+3:]
        info['gender'] = re.findall('For (.*?)\)', soup.title.text)[0].lower() if re.findall('For (.*?)\)', soup.title.text) else 'unisex'

        ### category ###
        category_meta = soup.find_all('ol', class_='breadcrumbs')
        info['category'] = []
        if len(category_meta) >= 1:
            info['category'] = [x for x in category_meta[-1].text.split("\n") if x != '']

        # 1st is brand name Review 去掉 review = brand name
        info['similar_items_more_information'] = [[info['brand']]] if info.get('brand', None) else []
        if len(category_meta) >= 2:
            # [1:] 是因為第一個是最上面的category, 比較粗略且會重複 因此省略
            for category_series in category_meta[1:]:
                info['similar_items_more_information'].append([x for x in category_series.text.split("\n") if x != ''])

        parser = MyHTMLParser()
        if soup.find_all('ul', class_='list'):
            parser.feed(soup.find_all('ul', class_='list')[0].text)
            info['product specifications'] = [x for x in parser.data_list[0].split('\n') if x]
        else:
            logging.info(f"[debug] {canonical_url} can not get product specifications")
            logging.info(f"[debug] current page's info: {info}")
            info['product specifications'] = []

        # color is indicated by a number, build dict for it {'03': 'White', ...}
        color_index_name = {}
        color_obj = soup.find(text='selectedProperty1DropDown')
        if color_obj:
            while True:
                color_obj = color_obj.findNext()
                if not color_obj.text:
                    break
                color_index_name[color_obj['value']] = color_obj.text
        else:
            ### Sold Out case ###
            return "sold out"

        ### dig info out from javascript  ###
        target_html = None
        for part in soup.find_all('script', type='text/javascript'):
            if 'var skus' in str(part):
                target_html = str(part)
        raw_stock_list = re.findall('availabilityMsg: "(.*?)",', target_html)

        # rakuten format
        # still available = '5'
        # out of stock = '0'
        stock_list = []
        for n in raw_stock_list:
            if not n or n == "Almost Gone":
                stock_list.append(True)
            elif "Only" in n:
                stock_list.append(True)
                # stock_list.append(int([x for x in n.split(' ') if x.isdigit()][0]))
            else:
                stock_list.append(True)

        """
        property1 = color
        property2 = size or waist
        property3 = inseam or sth or ""(if no info), if no property3, will get ['', '', '', ...]
        
        skip non fashion item, which has no property2 
        like https://www.sierra.com/thin-air-brands-dr-stem-toys-talking-cash-register~p~63tmj/
        """
        p2_name = soup.find_all('label', id='property2Label')
        #if not p2_name:
        #    return "Not Fashion Item"
        p2_name = p2_name[0].text[:-1] if p2_name else None  # rm ":" from Waist:
        p3_name = soup.find_all('label', id='property3Label')
        p3_name = p3_name[0].text[:-1] if p3_name else None

        color_list = [color_index_name[x] for x in re.findall('property1: "(.*?)",', target_html)]

        if not p2_name:
            size_list = ['']*len(color_list)
        elif p2_name == "Size":
            size_list = [x if x else 'one_size' for x in re.findall('property2: "(.*?)",', target_html)]
        else:
            size_list = [f"{p2_name}-{x}" if x else 'one_size' for x in re.findall('property2: "(.*?)",', target_html)]

        if p3_name:
            p3_list = [f"{p3_name}-{x}" for x in re.findall('property3: "(.*?)",', target_html)]
        else:
            p3_list = [x for x in re.findall('property3: "(.*?)",', target_html)]

        price_list = re.findall('finalPromoPrice: "(.*?)",', target_html)

        color_dict = defaultdict(list)  # { color: [] }
        for color, size, p3, price, stock in zip(color_list, size_list, p3_list, price_list, stock_list):
            color_dict[color].append([f"{size if size else 'Onesize'}:{p3 if p3 else 'Onesize'}", price, stock])


        ### align part ###
        """
        sierra can only get the items available. (e.g.  ['Waist-38:Inseam-36', '$39.99', '5'])
        to align the format, make the combo which is out of stock, e.g. ['Waist-33:Inseam-34', '$39.99', 0]
        """
        """
        p2_value_set = set(size_list)
        p3_value_set = set(p3_list)
        combo_set = set()
        for p2_v in p2_value_set:
            for p3_v in p3_value_set:
                combo_set.update([f"{p2_v if p2_v else 'Onesize'}:{p3_v if p3_v else 'Onesize'}"])
        for color_index, color_name in color_dict.items():
            existing_combos = set([x[0] for x in color_name])
            for combo in (combo_set - existing_combos):
                color_name.append([f"{combo}", price_list[0], 0])
        """
        ### image part ###
        # 正面有各顏色, 能拿到的是第一個 as anchor_img_url, 然後用color_index拼出其他顏色的
        # https://i.stpost.com/the-north-face-ventrix-jacket-insulated-for-men-in-botanical-garden-green-vandis-grey~p~730vr_${color_index}~460.2.jpg
        # color_index = 01, 02, 03, 04 ...

        anchor_img_url = soup.find(id='largeImageSrcTemplate')['value']  # soup.find('a', class_="altImage")['data-image']
        front_side_image_dict = {}
        color_index_name_with_photo = {}  # record the color w/ photo

        if '_0' in anchor_img_url:
            index_color_index = anchor_img_url.index("_0")
            for color_name, color_meta in color_index_name.items():
                img_url = f"{anchor_img_url[:index_color_index + 1]}{color_name}{anchor_img_url[index_color_index + 3:]}"
                front_side_image_dict[color_meta] = img_url
                color_index_name_with_photo[color_name] = color_meta
        else:  # for the case which has no bottom view bar (may be image not available now), 指定唯一可以拿到的給全部的color
            # if no photo available, skip this item
            logging.info("_0 not in anchor_img_url, sth wrong")
            return "_0 not in anchor_img_url"

        if not color_index_name_with_photo:  # if no photo available, skip this item
            logging.info("not color_index_name_with_photo, sth wrong")
            return "no photo available"

        print(f"{canonical_url} : color_index_name_with_photo = {color_index_name_with_photo}")

        # 第一張是正面,
        # 反面是[1:], 而且每顏色的反面都是同一組, *可能會沒有
        back_side_images_candidates = [x['data-image'] for x in soup.find_all('a', class_="altImage")][1:]
        back_side_images = []
        for img_url in back_side_images_candidates:
            back_side_images.append(img_url)

        ### assemble as output_array ###
        output_array = []
        for color_name, color_meta in color_dict.items():
            # output_dict + basic
            output_dict = info.copy()

            output_dict['color'] = color_name

            price_dict = {}
            onhand_dict = {}
            for size_obj in color_meta:  # [['S', '$79.99', -1], ...]
                price_dict[size_obj[0]] = size_obj[1]
                onhand_dict[size_obj[0]] = size_obj[2]

            output_dict['price'] = price_dict
            output_dict['onhand'] = onhand_dict

            output_dict['item_photos'] = front_side_image_dict.get(color_name, None)
            # photo may be unavailable -> skip this color
            if not output_dict['item_photos']:
                print(f'{color_name} has no item photos')
                continue
            output_dict['sub_item_photos'] = back_side_images
            output_array.append(output_dict)

        return output_array