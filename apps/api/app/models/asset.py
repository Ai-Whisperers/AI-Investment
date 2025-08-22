"""
Asset and pricing models.
"""

from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from ..core.database import Base


class Asset(Base):
    """Financial asset model with comprehensive classification."""

    __tablename__ = "assets"

    id = Column(Integer, primary_key=True)
    symbol = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    
    # Classification fields
    sector = Column(String(50), nullable=True, index=True)
    industry = Column(String(100), nullable=True, index=True)
    market_cap_category = Column(String(20), nullable=True, index=True)  # micro, small, mid, large, mega
    tags = Column(JSON, nullable=True, default=list)  # ["ai", "renewable", "biotech", etc.]
    
    # ESG scores (0-100 scale)
    esg_score = Column(Float, nullable=True, index=True)
    environmental_score = Column(Float, nullable=True)
    social_score = Column(Float, nullable=True)
    governance_score = Column(Float, nullable=True)
    
    # Supply chain and innovation
    supply_chain_dependencies = Column(JSON, nullable=True)  # List of critical suppliers/partners
    patent_portfolio_size = Column(Integer, nullable=True)
    
    # Fundamental data
    pe_ratio = Column(Float, nullable=True)
    dividend_yield = Column(Float, nullable=True)
    market_cap = Column(BigInteger, nullable=True)
    
    # Volatility metrics
    volatility_30d = Column(Float, nullable=True)
    volatility_90d = Column(Float, nullable=True)

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
