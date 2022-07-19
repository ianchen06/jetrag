# coding: utf-8
from sqlalchemy import Column, DECIMAL, DateTime, String, Text, text
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class Item(Base):
    __tablename__ = 'item'

    id = Column(String(17), primary_key=True)
    item_code = Column(INTEGER(11), nullable=False)
    item_name = Column(String(256), nullable=False)
    item_url = Column(String(512), nullable=False)
    color = Column(String(50), nullable=False)
    edited = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    created = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class Category(Base):
    __tablename__ = 'category'

    id = Column(INTEGER(11), primary_key=True)
    item_id = Column(String(17), nullable=False)
    value = Column(String(256), nullable=False)
    edited = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    created = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class Photo(Base):
    __tablename__ = 'photo'

    id = Column(INTEGER(11), primary_key=True)
    item_id = Column(String(17), nullable=False)
    url = Column(String(512), nullable=False)
    edited = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    created = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class ProductSpecification(Base):
    __tablename__ = 'product_specification'

    id = Column(INTEGER(11), primary_key=True)
    item_id = Column(String(17), nullable=False)
    value = Column(Text, nullable=False)
    edited = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    created = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class Size(Base):
    __tablename__ = 'size'

    id = Column(INTEGER(11), primary_key=True)
    item_id = Column(String(17), nullable=False)
    size = Column(String(128), nullable=False)
    item_no = Column(INTEGER(11), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    edited = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    created = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
