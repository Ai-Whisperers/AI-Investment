"""
MarketAux news provider implementation.
Implements NewsProvider interface using modularized components.
"""

import hashlib
import logging

from ...core.config import settings
from ..base import ProviderStatus
from .interface import (
    NewsArticle,
    NewsProvider,
    NewsSearchParams,
)
from .marketaux_provider import MarketAuxAPIClient, MarketAuxCacheManager, MarketAuxDataParser

logger = logging.getLogger(__name__)


class MarketauxProvider(NewsProvider):
    """
    MarketAux API provider implementation.
    Orchestrates news fetching using modular components.
    """

    def __init__(self, api_key: str | None = None, cache_enabled: bool = True):
        """
        Initialize MarketAux provider.
        
        Args:
            api_key: MarketAux API key
            cache_enabled: Whether to enable caching
        """
        super().__init__(api_key or settings.MARKETAUX_API_KEY, cache_enabled)

        # Initialize components
        self.client = MarketAuxAPIClient(self.api_key)
        self.parser = MarketAuxDataParser()
        self.cache_manager = MarketAuxCacheManager(cache_enabled)

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "Marketaux"

    def validate_config(self) -> bool:
        """Validate API key configuration."""
        return bool(self.api_key)

    def health_check(self) -> ProviderStatus:
        """Check MarketAux API health."""
        try:
            if self.client.health_check():
                return ProviderStatus.HEALTHY
            else:
                return ProviderStatus.DEGRADED
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return ProviderStatus.UNHEALTHY

    def search_news(self, params: NewsSearchParams) -> list[NewsArticle]:
        """
        Search for news articles.
        
        Args:
            params: Search parameters
            
        Returns:
            List of news articles
        """
        # Convert search params to API parameters
        api_params = self.parser.parse_search_params(params)

        # Check cache
        cached_articles = self.cache_manager.get_search_results(api_params)
        if cached_articles:
            return [self.parser.parse_article(a) for a in cached_articles]

        # Make API request
        response = self.client.search_news(api_params)

        if not response or "data" not in response:
            return []

        # Parse articles
        articles = [
            self.parser.parse_article(article_data)
            for article_data in response["data"]
        ]

        # Cache results
        if articles:
            articles_data = [self._article_to_dict(a) for a in articles]
            self.cache_manager.set_search_results(api_params, articles_data)

        return articles

    def get_article(self, article_id: str) -> NewsArticle | None:
        """
        Get specific article by UUID.
        
        Args:
            article_id: Article UUID
            
        Returns:
            NewsArticle or None if not found
        """
        # Check cache
        cached_article = self.cache_manager.get_article(article_id)
        if cached_article:
            return self.parser.parse_article(cached_article)

        # Fetch from API
        article_data = self.client.get_article(article_id)

        if not article_data:
            return None

        # Parse and cache
        article = self.parser.parse_article(article_data)
        self.cache_manager.set_article(article_id, self._article_to_dict(article))

        return article

    def get_trending_news(self, limit: int = 10) -> list[NewsArticle]:
        """
        Get trending news articles.
        
        Args:
            limit: Number of articles to fetch
            
        Returns:
            List of trending articles
        """
        # Check cache for trending
        cache_key_params = {"limit": limit, "sort": "trending"}
        cached_articles = self.cache_manager.get_search_results(cache_key_params)

        if cached_articles:
            return [self.parser.parse_article(a) for a in cached_articles]

        # Fetch from API
        response = self.client.get_trending_news(limit)

        if not response or "data" not in response:
            return []

        # Parse articles
        articles = [
            self.parser.parse_article(article_data)
            for article_data in response["data"]
        ]

        # Cache results
        if articles:
            articles_data = [self._article_to_dict(a) for a in articles]
            self.cache_manager.set_search_results(cache_key_params, articles_data)

        return articles

    def analyze_sentiment(self, text: str) -> dict | None:
        """
        Analyze sentiment of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment analysis result or None
        """
        # Create hash of text for caching
        text_hash = hashlib.md5(text.encode()).hexdigest()

        # Check cache
        cached_sentiment = self.cache_manager.get_sentiment(text_hash)
        if cached_sentiment:
            return cached_sentiment

        # Get from API
        sentiment_data = self.client.get_sentiment_analysis(text)

        if sentiment_data:
            self.cache_manager.set_sentiment(text_hash, sentiment_data)

        return sentiment_data

    def _article_to_dict(self, article: NewsArticle) -> dict:
        """
        Convert NewsArticle to dictionary for caching.
        
        Args:
            article: NewsArticle object
            
        Returns:
            Article data as dictionary
        """
        return {
            "uuid": article.uuid,
            "title": article.title,
            "description": article.description,
            "url": article.url,
            "source": article.source,
            "published_at": article.published_at.isoformat(),
            "snippet": article.content,
            "image_url": article.image_url,
            "language": article.language,
            "country": article.country,
            "entities": [
                {
                    "symbol": e.symbol,
                    "name": e.name,
                    "type": e.type,
                    "exchange": e.exchange,
                    "country": e.country,
                    "industry": e.industry,
                    "match_score": e.match_score,
                    "sentiment_score": e.sentiment_score,
                }
                for e in article.entities
            ],
            "sentiment": {
                "score": article.sentiment.score,
                "confidence": article.sentiment.confidence,
                "label": article.sentiment.label
            } if article.sentiment else None,
            "keywords": article.keywords,
            "categories": article.categories,
        }
