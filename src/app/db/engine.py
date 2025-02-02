from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .base import Base

AV_SEARCH_DB = "av_search"
SQLALCHEMY_DATABASE_URL = "sqlite:///./av_search.db"
engine_av_search = create_engine(SQLALCHEMY_DATABASE_URL, echo=False)

AV_STOCK_HIST_DB = "av_stock_hist"
SQLALCHEMY_DATABASE_URL = "sqlite:///./av_stock_hist.db"
engine_av_stock_hist = create_engine(SQLALCHEMY_DATABASE_URL, echo=False)


DB_SESSIONS = {
    AV_SEARCH_DB: sessionmaker(
        autocommit=False, autoflush=False, bind=engine_av_search
    ),
    AV_STOCK_HIST_DB: sessionmaker(
        autocommit=False, autoflush=False, bind=engine_av_stock_hist
    ),
}

Base.metadata.create_all(bind=engine_av_search)
Base.metadata.create_all(bind=engine_av_stock_hist)


def get_db_session_generator(db_name: str) -> Generator[Session, None, None]:
    database = DB_SESSIONS[db_name]()
    yield database
    database.close()


@contextmanager
def get_db_session_context(db_name: str) -> Generator[Session, None, None]:
    database = DB_SESSIONS[db_name]()
    try:
        yield database
    except:
        raise
    finally:
        database.close()
