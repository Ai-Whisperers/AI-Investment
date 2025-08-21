"""
Pydantic schemas for news and sentiment data.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SentimentLabel(str, Enum):
    """Sentiment classification labels."""

    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"


class NewsEntitySchema(BaseModel):
    """Entity mentioned in news."""

    symbol: str | None = None
    name: str
    type: str
    exchange: str | None = None
    sentiment_score: float | None = None

    class Config:
        from_attributes = True


class NewsSentimentSchema(BaseModel):
    """Sentiment analysis result."""

    score: float = Field(..., ge=-1, le=1)
    label: SentimentLabel
    confidence: float = Field(..., ge=0, le=1)

    class Config:
        from_attributes = True


class NewsArticleBase(BaseModel):
    """Base news article schema."""

    title: str
    description: str
    url: str
    source: str
    published_at: datetime

    class Config:
        from_attributes = True


class NewsArticleResponse(NewsArticleBase):
    """News article response with full details."""

    id: str
    content: str | None = None
    image_url: str | None = None
    language: str = "en"
    country: str | None = None
    entities: list[NewsEntitySchema] = []
    sentiment: NewsSentimentSchema | None = None
    keywords: list[str] = []
    categories: list[str] = []

    class Config:
        from_attributes = True


class NewsSearchRequest(BaseModel):
    """Request for news search."""

    symbols: list[str] | None = None
    keywords: str | None = None
    sources: list[str] | None = None
    sentiment_min: float | None = Field(None, ge=-1, le=1)
    sentiment_max: float | None = Field(None, ge=-1, le=1)
    published_after: datetime | None = None
    published_before: datetime | None = None
    limit: int = Field(50, ge=1, le=100)
    offset: int = Field(0, ge=0)


class NewsSentimentResponse(BaseModel):
    """Sentiment analysis response."""

    article_id: str
    sentiment_score: float
    sentiment_label: SentimentLabel
    confidence: float
    analyzed_at: datetime

    class Config:
        from_attributes = True


class EntitySentimentTrend(BaseModel):
    """Sentiment trend data point."""

    date: datetime
    sentiment_score: float
    article_count: int
    positive_count: int
    negative_count: int
    neutral_count: int


class EntitySentimentResponse(BaseModel):
    """Entity sentiment analysis over time."""

    symbol: str
    current_sentiment: float
    average_sentiment: float
    total_articles: int
    sentiment_trend: list[EntitySentimentTrend]
    top_sources: list[dict[str, Any]]

    class Config:
        from_attributes = True


class TrendingEntityResponse(BaseModel):
    """Trending entity information."""

    symbol: str | None = None
    name: str
    type: str
    mention_count: int
    average_sentiment: float
    article_count: int
    trend_score: float

    class Config:
        from_attributes = True
