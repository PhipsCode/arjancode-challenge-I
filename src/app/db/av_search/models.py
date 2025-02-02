from sqlalchemy import (
    ForeignKey,
    Column,
    Integer,
    String,
    Table,
)
from sqlalchemy.orm import relationship

from ..base import Base


class SearchEntryEntity(Base):
    __tablename__ = "search_entries"

    id = Column(Integer, primary_key=True)
    input = Column(String, nullable=False, index=True)
    results = relationship(
        "SearchResultEntity",
        secondary="search_entry_result_association",
        back_populates="search_entries",
    )


class SearchResultEntity(Base):
    __tablename__ = "search_results"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    asset_type = Column(String, nullable=False)
    currency = Column(String, nullable=False)
    search_entries = relationship(
        "SearchEntryEntity",
        secondary="search_entry_result_association",
        back_populates="results",
    )


# Many to many association table
search_entry_result_association = Table(
    "search_entry_result_association",
    Base.metadata,
    Column(
        "search_entry_id", Integer, ForeignKey("search_entries.id"), primary_key=True
    ),
    Column(
        "search_result_id", Integer, ForeignKey("search_results.id"), primary_key=True
    ),
)
