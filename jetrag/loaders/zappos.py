import uuid
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
        return uuid.uuid3(
            uuid.UUID("850aeee8-e173-4da1-9d6b-dd06e4b06747"), f"{item_code}{color}"
        ).hex[:17]

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
        done = {}
        to_insert = []
        for products in products_list:
            seen_size = {}
            for product in products:
                product_color = product["color"].lower()
                product_id = uuid.uuid3(
                    uuid.UUID("850aeee8-e173-4da1-9d6b-dd06e4b06747"),
                    f"{product['item_code']}{product_color}",
                ).hex[:17]
                if not product_id in done:
                    done[product_id] = 1
                    item = Item(
                        id=product_id,
                        item_code=product["item_code"],
                        item_name=product["item_name"],
                        item_url=product["item_url"],
                        color=product_color,
                    )
                    try:
                        self.session.add(item)
                        self.session.flush()
                    except Exception as e:
                        self.session.rollback()
                        logger.error(f"{e}")
                        for row in to_insert:
                            logger.error(row.__dict__)
                        raise (e)
                    product_spec = ProductSpecification(
                        item_id=product_id, value=product["product_specifications"]
                    )
                    to_insert.append(product_spec)
                    for category in product["category"]:
                        c = Category(item_id=product_id, value=category)
                        to_insert.append(c)
                    for photo in product["item_photo"]:
                        p = Photo(item_id=product_id, url=photo)
                        to_insert.append(p)
                k = f"{product_id}_{product['size']}"
                if k in seen_size:
                    seen_size[k] += 1
                    logger.info(products)
                else:
                    seen_size[k] = 1
                s = Size(
                    item_id=product_id,
                    size=product["size"],
                    item_no=product["item_no"],
                    price=product["price"],
                )
                to_insert.append(s)
        logger.info(f"add_all {len(to_insert)}")
        self.session.add_all(to_insert)
        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            logger.error(f"{e}")
            for row in to_insert:
                logger.error(row.__dict__)
            raise (e)
