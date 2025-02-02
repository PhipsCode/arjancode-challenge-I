import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date
from decimal import Decimal
from src.app.db.base import Base
from src.app.db.av_stock_data.exceptions import AssetNotFound


from src.app.db.av_stock_data.operations import (
    AssetCreate,
    AssetTimeSeriesCreate,
    add_asset,
    add_time_series_entry,
    get_time_series_by_date,
)


@pytest.fixture(scope="module")
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_add_time_series_entry_new(in_memory_db):
    session = in_memory_db
    asset = AssetCreate(
        name="Test Asset",
        identifier="123",
        symbol="TST",
        asset_type="Stock",
        currency="USD",
    )
    add_asset(session, asset)
    time_series = AssetTimeSeriesCreate(
        date=date(2023, 1, 1),
        open=Decimal("100.0"),
        high=Decimal("110.0"),
        low=Decimal("90.0"),
        close=Decimal("105.0"),
    )
    result = add_time_series_entry(session, "TST", time_series)
    assert result is not None
    assert result.asset_id is not None
    assert result.date == time_series.date


def test_add_time_series_entry_duplicate(in_memory_db):
    session = in_memory_db
    time_series = AssetTimeSeriesCreate(
        date=date(2023, 1, 1),
        open=Decimal("100.0"),
        high=Decimal("110.0"),
        low=Decimal("90.0"),
        close=Decimal("105.0"),
    )
    result = add_time_series_entry(session, "TST", time_series)
    duplicate_result = add_time_series_entry(session, "TST", time_series)
    assert duplicate_result is not None
    assert duplicate_result.id == result.id


def test_add_time_series_entry_non_existent_asset(in_memory_db):
    session = in_memory_db
    time_series = AssetTimeSeriesCreate(
        date=date(2023, 1, 1),
        open=Decimal("100.0"),
        high=Decimal("110.0"),
        low=Decimal("90.0"),
        close=Decimal("105.0"),
    )
    with pytest.raises(AssetNotFound):
        add_time_series_entry(session, "NON_EXISTENT", time_series)
