from typing import Any
from sqlalchemy import (
    ForeignKey,
    Table,
    Column,
    Integer,
    String,
    DateTime,
    DECIMAL,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def to_dict(model: Base) -> dict[str, Any]:
    return {
        column.name: getattr(model, column.name) for column in model.__table__.columns
    }


class AssetClassEntity(Base):
    __tablename__ = "asset_classes"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    # One-to-Many (One AssetClass to Many Assets)
    assets = relationship("AssetEntity", back_populates="asset_class")


class CurrencyEntity(Base):
    __tablename__ = "currencies"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    # # Many-to-Many relationship with AssetEntity through asset_symbol_currency
    # assets = relationship("SymbolCurrencyEntity", back_populates="currencies")

    # One-to-Many relationship with SymbolCurrencyEntity
    symbols = relationship("SymbolCurrencyEntity", back_populates="currency")


# class ForexEntity(Base):
#     __tablename__ = "forex"

#     identifier = Column(String, primary_key=True)
#     from_currency = Column(String, nullable=False)
#     to_currency = Column(String, nullable=False)

#     def __init__(self, from_currency, to_currency):
#         self.from_currency = from_currency
#         self.to_currency = to_currency
#         self.identifier = f"{from_currency}{to_currency}"


class SymbolCurrencyEntity(Base):
    __tablename__ = "symbol_currency"
    symbol = Column(String, primary_key=True)  # Symbol für API-Aufrufe
    asset_id = Column(Integer, ForeignKey("assets.id"), primary_key=True)
    currency_id = Column(Integer, ForeignKey("currencies.id"), primary_key=True)
    # exchange_id = Column(Integer, ForeignKey("exchanges.id"), nullable=True)

    asset = relationship("AssetEntity", back_populates="symbols")  # Many-to-One
    currency = relationship("CurrencyEntity", back_populates="symbols")  # Many-to-One
    # exchange = relationship("ExchangeEntity", back_populates="symbols")


class AssetEntity(Base):
    __tablename__ = "assets"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    identifier = Column(String, unique=True, nullable=False)

    asset_class_id = Column(Integer, ForeignKey("asset_classes.id"), nullable=False)
    asset_class = relationship("AssetClassEntity", back_populates="assets")

    symbols = relationship("SymbolCurrencyEntity", back_populates="asset")
    # Many-to-Many relationship with CurrencyEntity through asset_symbol_currency
    # currencies = relationship(
    #     "CurrencyEntity", secondary=asset_symbol_currency, back_populates="assets"
    # )


class TimeSeriesEntity(Base):

    __tablename__ = "time_series"

    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    currency_id = Column(Integer, ForeignKey("currencies.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(DECIMAL)
    high = Column(DECIMAL)
    low = Column(DECIMAL)
    close = Column(DECIMAL)

    # Beziehungen zu Asset und Currency
    asset = relationship("AssetEntity")
    currency = relationship("CurrencyEntity")

    __table_args__ = (
        UniqueConstraint(
            "asset_id",
            "currency_id",
            "timestamp",
            name="unique_asset_currency_timestamp",
        ),
        Index(
            "idx_asset_timestamp", "asset_id", "timestamp"
        ),  # used for faster queries on asset_id and timestamp
    )


# class ExchangeEntity(Base):
#     __tablename__ = "exchanges"

#     id = Column(Integer, primary_key=True)
#     name = Column(String, unique=True, nullable=False)
#     symbols = relationship("SymbolCurrencyEntity", back_populates="exchange")
