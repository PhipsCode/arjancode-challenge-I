from contextlib import contextmanager
from typing import Any
import pytest
from unittest.mock import patch, mock_open
from datetime import date, timedelta
import json
from src.app.alpha_vantage_api.limit_count import (
    create_new_daily_api_limit_count,
    open_file,
    counter_file,
    increment_api_count,
)
from src.app.alpha_vantage_api.exceptions import APILimitReached

FILE_NAME = "api_limit_count.json"
API_DAILY_LIMIT = 25


@contextmanager
def mock_open_file(mock_data: dict[str, Any]):
    with patch('src.app.alpha_vantage_api.limit_count.open', mock_open(read_data=json.dumps(mock_data))) as mocked_file:
        yield mocked_file


@pytest.fixture
def mock_file_path():
    with patch('src.app.alpha_vantage_api.limit_count.Path.exists', return_value=True):
        yield

def test_create_new_daily_api_limit_count():
    api_limit_count = create_new_daily_api_limit_count()
    assert api_limit_count.limit == API_DAILY_LIMIT
    assert api_limit_count.remaining == API_DAILY_LIMIT
    assert api_limit_count.last_update == date.today()

def test_open_file(mock_file_path):
    mock_data = {
        "limit": API_DAILY_LIMIT,
        "remaining": 20,
        "last_update": str(date.today())
    }
    with mock_open_file(mock_data):
        api_limit_count = open_file()
        assert api_limit_count.limit == API_DAILY_LIMIT
        assert api_limit_count.remaining == 20
        assert api_limit_count.last_update == date.today()

def test_counter_file_new_file():
    with patch('src.app.alpha_vantage_api.limit_count.Path.exists', return_value=False):
        with patch('src.app.alpha_vantage_api.limit_count.open', mock_open()) as mocked_file:
            with counter_file() as api_limit_count:
                assert api_limit_count.limit == API_DAILY_LIMIT
                assert api_limit_count.remaining == API_DAILY_LIMIT
                assert api_limit_count.last_update == date.today()

def test_counter_file_existing_file(mock_file_path):
    mock_data = {
        "limit": API_DAILY_LIMIT,
        "remaining": 20,
        "last_update": str(date.today())
    }
    with mock_open_file(mock_data):
        with counter_file() as api_limit_count:
            assert api_limit_count.limit == API_DAILY_LIMIT
            assert api_limit_count.remaining == 20
            assert api_limit_count.last_update == date.today()

def test_counter_file_new_day():
    mock_data = {
        "limit": API_DAILY_LIMIT,
        "remaining": 20,
        "last_update": str(date.today() - timedelta(days=1))
    }
    with mock_open_file(mock_data):
        with counter_file() as api_limit_count:
            assert api_limit_count.limit == API_DAILY_LIMIT
            assert api_limit_count.remaining == API_DAILY_LIMIT
            assert api_limit_count.last_update == date.today()

def test_increment_api_count():
    mock_data = {
        "limit": API_DAILY_LIMIT,
        "remaining": 20,
        "last_update": str(date.today())
    }
    with mock_open_file(mock_data):
        with patch('src.app.alpha_vantage_api.limit_count.Path.exists', return_value=True):
            api_limit_count = increment_api_count()
            assert api_limit_count.remaining == 19

def test_increment_api_count_limit_reached():
    mock_data = {
        "limit": API_DAILY_LIMIT,
        "remaining": 0,
        "last_update": str(date.today())
    }
    with mock_open_file(mock_data):
        with patch('src.app.alpha_vantage_api.limit_count.Path.exists', return_value=True):
            with pytest.raises(APILimitReached):
                increment_api_count()