from pydantic import BaseModel
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.app.db.av_search.operations import (
    get_search_inputs,
    get_search_results,
    save_search_results,
)
from src.app.db.av_search.models import Base

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


class SearchResult(BaseModel):
    name: str
    symbol: str
    asset_type: str
    currency: str


class SearchResults(BaseModel):
    best_matches: list[SearchResult]


def test_save_search_results(db_session: Session):

    first_search = "some search"
    second_search = "another search"

    unique_first_result = [
        SearchResult(
            name="first result",
            symbol="foo",
            asset_type="test",
            currency="EUR",
        ),
        SearchResult(
            name="second result",
            symbol="bar",
            asset_type="test",
            currency="EUR",
        ),
    ]
    unique_second_result = [
        SearchResult(
            name="third result",
            symbol="blub",
            asset_type="test",
            currency="EUR",
        ),
    ]

    overlapping_result = [
        SearchResult(
            name="search result",
            symbol="foobar",
            asset_type="test",
            currency="EUR",
        ),
    ]

    # line with SearchResults just for testing later concept or parsing the api data
    first_search_results = SearchResults(
        best_matches=unique_first_result + overlapping_result
    )

    second_search_results = SearchResults(
        best_matches=unique_second_result + overlapping_result
    )

    save_search_results(db_session, first_search, first_search_results.best_matches)
    assert get_search_inputs(db_session) == [first_search]

    save_search_results(db_session, second_search, second_search_results.best_matches)
    assert get_search_inputs(db_session) == [first_search, second_search]

    frist_search_results_db = [
        SearchResult(**result)
        for result in get_search_results(db_session, first_search)
    ]
    frist_search_results_db.sort(key=lambda x: x.name)
    first_search_results.best_matches.sort(key=lambda x: x.name)
    assert frist_search_results_db == first_search_results.best_matches

    second_search_results_db = [
        SearchResult(**result)
        for result in get_search_results(db_session, second_search)
    ]
    second_search_results_db.sort(key=lambda x: x.name)
    second_search_results.best_matches.sort(key=lambda x: x.name)
    assert second_search_results_db == second_search_results.best_matches


def test_save_empty_search_results(db_session: Session):
    search = "some search"
    empty_results = SearchResults(best_matches=[])
    save_search_results(db_session, search, empty_results.best_matches)
    assert get_search_inputs(db_session) == [search]
    assert get_search_results(db_session, search) == []
