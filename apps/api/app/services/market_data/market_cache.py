"""
Caching module for market data.
"""

import json
import logging
from datetime import date, datetime
from typing import Any

from ...core.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class MarketDataCache:
    """Cache manager for market data with Redis backend."""

    # Default TTL values in seconds
    DEFAULT_TTL = {
        'price': 3600,      # 1 hour for historical prices
        'quote': 60,        # 1 minute for real-time quotes
        'forex': 300,       # 5 minutes for forex rates
        'fundamentals': 86400,  # 24 hours for fundamental data
        'dividends': 86400,     # 24 hours for dividend data
        'profile': 604800,      # 7 days for company profiles
    }

    def __init__(self, cache_enabled: bool = True):
        """
        Initialize market data cache.

        Args:
            cache_enabled: Whether caching is enabled
        """
        self.cache_enabled = cache_enabled
        self.redis_client = get_redis_client()
        self.cache_prefix = "market_data"

    def get_cache_key(self, data_type: str, **params) -> str:
        """
        Generate cache key from parameters.

        Args:
            data_type: Type of data (price, quote, forex, etc.)
            **params: Parameters to include in key

        Returns:
            Cache key string
        """
        key_parts = [self.cache_prefix, data_type]

        for key, value in sorted(params.items()):
            if value is not None:
                # Convert dates to strings
                if isinstance(value, datetime | date):
                    value = value.isoformat()
                key_parts.append(f"{key}:{value}")

        return ":".join(key_parts)

    def get(
        self,
        data_type: str,
        **params
    ) -> Any | None:
        """
        Get data from cache.

        Args:
            data_type: Type of data
            **params: Parameters for cache key

        Returns:
            Cached data or None if not found/expired
        """
        if not self.cache_enabled or not self.redis_client.is_connected:
            return None

        cache_key = self.get_cache_key(data_type, **params)

        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for {cache_key}")
                return json.loads(cached_data)
            logger.debug(f"Cache miss for {cache_key}")
            return None
        except Exception as e:
            logger.warning(f"Failed to get from cache: {e}")
            return None

    def set(
        self,
        data: Any,
        data_type: str,
        ttl: int | None = None,
        **params
    ) -> bool:
        """
        Store data in cache.

        Args:
            data: Data to cache
            data_type: Type of data
            ttl: Time to live in seconds (uses default if not specified)
            **params: Parameters for cache key

        Returns:
            True if successfully cached
        """
        if not self.cache_enabled or not self.redis_client.is_connected:
            return False

        cache_key = self.get_cache_key(data_type, **params)

        # Use default TTL if not specified
        if ttl is None:
            ttl = self.DEFAULT_TTL.get(data_type, 3600)

        try:
            self.redis_client.set(
                cache_key,
                json.dumps(data, default=str),
                expire=ttl
            )
            logger.debug(f"Cached {cache_key} with TTL {ttl}s")
            return True
        except Exception as e:
            logger.warning(f"Failed to cache data: {e}")
            return False

    def delete(self, data_type: str, **params) -> bool:
        """
        Delete data from cache.

        Args:
            data_type: Type of data
            **params: Parameters for cache key

        Returns:
            True if successfully deleted
        """
        if not self.redis_client.is_connected:
            return False

        cache_key = self.get_cache_key(data_type, **params)

        try:
            result = self.redis_client.delete(cache_key)
            logger.debug(f"Deleted cache key {cache_key}")
            return result > 0
        except Exception as e:
            logger.warning(f"Failed to delete from cache: {e}")
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate cache entries matching pattern.

        Args:
            pattern: Pattern to match (e.g., "market_data:price:*")

        Returns:
            Number of keys deleted
        """
        if not self.redis_client.is_connected:
            return 0

        try:
            # Note: This requires SCAN command support
            keys = []
            cursor = 0

            # Use SCAN to find matching keys
            while True:
                cursor, partial_keys = self.redis_client.client.scan(
                    cursor,
                    match=pattern,
                    count=100
                )
                keys.extend(partial_keys)
                if cursor == 0:
                    break

            # Delete all matching keys
            if keys:
                deleted = self.redis_client.client.delete(*keys)
                logger.info(f"Invalidated {deleted} cache entries matching {pattern}")
                return deleted

            return 0

        except Exception as e:
            logger.warning(f"Failed to invalidate cache pattern: {e}")
            return 0

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        stats = {
            'enabled': self.cache_enabled,
            'connected': self.redis_client.is_connected if self.redis_client else False,
            'keys': 0,
            'memory_usage': 'unknown'
        }

        if self.redis_client.is_connected:
            try:
                info = self.redis_client.client.info('memory')
                stats['memory_usage'] = info.get('used_memory_human', 'unknown')

                # Count keys with our prefix
                pattern = f"{self.cache_prefix}:*"
                cursor = 0
                key_count = 0

                while True:
                    cursor, keys = self.redis_client.client.scan(
                        cursor,
                        match=pattern,
                        count=100
                    )
                    key_count += len(keys)
                    if cursor == 0:
                        break

                stats['keys'] = key_count

            except Exception as e:
                logger.warning(f"Failed to get cache stats: {e}")

        return stats


class CacheDecorator:
    """Decorator for caching function results."""

    def __init__(
        self,
        data_type: str,
        ttl: int | None = None,
        key_params: list | None = None
    ):
        """
        Initialize cache decorator.

        Args:
            data_type: Type of data being cached
            ttl: Time to live in seconds
            key_params: List of parameter names to include in cache key
        """
        self.data_type = data_type
        self.ttl = ttl
        self.key_params = key_params
        self.cache = MarketDataCache()

    def __call__(self, func):
        """Decorator implementation."""
        def wrapper(*args, **kwargs):
            # Build cache key parameters
            cache_params = {}

            if self.key_params:
                # Use specified parameters
                for param in self.key_params:
                    if param in kwargs:
                        cache_params[param] = kwargs[param]
            else:
                # Use all kwargs
                cache_params = kwargs

            # Try to get from cache
            cached_result = self.cache.get(self.data_type, **cache_params)
            if cached_result is not None:
                return cached_result

            # Call original function
            result = func(*args, **kwargs)

            # Cache the result
            if result is not None:
                self.cache.set(result, self.data_type, self.ttl, **cache_params)

            return result

        return wrapper
