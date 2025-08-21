"""
Simple caching utility with Redis (optional) or in-memory fallback.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

# Try to import Redis
try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not installed. Using in-memory cache.")


class CacheManager:
    """Simple cache manager with Redis or in-memory fallback."""

    def __init__(self):
        self.redis_client = None
        self.memory_cache = {}

        # Try to connect to Redis if available
        if REDIS_AVAILABLE and (redis_url := os.getenv("REDIS_URL")):
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
                logger.info("Connected to Redis cache")
            except Exception as e:
                logger.warning(f"Could not connect to Redis: {e}. Using memory cache.")
                self.redis_client = None

    def get(self, key: str) -> Any | None:
        """Get value from cache."""
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                return json.loads(value) if value else None
            except Exception as e:
                logger.error(f"Redis get error: {e}")
                return None
        else:
            # In-memory fallback
            if key in self.memory_cache:
                item = self.memory_cache[key]
                if item["expires"] > datetime.now():
                    return item["value"]
                else:
                    del self.memory_cache[key]
            return None

    def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL in seconds."""
        if self.redis_client:
            try:
                self.redis_client.setex(key, ttl, json.dumps(value))
            except Exception as e:
                logger.error(f"Redis set error: {e}")
        else:
            # In-memory fallback
            self.memory_cache[key] = {
                "value": value,
                "expires": datetime.now() + timedelta(seconds=ttl),
            }

            # Clean up old entries (simple cleanup)
            if len(self.memory_cache) > 100:
                now = datetime.now()
                self.memory_cache = {
                    k: v for k, v in self.memory_cache.items() if v["expires"] > now
                }

    def delete(self, key: str):
        """Delete key from cache."""
        if self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception as e:
                logger.error(f"Redis delete error: {e}")
        else:
            self.memory_cache.pop(key, None)

    def clear_pattern(self, pattern: str):
        """Clear all keys matching pattern."""
        if self.redis_client:
            try:
                for key in self.redis_client.scan_iter(match=pattern):
                    self.redis_client.delete(key)
            except Exception as e:
                logger.error(f"Redis clear pattern error: {e}")
        else:
            # In-memory pattern matching
            keys_to_delete = [
                k for k in self.memory_cache.keys() if pattern.replace("*", "") in k
            ]
            for key in keys_to_delete:
                del self.memory_cache[key]


# Singleton cache instance
cache = CacheManager()


# Decorator for caching function results
def cached(ttl: int = 300, key_prefix: str = ""):
    """Decorator to cache function results."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"

            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return result

            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            logger.debug(f"Cached result for {cache_key}")
            return result

        return wrapper

    return decorator
