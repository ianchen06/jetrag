# coding: utf-8
from sqlalchemy import Column, DECIMAL, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.mysql import INTEGER, TINYINT
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class Item(Base):
    __tablename__ = 'item'
    __table_args__ = (
        Index('model color unique constraint', 'sierra_id', 'color', unique=True),
    )

    id = Column(String(17), primary_key=True)
    sierra_id = Column(String(20), nullable=False)
    item_name = Column(String(255), nullable=False)
    url = Column(String(512), nullable=False)
    brand = Column(String(50), nullable=False)
    gender = Column(String(10), nullable=False)
    color = Column(String(128), nullable=False)
    active = Column(TINYINT(1), nullable=False, server_default=text("'1'"))
    edited = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    created = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class WidthSize(Base):
    __tablename__ = 'width_size'

    id = Column(INTEGER(11), primary_key=True)
    size = Column(String(64), nullable=False, unique=True)
    edited = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    created = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class Category(Base):
    __tablename__ = 'category'
    __table_args__ = (
        Index('item_id value unique constraint', 'item_id', 'value', unique=True),
    )

    id = Column(INTEGER(11), primary_key=True)
    item_id = Column(ForeignKey('item.id', ondelete='CASCADE'), nullable=False)
    value = Column(String(255), nullable=False)
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
    main = Column(TINYINT(1), nullable=False)
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


class Width(Base):
    __tablename__ = 'width'
    __table_args__ = (
        Index('item_id width_size_id unique constraint', 'item_id', 'width_size_id', unique=True),
    )

    id = Column(INTEGER(11), primary_key=True)
    item_id = Column(ForeignKey('item.id', ondelete='CASCADE'), nullable=False)
    width_size_id = Column(ForeignKey('width_size.id', ondelete='CASCADE'), nullable=False, index=True)
    edited = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    created = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    item = relationship('Item')
    width_size = relationship('WidthSize')


class Size(Base):
    __tablename__ = 'size'
    __table_args__ = (
        Index('width_id size unique constraint', 'width_id', 'size', unique=True),
    )

    id = Column(INTEGER(11), primary_key=True)
    width_id = Column(ForeignKey('width.id', ondelete='CASCADE'), nullable=False)
    size = Column(String(128), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    edited = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    created = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    width = relationship('Width')
