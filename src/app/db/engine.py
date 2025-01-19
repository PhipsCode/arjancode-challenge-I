



from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .models import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./finance.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, echo=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def get_db_session_generator() -> Generator[Session, None, None]:
    database = SessionLocal()
    yield database
    database.close()

@contextmanager
def get_db_session_context():
    database = SessionLocal()
    try:
        yield database
        database.commit()
    except:
        database.rollback()
        raise
    finally:
        database.close()