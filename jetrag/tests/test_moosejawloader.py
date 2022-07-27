import unittest
import logging
import json

from loaders.moosejaw import MoosejawLoader
from db.s3 import S3Store

CONNSTR = 'mysql+auroradataapi://:@/moosejaw?'
'aurora_cluster_arn=arn:aws:rds:ap-northeast-1:068993006585:cluster:jetrag3'
'&secret_arn=arn:aws:secretsmanager:ap-northeast-1:068993006585:secret:rds-db-credentials/cluster-YXGYNX2ORLFS6RYDNGEBFTMHHA/jetrag-PvBX2f'
CONNSTR = 'mysql+pymysql://root:mysql@localhost:3306/jetrag'

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

    def test_load_update(self):
        c = MoosejawLoader(CONNSTR, None, None)
        
        product_data = '''[{
        "color": "Deep Heather",
        "size": "Small",
        "item_no": "6772822",
        "category": [
            "Womens Outerwear",
            "Womens Jackets",
            "Womens Insulated Jackets",
            "Womens Down Jackets"
        ],
        "item_url": "https://www.moosejaw.com/product/rab-women-s-cubit-stretch-down-hoody_10537936",
        "item_name": "Rab Women's Cubit Stretch Down Hoody",
        "item_code": "10537936",
        "price": "299.95",
        "item_photo": [
            "https://s7d1.scene7.com/is/image/MoosejawMB/10537936x1087290_zm?$product1000$",
            "https://s7d1.scene7.com/is/image/MoosejawMB/10537936x1085886_vAlt4?$product700$",
            "https://s7d1.scene7.com/is/image/MoosejawMB/10537936x1085886_vAlt2?$product700$",
            "https://s7d1.scene7.com/is/image/MoosejawMB/10537936x1085886_vAlt1?$product700$",
            "https://s7d1.scene7.com/is/image/MoosejawMB/10537936x1085886_vAlt3?$product700$"
        ],
        "product_specifications": ""
    },{
        "color": "Deep Heather",
        "size": "Small",
        "item_no": "6772822",
        "category": [
            "Womens Outerwear",
            "Womens Jackets",
            "Womens Insulated Jackets",
            "Womens Down Jackets"
        ],
        "item_url": "https://www.moosejaw.com/product/rab-women-s-cubit-stretch-down-hoody_10537936",
        "item_name": "Rab Women's Cubit Stretch Down Hoody",
        "item_code": "10537936",
        "price": "299.95",
        "item_photo": [
            "https://s7d1.scene7.com/is/image/MoosejawMB/10537936x1087290_zm?$product1000$",
            "https://s7d1.scene7.com/is/image/MoosejawMB/10537936x1085886_vAlt4?$product700$",
            "https://s7d1.scene7.com/is/image/MoosejawMB/10537936x1085886_vAlt2?$product700$",
            "https://s7d1.scene7.com/is/image/MoosejawMB/10537936x1085886_vAlt1?$product700$",
            "https://s7d1.scene7.com/is/image/MoosejawMB/10537936x1085886_vAlt3?$product700$"
        ],
        "product_specifications": ""
    }]'''
        res = c.load_update(json.loads(product_data))


if __name__ == '__main__':
    unittest.main()