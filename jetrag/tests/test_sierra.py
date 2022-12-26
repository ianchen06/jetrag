import unittest
import logging
import json

from crawlers.sierra import Sierra
from loaders.sierra import SierraLoader
from parsers.sierra import SierraParser
from q.mock import FakeQueue
from db.mocks3 import FakeS3Store
from notification.mock import FakeNotifier
from config import get_config


class TestSierra(unittest.TestCase):
    logger = logging.getLogger(__name__)
    logging.basicConfig(
        format="%(asctime)s %(module)s %(levelname)s: %(message)s",
        datefmt="%m/%d/%Y %I:%M:%S %p",
        level=logging.INFO,
    )

    def get_crawler(self):
        cfg = get_config("test")
        crawler = Sierra(
            cfg["sierra"],
            FakeQueue("sierra"),
            FakeS3Store(),
            cfg["db"]["sqlalchemy"],
            FakeNotifier(),
        )
        return crawler

    def test_list_categories(self):
        p = self.get_crawler()
        categories = p.list_categories()
        self.logger.info(categories)

    def test_get_category(self):
        p = self.get_crawler()
        categories = p.get_category('https://www.sierra.com/newproducts~14/')
        self.logger.info(categories)

    def test_list_products(self):
        p = self.get_crawler()
        products = p.list_products('https://www.sierra.com/newproducts~14/12/?perPage=96')
        self.logger.info(products)

    def test_get_product(self):
        p = self.get_crawler()
        p.get_product('https://www.sierra.com/frogg-toggs-chilly-pad-cooling-towel-upf-50-plus--33x13~p~1hhwj/')

    def test_parser(self):
        html = open('./tests/html/sierra/product.html').read()
        p = SierraParser()
        res = p.parse(html)
        print(json.dumps(res, indent=4))

    # def test_parse_thestyleroom(self):
    #     html = open('./tests/html/zappos/thestyleroom.html').read()
    #     p = ZapposParser()
    #     res = p.parse(html)
    #     print(f"res: {res}")

    def test_loader(self):
        html = open('./tests/html/sierra/product.html').read()
        p = SierraParser()
        res = p.parse(html)

        cfg = get_config("test")
        sql_cfg = cfg['db']['sqlalchemy']
        loader = SierraLoader(sql_cfg, '', '20221226', True)
        loader.load_update(res)

if __name__ == "__main__":
    unittest.main()
