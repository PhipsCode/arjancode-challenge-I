from typing import Any, Protocol
from pydantic import BaseModel
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import date

from .exceptions import AssetNotFound

from .models import AssetEntity, AssetTimeSeriesEntity


class AssetCreate(BaseModel):
    name: str
    identifier: str
    symbol: str
    asset_type: str
    currency: str


class AssetTimeSeriesCreate(BaseModel):
    date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal


def get_asset(session: Session, symbol: str) -> AssetEntity | None:
    return session.query(AssetEntity).filter_by(symbol=symbol).first()


def add_asset(
    session: Session,
    asset: AssetCreate,
):
    asset_entry = get_asset(session, asset.symbol)
    if asset_entry:
        return asset_entry
    asset_entry = AssetEntity(**asset.model_dump())
    try:
        session.add(asset_entry)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    return asset_entry


def get_time_series_by_date(
    session: Session, asset_id: int, date: date
) -> AssetTimeSeriesEntity | None:
    return (
        session.query(AssetTimeSeriesEntity)
        .filter(
            AssetTimeSeriesEntity.asset_id == asset_id,
            AssetTimeSeriesEntity.date == date,
        )
        .first()
    )


def add_time_series_entry(
    session: Session,
    asset_symbol: str,
    asset_time_series: AssetTimeSeriesCreate,
) -> AssetTimeSeriesEntity:
    asset = get_asset(session, asset_symbol)
    if not asset:
        raise AssetNotFound(f"No asset found with symbol {asset_symbol}")

    time_series_entry = get_time_series_by_date(
        session, asset.id, asset_time_series.date
    )
    if time_series_entry:
        return time_series_entry

    time_series_entry = AssetTimeSeriesEntity(
        asset_id=asset.id, **asset_time_series.model_dump()
    )
    try:
        session.add(time_series_entry)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    return time_series_entry


def get_assets_by_identifier(session: Session, identifier: str) -> list[AssetEntity]:
    return session.query(AssetEntity).filter_by(identifier=identifier).all()


def add_time_series_entries(
    session: Session,
    asset_symbol: str,
    asset_time_series_entries: list[AssetTimeSeriesCreate],
) -> list[AssetTimeSeriesEntity]:
    asset = get_asset(session, asset_symbol)
    if not asset:
        raise AssetNotFound(f"No asset found with symbol {asset_symbol}")

    time_series_entries = []
    for asset_time_series in asset_time_series_entries:
        time_series_entry = get_time_series_by_date(
            session, asset.id, asset_time_series.date
        )
        if time_series_entry:
            time_series_entries.append(time_series_entry)
            continue

        time_series_entry = AssetTimeSeriesEntity(
            asset_id=asset.id, **asset_time_series.model_dump()
        )
        try:
            session.add(time_series_entry)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        time_series_entries.append(time_series_entry)
    return time_series_entries
