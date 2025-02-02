from collections import defaultdict
from decimal import Decimal
import itertools
import random
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import pytest

from src.app.db.v0.models import Base, to_dict
from src.app.db.v0.exceptions import AssetClassNotFound, AssetNotFound, CurrencyNotFound
from src.app.db.v0.operations import (
    create_asset,
    get_asset_by_identifier,
    get_asset_by_symbol,
    get_asset_class,
    get_asset_classes,
    create_asset_class,
    get_assets,
    get_currencies,
    create_currency,
    get_currency,
)

from src.app.models import Asset, AssetClass, Currency, SymbolCurrencyMapping

DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


ASSET_CLASS_NAMES: list[str] = ["Equity", "Forex", "Commodities", "Real Estate"]
ASSET_CLASSES: list[AssetClass] = [AssetClass(name=name) for name in ASSET_CLASS_NAMES]

CURRENCY_NAMES: list[str] = ["USD", "EUR", "BRL", "GBX"]
CURRENCIES: list[Currency] = [Currency(name=name) for name in CURRENCY_NAMES]

SYMBOL_CURRENCY_MAPPINGS: list[tuple[str, str, SymbolCurrencyMapping]] = [
    ("Apple Inc", "AAPL", SymbolCurrencyMapping(symbol="AAPL", currency="USD")),
    ("Apple Inc", "AAPL", SymbolCurrencyMapping(symbol="APC.DEX", currency="EUR")),
    ("Apple Inc", "AAPL", SymbolCurrencyMapping(symbol="APC.FRK", currency="EUR")),
    ("Alphabet Inc", "GOOGL", SymbolCurrencyMapping(symbol="GOOGL", currency="USD")),
    ("Alphabet Inc", "GOOGL", SymbolCurrencyMapping(symbol="ABEC.DEX", currency="EUR")),
    ("Tesla Inc", "TSLA", SymbolCurrencyMapping(symbol="TSLA", currency="USD")),
    ("Tesla Inc", "TSLA", SymbolCurrencyMapping(symbol="TL0.FRK", currency="EUR")),
    ("Tesla Inc", "TSLA", SymbolCurrencyMapping(symbol="TSLA34.SAO", currency="BRL")),
]


ASSETS: list[Asset] = []
FOREX_ASSETS: list[Asset] = [
    Asset(
        name=f"from_{CURRENCY_NAMES[0]}_to_{currency}",
        identifier=CURRENCY_NAMES[0],
        asset_class=AssetClass(name="Forex"),
        symbol_currency_mapping=[
            SymbolCurrencyMapping(
                symbol=f"{CURRENCY_NAMES[0]}_to_{currency}", currency=currency
            )
        ],
    )
    for currency in CURRENCY_NAMES[1:]
]
FOREX_ASSETS += [
    Asset(
        name=f"from_{CURRENCY_NAMES[1]}_to_{currency}",
        identifier=CURRENCY_NAMES[1],
        asset_class=AssetClass(name="Forex"),
        symbol_currency_mapping=[
            SymbolCurrencyMapping(
                symbol=f"{CURRENCY_NAMES[1]}_to_{currency}", currency=currency
            )
        ],
    )
    for currency in CURRENCY_NAMES[2:]
]
EQUITITY_ASSETS: list[Asset] = [
    Asset(
        name=name,
        identifier=identifier,
        asset_class=AssetClass(name="Stock"),
        symbol_currency_mapping=[symbol_currency_mapping],
    )
    for name, identifier, symbol_currency_mapping in SYMBOL_CURRENCY_MAPPINGS
]
ASSETS += FOREX_ASSETS + EQUITITY_ASSETS


class Test_SingleOperations:

    def test_add_asset_without_symbol_currency(self, db_session: Session):
        asset = Asset(
            name="AAPL",
            identifier="Apple Inc",
            asset_class=AssetClass(name="Equity"),
        )
        created_asset = create_asset(db_session, asset)
        asset_from_db = get_asset_by_identifier(db_session, asset.identifier)
        assert created_asset == asset_from_db
        assert str(asset_from_db.name) == asset.name
        assert str(asset_from_db.identifier) == asset.identifier
        assert asset_from_db.asset_class.name == asset.asset_class.name
        assert len(asset_from_db.symbols) == 0
        # assert len(asset_from_db.currencies) == 0

    def test_add_asset_with_symbol_currency(self, db_session: Session):

        symbol_currency_mapping = SymbolCurrencyMapping(symbol="AAPL", currency="USD")
        asset = Asset(
            name="AAPL",
            identifier="Apple Inc",
            asset_class=AssetClass(name="Equity"),
            symbol_currency_mapping=[symbol_currency_mapping],
        )

        created_asset = create_asset(db_session, asset)

        asset_from_db = get_asset_by_identifier(db_session, asset.identifier)

        assert created_asset == asset_from_db
        assert str(asset_from_db.name) == asset.name
        assert str(asset_from_db.identifier) == asset.identifier
        assert asset_from_db.asset_class.name == asset.asset_class.name
        assert len(asset_from_db.symbols) == 1
        assert asset_from_db.symbols[0].symbol == symbol_currency_mapping.symbol
        assert (
            asset_from_db.symbols[0].currency.name == symbol_currency_mapping.currency
        )


class Test_CurrencyOperations:

    def test_get_currencies_empty(self, db_session: Session):
        assert get_currencies(db_session) == []

    def test_get_not_existing_currency(self, db_session: Session):
        with pytest.raises(CurrencyNotFound):
            get_currency(db_session, "foo")

    def test_create_currency(self, db_session: Session):
        currency_data = Currency(name=CURRENCY_NAMES[0])
        create_currency(db_session, currency_data)

        currencies = get_currencies(db_session)
        assert len(currencies) == 1
        assert str(currencies[0].name) == currency_data.name

    def test_create_currencies(self, db_session: Session):

        currencies_to_create = tuple(
            Currency(name=currency_name) for currency_name in CURRENCY_NAMES
        )
        for currency in currencies_to_create:
            create_currency(db_session, currency)

        # add duplicate currency
        create_currency(db_session, Currency(name=CURRENCY_NAMES[0]))

        currencies_from_db = tuple(
            Currency(**to_dict(currency)) for currency in get_currencies(db_session)
        )

        # assert that no duplicate was created
        assert len(currencies_from_db) == len(CURRENCY_NAMES)
        sorted_from_db = sorted(currencies_from_db, key=lambda x: x.name)
        sorted_to_create = sorted(CURRENCY_NAMES)

        for currency_from_db, currency_to_create in zip(
            sorted_from_db, sorted_to_create
        ):
            assert currency_from_db.name == currency_to_create


class Test_AssesClassOperations:

    def test_get_asset_classes_empty(self, db_session: Session):
        assert get_asset_classes(db_session) == []

    def test_get_not_existing_asset_class(self, db_session: Session):
        with pytest.raises(AssetClassNotFound):
            get_asset_class(db_session, "foo")

    def test_create_asset_class(self, db_session: Session):
        asset_class_data = AssetClass(name=ASSET_CLASS_NAMES[0])
        create_asset_class(db_session, asset_class_data)

        asset_classes = get_asset_classes(db_session)
        assert len(asset_classes) == 1
        assert AssetClass(**to_dict(asset_classes[0])) == asset_class_data

    def test_create_asset_classes(self, db_session: Session):

        asset_classes_to_create = tuple(
            AssetClass(name=asset_name) for asset_name in ASSET_CLASS_NAMES
        )
        for asset_class in asset_classes_to_create:
            create_asset_class(db_session, asset_class)

        # add duplicate asset class
        create_asset_class(db_session, AssetClass(name=ASSET_CLASS_NAMES[0]))

        asset_classes_from_db = tuple(
            AssetClass(**to_dict(asset_class))
            for asset_class in get_asset_classes(db_session)
        )

        # assert that no duplicate was created
        assert len(asset_classes_from_db) == len(ASSET_CLASS_NAMES)
        sorted_from_db = sorted(asset_classes_from_db, key=lambda x: x.name)
        sorted_to_create = sorted(asset_classes_to_create, key=lambda x: x.name)

        for asset_from_db, asset_to_create in zip(sorted_from_db, sorted_to_create):
            assert asset_from_db.name == asset_to_create.name


class Test_AssetOperations:

    @pytest.fixture(autouse=True)
    def setup(self, db_session: Session):
        for asset in ASSETS:
            create_asset(db_session, asset)

    def test_get_not_existing_asset(self, db_session: Session):
        with pytest.raises(AssetNotFound):
            get_asset_by_identifier(db_session, "foo")

    def test_get_asset_by_identifier(self, db_session: Session):

        requested_asset_identifier: list[str] = []
        return_assets_identifier: list[str] = []
        for asset in ASSETS:
            asset_from_db = get_asset_by_identifier(db_session, asset.identifier)
            requested_asset_identifier.append(asset.identifier)
            return_assets_identifier.append(str(asset_from_db.identifier))
        assert requested_asset_identifier == return_assets_identifier

    def test_get_asset_by_symbol(self, db_session: Session):
        requested_asset_symbols: defaultdict[str, list[str]] = defaultdict(list)
        returned_asset_symbols: defaultdict[str, list[str]] = defaultdict(list)
        for asset in ASSETS:
            for symbol in asset.symbol_currency_mapping:
                requested_asset_symbols[asset.identifier].append(symbol.symbol)

                asset_from_db = get_asset_by_symbol(db_session, symbol.symbol)
                returned_asset_symbols[str(asset_from_db.identifier)].append(
                    str(symbol.symbol)
                )

        assert requested_asset_symbols == returned_asset_symbols

    def test_get_assets(self, db_session: Session):
        assets = get_assets(db_session)
        assert len(assets) == len(set([asset.identifier for asset in ASSETS]))

    def test_currency_symbol_mapping(self, db_session: Session):

        assets: dict[str, list[SymbolCurrencyMapping]] = defaultdict(list)
        for asset in ASSETS:
            assets[asset.identifier] += asset.symbol_currency_mapping
        # TODO: mapping missing
        for identifier, symbol_currency_mappings in assets.items():
            asset_from_db = get_asset_by_identifier(db_session, identifier)
            assert len(symbol_currency_mappings) == len(asset_from_db.symbols)
            # assert len(symbol_currency_mappings) == len(asset_from_db.currencies)
            # for symbol_currency in symbol_currencies:
            #     assert symbol_currency in asset_from_db.symbols
            # assert len(asset.symbol_currency_mapping) == len(
            #     asset_from_db.
            # )

            # for symbol_currency_mapping in asset.symbol_currency_mapping:
            #     assert symbol_currency_mapping in asset_from_db.symbol_currency_mapping
