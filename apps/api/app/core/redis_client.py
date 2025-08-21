"""Redis client configuration and connection management."""

import json
import logging
from datetime import timedelta
from typing import Any

import redis

from .config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client wrapper with connection pooling and error handling."""

    def __init__(self):
        """Initialize Redis client with connection pool."""
        self.redis_url = settings.REDIS_URL if hasattr(settings, "REDIS_URL") else None
        self.client: redis.Redis | None = None
        self.is_connected = False

        if self.redis_url:
            try:
                # Create connection pool for better performance
                pool = redis.ConnectionPool.from_url(
                    self.redis_url,
                    max_connections=50,
                    decode_responses=True,
                    socket_keepalive=True,
                    socket_keepalive_options={
                        1: 1,  # TCP_KEEPIDLE
                        2: 1,  # TCP_KEEPINTVL
                        3: 5,  # TCP_KEEPCNT
                    },
                )
                self.client = redis.Redis(connection_pool=pool)

                # Test connection
                self.client.ping()
                self.is_connected = True
                logger.info("Redis connection established successfully")

            except (redis.ConnectionError, redis.TimeoutError) as e:
                logger.warning(f"Redis connection failed: {e}. Cache will be disabled.")
                self.client = None
                self.is_connected = False
        else:
            logger.info("Redis URL not configured. Cache will be disabled.")

    def get(self, key: str) -> Any | None:
        """Get value from cache."""
        if not self.is_connected:
            return None

        try:
            value = self.client.get(key)
            if value:
                # Try to deserialize JSON
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            return None

    def set(
        self, key: str, value: Any, expire: int | timedelta | None = None
    ) -> bool:
        """Set value in cache with optional expiration."""
        if not self.is_connected:
            return False

        try:
            # Serialize to JSON if not string
            if not isinstance(value, str):
                value = json.dumps(value)

            # Convert timedelta to seconds
            if isinstance(expire, timedelta):
                expire = int(expire.total_seconds())

            if expire:
                return self.client.setex(key, expire, value)
            else:
                return self.client.set(key, value)
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.is_connected:
            return False

        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"Redis DELETE error for key {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.is_connected:
            return False

        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Redis EXISTS error for key {key}: {e}")
            return False

    def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for a key."""
        if not self.is_connected:
            return False

        try:
            return bool(self.client.expire(key, seconds))
        except Exception as e:
            logger.error(f"Redis EXPIRE error for key {key}: {e}")
            return False

    def flush_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        if not self.is_connected:
            return 0

        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis flush pattern error for {pattern}: {e}")
            return 0

    def health_check(self) -> bool:
        """Check Redis connection health."""
        if not self.client:
            return False

        try:
            self.client.ping()
            self.is_connected = True
            return True
        except Exception:
            self.is_connected = False
            return False


# Global Redis client instance
redis_client = RedisClient()


def get_redis_client() -> RedisClient:
    """Get Redis client instance."""
    return redis_client
