"""
Models from the Alpha Vantage API tailored for the simplified Asset-Database

Using Pydantic to convert them to a unified format

Currently covered API-Endpoints:

Stocks/ETFs:
- Time Series (Daily)

Forex:
- Time Series FX (Daily)

Digital Currencies:
- Time Series (Digital Currency Daily)

"""

from pydantic import AliasChoices, BaseModel, Field
from datetime import datetime

ASSET_ALIAS_CHOICES = AliasChoices(
    "asset", "2. Symbol", "2. From Symbol", "2. Digital Currency Code"
)
"""Alias for asset(-symbol) of Stocks/ETFs, Forex and Digital Currencies"""

CURRENCY_ALIAS_CHOICES = AliasChoices("currency", "3. To Symbol", "4. Market Code")
"""Alias for currency of Forex and Digital Currencies. Not present in Stocks/ETFs"""

TIME_ZONE_ALIAS_CHOICES = AliasChoices(
    "timezone", "5. Time Zone", "6. Time Zone", "7. Time Zone"
)
"""Alias for timezone of Stocks/ETFs, Forex and Digital Currencies"""


class MetaData(BaseModel):
    information: str = Field(
        validation_alias=AliasChoices("information", "1. Information")
    )  # everytime the same
    asset: str = Field(validation_alias=ASSET_ALIAS_CHOICES)
    currency: str = Field(default="", validation_alias=CURRENCY_ALIAS_CHOICES)
    timezone: str = Field(validation_alias=TIME_ZONE_ALIAS_CHOICES)


class TimeSeriesData(BaseModel):
    """
    The common fields for all time series data are named:
    - "1. open"
    - "2. high"
    - "3. low"
    - "4. close"

    The volume field is not always present, so it is not included in this model
    """

    open: float = Field(validation_alias=AliasChoices("open", "1. open"))
    high: float = Field(validation_alias=AliasChoices("high", "2. high"))
    low: float = Field(validation_alias=AliasChoices("low", "3. low"))
    close: float = Field(validation_alias=AliasChoices("close", "4. close"))


TIME_SERIES_ALIAS_CHOICES: AliasChoices = AliasChoices(
    "time_series",
    "Time Series (Daily)",
    "Time Series FX (Daily)",
    "Time Series (Digital Currency Daily)",
)
""" Alias for the time series data of Stocks/ETFs, Forex and Digital Currencies"""


class AssetHistoryData(BaseModel):
    meta_data: MetaData = Field(validation_alias=AliasChoices("meta_data", "Meta Data"))
    time_series: dict[datetime, TimeSeriesData] = Field(
        validation_alias=TIME_SERIES_ALIAS_CHOICES
    )


class MarketMetaData(BaseModel):
    name: str = Field(validation_alias=AliasChoices("name", "2. name"))
    symbol: str = Field(validation_alias=AliasChoices("symbol", "1. symbol"))
    asset_type: str = Field(validation_alias=AliasChoices("asset_type", "3. type"))
    currency: str = Field(validation_alias=AliasChoices("currency", "8. currency"))


class SymbolMarketSearchResults(BaseModel):
    best_matches: list[MarketMetaData] = Field(
        validation_alias=AliasChoices("best_matches", "bestMatches")
    )
