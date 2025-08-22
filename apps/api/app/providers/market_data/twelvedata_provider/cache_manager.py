"""
Cache management for TwelveData API responses.
Handles caching of prices, quotes, and forex data to reduce API calls.
"""

import json
import logging
from typing import Any

import pandas as pd

from ....core.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class TwelveDataCacheManager:
    """
    Manages caching for TwelveData API responses.
    Uses Redis when available for distributed caching.
    """

    # Default TTL values in seconds
    DEFAULT_PRICE_TTL = 3600  # 1 hour for historical prices
    DEFAULT_QUOTE_TTL = 60    # 1 minute for real-time quotes
    DEFAULT_FOREX_TTL = 300   # 5 minutes for forex rates

    def __init__(self, cache_enabled: bool = True):
        """
        Initialize cache manager.

        Args:
            cache_enabled: Whether caching is enabled
        """
        self.cache_enabled = cache_enabled
        self.redis_client = get_redis_client()

        # TTL settings
        self.price_cache_ttl = self.DEFAULT_PRICE_TTL
        self.quote_cache_ttl = self.DEFAULT_QUOTE_TTL
        self.forex_cache_ttl = self.DEFAULT_FOREX_TTL

    def generate_cache_key(self, prefix: str, **kwargs) -> str:
        """
        Generate a consistent cache key.

        Args:
            prefix: Cache key prefix (e.g., 'prices', 'quote')
            **kwargs: Key components

        Returns:
            Generated cache key
        """
        parts = [f"twelvedata:{prefix}"]
        for k, v in sorted(kwargs.items()):
            if v is not None:
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

    def get_price_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str
    ) -> pd.DataFrame | None:
        """
        Get cached price data for a symbol.

        Args:
            symbol: Stock symbol
            start_date: Start date ISO format
            end_date: End date ISO format
            interval: Data interval

        Returns:
            DataFrame of price data or None if not cached
        """
        cache_key = self.generate_cache_key(
            "prices",
            symbol=symbol,
            start=start_date,
            end=end_date,
            interval=interval
        )

        cached_data = self.get(cache_key)
        if cached_data:
            df = pd.DataFrame(cached_data)
            if not df.empty:
                df.index = pd.to_datetime(df.index)
                return df

        return None

    def set_price_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str,
        data: pd.DataFrame
    ) -> None:
        """
        Cache price data for a symbol.

        Args:
            symbol: Stock symbol
            start_date: Start date ISO format
            end_date: End date ISO format
            interval: Data interval
            data: DataFrame to cache
        """
        cache_key = self.generate_cache_key(
            "prices",
            symbol=symbol,
            start=start_date,
            end=end_date,
            interval=interval
        )

        self.set(cache_key, data.to_json(), self.price_cache_ttl)

    def get_quote(self, symbol: str) -> dict | None:
        """
        Get cached quote for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Quote data or None if not cached
        """
        cache_key = self.generate_cache_key("quote", symbol=symbol)
        return self.get(cache_key)

    def set_quote(self, symbol: str, quote_data: dict) -> None:
        """
        Cache quote data for a symbol.

        Args:
            symbol: Stock symbol
            quote_data: Quote data to cache
        """
        cache_key = self.generate_cache_key("quote", symbol=symbol)
        self.set(cache_key, quote_data, self.quote_cache_ttl)

    def get_forex_rate(self, from_currency: str, to_currency: str) -> float | None:
        """
        Get cached forex exchange rate.

        Args:
            from_currency: Source currency
            to_currency: Target currency

        Returns:
            Exchange rate or None if not cached
        """
        cache_key = self.generate_cache_key(
            "forex",
            from_cur=from_currency,
            to_cur=to_currency
        )
        return self.get(cache_key)

    def set_forex_rate(
        self,
        from_currency: str,
        to_currency: str,
        rate: float
    ) -> None:
        """
        Cache forex exchange rate.

        Args:
            from_currency: Source currency
            to_currency: Target currency
            rate: Exchange rate
        """
        cache_key = self.generate_cache_key(
            "forex",
            from_cur=from_currency,
            to_cur=to_currency
        )
        self.set(cache_key, rate, self.forex_cache_ttl)

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
            keys = self.redis_client.client.keys(f"twelvedata:{pattern}")
            if keys:
                return self.redis_client.client.delete(*keys)
        except Exception as e:
            logger.error(f"Cache clear failed: {e}")

        return 0
