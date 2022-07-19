import unittest
import logging

from jetrag.parsers.moosejaw import MoosejawParser

class TestMoosejawParser(unittest.TestCase):
    logger = logging.getLogger(__name__)
    logging.basicConfig(format = '%(asctime)s %(module)s %(levelname)s: %(message)s',
                    datefmt = '%m/%d/%Y %I:%M:%S %p', level = logging.INFO)
    def test_parse(self):
        p = MoosejawParser()
        html = open('./tests/html/moosejaw/product.html').read()
        res = p.parse(html)
        self.logger.info(res)

if __name__ == '__main__':
    unittest.main()