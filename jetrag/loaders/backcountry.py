import logging
import datetime
import hashlib

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# For MySQL upsert
from sqlalchemy import func
from sqlalchemy import insert, update, select, text

import boto3

from models.backcountry import *

logger = logging.getLogger(__name__)


class BackcountryLoader:
    def __init__(self, cfg, raw_store, dt, debug=False):
        self.boto_client = boto3.client(
            "rds-data",
            aws_access_key_id=cfg["aws_access_key_id"],
            aws_secret_access_key=cfg["aws_secret_access_key"],
            region_name="us-east-2",
        )
        self.connect_args = cfg["connect_args"]
        self.connect_args["rds_data_client"] = self.boto_client
        self.engine = create_engine(
            cfg["conn_str"] + "/backcountry", connect_args=self.connect_args, echo=debug
        )
        self.session = Session(self.engine)
        self.raw_store = raw_store
        self.dt = dt

    def get(self):
        return self.raw_store.list(f"backcountry/{self.dt}")

    def cleanup(self, before_dt):
        logger.info(f"cleanup before {before_dt}")
        tables = [
            Item,
            Size,
            Spec,
            Category,
            Onhand,
            Photo,
            Price,
            ProductSpecification,
            TechSpec,
        ]
        for table in tables:
            (
                self.session.query(table)
                .filter(table.edited < before_dt)
                .delete(synchronize_session=False)
            )
            self.session.commit()

    def gen_item_id(self, item_code, color):
        input_ = f"{item_code}_{color}".encode('utf-8')
        hash_func = hashlib.shake_256()
        hash_func.update(input_)
        return hash_func.hexdigest(8)

    # TODO: refactor into common lib
    def upsert(self, model, insert_dict, where_list, fetch=False):
        inserted = model(**insert_dict)
        self.session.add(inserted)
        try:
            self.session.commit()
        except Exception as e:
            if 'ER_DUP_ENTRY' not in str(e):
                raise e
            self.session.rollback()
            stmt = (
                update(model)
                .where(*where_list)
                .values(
                    **insert_dict,
                    edited=datetime.datetime.now(datetime.timezone.utc)
                )
            )
            self.session.execute(stmt)
            self.session.commit()
        if not fetch:
            return
        stmt = select(model.id).where(*where_list)
        row = self.session.execute(stmt).first()
        return row[0]

    def load_update(self, variants):
        """
        {
            "item_url": "https://www.backcountry.com/backcountry-corduroy-sherpa-lined-shirt-jacket-mens",
            "item_name": "Corduroy Sherpa Lined Shirt Jacket - Men's",
            "backcountry_id": "BCCZ2MN",
            "brand": "Backcountry",
            "category": [
                "Men's Clothing",
                "Men's Shirts",
                "Men's Shirt Jackets"
            ],
            "gender": "men",
            "product_specifications": [
                "Classic corduroy jacket with sherpa lining for the chilly seasons",
                "Sherpa lining on the core ensures cold drafts won't leave you shivering",
                "Synthetic insulation in the sleeves to keep your arms active",
                "Button-up design offers versatility for jacket or shirt style"
            ],
            "tech_specs": {
                "Material": "[face fabric] 100% cotton, [lining] 100% polyester sherpa fleece, [sleeve lining] 100% polyester woven, [sleeve insulation] 20g synthetic (100% polyester)",
                "Fit": "regular",
                "Center Back Length": "[large] 30.5in",
                "Style": "button-up",
                "Pockets": "2 hand, 2 snapped chest",
                "Activity": "casual",
                "Manufacturer Warranty": "limited lifetime",
                "storecredits": "0.0"
            },
            "color": "Pika",
            "price": {
                "L": 129,
                "M": 129,
                "S": 129,
                "XL": 129,
                "XXL": 129
            },
            "onhand": {
                "L": 177,
                "M": 138,
                "S": 35,
                "XL": 108,
                "XXL": 29
            },
            "item_photos": [
                "https://content.backcountry.com/images/items/900/BCC/BCCZ2MN/PIK.jpg",
                "https://content.backcountry.com/images/items/1200/BCC/BCCZ2MN/PIK_D4.jpg",
                "https://content.backcountry.com/images/items/1200/BCC/BCCZ2MN/PIK_D3.jpg",
                "https://content.backcountry.com/images/items/1200/BCC/BCCZ2MN/PIK_D2.jpg",
                "https://content.backcountry.com/images/items/1200/BCC/BCCZ2MN/PIK_D1.jpg"
            ],
            "sub_item_photos": [
                "https://content.backcountry.com/images/items/1200/BCC/BCCZ2MN/KAT_D5.jpg",
                "https://content.backcountry.com/images/items/1200/BCC/BCCZ2MN/KAT_D3.jpg",
                "https://content.backcountry.com/images/items/1200/BCC/BCCZ2MN/KAT_D2.jpg",
                "https://content.backcountry.com/images/items/1200/BCC/BCCZ2MN/KAT_D1.jpg"
            ]
        }

        :param variants: _description_
        :type variants: _type_
        """
        for variant in variants:
            item_id = self.gen_item_id(variant['backcountry_id'], variant['color'])
            insert_dict = dict(
                id=item_id,
                backcountry_id=variant['backcountry_id'],
                name=variant['item_name'],
                url=variant['item_url'],
                brand=variant['brand'],
                gender=variant['gender'],
                color=variant['color'], 
            )
            where_list = [Item.id == item_id]
            self.upsert(Item, insert_dict, where_list)
            
            for size in variant['price'].keys():
                insert_dict = {'size': size}
                where_list = [Size.size == size]
                size_id = self.upsert(Size, insert_dict, where_list, True)

                price_value = variant['price'][size]
                insert_dict = dict(
                    item_id=item_id,
                    size_id=size_id,
                    price=price_value,
                )
                where_list = [
                    Price.item_id == item_id,
                    Price.size_id == size_id,
                ]
                self.upsert(Price, insert_dict, where_list)

                onhand_value = variant['onhand'][size]
                insert_dict = dict(
                    item_id=item_id,
                    size_id=size_id,
                    onhand=onhand_value,
                )
                where_list = [
                    Onhand.item_id == item_id,
                    Onhand.size_id == size_id,
                ]
                self.upsert(Onhand, insert_dict, where_list)

            for spec in variant['tech_specs'].keys():
                insert_dict = {'value': spec}
                where_list = [Spec.value == spec]
                spec_id = self.upsert(Spec, insert_dict, where_list, True)

                tech_spec_value = variant['tech_specs'][spec]
                insert_dict = dict(
                    item_id=item_id,
                    spec_id=spec_id,
                    value=tech_spec_value,
                )
                where_list = [
                    TechSpec.item_id == item_id,
                    TechSpec.spec_id == spec_id,
                    TechSpec.value == tech_spec_value,
                ]
                self.upsert(TechSpec, insert_dict, where_list)

            for category in variant['category']:
                insert_dict = dict(item_id=item_id, value=category)
                where_list = [Category.item_id == item_id, Category.value == category]
                self.upsert(Category, insert_dict, where_list)

            for photo in variant['item_photos']+variant['sub_item_photos']:
                insert_dict = dict(item_id=item_id, url=photo)
                where_list = [Photo.item_id == item_id, Photo.url == photo]
                self.upsert(Photo, insert_dict, where_list)
            
            for p_spec in variant['product_specifications']:
                insert_dict = dict(item_id=item_id, value=p_spec)
                where_list = [
                    ProductSpecification.item_id == item_id,
                    ProductSpecification.value == p_spec,
                ]
                self.upsert(ProductSpecification, insert_dict, where_list)

    def load(self, products_list):
        pass
