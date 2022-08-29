import unittest
import logging
import json

from crawlers.zappos import Zappos
from parsers.zappos import ZapposParser
from q.mock import FakeQueue
from db.mocks3 import FakeS3Store
from notification.mock import FakeNotifier
from config import get_config


class TestZappos(unittest.TestCase):
    logger = logging.getLogger(__name__)
    logging.basicConfig(
        format="%(asctime)s %(module)s %(levelname)s: %(message)s",
        datefmt="%m/%d/%Y %I:%M:%S %p",
        level=logging.INFO,
    )

    def test_list_categories(self):
        cfg = get_config("test")
        p = Zappos(
            cfg["zappos"],
            FakeQueue("zappos"),
            FakeS3Store(),
            cfg["db"]["sqlalchemy"],
            FakeNotifier(),
        )
        p.list_categories()

    def test_list_products(self):
        cfg = get_config("test")
        p = Zappos(
            cfg["zappos"],
            FakeQueue("zappos"),
            FakeS3Store(),
            cfg["db"]["sqlalchemy"],
            FakeNotifier(),
        )
        p.list_products('https://www.zappos.com/null/.zso?p=1')

    def test_get_product(self):
        cfg = get_config("test")
        p = Zappos(
            cfg["zappos"],
            FakeQueue("zappos"),
            FakeS3Store(),
            cfg["db"]["sqlalchemy"],
            FakeNotifier(),
        )
        p.get_product('https://www.zappos.com/product/9836826')

    def test_parse_standard(self):
        html = open('./tests/html/zappos/standard.html').read()
        p = ZapposParser()
        res = p.parse(html)
        print(f"res: {res}")

    def test_parse_thestyleroom(self):
        html = open('./tests/html/zappos/thestyleroom.html').read()
        p = ZapposParser()
        res = p.parse(html)
        print(f"res: {res}")

if __name__ == "__main__":
    unittest.main()
