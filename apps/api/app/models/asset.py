"""
Asset and pricing models.
"""

from sqlalchemy import (
    Column,
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from ..core.database import Base


class Asset(Base):
    """Financial asset model."""

    __tablename__ = "assets"

    id = Column(Integer, primary_key=True)
    symbol = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    sector = Column(String, nullable=True)

    # Relationships
    news_articles = relationship(
        "NewsArticle",
        secondary="asset_news",
        back_populates="assets",
        overlaps="assets",
    )

    def __repr__(self):
        return f"<Asset(symbol='{self.symbol}', name='{self.name}')>"


class Price(Base):
    """Asset price history model."""

    __tablename__ = "prices"

    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), index=True, nullable=False)
    date = Column(Date, index=True, nullable=False)
    close = Column(Float, nullable=False)

    __table_args__ = (UniqueConstraint("asset_id", "date", name="_asset_date_uc"),)

    def __repr__(self):
        return (
            f"<Price(asset_id={self.asset_id}, date={self.date}, close={self.close})>"
        )
