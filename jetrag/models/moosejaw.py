# coding: utf-8
from sqlalchemy import Column, DECIMAL, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class Item(Base):
    __tablename__ = 'item'
    __table_args__ = (
        Index('item_code color unique constraint', 'item_code', 'color', unique=True),
    )

    id = Column(String(17), primary_key=True)
    item_code = Column(INTEGER(11), nullable=False)
    item_name = Column(String(256), nullable=False)
    item_url = Column(String(512), nullable=False)
    color = Column(String(50), nullable=False)
    edited = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    created = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class Category(Base):
    __tablename__ = 'category'
    __table_args__ = (
        Index('item_id value unique constraint', 'item_id', 'value', unique=True),
    )

    id = Column(INTEGER(11), primary_key=True)
    item_id = Column(ForeignKey('item.id', ondelete='CASCADE'), nullable=False)
    value = Column(String(256), nullable=False)
    edited = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    created = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    item = relationship('Item')


class Photo(Base):
    __tablename__ = 'photo'
    __table_args__ = (
        Index('item_id value unique constraint', 'item_id', 'url', unique=True),
    )

    id = Column(INTEGER(11), primary_key=True)
    item_id = Column(ForeignKey('item.id', ondelete='CASCADE'), nullable=False)
    url = Column(String(512), nullable=False)
    edited = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    created = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    item = relationship('Item')


class ProductSpecification(Base):
    __tablename__ = 'product_specification'

    id = Column(INTEGER(11), primary_key=True)
    item_id = Column(ForeignKey('item.id', ondelete='CASCADE'), nullable=False, index=True)
    value = Column(Text, nullable=False)
    edited = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    created = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    item = relationship('Item')


class Size(Base):
    __tablename__ = 'size'
    __table_args__ = (
        Index('item_id size unique constraint', 'item_id', 'size', unique=True),
    )

    id = Column(INTEGER(11), primary_key=True)
    item_id = Column(ForeignKey('item.id', ondelete='CASCADE'), nullable=False)
    size = Column(String(128), nullable=False)
    item_no = Column(INTEGER(11), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    edited = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    created = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    item = relationship('Item')
