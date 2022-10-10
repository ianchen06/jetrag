import json
import logging
import re

from bs4 import BeautifulSoup

from models.moosejaw import *

logger = logging.getLogger(__name__)


class MoosejawParser:
    def __init__(self):
        pass

    def list_html(self):
        self.db.list()

    def get_html(self):
        self.db.get()

    def parse(self, html):
        soup = BeautifulSoup(html, "lxml")
        general_imgs = set(
            re.findall(
                r"updateImage\('(https://.+?\.scene7.com/is/image/MoosejawMB/\d+?x\d+?_vAlt\d+?\?\$product700\$)'",
                html,
            )
        )
        product_specification = []
        for row in soup.select(".pdp-specifications tr"):
            aux = row.find_all("td")
            k = aux[0].string.strip().replace(":", "")
            v = aux[1].string.strip()
            product_specification.append(f"{k}: {v}")
        scripts = soup.find_all("script", {"type": "application/ld+json"})
        data = json.loads(scripts[0].text)
        category = [x["name"] for x in data["itemListElement"]]
        try:
            data = json.loads(scripts[1].text)
        except json.decoder.JSONDecodeError as e:
            logger.error(f"{e}: {scripts[1]}")
            return []
        res = {}
        for row in data["hasVariant"]:
            try:
                is_outofstock = (
                    row["offers"]["availability"] == "https://schema.org/OutOfStock"
                )
                if is_outofstock:
                    continue
                
                color = row.get("color", "None")
                if color not in res:
                    res[color] = {'size': []}         
                    res[color]["brand"] = re.findall('var manufacturerName = "(.+?)";', html)[0]
                    res[color]["color"] = color
                    res[color]["item_url"] = data["url"]
                    res[color]["item_code"] = data["url"].split("_")[1]
                    res[color]["item_photo"] = [row["image"]] + list(general_imgs)
                    res[color]["product_specifications"] = product_specification
                    res[color]["category"] = category
                    res[color]["item_name"] = data["name"]
                    
                size = {}
                size["item_no"] = row["sku"]
                size["size"] = row.get("size", "None")
                size["price"] = (
                    0 if not row["offers"]["price"] else row["offers"]["price"]
                )
                res[color]['size'].append(size)
            except Exception as e:
                logger.error(f"{e}: {data}")
                raise (e)
        return [x for x in res.values()]
