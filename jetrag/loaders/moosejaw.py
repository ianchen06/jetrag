import uuid
import logging
import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import boto3

from models.moosejaw import *

logger = logging.getLogger(__name__)

class MoosejawLoader:
    def __init__(self, cfg, raw_store, dt):
        self.boto_client = boto3.client(
            'rds-data', 
            aws_access_key_id=cfg['aws_access_key_id'], 
            aws_secret_access_key=cfg['aws_secret_access_key'], 
            region_name='ap-northeast-1'
        )
        self.connect_args = cfg['connect_args']
        self.connect_args['rds_data_client'] = self.boto_client
        self.engine = create_engine(
            cfg['conn_str']+'/moosejaw', 
            connect_args=self.connect_args)
        self.session = Session(self.engine)
        self.raw_store = raw_store
        self.dt = dt

    def get(self):
        return self.raw_store.list(f'moosejaw/{self.dt}')

    def gen_item_id(self, item_code, color):
        return uuid.uuid3(
            uuid.UUID("850aeee8-e173-4da1-9d6b-dd06e4b06747"),
            f"{item_code}{color}"
        ).hex[:17]

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
        seen_product_id = {}
        for variant in variants:
            product_color = variant['color'].lower()
            product_id = self.gen_item_id(variant['item_code'], product_color)
            if product_id in seen_product_id:
                continue
            seen_product_id[product_id] = 1

            # insert Item, ProductSpecification, Category, Photo

            # Item
            item = Item(
                        id=product_id,
                        item_code=variant['item_code'],
                        item_name=variant['item_name'],
                        item_url=variant['item_url'],
                        color=product_color
                    )
            self.session.add(item)
            try:
                self.session.flush()
            except Exception as e:
                if 'Duplicate' in str(e):
                    self.session.rollback()
                    self.session.query(Item).filter(Item.id == product_id).update({
                        'item_name': variant['item_name'],
                        'item_url': variant['item_url'],
                        'edited': datetime.datetime.now(datetime.timezone.utc)
                    }, synchronize_session=False)
            self.session.commit()

            # ProductSpecification
            product_spec = ProductSpecification(
                item_id=product_id,
                value=variant['product_specifications']
            )
            self.session.add(product_spec)
            try:
                self.session.flush()
            except Exception as e:
                if 'Duplicate' in str(e):
                    self.session.query(ProductSpecification).filter(
                        ProductSpecification.item_id == product_id
                    ).update({
                        'item_id': product_id,
                        'value': variant['product_specifications'],
                        'edited': datetime.datetime.now(datetime.timezone.utc)
                    }, synchronize_session=False)
            self.session.commit()
            
            # Category
            db_category = self.session.query(Category.value).filter(Category.item_id == product_id).all()
            if db_category:
                db_category = [x[0] for x in db_category]
            for category in variant['category']:
                if category not in db_category:    
                    c = Category(
                        item_id=product_id,
                        value=category
                    )
                    self.session.add(c)
                else:
                    self.session.query(
                        Category
                    ).filter(
                        Category.item_id == product_id,
                        Category.value == category
                    ).update({
                        'edited': datetime.datetime.now(datetime.timezone.utc)
                    })
                self.session.commit()

            # Photo
            db_photo = self.session.query(Photo.url).filter(Photo.item_id == product_id).all()
            if db_photo:
                db_photo = [x[0] for x in db_photo]
            for photo in variant['item_photo']:
                if photo not in db_photo:    
                    p = Photo(
                        item_id=product_id,
                        url=photo
                    )
                    self.session.add(p)
                else:
                    self.session.query(
                        Photo
                    ).filter(
                        Photo.item_id == product_id,
                        Photo.url == photo
                    ).update({
                        'edited': datetime.datetime.now(datetime.timezone.utc)
                    })
                self.session.commit()

            # Size
            size = variant['item_no'].lower()
            s = Size(
                item_id=product_id,
                size=variant['size'],
                item_no=size,
                price=variant['price']
            )
            self.session.add(s)
            try:
                self.session.flush()
            except Exception as e:
                if 'Duplicate' in str(e):
                    self.session.rollback()
                    self.session.query(
                        Size
                    ).filter(
                        Size.item_id == product_id,
                        Size.size == size
                    ).update({
                        'size': size,
                        'item_no': variant['item_no'],
                        'price': variant['price'],
                        'edited': datetime.datetime.now(datetime.timezone.utc)
                    }, synchronize_session=False)
            self.session.commit()


    def load(self, products_list):
        done = {}
        to_insert = []
        for products in products_list:
            seen_size = {}
            for product in products:
                product_color = product['color'].lower()
                product_id = uuid.uuid3(
                    uuid.UUID("850aeee8-e173-4da1-9d6b-dd06e4b06747"),
                    f"{product['item_code']}{product_color}"
                ).hex[:17]
                if not product_id in done:
                    done[product_id] = 1
                    item = Item(
                        id=product_id,
                        item_code=product['item_code'],
                        item_name=product['item_name'],
                        item_url=product['item_url'],
                        color=product_color
                    )
                    try:
                        self.session.add(item)
                        self.session.flush()
                    except Exception as e:
                        self.session.rollback()
                        logger.error(f"{e}")
                        for row in to_insert:
                            logger.error(row.__dict__)
                        raise(e)
                    product_spec = ProductSpecification(
                        item_id=product_id,
                        value=product['product_specifications']
                    )
                    to_insert.append(product_spec)
                    for category in product['category']:
                        c = Category(
                            item_id=product_id,
                            value=category
                        )
                        to_insert.append(c)
                    for photo in product['item_photo']:
                        p = Photo(
                            item_id=product_id,
                            url=photo
                        )
                        to_insert.append(p)
                k = f"{product_id}_{product['size']}"
                if k in seen_size:
                    seen_size[k] += 1
                    logger.info(products)
                else:
                    seen_size[k] = 1
                s = Size(
                    item_id=product_id,
                    size=product['size'],
                    item_no=product['item_no'],
                    price=product['price']
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
            raise(e)
