import unittest
import logging

from jetrag.db.s3 import S3Store

class TestS3Store(unittest.TestCase):
    logger = logging.getLogger(__name__)
    logging.basicConfig(format = '%(asctime)s %(module)s %(levelname)s: %(message)s',
                    datefmt = '%m/%d/%Y %I:%M:%S %p', level = logging.INFO)
    def test_list(self):
        c = S3Store('jetrag3', '')
        res = c.list('moosejaw/20220718')
        self.logger.info(len(res))
        self.logger.info(res[0])

    def test_get(self):
        c = S3Store('jetrag3', '')
        res = c.get('moosejaw/20220718/100-aircraft-composite-helmet_10470882.html')
        self.logger.info(res)


if __name__ == '__main__':
    unittest.main()