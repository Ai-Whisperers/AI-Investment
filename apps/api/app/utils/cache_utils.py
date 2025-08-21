"""Cache utilities and decorators."""

import functools
import hashlib
import logging
from collections.abc import Callable

from ..core.config import settings
from ..core.redis_client import get_redis_client

logger = logging.getLogger(__name__)


def generate_cache_key(*args, **kwargs) -> str:
    """Generate a cache key from function arguments using SHA256."""
    # Combine args and kwargs into a single string
    key_parts = []

    # Add positional arguments
    for arg in args:
        if hasattr(arg, "__dict__"):
            # Skip complex objects like database sessions
            continue
        key_parts.append(str(arg))

    # Add keyword arguments
    for k, v in sorted(kwargs.items()):
        if hasattr(v, "__dict__"):
            continue
        key_parts.append(f"{k}={v}")

    # Create SHA256 hash of the key parts (more secure than MD5)
    key_string = ":".join(key_parts)
    # Use SHA256 for better security and collision resistance
    return hashlib.sha256(key_string.encode()).hexdigest()


def cache_result(
    prefix: str,
    expire: int | None = None,
    key_func: Callable | None = None,
    include_user: bool = True,
):
    """
    Decorator to cache function results in Redis.

    Args:
        prefix: Cache key prefix (e.g., "index_history")
        expire: Expiration time in seconds (default from config)
        key_func: Custom function to generate cache key
        include_user: Include user context in cache key for isolation
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Skip caching if Redis is not available
            redis_client = get_redis_client()
            if not redis_client.is_connected:
                return func(*args, **kwargs)

            # Extract user context if available and requested
            user_prefix = ""
            if include_user:
                # Look for user in kwargs or args (common patterns)
                user = kwargs.get("user") or kwargs.get("current_user")
                if user and hasattr(user, "id"):
                    user_prefix = f"u{user.id}:"

            # Generate cache key
            if key_func:
                cache_key = f"{prefix}:{user_prefix}{key_func(*args, **kwargs)}"
            else:
                cache_key = (
                    f"{prefix}:{user_prefix}{generate_cache_key(*args, **kwargs)}"
                )

            # Try to get from cache
            try:
                cached_value = redis_client.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"Cache hit for key: {cache_key}")
                    return cached_value
            except Exception as e:
                logger.warning(f"Cache get failed: {e}")

            # Execute function
            result = func(*args, **kwargs)

            # Store in cache
            try:
                ttl = expire or settings.CACHE_TTL_SECONDS
                redis_client.set(cache_key, result, expire=ttl)
                logger.debug(f"Cached result for key: {cache_key}, TTL: {ttl}s")
            except Exception as e:
                logger.warning(f"Cache set failed: {e}")

            return result

        # Add method to invalidate cache
        def invalidate(*args, **kwargs):
            redis_client = get_redis_client()
            if key_func:
                cache_key = f"{prefix}:{key_func(*args, **kwargs)}"
            else:
                cache_key = f"{prefix}:{generate_cache_key(*args, **kwargs)}"

            redis_client.delete(cache_key)
            logger.debug(f"Invalidated cache for key: {cache_key}")

        wrapper.invalidate = invalidate
        wrapper.cache_prefix = prefix

        return wrapper

    return decorator


def invalidate_pattern(pattern: str) -> int:
    """
    Invalidate all cache keys matching a pattern.

    Args:
        pattern: Redis key pattern (e.g., "index_*")

    Returns:
        Number of keys deleted
    """
    redis_client = get_redis_client()
    count = redis_client.flush_pattern(pattern)
    logger.info(f"Invalidated {count} cache keys matching pattern: {pattern}")
    return count


class CacheManager:
    """Manager for application-wide cache operations."""

    CACHE_PREFIXES = {
        "index_history": "idx:hist",
        "index_current": "idx:curr",
        "asset_history": "asset:hist",
        "benchmark": "bench",
        "portfolio_metrics": "metrics",
        "strategy_config": "strategy",
        "market_data": "market",
        "simulation": "sim",
    }

    @classmethod
    def invalidate_index_data(cls):
        """Invalidate all index-related cache."""
        patterns = [
            f"{cls.CACHE_PREFIXES['index_history']}:*",
            f"{cls.CACHE_PREFIXES['index_current']}:*",
            f"{cls.CACHE_PREFIXES['portfolio_metrics']}:*",
        ]

        total = 0
        for pattern in patterns:
            total += invalidate_pattern(pattern)

        logger.info(f"Invalidated {total} index-related cache entries")
        return total

    @classmethod
    def invalidate_market_data(cls):
        """Invalidate all market data cache."""
        patterns = [
            f"{cls.CACHE_PREFIXES['market_data']}:*",
            f"{cls.CACHE_PREFIXES['asset_history']}:*",
            f"{cls.CACHE_PREFIXES['benchmark']}:*",
        ]

        total = 0
        for pattern in patterns:
            total += invalidate_pattern(pattern)

        logger.info(f"Invalidated {total} market data cache entries")
        return total

    @classmethod
    def invalidate_all(cls):
        """Invalidate all application cache."""
        total = 0
        for prefix in cls.CACHE_PREFIXES.values():
            total += invalidate_pattern(f"{prefix}:*")

        logger.info(f"Invalidated {total} total cache entries")
        return total

    @classmethod
    def get_cache_stats(cls) -> dict:
        """Get cache statistics."""
        redis_client = get_redis_client()

        if not redis_client.is_connected:
            return {"status": "disconnected", "entries": 0}

        stats = {"status": "connected", "prefixes": {}}

        try:
            for name, prefix in cls.CACHE_PREFIXES.items():
                keys = redis_client.client.keys(f"{prefix}:*")
                stats["prefixes"][name] = len(keys)

            stats["total_entries"] = sum(stats["prefixes"].values())

            # Get Redis info
            info = redis_client.client.info()
            stats["memory_used"] = info.get("used_memory_human", "N/A")
            stats["connected_clients"] = info.get("connected_clients", 0)

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            stats["error"] = str(e)

        return stats


# Convenience decorators for common cache scenarios
def cache_for_5min(prefix: str):
    """Cache for 5 minutes."""
    return cache_result(prefix, expire=300)


def cache_for_1hour(prefix: str):
    """Cache for 1 hour."""
    return cache_result(prefix, expire=3600)


def cache_for_1day(prefix: str):
    """Cache for 1 day."""
    return cache_result(prefix, expire=86400)
