"""
Rate limiting module for API calls.
"""

import time
import json
import logging
from typing import Optional

from ...core.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for API calls with Redis support for distributed systems."""

    def __init__(
        self,
        credits_per_minute: int = 8,
        redis_key_prefix: str = "rate_limit"
    ):
        """
        Initialize rate limiter.
        
        Args:
            credits_per_minute: Maximum API credits per minute
            redis_key_prefix: Prefix for Redis keys
        """
        self.credits_per_minute = credits_per_minute
        self.credits_used = []
        self.redis_client = get_redis_client()
        self.redis_key = f"{redis_key_prefix}:credits"
        self.window_seconds = 60  # 1 minute window

    def wait_if_needed(self, credits_required: int = 1) -> float:
        """
        Wait if rate limit would be exceeded.
        
        Args:
            credits_required: Number of credits required for operation
            
        Returns:
            Time waited in seconds
        """
        now = time.time()
        wait_time = 0

        # Try to use Redis for distributed rate limiting
        if self.redis_client.is_connected:
            wait_time = self._check_redis_rate_limit(credits_required, now)
        else:
            wait_time = self._check_local_rate_limit(credits_required, now)

        if wait_time > 0:
            logger.info(f"Rate limit reached. Waiting {wait_time:.1f} seconds...")
            time.sleep(wait_time)

        # Record new credit usage
        self._record_credit_usage(credits_required, now)
        
        return wait_time

    def _check_redis_rate_limit(
        self,
        credits_required: int,
        current_time: float
    ) -> float:
        """Check rate limit using Redis."""
        try:
            # Get credit usage from Redis
            usage_data = self.redis_client.get(self.redis_key)
            if usage_data:
                self.credits_used = json.loads(usage_data)
            
            # Clean up old credits
            self.credits_used = [
                t for t in self.credits_used 
                if current_time - t < self.window_seconds
            ]
            
            # Check if we need to wait
            if len(self.credits_used) + credits_required > self.credits_per_minute:
                oldest_credit = min(self.credits_used)
                return self.window_seconds - (current_time - oldest_credit) + 1
            
            return 0
            
        except Exception as e:
            logger.warning(f"Failed to check Redis rate limit: {e}")
            # Fall back to local rate limiting
            return self._check_local_rate_limit(credits_required, current_time)

    def _check_local_rate_limit(
        self,
        credits_required: int,
        current_time: float
    ) -> float:
        """Check rate limit using local memory."""
        # Remove credits older than window
        self.credits_used = [
            t for t in self.credits_used 
            if current_time - t < self.window_seconds
        ]

        # Check if we need to wait
        if len(self.credits_used) + credits_required > self.credits_per_minute:
            oldest_credit = min(self.credits_used)
            return self.window_seconds - (current_time - oldest_credit) + 1

        return 0

    def _record_credit_usage(self, credits_required: int, current_time: float):
        """Record credit usage in both local and Redis."""
        # Record locally
        for _ in range(credits_required):
            self.credits_used.append(current_time)

        # Update Redis if available
        if self.redis_client.is_connected:
            try:
                self.redis_client.set(
                    self.redis_key,
                    json.dumps(self.credits_used),
                    expire=self.window_seconds * 2  # Expire after 2 windows
                )
            except Exception as e:
                logger.warning(f"Failed to update rate limit in Redis: {e}")

    def get_remaining_credits(self) -> int:
        """Get number of remaining credits in current window."""
        now = time.time()
        
        # Clean up old credits
        self.credits_used = [
            t for t in self.credits_used 
            if now - t < self.window_seconds
        ]
        
        return max(0, self.credits_per_minute - len(self.credits_used))

    def reset(self):
        """Reset rate limiter (clear all credit usage)."""
        self.credits_used = []
        
        if self.redis_client.is_connected:
            try:
                self.redis_client.delete(self.redis_key)
            except Exception as e:
                logger.warning(f"Failed to reset rate limit in Redis: {e}")


class BatchRateLimiter(RateLimiter):
    """Extended rate limiter for batch operations."""

    def __init__(
        self,
        credits_per_minute: int = 8,
        batch_multiplier: float = 0.5,
        redis_key_prefix: str = "batch_rate_limit"
    ):
        """
        Initialize batch rate limiter.
        
        Args:
            credits_per_minute: Maximum API credits per minute
            batch_multiplier: Credit cost multiplier for batch operations
            redis_key_prefix: Prefix for Redis keys
        """
        super().__init__(credits_per_minute, redis_key_prefix)
        self.batch_multiplier = batch_multiplier

    def calculate_batch_credits(self, batch_size: int) -> int:
        """
        Calculate credits required for batch operation.
        
        Args:
            batch_size: Number of items in batch
            
        Returns:
            Number of credits required
        """
        # Batch operations often cost less per item
        return max(1, int(batch_size * self.batch_multiplier))

    def wait_for_batch(self, batch_size: int) -> float:
        """
        Wait if needed for batch operation.
        
        Args:
            batch_size: Number of items in batch
            
        Returns:
            Time waited in seconds
        """
        credits_required = self.calculate_batch_credits(batch_size)
        return self.wait_if_needed(credits_required)