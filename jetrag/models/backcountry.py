# coding: utf-8
from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, String, text
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class Item(Base):
    __tablename__ = 'item'
    __table_args__ = (
        Index('backcountry_id color unique constraint', 'backcountry_id', 'color', unique=True),
    )

    id = Column(String(17), primary_key=True)
    backcountry_id = Column(String(20), nullable=False)
    name = Column(String(255), nullable=False)
    url = Column(String(512), nullable=False)
    brand = Column(String(50), nullable=False)
    gender = Column(String(10), nullable=False)
    color = Column(String(128), nullable=False)
    edited = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    created = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class Size(Base):
    __tablename__ = 'size'

    id = Column(INTEGER(11), primary_key=True)
    size = Column(String(10), nullable=False, unique=True)
    edited = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    created = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class Spec(Base):
    __tablename__ = 'spec'

    id = Column(INTEGER(11), primary_key=True)
    value = Column(String(64), nullable=False, unique=True)
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


class Onhand(Base):
    __tablename__ = 'onhand'
    __table_args__ = (
        Index('item_id size_id unique constraint', 'item_id', 'size_id', unique=True),
    )

    id = Column(INTEGER(11), primary_key=True)
    item_id = Column(ForeignKey('item.id', ondelete='CASCADE'), nullable=False)
    size_id = Column(ForeignKey('size.id', ondelete='CASCADE'), nullable=False, index=True)
    onhand = Column(INTEGER(11), nullable=False)
    edited = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    created = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    item = relationship('Item')
    size = relationship('Size')


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


class Price(Base):
    __tablename__ = 'price'
    __table_args__ = (
        Index('item_id size_id unique constraint', 'item_id', 'size_id', unique=True),
    )

    id = Column(INTEGER(11), primary_key=True)
    item_id = Column(ForeignKey('item.id', ondelete='CASCADE'), nullable=False)
    size_id = Column(ForeignKey('size.id', ondelete='CASCADE'), nullable=False, index=True)
    price = Column(Float, nullable=False)
    edited = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    created = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    item = relationship('Item')
    size = relationship('Size')


class ProductSpecification(Base):
    __tablename__ = 'product_specification'
    __table_args__ = (
        Index('item_id value unique constraint', 'item_id', 'value', unique=True),
    )

    id = Column(INTEGER(11), primary_key=True)
    item_id = Column(ForeignKey('item.id', ondelete='CASCADE'), nullable=False)
    value = Column(String(255), nullable=False)
    edited = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    created = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    item = relationship('Item')


class TechSpec(Base):
    __tablename__ = 'tech_spec'
    __table_args__ = (
        Index('item_id spec_id unique constraint', 'item_id', 'spec_id', unique=True),
    )

    id = Column(INTEGER(11), primary_key=True)
    item_id = Column(ForeignKey('item.id', ondelete='CASCADE'), nullable=False)
    spec_id = Column(ForeignKey('spec.id', ondelete='CASCADE'), nullable=False, index=True)
    value = Column(String(255), nullable=False)
    edited = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    created = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    item = relationship('Item')
    spec = relationship('Spec')
