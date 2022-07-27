import unittest
import logging
import json

from parsers.moosejaw import MoosejawParser

class TestMoosejawParser(unittest.TestCase):
    logger = logging.getLogger(__name__)
    logging.basicConfig(format = '%(asctime)s %(module)s %(levelname)s: %(message)s',
                    datefmt = '%m/%d/%Y %I:%M:%S %p', level = logging.INFO)
    def test_parse(self):
        p = MoosejawParser()
        html = open('./tests/html/moosejaw/product.html').read()
        res = p.parse(html)
        json_data = json.dumps(res, indent=4, ensure_ascii=False)
        self.logger.info(json_data)

if __name__ == '__main__':
    unittest.main()