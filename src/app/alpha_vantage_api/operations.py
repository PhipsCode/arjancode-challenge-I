from dataclasses import asdict, dataclass, field
from enum import StrEnum
from functools import partial
from typing import Any, ClassVar, Optional, Protocol, Type, TypeVar
from pydantic import BaseModel
import requests


from .exceptions import APIMessageError, UncaughtAPIError
from .models import AssetHistoryData, SymbolMarketSearchResults
from .limit_count import increment_api_count, get_api_count
from .config import BASE_URL


class STOCK_INTERVALL(StrEnum):
    """Function Word for Stock Data"""

    DAILY = "TIME_SERIES_DAILY"
    WEEKLY = "TIME_SERIES_WEEKLY"
    MONTHLY = "TIME_SERIES_MONTHLY"


class DAILY_OUTPUTSIZE(StrEnum):
    """Outputsize for request of daily data"""

    COMPACT = "compact"
    FULL = "full"


@dataclass(kw_only=True)
class StockParams:
    function: STOCK_INTERVALL = STOCK_INTERVALL.DAILY
    symbol: str
    outputsize: Optional[DAILY_OUTPUTSIZE] = field(default=None, init=False)

    def __post_init__(self):
        if self.function != STOCK_INTERVALL.DAILY:
            self.outputsize = DAILY_OUTPUTSIZE.COMPACT

    def as_dict(self) -> dict[str, str]:
        data = asdict(self)
        if not self.outputsize:
            del data["outputsize"]
        return data


class FOREX_INTERVALL(StrEnum):
    """Function Word for Forex (Foreign Exchange Rates) Data"""

    DAILY = "FX_DAILY"
    WEEKLY = "FX_WEEKLY"
    MONTHLY = "FX_MONTHLY"


@dataclass(kw_only=True)
class ForexParams:
    function: FOREX_INTERVALL = FOREX_INTERVALL.DAILY
    from_symbol: str
    to_symbol: str
    outputsize: Optional[DAILY_OUTPUTSIZE] = field(default=None, init=False)
    all_data: bool = False

    def __post_init__(self):
        if self.function == STOCK_INTERVALL.DAILY:
            self.outputsize = DAILY_OUTPUTSIZE.COMPACT

    def as_dict(self) -> dict[str, str]:
        data = asdict(self)
        if self.outputsize:
            del data["outputsize"]
        return data


class CRYPTO_INTERVALL(StrEnum):
    """Function Word for Crypto Currency Data"""

    DAILY = "DIGITAL_CURRENCY_DAILY"
    WEEKLY = "DIGITAL_CURRENCY_WEEKLY"
    MONTHLY = "DIGITAL_CURRENCY_MONTHLY"


@dataclass(kw_only=True)
class CryptoParams:
    function: CRYPTO_INTERVALL = CRYPTO_INTERVALL.DAILY
    symbol: str
    market: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


class APIParams(Protocol):

    def as_dict(self) -> dict[str, str]: ...


RESPONSE_ERROR_MESSAGE_KEY = "Error Message"


@dataclass(kw_only=True)
class MarkedDataParams:
    function: str = "SYMBOL_SEARCH"
    keywords: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


# def request_history_data(api_params: APIParams, api_key: str) -> AssetHistoryData:
#     params = api_params.as_dict()
#     params["apikey"] = api_key

#     if get_api_count().remaining <= 0:
#         raise APIMessageError("API Limit reached. Please try again next day.")

#     try:
#         response = requests.get(BASE_URL, params=params)
#     except requests.RequestException as e:
#         raise UncaughtAPIError(f"Request failed: {e}")
#     increment_api_count()

#     if response.status_code != 200:
#         response.raise_for_status()
#         raise UncaughtAPIError(
#             f"Request failed with status code {response.status_code}: {response.text}"
#         )

#     data: dict[str, Any] = response.json()

#     if RESPONSE_ERROR_MESSAGE_KEY in data:
#         raise APIMessageError(data[RESPONSE_ERROR_MESSAGE_KEY])

#     return AssetHistoryData(**data)


# def request_symbol_search(api_params: APIParams, api_key: str) -> MarketMetaData:

#     APIParams(function="SYMBOL_SEARCH", keywords="AAPL", apikey="demo")

#     try:
#         response = requests.get(BASE_URL, params=params)
#     except requests.RequestException as e:
#         raise UncaughtAPIError(f"Request failed: {e}")

#     data: dict[str, Any] = response.json()

#     if RESPONSE_ERROR_MESSAGE_KEY in data:
#         raise APIMessageError(data[RESPONSE_ERROR_MESSAGE_KEY])

#     return MarketMetaData(**data)

T = TypeVar("T", bound=BaseModel)


def request_data(api_params: APIParams, api_key: str, expected_output: Type[T]) -> T:
    # def request_data[T](api_params: APIParams, expected_output: type[T], api_key: str) -> T:
    params = api_params.as_dict()
    params["apikey"] = api_key

    if get_api_count().remaining <= 0:
        raise APIMessageError("API Limit reached. Please try again next day.")

    try:
        response = requests.get(BASE_URL, params=params)
    except requests.RequestException as e:
        raise UncaughtAPIError(f"Request failed: {e}")
    increment_api_count()

    if response.status_code != 200:
        response.raise_for_status()
        raise UncaughtAPIError(
            f"Request failed with status code {response.status_code}: {response.text}"
        )

    data: dict[str, Any] = response.json()

    if RESPONSE_ERROR_MESSAGE_KEY in data:
        raise APIMessageError(data[RESPONSE_ERROR_MESSAGE_KEY])

    return expected_output(**data)


request_history_data = partial(request_data, expected_output=AssetHistoryData)
request_market_meda_data = partial(
    request_data, expected_output=SymbolMarketSearchResults
)


class AssetType(StrEnum):
    STOCK = "stock"
    FOREX = "forex"
    CRYPTO = "crypto"


class DATA_INTERVAL(StrEnum):
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"


def get_function(asset_type: AssetType, interval: str) -> str:
    if asset_type == AssetType.STOCK:
        return STOCK_INTERVALL(interval)
    elif asset_type == AssetType.FOREX:
        return FOREX_INTERVALL(interval)
    elif asset_type == AssetType.CRYPTO:
        return CRYPTO_INTERVALL(interval)
    else:
        raise ValueError("Invalid Asset Type")


def create_stock_params(
    function: str,
    symbol: str,
    outputsize: Optional[DAILY_OUTPUTSIZE] = None,
) -> StockParams:
    params = StockParams(function=STOCK_INTERVALL(function), symbol=symbol)
    if outputsize:
        params.outputsize = outputsize
    return params


def create_forex_params(
    function: str,
    from_symbol: str,
    to_symbol: str,
    outputsize: Optional[DAILY_OUTPUTSIZE] = None,
) -> ForexParams:
    params = ForexParams(
        function=FOREX_INTERVALL(function), from_symbol=from_symbol, to_symbol=to_symbol
    )
    if outputsize:
        params.outputsize = outputsize
    return params


def create_crypto_params(
    function: str,
    symbol: str,
    market: str,
) -> CryptoParams:
    return CryptoParams(
        function=CRYPTO_INTERVALL(function), symbol=symbol, market=market
    )


def main():

    daily_stock_params = StockParams(symbol="AAPL")
    print(asdict(daily_stock_params))

    monthly_stock_params = StockParams(symbol="AAPL", function=STOCK_INTERVALL.MONTHLY)
    print(asdict(monthly_stock_params))


if __name__ == "__main__":
    main()
