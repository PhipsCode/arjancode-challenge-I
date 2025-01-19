import decimal
from typing import Any, Sequence, Protocol
from datetime import datetime

from pydantic import BaseModel

from .exceptions import (
    AssetClassNotFound,
    AssetNotFound,
    CurrencyNotFound,
    TimeSeriesNotFound,
)

from .models import (
    AssetClassEntity,
    AssetEntity,
    CurrencyEntity,
    SymbolCurrencyEntity,
    TimeSeriesEntity,
)


class Database(Protocol):
    def add(self, instance: object, _warn: bool = True) -> None: ...

    def commit(self) -> None: ...

    def delete(self, instance: object) -> None: ...

    def query(self, model: type) -> Any: ...  # Updated to make `model` type explicit

    def refresh(self, instance: object) -> None: ...


class AssetClassCreateSpec(Protocol):
    name: str

    def model_dump(self) -> dict[str, Any]: ...


class CurrencyCreateSpec(Protocol):
    name: str

    def model_dump(self) -> dict[str, Any]: ...


class SymbolCurrencyMappingSpec(Protocol):
    symbol: str
    currency: str


# class SymbolCurrencyMappingCreateSpec(Protocol):
#     identifier: str
#     symbol: str
#     currency: str


class AssetCreateSpec(Protocol):
    name: str
    identifier: str

    @property
    def asset_class(self) -> AssetClassCreateSpec: ...

    @property
    def symbol_currency_mapping(self) -> Sequence[SymbolCurrencyMappingSpec]: ...

    def model_dump(self) -> dict[str, Any]: ...


class TimeSeriesCreateSpec(Protocol):
    identifier: str
    currency: str
    timestamp: datetime
    open: decimal.Decimal
    high: decimal.Decimal
    low: decimal.Decimal
    close: decimal.Decimal

    def model_dump(self) -> dict[str, Any]: ...


class AssetClass(BaseModel):
    name: str


class Currency(BaseModel):
    name: str


# more generic version of the below operations code could be like this:
# class EntryNotFound(Exception):
#     pass

# def get_db_entry_by_name[T: type](db: Database, model: T, name: str) -> T:
#     entry = db.query(model).filter_by(name=name).first()
#     if not entry:
#         raise model.__name__ + "NotFound" (f"{model.__name__} '{name}' not found")
#     return entry

# region Currency Operations


def get_currency(db: Database, name: str) -> CurrencyEntity:
    currency = db.query(CurrencyEntity).filter_by(name=name).first()
    if not currency:
        raise CurrencyNotFound(f"Currency '{name}' not found")
    return currency


def get_currencies(db: Database) -> list[CurrencyEntity]:
    currencies = db.query(CurrencyEntity).all()
    return currencies


def create_currency(db: Database, currency_data: CurrencyCreateSpec) -> CurrencyEntity:
    """
    Creates a new Currency in the database.
    """
    try:
        currency = get_currency(db, currency_data.name)
    except CurrencyNotFound:
        currency = CurrencyEntity(**currency_data.model_dump())
        db.add(currency)
        db.commit()
        db.refresh(currency)
    return currency


# endregion Currency Operations


# region Asset Class Operations


def get_asset_class(db: Database, name: str) -> AssetClassEntity:
    asset_class = db.query(AssetClassEntity).filter_by(name=name).first()
    if not asset_class:
        raise AssetClassNotFound(f"Asset Class '{name}' not found")
    return asset_class


def get_asset_classes(db: Database) -> list[AssetClassEntity]:
    asset_classes = db.query(AssetClassEntity).all()
    return asset_classes


def create_asset_class(
    db: Database, asset_class_data: AssetClassCreateSpec
) -> AssetClassEntity:
    """
    Creates a new AssetClass in the database.
    """
    try:
        asset_class = get_asset_class(db, asset_class_data.name)
    except AssetClassNotFound:
        asset_class = AssetClassEntity(**asset_class_data.model_dump())
        db.add(asset_class)
        db.commit()
        db.refresh(asset_class)
    return asset_class


# endregion Asset Class Operations

# region Asset Operations


def get_asset_by_identifier(db: Database, identifier: str) -> AssetEntity:
    asset = db.query(AssetEntity).filter_by(identifier=identifier).first()
    if not asset:
        raise AssetNotFound(f"No Asset with '{identifier}' found")
    return asset


def get_asset_by_symbol(db: Database, symbol: str) -> AssetEntity:
    asset = (
        db.query(AssetEntity)
        .join(SymbolCurrencyEntity)
        .filter(SymbolCurrencyEntity.symbol == symbol)
        .first()
    )
    if not asset:
        raise AssetNotFound(f"No Asset with '{symbol}' found")
    return asset


def get_assets(db: Database) -> list[AssetEntity]:
    assets = db.query(AssetEntity).all()
    return assets


def map_symbol_currency_to_asset(
    db: Database,
    asset: AssetEntity,
    symbol_currency_mapping: Sequence[SymbolCurrencyMappingSpec],
) -> AssetEntity:
    for mapping in symbol_currency_mapping:
        currency = create_currency(db, Currency(name=mapping.currency))
        symbol_currency = SymbolCurrencyEntity(
            symbol=mapping.symbol,
            asset_id=asset.id,
            currency_id=currency.id,
            asset=asset,
            currency=currency,
        )
        db.add(symbol_currency)

    db.commit()
    db.refresh(asset)
    return asset


def add_symbol_currency_mapping(
    db: Database,
    asset_identifier: str,
    symbol_currency_mapping: Sequence[SymbolCurrencyMappingSpec],
) -> AssetEntity:
    asset = get_asset_by_identifier(db, asset_identifier)
    map_symbol_currency_to_asset(db, asset, symbol_currency_mapping)
    return asset


def create_asset(db: Database, asset_data: AssetCreateSpec) -> AssetEntity:
    """
    Creates a new Asset in the database.
    """
    asset_class = create_asset_class(db, asset_data.asset_class)

    try:
        asset = get_asset_by_identifier(db, asset_data.identifier)
    except AssetNotFound:
        asset = AssetEntity(
            name=asset_data.name,
            identifier=asset_data.identifier,
            asset_class=asset_class,
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)

    if asset_data.symbol_currency_mapping:
        map_symbol_currency_to_asset(db, asset, asset_data.symbol_currency_mapping)

    return asset


# def map_symbol_and_currency_to_asset(
#     db: Database, asset_data: AssetCreateSpec
# ) -> AssetEntity:

#     asset = get_asset_by_identifier(db, asset_data.identifier)

#     for mapping in asset_data.symbol_currency_mapping:

#         existing_mapping = (
#             db.query(SymbolCurrencyEntity)
#             .filter(SymbolCurrencyEntity.symbol == mapping.symbol)
#             .first()
#         )
#         if existing_mapping:
#             continue

#         currency = create_currency(db, Currency(name=mapping.currency))
#         db.add(
#             SymbolCurrencyEntity(
#                 symbol=mapping.symbol, currency_id=currency.id, asset=asset
#             )
#         )
#     db.commit()
#     db.refresh(asset)
#     return asset


# endregion Asset Operations

# region Time Series Operations


def get_time_series_by_date(
    db: Database, asset: str, currency: str, date: datetime
) -> TimeSeriesEntity:
    time_series = (
        db.query(TimeSeriesEntity)
        .join(AssetEntity)
        .join(CurrencyEntity)
        .filter(
            AssetEntity.name == asset,
            CurrencyEntity.name == currency,
            TimeSeriesEntity.timestamp == date,
        )
        .first()
    )
    if not time_series:
        raise TimeSeriesNotFound(
            f"TimeSeries entry for '{asset}' and '{currency}' on '{date}' not found"
        )
    return time_series


def get_latest_time_series(db: Database, asset: str, currency: str) -> TimeSeriesEntity:
    time_series = (
        db.query(TimeSeriesEntity)
        .join(AssetEntity)
        .join(CurrencyEntity)
        .filter(AssetEntity.name == asset, CurrencyEntity.name == currency)
        .order_by(TimeSeriesEntity.timestamp.desc())
        .first()
    )
    if not time_series:
        raise TimeSeriesNotFound(
            f"TimeSeries entry for '{asset}' and '{currency}' not found"
        )
    return time_series


def get_all_time_series(
    db: Database, asset: str, currency: str
) -> list[TimeSeriesEntity]:
    time_series = (
        db.query(TimeSeriesEntity)
        .join(AssetEntity)
        .join(CurrencyEntity)
        .filter(AssetEntity.name == asset, CurrencyEntity.name == currency)
        .all()
    )
    if not time_series:
        raise TimeSeriesNotFound(
            f"TimeSeries entries for '{asset}' and '{currency}' not found"
        )
    return time_series


def add_time_series_data(
    db: Database, time_series_data: TimeSeriesCreateSpec
) -> TimeSeriesEntity:
    """
    Creates a new TimeSeries entry in the database.
    """
    asset = get_asset_class(db, time_series_data.asset)
    currency = get_currency(db, time_series_data.currency)

    try:
        time_series = get_time_series_by_date(
            db,
            time_series_data.asset,
            time_series_data.currency,
            time_series_data.timestamp,
        )
    except TimeSeriesNotFound:
        time_series = TimeSeriesEntity(
            asset_id=asset.id,
            currency_id=currency.id,
            timestamp=time_series_data.timestamp,
            open=time_series_data.open,
            high=time_series_data.high,
            low=time_series_data.low,
            close=time_series_data.close,
        )
        db.add(time_series)
        db.commit()
        db.refresh(time_series)
    return time_series


# endregion Time Series Operations

# # special operations

# def add_new_asset_data(db: Database, time_series_dataset: Sequence[TimeSeriesCreate]) -> None:

#     if not time_series_dataset:
#         return

#     asset_name = time_series_dataset[0].asset
#     currency_name = time_series_dataset[0].currency

#     try:
#         time_series_data = get_latest_time_series(db, asset_name, currency_name)
#         raise AssetClassAlreadyExists(f"Asset Class '{asset_name}' already exists, use update_asset_data instead")
#     except TimeSeriesNotFound:
#         pass

#     asset = create_asset(db, asset_name)
#     currency = create_currency(db, time_series_dataset[0].currency)

#     for time_series_data in time_series_dataset:
#         add_time_series_data(db, time_series_data)
#     db.commit()
#     return None

# def update_asset_data(db: Database, time_series_dataset: Sequence[TimeSeriesCreate]) -> None:

#     for time_series_data in time_series_dataset:
#         add_time_series_data(db, time_series_data)
#     db.commit()
#     return None
