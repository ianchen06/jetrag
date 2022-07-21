import unittest
import logging

from jetrag.loaders.moosejaw import MoosejawLoader
from jetrag.db.s3 import S3Store

CONNSTR = 'mysql+auroradataapi://:@/moosejaw?'
'aurora_cluster_arn=arn:aws:rds:ap-northeast-1:068993006585:cluster:jetrag3'
'&secret_arn=arn:aws:secretsmanager:ap-northeast-1:068993006585:secret:rds-db-credentials/cluster-YXGYNX2ORLFS6RYDNGEBFTMHHA/jetrag-PvBX2f'

class TestMoosejawLoader(unittest.TestCase):
    logger = logging.getLogger(__name__)
    logging.basicConfig(format = '%(asctime)s %(module)s %(levelname)s: %(message)s',
                    datefmt = '%m/%d/%Y %I:%M:%S %p', level = logging.INFO)

    def test_get(self):
        s3 = S3Store('jetrag3', '')
        c = MoosejawLoader(CONNSTR, s3, '20220720')
        for res in c.get():
            self.logger.info(res)
            break
        
    def test_do(self):
        s3 = S3Store('jetrag3', '')
        c = MoosejawLoader(CONNSTR, s3, '20220720')
        c.do()

    def test_list(self):
        c = MoosejawLoader(CONNSTR, None, None)
        
        product_data = [{'category': ['Mens Footwear', 'Mens Sandals', 'Mens Sport Sandals'],
            'item_url': 'https://www.moosejaw.com/product/keen-men-s-drift-creek-h2-sandal_10557547',
            'item_name': "KEEN Men's Drift Creek H2 Sandal",
            'item_code': '10557547',
            'color': 'Red Carpet / Black',
            'size': '7.5',
            'item_no': '7055079',
            'price': '109.95',
            'item_photo': ['https://s7d1.scene7.com/is/image/MoosejawMB/10557547x1254116_zm?$product1000$',
            'https://s7d1.scene7.com/is/image/MoosejawMB/10557547x1064714_vAlt5?$product700$',
            'https://s7d1.scene7.com/is/image/MoosejawMB/10557547x1064714_vAlt3?$product700$',
            'https://s7d1.scene7.com/is/image/MoosejawMB/10557547x1064714_vAlt4?$product700$',
            'https://s7d1.scene7.com/is/image/MoosejawMB/10557547x1064714_vAlt2?$product700$',
            'https://s7d1.scene7.com/is/image/MoosejawMB/10557547x1064714_vAlt1?$product700$'],
            'product_specifications': '{"Footwear Height:": "Ankle", "Upper:": "Polyester Webbing", "Outsole:": "TPR", "Disclaimer:": "We only ship this brand to US Addresses.", "Gender:": "Mens", "Best Use:": "Day Hiking, Water Sports", "Footwear Closure:": "Cable / Quick Lace", "Toe Coverage:": "Closed Toe"}'
        }]
        res = c.load(product_data)


if __name__ == '__main__':
    unittest.main()