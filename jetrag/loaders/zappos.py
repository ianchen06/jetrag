import hashlib
import logging
import datetime
import time

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import boto3

from models.zappos import *
from loaders.base_loader import upsert

logger = logging.getLogger(__name__)


class ZapposLoader:
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
            self.session.commit()

    def gen_item_id(self, item_code, color):
        input_ = f"{item_code}_{color}".encode('utf-8')
        hash_func = hashlib.shake_256()
        hash_func.update(input_)
        return hash_func.hexdigest(8)

    def load_update_new(self, products):
        """
        {
            "zappos_id": "9515355",
            "brand": "Brooks",
            "item_name": "Brooks Ghost 14",
            "category": [
                "Shoes",
                "Sneakers & Athletic Shoes"
            ],
            "gender": "women",
            "product_specifications": [
                "Treat yourself to a brand new ride this season. Elevate your running experience with the Brooks\u00ae Ghost 14 running shoes! These road runners offer a smooth-as-silk ride with a form-fitting interior that keeps your feet cushioned and secure even after miles on the road.",
                "Predecessor: Ghost 13.",
                "Support Type: Neutral.",
                "Cushioning: High energizing cushioning.",
                "Surface: Road.",
                "Differential: 12mm.",
                "Open-engineered air mesh upper with 3D Fit Print technology that provides strategic stretch and structure to the upper.",
                "Traditional lace-up closure.",
                "Plush tongue and collar.",
                "Soft fabric lining for a great in-shoe feel.",
                "Removable foam insole for excellent underfoot comfort and support.",
                "DNA LOFT offers incredibly soft cushioning that now extends beyond the heel, allowing for an easy transition from landing to toe-off.",
                "BioMoGo DNA is a blend of earth-friendly BioMoGo and responsive Brooks DNA, and has a gender-friendly cushioning design, making for a dynamic ride.",
                "Flex grooves allow for more natural forefoot movement and fluidity.",
                "Soft blown rubber forefoot material supplies light cushioning and grip.",
                "APMA Approved: The American Podiatric Medical Association Seal of Acceptance is awarded to products that promote good foot health and are substantiated by a committee of discerning podiatrists by wear-testing and review of the application and supporting documentation. APMA Acceptance must be applied for and is not automatically available to styles that meet its criteria.",
                "PDAC A5500 Approved: Pricing, Data Analysis and Coding A5500 Diabetic Medicare Coding is awarded to footwear that is available in three or more widths, with a removable insole (sock-liner). It allows individuals to pay for their footwear through their Medicare. PDAC must be applied for on a yearly basis and is not automatically available to styles that meet its criteria. For more specific info, visit the Medicare website or call 1-800-MEDICARE. ",
                "Imported.",
                "Product measurements were taken using size 9, width B - Medium. Please note that measurements may vary by size.",
                "Weight of footwear is based on a single item, not a pair.",
                "Measurements:     Weight: 9 oz    "
            ],
            "color": "Peacoat/Yucca/Navy",
            "width": {
                "d_-_wide": {
                    "price": {
                        "5.5": "109.95",
                        "7": "109.95",
                        "7.5": "109.95",
                        "8": "109.95",
                        "8.5": "109.95",
                        "9": "109.95",
                        "9.5": "109.95",
                        "10": "109.95",
                        "11": "109.95",
                        "11.5": "109.95",
                        "12": "109.95",
                        "13": "109.95"
                    },
                    "onhand": {
                        "5.5": "1",
                        "7": "102",
                        "7.5": "133",
                        "8": "297",
                        "8.5": "352",
                        "9": "94",
                        "9.5": "204",
                        "10": "128",
                        "11": "77",
                        "11.5": "23",
                        "12": "1",
                        "13": "2"
                    },
                    "asin": {
                        "5.5": "B08QVFZNLM",
                        "7": "B08QTPZFPC",
                        "7.5": "B08QVD1SKD",
                        "8": "B08QTQW4ZZ",
                        "8.5": "B08QVCLT1B",
                        "9": "B08QV6VZJY",
                        "9.5": "B08QV3MQ9D",
                        "10": "B08QVNZDCJ",
                        "11": "B08QVQZN7J",
                        "11.5": "B08QV19S6B",
                        "12": "B08QTNRWZ4",
                        "13": "B094N78V6Q"
                    }
                },
                "b_-_medium": {
                    "price": {
                        "6": "109.95",
                        "6.5": "109.95",
                        "7": "109.95",
                        "7.5": "109.95",
                        "8": "109.95",
                        "8.5": "109.95",
                        "9": "109.95",
                        "9.5": "109.95",
                        "10": "109.95",
                        "11": "109.95",
                        "11.5": "109.95",
                        "12": "109.95"
                    },
                    "onhand": {
                        "6": "16",
                        "6.5": "30",
                        "7": "81",
                        "7.5": "280",
                        "8": "484",
                        "8.5": "952",
                        "9": "796",
                        "9.5": "637",
                        "10": "143",
                        "11": "25",
                        "11.5": "23",
                        "12": "15"
                    },
                    "asin": {
                        "6": "B08QTPFN6M",
                        "6.5": "B08QTT3L4L",
                        "7": "B08QV4QT2N",
                        "7.5": "B08QV1VPDR",
                        "8": "B08QTP65CG",
                        "8.5": "B08QTXCJW1",
                        "9": "B08QVNT9CQ",
                        "9.5": "B08QV4NBPW",
                        "10": "B08QVHQ54S",
                        "11": "B08QV49NCM",
                        "11.5": "B08QV66TM7",
                        "12": "B08QVGNXBW"
                    }
                },
                "2a_-_narrow": {
                    "price": {
                        "8.5": "109.95"
                    },
                    "onhand": {
                        "8.5": "3"
                    },
                    "asin": {
                        "8.5": "B08QV8PF3T"
                    }
                }
            },
            "item_photo_files": [
                "81zeWxGFVQS.jpg",
                "81YNz6pP9HS.jpg",
                "71tBDCMzHyS.jpg",
                "811RNwkmDLS.jpg",
                "714NJMCb9eS.jpg",
                "71LA2gI4amS.jpg"
            ],
            "item_photo": [
                "https://m.media-amazon.com/images/I/81zeWxGFVQS._AC_SR700,525_.jpg",
                "https://m.media-amazon.com/images/I/81YNz6pP9HS._AC_SR700,525_.jpg",
                "https://m.media-amazon.com/images/I/71tBDCMzHyS._AC_SR700,525_.jpg",
                "https://m.media-amazon.com/images/I/811RNwkmDLS._AC_SR700,525_.jpg",
                "https://m.media-amazon.com/images/I/714NJMCb9eS._AC_SR700,525_.jpg",
                "https://m.media-amazon.com/images/I/71LA2gI4amS._AC_SR700,525_.jpg"
            ],
            "item_url": "https://www.zappos.com/p/brooks-ghost-14/product/9515355"
        },

        :param products: _description_
        :type products: _type_
        """
        for product in products:
            product_id = self.gen_item_id(product['zappos_id'], product['color'])
            upsert(self.session, Item, dict(
                id=product_id,
                model=product['zappos_id'],
                name=product['item_name'],
                url=product['item_url'],
                brand=product['brand'],
                gender=product['gender'],
                color=product['color']
            ))
            self.session.commit()

            # Photo
            for photo in product['item_photo']:
                upsert(self.session, Photo, dict(
                    item_id=product_id,
                    url=photo,
                ))
            self.session.commit()

            # Category
            for category in product["category"]:
                upsert(self.session, Category, dict(
                    item_id=product_id,
                    value=category,
                ))
            self.session.commit()

            # Product Specification
            for p_spec in product["product_specifications"]:
                upsert(self.session, ProductSpecification, dict(
                    item_id=product_id,
                    value=p_spec
                ))
            self.session.commit()

            for width in product['width'].keys():
                width_size_id = upsert(self.session, WidthSize, dict(
                    size=width
                ))
                self.session.commit()
                width_id = upsert(self.session, Width, dict(
                    item_id=product_id,
                    width_size_id=width_size_id,
                ))
                self.session.commit()
                info = product['width'][width]
                for size in info['price'].keys():
                    asin = info['asin'][size]
                    onhand = info['onhand'][size]
                    price = self.nb_str_processing(info['price'][size])
                    size = self.remove_error_chars(size)
                    upsert(self.session, Size, dict(
                        width_id=width_id,
                        size=size,
                        price=price,
                        onhand=onhand,
                        asin=asin
                    ))
                    self.session.commit()

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
            logger.debug(f"item done: took {t2 - t1}s")

            # Photo
            t1 = time.time()
            db_photo = (
                self.session.query(Photo.url)
                .filter(Photo.item_id == product_id)
                .all()
            )
            if db_photo:
                db_photo = [x[0] for x in db_photo]
            for photo in product['item_photo']:
                if photo not in db_photo:
                    p = Photo(item_id=product_id, url=photo)
                    self.session.add(p)
                else:
                    self.session.query(Photo).filter(
                        Photo.item_id == product_id, Photo.url == photo
                    ).update({"edited": datetime.datetime.now(datetime.timezone.utc)},
                    synchronize_session=False)
                try:
                    self.session.commit()
                except Exception as e:
                    self.session.rollback()
                    if 'ER_DUP_ENTRY' not in str(e):
                        raise e
                    
            t2 = time.time()
            logger.debug(f"photo done: took {t2 - t1}s")

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
            logger.debug(f"width_size done: took {t2 - t1}s")

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
            logger.debug(f"width done: took {t2 - t1}s")

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
            logger.debug(f"size: db_width read done: took {t2 - t1}s")
            
            t1 = time.time()
            db_size = (
                self.session
                .query(Size.id, Size.size, Width.id)
                .filter(Size.width_id == Width.id)
                .filter(Width.item_id == product_id)
                .all()
            )
            t2 = time.time()
            logger.debug(f"size: db_size read done {len(db_size)} rows: took {t2 - t1}s")

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
            logger.debug(f"size done: took {t2 - t1}s")

            # Category
            db_category = (
                self.session.query(Category.value)
                .filter(Category.item_id == product_id)
                .all()
            )
            if db_category:
                db_category = [x[0] for x in db_category]
            for category in product["category"]:
                # Sometimes category is None
                if not category:
                    continue
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
            # TODO: maybe store id here
            db_product_spec = (
                self.session.query(ProductSpecification.value)
                .filter(ProductSpecification.item_id == product_id)
                .all()
            )
            # update
            for row in product["product_specifications"]:
                if row in [x[0] for x in db_product_spec]:
                    # TODO: use id from db_product_spec to filter
                    self.session.query(ProductSpecification).filter(
                        ProductSpecification.item_id == product_id,
                        ProductSpecification.value == row,
                    ).update(
                        {
                            "value": row,
                            "edited": datetime.datetime.now(datetime.timezone.utc),
                        },
                        synchronize_session=False
                    )
                else:
                    # add
                    ps = ProductSpecification(
                        item_id=product_id, value=row
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