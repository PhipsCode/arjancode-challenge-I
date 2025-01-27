from contextlib import contextmanager
from datetime import date
import json
from pathlib import Path
from typing import Generator
from pydantic import BaseModel

from .exceptions import APILimitReached

FILE_NAME = "api_limit_count.json"
API_DALY_LIMIT = 25


class ApiLimitCount(BaseModel):
    limit: int = API_DALY_LIMIT
    remaining: int
    last_update: date


def create_new_daily_api_limit_count() -> ApiLimitCount:
    api_limit_count = ApiLimitCount(
        limit=API_DALY_LIMIT, remaining=API_DALY_LIMIT, last_update=date.today()
    )
    return api_limit_count


def open_file() -> ApiLimitCount:
    with open(FILE_NAME, "r") as file:
        data = json.load(file)
        api_limit_count = ApiLimitCount(**data)
    return api_limit_count


@contextmanager
def counter_file() -> Generator[ApiLimitCount, None, None]:
    if not Path(FILE_NAME).exists():
        api_limit_count_file = create_new_daily_api_limit_count()
    else:
        api_limit_count_file = open_file()
        if api_limit_count_file.last_update != date.today():
            api_limit_count_file = create_new_daily_api_limit_count()

    yield api_limit_count_file

    with open(FILE_NAME, "w") as file:
        file.write(api_limit_count_file.model_dump_json())


def increment_api_count() -> ApiLimitCount:
    with counter_file() as api_limit_count:
        if api_limit_count.remaining == 0:
            raise APILimitReached(f"Daily API limit of {API_DALY_LIMIT} reached.")
        api_limit_count.remaining -= 1
    return api_limit_count


def get_api_count() -> ApiLimitCount:
    with counter_file() as api_limit_count:
        return api_limit_count
