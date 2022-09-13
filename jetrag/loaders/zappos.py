import hashlib
import logging
import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import boto3

from models.zappos import *

logger = logging.getLogger(__name__)


class ZapposLoader:
    def __init__(self, cfg, raw_store, dt, debug=False):
        self.boto_client = boto3.client(
            "rds-data",
            aws_access_key_id=cfg["aws_access_key_id"],
            aws_secret_access_key=cfg["aws_secret_access_key"],
            region_name="ap-northeast-1",
        )
        self.connect_args = cfg["connect_args"]
        self.connect_args["rds_data_client"] = self.boto_client
        self.engine = create_engine(
            cfg["conn_str"] + "/zappos", connect_args=self.connect_args, echo=debug
        )
        self.session = Session(self.engine)
        self.raw_store = raw_store
        self.dt = dt

    def get(self):
        return self.raw_store.list(f"zappos/{self.dt}")

    def cleanup(self, before_dt):
        logger.info(f"cleanup before {before_dt}")
        tables = [
            Item,
            WidthSize,
            Category,
            Photo,
            ProductSpecification,
            Width,
            Size
        ]
        for table in tables:
            res = (
                self.session.query(table)
                .filter(table.edited < before_dt)
                .delete(synchronize_session=False)
            )
            print(res)
            self.session.commit()

    def gen_item_id(self, item_code, color):
        input_ = f"{item_code}_{color}".encode('utf-8')
        hash_func = hashlib.shake_256()
        hash_func.update(input_)
        return hash_func.hexdigest(8)

    def load_update(self, products):
        for product in products:
            product_id = self.gen_item_id(product['zappos_id'], product['color'])
            item = Item(
                id=product_id,
                model=product['zappos_id'],
                name=product['item_name'],
                url=product['item_url'],
                brand=product['brand'],
                gender=product['gender'],
                color=product['color']
            )
            self.session.add(item)
            try:
                self.session.flush()
            except Exception as e:
                if "Duplicate" in str(e):
                    self.session.rollback()
                    (
                        self.session
                        .query(Item)
                        .filter(Item.id == product_id)
                        .update(
                            {
                                "edited": datetime.datetime.now(datetime.timezone.utc),
                            },
                            synchronize_session=False
                        )
                    )
                else:
                    raise e
            self.session.commit()

            # Category
            db_category = (
                self.session.query(Category.value)
                .filter(Category.item_id == product_id)
                .all()
            )
            if db_category:
                db_category = [x[0] for x in db_category]
            for category in product["category"]:
                if category not in db_category:
                    c = Category(item_id=product_id, value=category)
                    self.session.add(c)
                else:
                    self.session.query(Category).filter(
                        Category.item_id == product_id, Category.value == category
                    ).update({"edited": datetime.datetime.now(datetime.timezone.utc)})
                self.session.commit()

            # ProductSpecification
            db_product_spec = (
                self.session.query(ProductSpecification)
                .filter(ProductSpecification.item_id == product_id)
                .all()
            )
            if db_product_spec:
                # update
                self.session.query(ProductSpecification).filter(
                    ProductSpecification.item_id == product_id
                ).update(
                    {
                        "value": product["product_specifications"],
                        "edited": datetime.datetime.now(datetime.timezone.utc),
                    }
                )
            else:
                # add
                ps = ProductSpecification(
                    item_id=product_id, value=product["product_specifications"]
                )
                self.session.add(ps)
            self.session.commit()

    def load(self, products_list):
        raise Exception('Not implemented, please use load_update')
