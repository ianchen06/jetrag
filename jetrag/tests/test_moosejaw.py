import unittest
import logging
import json

from crawlers.moosejaw import Moosejaw
from loaders.moosejaw import MoosejawLoader
from parsers.moosejaw import MoosejawParser
from q.mock import FakeQueue
from db.mocks3 import FakeS3Store
from notification.mock import FakeNotifier
from config import get_config


class TestMoosejaw(unittest.TestCase):
    logger = logging.getLogger(__name__)
    logging.basicConfig(
        format="%(asctime)s %(module)s %(levelname)s: %(message)s",
        datefmt="%m/%d/%Y %I:%M:%S %p",
        level=logging.INFO,
    )

    def test_list_categories(self):
        cfg = get_config("test")
        p = Moosejaw(
            cfg["moosejaw"],
            FakeQueue("moosejaw"),
            FakeS3Store(),
            cfg["db"]["sqlalchemy"],
            FakeNotifier(),
        )
        categories = p.list_categories()
        self.logger.info(categories)

    def test_get_category(self):
        cfg = get_config("test")
        p = Moosejaw(
            cfg["moosejaw"],
            FakeQueue("moosejaw"),
            FakeS3Store(),
            cfg["db"]["sqlalchemy"],
            FakeNotifier(),
        )
        categories = p.get_category('https://www.backcountry.com/womens-footwear')
        self.logger.info(categories)

    def test_list_products(self):
        cfg = get_config("test")
        p = Moosejaw(
            cfg["moosejaw"],
            FakeQueue("moosejaw"),
            FakeS3Store(),
            cfg["db"]["sqlalchemy"],
            FakeNotifier(),
        )
        products = p.list_products('https://www.backcountry.com/womens-footwear')
        self.logger.info(products)

    # def test_list_products(self):
    #     cfg = get_config("test")
    #     p = Zappos(
    #         cfg["zappos"],
    #         FakeQueue("zappos"),
    #         FakeS3Store(),
    #         cfg["db"]["sqlalchemy"],
    #         FakeNotifier(),
    #     )
    #     p.list_products('https://www.zappos.com/null/.zso?p=1')

    # def test_get_product(self):
    #     cfg = get_config("test")
    #     p = Zappos(
    #         cfg["zappos"],
    #         FakeQueue("zappos"),
    #         FakeS3Store(),
    #         cfg["db"]["sqlalchemy"],
    #         FakeNotifier(),
    #     )
    #     p.get_product('https://www.zappos.com/product/9836826')

    def test_parser(self):
        html = open('./tests/html/moosejaw/product.html').read()
        p = MoosejawParser()
        res = p.parse(html)
        print(json.dumps(res, indent=4))

    # def test_parse_thestyleroom(self):
    #     html = open('./tests/html/zappos/thestyleroom.html').read()
    #     p = ZapposParser()
    #     res = p.parse(html)
    #     print(f"res: {res}")

    def test_loader(self):
        html = open('./tests/html/moosejaw/product.html').read()
        p = MoosejawParser()
        res = p.parse(html)

        cfg = get_config("test")
        sql_cfg = cfg['db']['sqlalchemy']
        loader = MoosejawLoader(sql_cfg, '', '20221006', True)
        loader.load_update(res)

if __name__ == "__main__":
    unittest.main()
