"""
Rate limiting implementation for TwelveData API.
Handles distributed rate limiting via Redis for multi-instance deployments.
"""

import json
import logging
import time

from ....core.config import settings
from ....core.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class TwelveDataRateLimiter:
    """
    Rate limiter specific to TwelveData API.
    Handles distributed rate limiting via Redis when available.
    """

    def __init__(self, credits_per_minute: int = None):
        """
        Initialize rate limiter.

        Args:
            credits_per_minute: API credits per minute (defaults to settings)
        """
        self.credits_per_minute = credits_per_minute or settings.TWELVEDATA_RATE_LIMIT
        self.credits_used: list[float] = []
        self.redis_client = get_redis_client()
        self.redis_key = "twelvedata:rate_limit"

    def wait_if_needed(self, credits_required: int = 1) -> None:
        """
        Wait if rate limit would be exceeded.

        Args:
            credits_required: Number of API credits required for the request
        """
        now = time.time()

        # Try Redis for distributed rate limiting
        if self.redis_client.is_connected:
            try:
                usage_data = self.redis_client.get(self.redis_key)
                if usage_data:
                    self.credits_used = json.loads(usage_data)
            except Exception as e:
                logger.debug(f"Redis rate limit fetch failed: {e}")

        # Clean old credits (older than 60 seconds)
        self.credits_used = [t for t in self.credits_used if now - t < 60]

        # Check if we need to wait
        if len(self.credits_used) + credits_required > self.credits_per_minute:
            oldest_credit = min(self.credits_used)
            wait_time = 60 - (now - oldest_credit) + 1
            logger.info(f"Rate limit: waiting {wait_time:.1f}s...")
            time.sleep(wait_time)

            # Refresh timestamp and clean again
            now = time.time()
            self.credits_used = [t for t in self.credits_used if now - t < 60]

        # Record usage
        for _ in range(credits_required):
            self.credits_used.append(now)

        # Update Redis for distributed rate limiting
        if self.redis_client.is_connected:
            try:
                self.redis_client.set(
                    self.redis_key,
                    json.dumps(self.credits_used),
                    expire=120  # Keep for 2 minutes
                )
            except Exception as e:
                logger.debug(f"Redis rate limit update failed: {e}")

    def get_available_credits(self) -> int:
        """
        Get number of available API credits.

        Returns:
            Number of credits available in current minute
        """
        now = time.time()
        self.credits_used = [t for t in self.credits_used if now - t < 60]
        return self.credits_per_minute - len(self.credits_used)

    def reset(self) -> None:
        """Reset rate limiter state."""
        self.credits_used = []

        if self.redis_client.is_connected:
            try:
                self.redis_client.delete(self.redis_key)
            except Exception as e:
                logger.debug(f"Redis rate limit reset failed: {e}")
