"""
News provider interface and data models.
"""

from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from ..base import BaseProvider


class SentimentLabel(Enum):
    """Sentiment classification labels."""

    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"


@dataclass
class NewsEntity:
    """Entity mentioned in news article."""

    symbol: str
    name: str
    type: str  # company, person, location, etc.
    exchange: str | None = None
    country: str | None = None
    industry: str | None = None
    match_score: float | None = None
    sentiment_score: float | None = None


@dataclass
class NewsSentiment:
    """Sentiment analysis result."""

    score: float  # -1 to 1
    label: SentimentLabel
    confidence: float  # 0 to 1

    @classmethod
    def from_score(cls, score: float, confidence: float = 0.8):
        """Create sentiment from score."""
        if score <= -0.6:
            label = SentimentLabel.VERY_NEGATIVE
        elif score <= -0.2:
            label = SentimentLabel.NEGATIVE
        elif score <= 0.2:
            label = SentimentLabel.NEUTRAL
        elif score <= 0.6:
            label = SentimentLabel.POSITIVE
        else:
            label = SentimentLabel.VERY_POSITIVE

        return cls(score=score, label=label, confidence=confidence)


@dataclass
class NewsArticle:
    """News article data model."""

    uuid: str
    title: str
    description: str
    url: str
    source: str
    published_at: datetime
    content: str | None = None
    image_url: str | None = None
    language: str = "en"
    country: str | None = None
    entities: list[NewsEntity] = field(default_factory=list)
    sentiment: NewsSentiment | None = None
    keywords: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "uuid": self.uuid,
            "title": self.title,
            "description": self.description,
            "url": self.url,
            "source": self.source,
            "published_at": self.published_at.isoformat(),
            "content": self.content,
            "image_url": self.image_url,
            "language": self.language,
            "country": self.country,
            "entities": [
                {
                    "symbol": e.symbol,
                    "name": e.name,
                    "type": e.type,
                    "exchange": e.exchange,
                    "sentiment_score": e.sentiment_score,
                }
                for e in self.entities
            ],
            "sentiment": (
                {
                    "score": self.sentiment.score,
                    "label": self.sentiment.label.value,
                    "confidence": self.sentiment.confidence,
                }
                if self.sentiment
                else None
            ),
            "keywords": self.keywords,
            "categories": self.categories,
        }


@dataclass
class NewsSearchParams:
    """Parameters for news search."""

    symbols: list[str] | None = None
    keywords: list[str] | None = None
    sources: list[str] | None = None
    countries: list[str] | None = None
    languages: list[str] | None = None
    categories: list[str] | None = None
    industries: list[str] | None = None
    sentiment_min: float | None = None
    sentiment_max: float | None = None
    published_after: datetime | None = None
    published_before: datetime | None = None
    limit: int = 50
    offset: int = 0


class NewsProvider(BaseProvider):
    """
    Abstract interface for news providers.
    All news providers must implement this interface.
    """

    @abstractmethod
    def search_news(self, params: NewsSearchParams) -> list[NewsArticle]:
        """
        Search for news articles based on parameters.

        Args:
            params: Search parameters

        Returns:
            List of NewsArticle objects
        """
        pass

    @abstractmethod
    def get_article(self, article_id: str) -> NewsArticle | None:
        """
        Get a specific article by ID.

        Args:
            article_id: Article UUID or ID

        Returns:
            NewsArticle or None if not found
        """
        pass

    @abstractmethod
    def get_similar_articles(
        self, article_id: str, limit: int = 10
    ) -> list[NewsArticle]:
        """
        Get articles similar to a given article.

        Args:
            article_id: Reference article ID
            limit: Maximum number of results

        Returns:
            List of similar NewsArticle objects
        """
        pass

    @abstractmethod
    def get_trending_entities(
        self, entity_type: str | None = None, limit: int = 20
    ) -> list[dict[str, Any]]:
        """
        Get trending entities in news.

        Args:
            entity_type: Filter by entity type (e.g., 'company')
            limit: Maximum number of results

        Returns:
            List of trending entity data
        """
        pass

    @abstractmethod
    def get_entity_sentiment(
        self,
        symbol: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Get sentiment analysis for a specific entity over time.

        Args:
            symbol: Entity symbol (e.g., stock ticker)
            start_date: Start of time range
            end_date: End of time range

        Returns:
            Sentiment data including scores and trends
        """
        pass

    def analyze_sentiment(self, text: str) -> NewsSentiment:
        """
        Analyze sentiment of text (if provider supports it).

        Args:
            text: Text to analyze

        Returns:
            NewsSentiment object
        """
        # Default implementation - can be overridden
        return NewsSentiment(score=0.0, label=SentimentLabel.NEUTRAL, confidence=0.5)

    def extract_entities(self, text: str) -> list[NewsEntity]:
        """
        Extract entities from text (if provider supports it).

        Args:
            text: Text to analyze

        Returns:
            List of NewsEntity objects
        """
        # Default implementation - can be overridden
        return []
