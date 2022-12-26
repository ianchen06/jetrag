import logging
import datetime
import hashlib
import time

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# For MySQL upsert
from sqlalchemy import func
from sqlalchemy import insert, update, select, text

import boto3

from models.sierra import *

logger = logging.getLogger(__name__)


class SierraLoader:
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
            cfg["conn_str"] + "/sierra", connect_args=self.connect_args, echo=debug
        )
        self.session = Session(self.engine)
        self.raw_store = raw_store
        self.dt = dt

    def get(self):
        return self.raw_store.list(f"sierra/{self.dt}")

    def cleanup(self, before_dt):
        logger.info(f"cleanup before {before_dt}")
        tables = [
            Item,
            WidthSize,
            Category,
            Photo,
            ProductSpecification,
            Width,
            Size,
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

    def load_update(self, variants):
        """
        [
            {
                "item_name": "Dearfoams Jason Perforated Moccasins (For Men) - Save 38%",
                "brand": "Dearfoams",
                "sierra_id": "82rxt",
                "gender": "men",
                "category": [
                    "Shoes",
                    "Men's Shoes",
                    "Men's Slippers"
                ],
                "similar_items_more_information": [
                    [
                        "Dearfoams"
                    ],
                    [
                        "Shoes",
                        "Men's Shoes",
                        "Men's Slippers"
                    ]
                ],
                "product specifications": [
                    "Perforated fabric upper",
                    "Soft fabric lining",
                    "Moc toe",
                    "Memory foam cushioned footbed",
                    "Synthetic outsole",
                    "Imported"
                ],
                "color": "Black",
                "price": {
                    "L:Onesize": "$11.00",
                    "S:Onesize": "$11.00",
                    "M:Onesize": "$11.00",
                    "XL:Onesize": "$11.00"
                },
                "onhand": {
                    "L:Onesize": true,
                    "S:Onesize": true,
                    "M:Onesize": true,
                    "XL:Onesize": true
                },
                "item_photos": "https://i.stpost.com/dearfoams-jason-perforated-moccasins-for-men-in-black~p~82rxt_03~460.2.jpg",
                "sub_item_photos": [
                    "https://i.stpost.com/dearfoams-jason-perforated-moccasins-for-men~a~82rxt_2~460.2.jpg",
                    "https://i.stpost.com/dearfoams-jason-perforated-moccasins-for-men~a~82rxt_3~460.2.jpg",
                    "https://i.stpost.com/dearfoams-jason-perforated-moccasins-for-men~a~82rxt_4~460.2.jpg",
                    "https://i.stpost.com/dearfoams-jason-perforated-moccasins-for-men~a~82rxt_5~460.2.jpg",
                    "https://i.stpost.com/dearfoams-jason-perforated-moccasins-for-men~a~82rxt_6~460.2.jpg"
                ]
            }
        ]        

        :param variants: _description_
        :type variants: _type_
        """
        for variant in variants:
            logger.info(f'variant: {variant}')
            variant['color'] = variant['color'] if variant['color'] else 'none'
            item_id = self.gen_item_id(variant['sierra_id'], variant['color'])
            insert_dict = dict(
                id=item_id,
                sierra_id=variant['sierra_id'],
                item_name=variant['item_name'],
                url=variant['item_url'],
                brand=variant['brand'],
                gender=variant['gender'],
                color=variant['color'],
            )
            where_list = [Item.id == item_id]
            self.upsert(Item, insert_dict, where_list)
            
            width_sizes = [x.split(':')[1] for x in list(variant['price'].keys())]

            width_dict = {}
            for width_size in width_sizes:
                insert_dict = dict(
                    size=width_size,
                )
                where_list = [WidthSize.size == width_size]
                inserted_width_size_id = self.upsert(WidthSize, insert_dict, where_list, True)

                insert_dict = dict(
                    item_id=item_id,
                    width_size_id=inserted_width_size_id,
                )
                where_list = [
                    Width.item_id == item_id,
                    Width.width_size_id == inserted_width_size_id,
                ]
                inserted_width_id = self.upsert(Width, insert_dict, where_list, True)
                width_dict[width_size] = inserted_width_id

            for category in variant['category']:
                insert_dict = dict(
                    item_id=item_id,
                    value=category,
                )
                where_list = [
                    Category.item_id == item_id,
                    Category.value == category,
                ]
                self.upsert(Category, insert_dict, where_list)

            for spec in variant['product specifications']:
                insert_dict = dict(
                    item_id=item_id,
                    value=spec,
                )
                where_list = [
                    ProductSpecification.item_id == item_id,
                    ProductSpecification.value == spec,
                ]
                self.upsert(ProductSpecification, insert_dict, where_list)

            for size in variant['price'].keys():
                width = size.split(':')[1]
                size_value = size.split(':')[0]
                width_id = width_dict[width]
                insert_dict = dict(
                    width_id=width_id,
                    size=size_value,
                    price=float(variant['price'][size][1:]),
                )
                where_list = [
                    Size.width_id == width_id,
                    Size.size == size_value,
                ]
                self.upsert(Size, insert_dict, where_list)

            insert_dict = dict(
                item_id=item_id,
                url=variant['item_photos'],
                main=True
            )
            where_list = [
                Photo.item_id == item_id,
                Photo.url == variant['item_photos'],
            ]
            self.upsert(Photo, insert_dict, where_list)

            for sub_p in variant['sub_item_photos']:
                insert_dict = dict(
                    item_id=item_id,
                    url=sub_p,
                    main=False,
                )
                where_list = [
                    Photo.item_id == item_id,
                    Photo.url == sub_p,
                ]
                self.upsert(Photo, insert_dict, where_list)

    def load(self, products_list):
        pass
