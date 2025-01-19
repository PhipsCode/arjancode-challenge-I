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
    "2. Symbol", "2. From Symbol", "2. Digital Currency Code"
)
"""Alias for asset(-symbol) of Stocks/ETFs, Forex and Digital Currencies"""

CURRENCY_ALIAS_CHOICES = AliasChoices("3. To Symbol", "4. Market Code")
"""Alias for currency of Forex and Digital Currencies. Not present in Stocks/ETFs"""

TIME_ZONE_ALIAS_CHOICES = AliasChoices("5. Time Zone", "6. Time Zone", "7. Time Zone")
"""Alias for timezone of Stocks/ETFs, Forex and Digital Currencies"""


class MetaData(BaseModel):
    information: str = Field(alias="1. Information")  # everytime the same
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

    open: float = Field(alias="1. open")
    high: float = Field(alias="2. high")
    low: float = Field(alias="3. low")
    close: float = Field(alias="4. close")


TIME_SERIES_ALIAS_CHOICES: AliasChoices = AliasChoices(
    "Time Series (Daily)",
    "Time Series FX (Daily)",
    "Time Series (Digital Currency Daily)",
)
""" Alias for the time series data of Stocks/ETFs, Forex and Digital Currencies"""


class AssetHistoryData(BaseModel):
    meta_data: MetaData = Field(alias="Meta Data")
    time_series: dict[datetime, TimeSeriesData] = Field(
        validation_alias=TIME_SERIES_ALIAS_CHOICES
    )


class MarketMetaData(BaseModel):
    name: str = Field(alias="2. name")
    identifier: str = Field(alias="1. symbol")
    type: str = Field(alias="3. type")
    currency: str = Field(alias="8. currency")


class SymbolMarketSearchResults(BaseModel):
    best_matches: list[MarketMetaData] = Field(alias="bestMatches")


def main():
    from pathlib import Path
    import json
    import pandas as pd

    def convert_time_series_data(data: dict) -> pd.DataFrame:
        rows = []
        for timestamp, values in data.items():
            row = {"timestamp": timestamp}
            row.update(values)
            rows.append(row)
        df = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.sort_values("timestamp", inplace=True)
        return df

    base_path = Path().joinpath(r"alpha_vantage_examples")

    daily_crypto_data = base_path.joinpath(r"btc_daily.json")
    daily_etf_data = base_path.joinpath(r"etf_data_usd.json")
    daily_gold = base_path.joinpath(r"gold_usd.json")
    daily_forex = base_path.joinpath(r"forex_data.json")

    for file in [daily_crypto_data, daily_etf_data, daily_gold, daily_forex]:
        print(f"Reading file: {file}")
        try:
            with open(file) as f:
                data = json.load(f)
                asset_data = AssetHistoryData(**data)
                pd.DataFrame.from_dict(
                    {
                        date: data.model_dump()
                        for date, data in asset_data.time_series.items()
                    },
                    orient="index",
                )
                print(pd.DataFrame(asset_data.time_series))
                print(asset_data)
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
