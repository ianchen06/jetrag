import uuid
import logging
import datetime
import hashlib
import time

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import boto3

# For MySQL upsert
from sqlalchemy import update, select

from models.moosejaw import *

logger = logging.getLogger(__name__)


class MoosejawLoader:
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
            cfg["conn_str"] + "/moosejaw", connect_args=self.connect_args, echo=debug
        )
        self.session = Session(self.engine)
        self.raw_store = raw_store
        self.dt = dt

    def get(self):
        return self.raw_store.list(f"moosejaw/{self.dt}")

    def cleanup(self, before_dt):
        logger.info(f"cleanup before {before_dt}")
        tables = [Item, Category, Photo, Size, ProductSpecification]
        for table in tables:
            res = (
                self.session.query(table)
                .filter(table.edited < before_dt)
                .delete(synchronize_session=False)
            )
            self.session.commit()

    # TODO: refactor into common lib
    def upsert(self, model, insert_dict, where_list, fetch=False):
        t1 = time.time()
        inserted = model(**insert_dict)
        to_update = False
        try:
            self.session.add(inserted)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            if 'Duplicate entry' not in str(e):
                raise Exception(f"error inserting, model:{model}, data: {insert_dict}") from e
            to_update = True
        
        if to_update:
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

        t2 = time.time()
        logger.info(f'to_update: {to_update}, time: {t2-t1}, model: {model}, insert: {insert_dict}')
        if not fetch:
            return
        stmt = select(model.id).where(*where_list)
        row = self.session.execute(stmt).first()
        return row[0]

    def gen_item_id(self, item_code, color):
        input_ = f"{item_code}_{color}".encode('utf-8')
        hash_func = hashlib.shake_256()
        hash_func.update(input_)
        return hash_func.hexdigest(8)

    def load_update(self, variants):
        """load one product (all variants) into db

        {'color': 'Deep Heather',
         'size': 'Small',
         'item_no': '6772822',
         'category': ['Womens Outerwear',
                      'Womens Jackets',
                      'Womens Insulated Jackets',
                      'Womens Down Jackets'],
         'item_url': 'https://www.moosejaw.com/product/rab-women-s-cubit-stretch-down-hoody_10537936',
        'item_name': "Rab Women's Cubit Stretch Down Hoody",
        'item_code': '10537936',
        'price': '299.95',
        'item_photo': ['https://s7d1.scene7.com/is/image/MoosejawMB/10537936x1087290_zm?$product1000$',
                       'https://s7d1.scene7.com/is/image/MoosejawMB/10537936x1085886_vAlt4?$product700$',
                       'https://s7d1.scene7.com/is/image/MoosejawMB/10537936x1085886_vAlt1?$product700$',
                       'https://s7d1.scene7.com/is/image/MoosejawMB/10537936x1085886_vAlt2?$product700$',
                       'https://s7d1.scene7.com/is/image/MoosejawMB/10537936x1085886_vAlt3?$product700$'],
        'product_specifications': '{"Fit Type:": "Slim Fit", "Sleeve Length:": "Long Sleeve"}'}

        :param product: list of all variants
        :type product: list
        """
        for variant in variants:
            item_id = self.gen_item_id(variant["item_code"], variant["color"])

            # insert Item, ProductSpecification, Category, Photo

            # Item
            insert_dict = dict(
                id=item_id,
                brand=variant["brand"],
                item_code=variant["item_code"],
                item_name=variant["item_name"],
                item_url=variant["item_url"],
                color=variant["color"],            )
            where_list = [Item.id == item_id]
            self.upsert(Item, insert_dict, where_list)

            # ProductSpecification
            insert_dict = dict(
                item_id=item_id,
                value=variant["product_specifications"]
            )
            where_list = [
                ProductSpecification.item_id == item_id,
                ProductSpecification.value == variant["product_specifications"],
            ]
            self.upsert(ProductSpecification, insert_dict, where_list)

            # Category
            for category in variant["category"]:
                insert_dict = dict(
                    item_id=item_id,
                    value=category
                )
                where_list = [
                    Category.item_id == item_id,
                    Category.value == category,
                ]
                self.upsert(Category, insert_dict, where_list)

            # Photo
            for photo in variant["item_photo"]:
                insert_dict = dict(
                    item_id=item_id,
                    url=photo
                )
                where_list = [
                    Photo.item_id == item_id,
                    Photo.url == photo
                ]
                self.upsert(Photo, insert_dict, where_list)

            # Size
            for row in variant['size']:
                insert_dict = dict(
                    item_id=item_id,
                    size=row['size'],
                    item_no=row["item_no"],
                    price=row["price"],
                )
                where_list = [
                    Size.item_id == item_id,
                    Size.size == row['size']
                ]
                self.upsert(Size, insert_dict, where_list)

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
