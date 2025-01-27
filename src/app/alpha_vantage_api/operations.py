from dataclasses import asdict, dataclass, field
from enum import StrEnum
from functools import partial
from typing import Any, Literal, Protocol, Type, TypeVar
from pydantic import BaseModel
import requests


from .exceptions import APIMessageError, UncaughtAPIError
from .models import AssetHistoryData, SymbolMarketSearchResults
from .limit_count import increment_api_count, get_api_count
from .config import BASE_URL


class IntervalTypeError(Exception):
    pass


class AssetType(StrEnum):
    STOCK = "stock"
    FOREX = "forex"
    CRYPTO = "crypto"


class Interval(StrEnum):
    """Function Word for Stock Data"""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


INTERVAL_CHOICES = Literal[
    "daily", "weekly", "monthly", Interval.DAILY, Interval.WEEKLY, Interval.MONTHLY
]

TICKER_SEARCH_FUNCTION = "SYMBOL_SEARCH"

STOCK_INTERVALL_FUNCTION: dict[Interval, str] = {
    Interval.DAILY: "TIME_SERIES_DAILY",
    Interval.WEEKLY: "TIME_SERIES_WEEKLY",
    Interval.MONTHLY: "TIME_SERIES_MONTHLY",
}

FOREX_INTERVALL_FUNCTION: dict[Interval, str] = {
    Interval.DAILY: "FX_DAILY",
    Interval.WEEKLY: "FX_WEEKLY",
    Interval.MONTHLY: "FX_MONTHLY",
}

CRYPTO_INTERVALL_FUNCTION: dict[Interval, str] = {
    Interval.DAILY: "DIGITAL_CURRENCY_DAILY",
    Interval.WEEKLY: "DIGITAL_CURRENCY_WEEKLY",
    Interval.MONTHLY: "DIGITAL_CURRENCY_MONTHLY",
}


class DAILY_OUTPUTSIZE(StrEnum):
    """Outputsize for request of daily data"""

    COMPACT = "compact"
    FULL = "full"


def convert_to_interval(interval: str) -> Interval:
    if interval not in Interval:
        raise IntervalTypeError(
            f"Invalid Interval: {interval}, must be one of {INTERVAL_CHOICES}"
        )
    return Interval(interval)


def create_stock_request_params(
    interval: str,
    symbol: str,
    outputsize: DAILY_OUTPUTSIZE = DAILY_OUTPUTSIZE.COMPACT,
) -> dict[str, str]:
    function = STOCK_INTERVALL_FUNCTION[convert_to_interval(interval)]
    params = {"function": function, "symbol": symbol}
    if interval == Interval.DAILY:
        params["outputsize"] = outputsize
    return params


def create_forex_request_params(
    interval: str,
    from_symbol: str,
    to_symbol: str,
    outputsize: DAILY_OUTPUTSIZE = DAILY_OUTPUTSIZE.COMPACT,
) -> dict[str, str]:
    function = FOREX_INTERVALL_FUNCTION[convert_to_interval(interval)]
    params = {"function": function, "from_symbol": from_symbol, "to_symbol": to_symbol}
    if interval == Interval.DAILY:
        params["outputsize"] = outputsize
    return params


def create_crypto_request_params(
    interval: str,
    symbol: str,
    market: str,
) -> dict[str, str]:
    function = CRYPTO_INTERVALL_FUNCTION[convert_to_interval(interval)]
    return {"function": function, "symbol": symbol, "market": market}


class APIParams(Protocol):

    def as_dict(self) -> dict[str, str]: ...


RESPONSE_ERROR_MESSAGE_KEY = "Error Message"


@dataclass(kw_only=True)
class MarkedDataParams:
    function: str = "SYMBOL_SEARCH"
    keywords: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


def request_history_data(api_params: APIParams, api_key: str) -> AssetHistoryData:
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

    return AssetHistoryData(**data)


def request_symbol_search(keywords: str, api_key: str) -> SymbolMarketSearchResults:
    params = {
        "function": TICKER_SEARCH_FUNCTION,
        "keywords": keywords,
        "apikey": api_key,
    }

    try:
        response = requests.get(BASE_URL, params=params)
    except requests.RequestException as e:
        raise UncaughtAPIError(f"Request failed: {e}")
    increment_api_count()
    data: dict[str, Any] = response.json()

    if RESPONSE_ERROR_MESSAGE_KEY in data:
        raise APIMessageError(data[RESPONSE_ERROR_MESSAGE_KEY])

    return SymbolMarketSearchResults(**data)


T = TypeVar("T", bound=BaseModel)


def request_data(
    api_params: dict[str, str], api_key: str, expected_output: Type[T]
) -> T:
    # def request_data(api_params: APIParams, api_key: str, expected_output: Type[T]) -> T:
    # def request_data[T](api_params: APIParams, expected_output: type[T], api_key: str) -> T:
    params = api_params.copy()
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


# request_history_data = partial(request_data, expected_output=AssetHistoryData)
# request_market_meda_data = partial(
#     request_data, expected_output=SymbolMarketSearchResults
# )
