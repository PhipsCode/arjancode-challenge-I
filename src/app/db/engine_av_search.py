from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .base import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./alpha_vantage.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def get_db_session_generator() -> Generator[Session, None, None]:
    database = SessionLocal()
    yield database
    database.close()


@contextmanager
def alpha_vantage_db():
    database = SessionLocal()
    try:
        yield database
    except:
        raise
    finally:
        database.close()
