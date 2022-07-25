import uuid
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models.moosejaw import *

logger = logging.getLogger(__name__)

class MoosejawLoader:
    def __init__(self, conn_str, db, dt):
        self.engine = create_engine(conn_str)
        self.session = Session(self.engine)
        self.db = db
        self.dt = dt

    def get(self):
        return self.db.list(f'moosejaw/{self.dt}')

    def load(self, products_list):
        done = {}
        to_insert = []
        for products in products_list:
            seen_size = {}
            for product in products:
                product_id = uuid.uuid3(
                    uuid.UUID("850aeee8-e173-4da1-9d6b-dd06e4b06747"),
                    f"{product['item_code']}{product['color']}"
                ).hex[:17]
                if not product_id in done:
                    done[product_id] = 1
                    item = Item(
                        id=product_id,
                        item_code=product['item_code'],
                        item_name=product['item_name'],
                        item_url=product['item_url'],
                        color=product['color']
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
