import hashlib
import logging
import datetime
import time

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

            t1 = time.time()
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
            t2 = time.time()
            print(f"item done: took {t2 - t1}s")

            # Photo
            t1 = time.time()
            db_photo = (
                self.session.query(Photo.url)
                .filter(Photo.item_id == product_id)
                .all()
            )
            if db_photo:
                db_photo = [x[0] for x in db_photo]
            product['item_photo'] = list(set(product['item_photo']))
            for photo in product['item_photo']:
                if photo not in db_photo:
                    p = Photo(item_id=product_id, url=photo)
                    self.session.add(p)
                else:
                    self.session.query(Photo).filter(
                        Photo.item_id == product_id, Photo.url == photo
                    ).update({"edited": datetime.datetime.now(datetime.timezone.utc)},
                    synchronize_session=False)
                self.session.commit()
            t2 = time.time()
            print(f"photo done: took {t2 - t1}s")

            # WidthSize
            t1 = time.time()
            db_width_size = (
                self.session.query(WidthSize.size)
                .all()
            )
            if db_width_size:
                db_width_size = [x[0] for x in db_width_size]
            for width in product['width'].keys():
                if width not in db_width_size:
                    w = WidthSize(size=width)
                    self.session.add(w)
                else:
                    self.session.query(WidthSize).filter(
                        WidthSize.size == width
                    ).update({"edited": datetime.datetime.now(datetime.timezone.utc)},
                    synchronize_session=False)
                self.session.commit()
            t2 = time.time()
            print(f"width_size done: took {t2 - t1}s")

            # Width
            t1 = time.time()
            db_width_size = (
                self.session.query(WidthSize.id, WidthSize.size)
                .all()
            )
            if db_width_size:
                # size : id
                db_width_size = {x[1]:x[0] for x in db_width_size}
 
            db_width = (
                self.session
                .query(Width.id, WidthSize.id, WidthSize.size)
                .filter(Width.width_size_id == WidthSize.id)
                .filter(Width.item_id == product_id)
                .all()
            )

            for width in product['width'].keys():
                record = [x for x in db_width if x[2] == width]
                if not record:
                    insert_sql = f'''INSERT IGNORE into zappos.width (item_id, width_size_id) VALUES ("{product_id}","{db_width_size[width]}");'''
                    self.session.execute(insert_sql)
                else:
                    self.session.query(Width).filter(
                        Width.id == record[0][0] 
                    ).update({"edited": datetime.datetime.now(datetime.timezone.utc)},
                    synchronize_session=False)
                self.session.commit()
            t2 = time.time()
            print(f"width done: took {t2 - t1}s")

            # Size
            t1 = time.time()
            db_width = (
                self.session
                .query(Width.id, WidthSize.size)
                .filter(Width.width_size_id == WidthSize.id)
                .filter(Width.item_id == product_id)
                .all()
            )
            if db_width:
                #  size : width id
                db_width_dict = {x[1]:x[0] for x in db_width}
            t2 = time.time()
            print(f"size: db_width read done: took {t2 - t1}s")
            
            t1 = time.time()
            db_size = (
                self.session
                .query(Size.id, Size.size, Width.id)
                .filter(Size.width_id == Width.id)
                .filter(Width.item_id == product_id)
                .all()
            )
            t2 = time.time()
            print(f"size: db_size read done {len(db_size)} rows: took {t2 - t1}s")

            t1 = time.time()
            for width, info in product['width'].items():
                width_id = db_width_dict[width]
                for size in info['price'].keys():
                    asin = info['asin'][size]
                    onhand = info['onhand'][size]
                    price = self.nb_str_processing(info['price'][size])
                    size = self.remove_error_chars(size)

                    record = [x for x in db_size if x[1] == size]
                    if not record:
                        insert_sql = f'''INSERT INTO zappos.size (width_id, size, price, onhand, asin) 
                        VALUES ({width_id}, "{size}", {price}, {onhand}, "{asin}");'''
                        self.session.execute(insert_sql)
                    else:
                        self.session.query(Size).filter(
                            Size.id == record[0][0]
                        ).update({
                            "asin": asin,
                            "price": price,
                            "onhand": onhand,
                            "edited": datetime.datetime.now(datetime.timezone.utc)
                        }, synchronize_session=False)
                    self.session.commit()
            t2 = time.time()
            print(f"size done: took {t2 - t1}s")

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
                    ).update({"edited": datetime.datetime.now(datetime.timezone.utc)},
                    synchronize_session=False)
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
                    },
                    synchronize_session=False
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

    def remove_error_chars(self, input_str):
        if input_str:
            return input_str.replace('"', '').replace("'", "")

    def nb_str_processing(self, input_str):
        if input_str:
            return input_str.replace(',', '')  # 1,050 -> 1000