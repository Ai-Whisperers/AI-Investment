"""
Database models for news and sentiment data.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..core.database import Base

# Association table for many-to-many relationship between articles and assets
asset_news_association = Table(
    "asset_news",
    Base.metadata,
    Column("asset_id", Integer, ForeignKey("assets.id"), primary_key=True),
    Column(
        "article_id",
        UUID(as_uuid=True),
        ForeignKey("news_articles.id"),
        primary_key=True,
    ),
    Column("relevance_score", Float, default=1.0),
    Column("sentiment_score", Float),
    Column("created_at", DateTime(timezone=True), default=datetime.utcnow),
)


class NewsSource(Base):
    """News source/publisher model."""

    __tablename__ = "news_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    domain = Column(String(255))
    country = Column(String(2))
    language = Column(String(2))
    credibility_score = Column(Float, default=0.5)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    articles = relationship("NewsArticle", back_populates="source_obj")

    __table_args__ = (
        Index("ix_news_sources_name", "name"),
        Index("ix_news_sources_domain", "domain"),
    )


class NewsArticle(Base):
    """News article model."""

    __tablename__ = "news_articles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id = Column(String(255), unique=True)  # Provider's UUID
    title = Column(String(500), nullable=False)
    description = Column(Text)
    content = Column(Text)
    url = Column(String(500), nullable=False, unique=True)
    image_url = Column(String(500))

    # Source information
    source_id = Column(UUID(as_uuid=True), ForeignKey("news_sources.id"))
    source_name = Column(String(100))  # Denormalized for quick access

    # Metadata
    language = Column(String(2), default="en")
    country = Column(String(2))
    published_at = Column(DateTime(timezone=True), nullable=False)

    # Categories and keywords
    categories = Column(JSON, default=list)
    keywords = Column(JSON, default=list)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    source_obj = relationship("NewsSource", back_populates="articles")
    sentiment = relationship(
        "NewsSentiment",
        back_populates="article",
        uselist=False,
        cascade="all, delete-orphan",
    )
    entities = relationship(
        "NewsEntity", back_populates="article", cascade="all, delete-orphan"
    )
    assets = relationship(
        "Asset", secondary=asset_news_association, back_populates="news_articles"
    )

    __table_args__ = (
        Index("ix_news_articles_published_at", "published_at"),
        Index("ix_news_articles_source_id", "source_id"),
        Index("ix_news_articles_external_id", "external_id"),
        Index("ix_news_articles_url", "url"),
        UniqueConstraint("external_id", name="uq_news_articles_external_id"),
        UniqueConstraint("url", name="uq_news_articles_url"),
    )


class NewsSentiment(Base):
    """Sentiment analysis for news articles."""

    __tablename__ = "news_sentiment"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(
        UUID(as_uuid=True), ForeignKey("news_articles.id"), nullable=False, unique=True
    )

    # Overall sentiment
    sentiment_score = Column(Float, nullable=False)  # -1 to 1
    sentiment_label = Column(String(20))  # positive, negative, neutral, etc.
    confidence = Column(Float, default=0.5)  # 0 to 1

    # Detailed scores (optional)
    positive_score = Column(Float)
    negative_score = Column(Float)
    neutral_score = Column(Float)

    # Analysis metadata
    provider = Column(String(50))  # Which service provided the sentiment
    analyzed_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    article = relationship("NewsArticle", back_populates="sentiment")

    __table_args__ = (
        Index("ix_news_sentiment_article_id", "article_id"),
        Index("ix_news_sentiment_score", "sentiment_score"),
        Index("ix_news_sentiment_label", "sentiment_label"),
    )


class NewsEntity(Base):
    """Entities mentioned in news articles."""

    __tablename__ = "news_entities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(
        UUID(as_uuid=True), ForeignKey("news_articles.id"), nullable=False
    )

    # Entity information
    symbol = Column(String(20))
    name = Column(String(255), nullable=False)
    type = Column(String(50))  # company, person, location, product, etc.

    # Additional metadata
    exchange = Column(String(20))
    country = Column(String(2))
    industry = Column(String(100))

    # Relevance and sentiment
    match_score = Column(Float)  # How well the entity matches
    sentiment_score = Column(Float)  # Entity-specific sentiment
    mention_count = Column(Integer, default=1)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    article = relationship("NewsArticle", back_populates="entities")

    __table_args__ = (
        Index("ix_news_entities_article_id", "article_id"),
        Index("ix_news_entities_symbol", "symbol"),
        Index("ix_news_entities_type", "type"),
        Index("ix_news_entities_name", "name"),
    )


class EntitySentimentHistory(Base):
    """Historical sentiment tracking for entities."""

    __tablename__ = "entity_sentiment_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(20), nullable=False)

    # Aggregated sentiment for a time period
    date = Column(DateTime(timezone=True), nullable=False)
    sentiment_score = Column(Float, nullable=False)

    # Statistics
    article_count = Column(Integer, default=0)
    positive_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)
    neutral_count = Column(Integer, default=0)

    # Volume metrics
    total_mentions = Column(Integer, default=0)
    unique_sources = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        Index("ix_entity_sentiment_history_symbol_date", "symbol", "date"),
        UniqueConstraint(
            "symbol", "date", name="uq_entity_sentiment_history_symbol_date"
        ),
    )
