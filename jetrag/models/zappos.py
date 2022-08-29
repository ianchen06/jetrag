# coding: utf-8
from sqlalchemy import Column, DECIMAL, DateTime, String, Text, text
from sqlalchemy.dialects.mysql import INTEGER, TINYINT
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class Item(Base):
    __tablename__ = 'item'

    id = Column(String(17), primary_key=True)
    model = Column(String(20), nullable=False)
    name = Column(String(256), nullable=False)
    url = Column(String(512), nullable=False)
    brand = Column(String(50), nullable=False)
    gender = Column(String(10), nullable=False)
    color = Column(String(50), nullable=False)
    active = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    edited = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    created = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class WidthSize(Base):
    __tablename__ = 'width_size'

    id = Column(INTEGER(11), primary_key=True)
    size = Column(String(64), nullable=False)
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


class Width(Base):
    __tablename__ = 'width'

    id = Column(INTEGER(11), primary_key=True)
    item_id = Column(String(17), nullable=False)
    width_size_id = Column(INTEGER(11), nullable=False)
    edited = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    created = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class Size(Base):
    __tablename__ = 'size'

    id = Column(INTEGER(11), primary_key=True)
    width_id = Column(INTEGER(11), nullable=False)
    size = Column(String(128), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    onhand = Column(INTEGER(11), nullable=False)
    asin = Column(String(20), nullable=False)
    edited = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    created = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
