from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Date,
    DECIMAL,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship


from ..base import Base


class AssetEntity(Base):
    __tablename__ = "assets"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    identifier = Column(String, nullable=False, index=True)
    symbol = Column(String, nullable=False, index=True, unique=True)
    asset_type = Column(String, nullable=False, index=True)
    currency = Column(String, nullable=False)

    time_series = relationship(
        "AssetTimeSeriesEntity", back_populates="asset", cascade="all, delete-orphan"
    )


class AssetTimeSeriesEntity(Base):
    __tablename__ = "asset_time_series"
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    open = Column(DECIMAL, nullable=False)
    high = Column(DECIMAL, nullable=False)
    low = Column(DECIMAL, nullable=False)
    close = Column(DECIMAL, nullable=False)

    asset = relationship("AssetEntity", back_populates="time_series")

    # ensure that the combination of asset_id and date is unique -> only one entry per date
    _table_args__ = (UniqueConstraint("asset_id", "date", name="uq_asset_date"),)
