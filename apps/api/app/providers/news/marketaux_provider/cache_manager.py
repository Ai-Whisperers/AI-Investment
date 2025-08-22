"""
Cache management for MarketAux news data.
Handles caching of articles, searches, and sentiment analysis.
"""

import json
import logging
from typing import Any

from ....core.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class MarketAuxCacheManager:
    """
    Manages caching for MarketAux news data.
    Uses Redis when available for distributed caching.
    """

    # Default TTL values in seconds
    DEFAULT_NEWS_TTL = 900       # 15 minutes for news articles
    DEFAULT_SENTIMENT_TTL = 3600  # 1 hour for sentiment analysis
    DEFAULT_ENTITY_TTL = 1800     # 30 minutes for entity data

    def __init__(self, cache_enabled: bool = True):
        """
        Initialize cache manager.

        Args:
            cache_enabled: Whether caching is enabled
        """
        self.cache_enabled = cache_enabled
        self.redis_client = get_redis_client()

        # TTL settings
        self.news_cache_ttl = self.DEFAULT_NEWS_TTL
        self.sentiment_cache_ttl = self.DEFAULT_SENTIMENT_TTL
        self.entity_cache_ttl = self.DEFAULT_ENTITY_TTL

    def generate_cache_key(self, prefix: str, **kwargs) -> str:
        """
        Generate a consistent cache key.

        Args:
            prefix: Cache key prefix (e.g., 'search', 'article')
            **kwargs: Key components

        Returns:
            Generated cache key
        """
        parts = [f"marketaux:{prefix}"]
        for k, v in sorted(kwargs.items()):
            if v is not None:
                if isinstance(v, list):
                    v = ",".join(str(x) for x in v)
                parts.append(f"{k}:{v}")
        return ":".join(parts)

    def get(self, cache_key: str) -> Any | None:
        """
        Get data from cache.

        Args:
            cache_key: Cache key to retrieve

        Returns:
            Cached data or None if not found
        """
        if not self.cache_enabled or not self.redis_client.is_connected:
            return None

        try:
            cached = self.redis_client.get(cache_key)
            if cached:
                logger.debug(f"Cache hit: {cache_key}")
                return json.loads(cached) if isinstance(cached, str) else cached
        except Exception as e:
            logger.debug(f"Cache get failed: {e}")

        return None

    def set(self, cache_key: str, data: Any, ttl: int | None = None) -> None:
        """
        Store data in cache.

        Args:
            cache_key: Cache key to store under
            data: Data to cache
            ttl: Time to live in seconds (optional)
        """
        if not self.cache_enabled or not self.redis_client.is_connected:
            return

        try:
            json_data = json.dumps(data) if not isinstance(data, str) else data
            self.redis_client.set(cache_key, json_data, expire=ttl)
            logger.debug(f"Cached: {cache_key}, TTL: {ttl}s")
        except Exception as e:
            logger.debug(f"Cache set failed: {e}")

    def get_search_results(self, search_params: dict) -> list[dict] | None:
        """
        Get cached search results.

        Args:
            search_params: Search parameters

        Returns:
            List of cached articles or None
        """
        cache_key = self.generate_cache_key("search", **search_params)
        return self.get(cache_key)

    def set_search_results(
        self,
        search_params: dict,
        articles: list[dict]
    ) -> None:
        """
        Cache search results.

        Args:
            search_params: Search parameters
            articles: Articles to cache
        """
        cache_key = self.generate_cache_key("search", **search_params)
        self.set(cache_key, articles, self.news_cache_ttl)

    def get_article(self, article_id: str) -> dict | None:
        """
        Get cached article.

        Args:
            article_id: Article UUID

        Returns:
            Cached article data or None
        """
        cache_key = self.generate_cache_key("article", uuid=article_id)
        return self.get(cache_key)

    def set_article(self, article_id: str, article_data: dict) -> None:
        """
        Cache article data.

        Args:
            article_id: Article UUID
            article_data: Article data to cache
        """
        cache_key = self.generate_cache_key("article", uuid=article_id)
        self.set(cache_key, article_data, self.news_cache_ttl)

    def get_sentiment(self, text_hash: str) -> dict | None:
        """
        Get cached sentiment analysis.

        Args:
            text_hash: Hash of the analyzed text

        Returns:
            Cached sentiment data or None
        """
        cache_key = self.generate_cache_key("sentiment", hash=text_hash)
        return self.get(cache_key)

    def set_sentiment(self, text_hash: str, sentiment_data: dict) -> None:
        """
        Cache sentiment analysis.

        Args:
            text_hash: Hash of the analyzed text
            sentiment_data: Sentiment analysis result
        """
        cache_key = self.generate_cache_key("sentiment", hash=text_hash)
        self.set(cache_key, sentiment_data, self.sentiment_cache_ttl)

    def clear_cache(self, pattern: str = "*") -> int:
        """
        Clear cache entries matching pattern.

        Args:
            pattern: Redis key pattern to match

        Returns:
            Number of keys deleted
        """
        if not self.redis_client.is_connected:
            return 0

        try:
            keys = self.redis_client.client.keys(f"marketaux:{pattern}")
            if keys:
                return self.redis_client.client.delete(*keys)
        except Exception as e:
            logger.error(f"Cache clear failed: {e}")

        return 0
