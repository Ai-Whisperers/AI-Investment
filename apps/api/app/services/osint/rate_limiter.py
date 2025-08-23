"""
Rate Limiter for API Management
Ensures we stay within free tier limits while maximizing data collection
Implements token bucket algorithm with cascade fallback
"""

import asyncio
from typing import Dict, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting a specific API."""
    name: str
    calls_per_minute: int
    calls_per_hour: Optional[int] = None
    calls_per_day: Optional[int] = None
    calls_per_month: Optional[int] = None
    burst_size: int = 1  # Max calls in a burst
    cooldown_seconds: int = 0  # Cooldown after hitting limit
    

@dataclass
class TokenBucket:
    """Token bucket for rate limiting."""
    capacity: int
    refill_rate: float  # tokens per second
    tokens: float = field(init=False)
    last_refill: datetime = field(init=False)
    
    def __post_init__(self):
        self.tokens = float(self.capacity)
        self.last_refill = datetime.now()
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens from the bucket."""
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def _refill(self):
        """Refill tokens based on time elapsed."""
        now = datetime.now()
        elapsed = (now - self.last_refill).total_seconds()
        
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def time_until_tokens(self, tokens: int) -> float:
        """Calculate seconds until enough tokens are available."""
        self._refill()
        
        if self.tokens >= tokens:
            return 0
        
        tokens_needed = tokens - self.tokens
        return tokens_needed / self.refill_rate


class RateLimitManager:
    """
    Manages rate limiting across multiple APIs.
    Implements intelligent routing to maximize data collection within limits.
    """
    
    # Free tier configurations for popular APIs
    FREE_TIER_LIMITS = {
        "alpha_vantage": RateLimitConfig(
            name="Alpha Vantage",
            calls_per_minute=5,
            calls_per_day=500,
            burst_size=1
        ),
        "iex_cloud": RateLimitConfig(
            name="IEX Cloud",
            calls_per_minute=100,
            calls_per_month=50000,
            burst_size=10
        ),
        "polygon_io": RateLimitConfig(
            name="Polygon.io",
            calls_per_minute=5,
            burst_size=1
        ),
        "finnhub": RateLimitConfig(
            name="Finnhub",
            calls_per_minute=60,
            burst_size=5
        ),
        "coingecko": RateLimitConfig(
            name="CoinGecko",
            calls_per_minute=50,
            burst_size=5
        ),
        "newsapi": RateLimitConfig(
            name="NewsAPI",
            calls_per_minute=30,
            calls_per_day=500,
            burst_size=1
        ),
        "yahoo_finance": RateLimitConfig(
            name="Yahoo Finance",
            calls_per_minute=2000,  # Unofficial, very high
            burst_size=20
        )
    }
    
    def __init__(self):
        """Initialize rate limiter with token buckets for each API."""
        self.buckets = {}
        self.call_history = {}  # Track calls for daily/monthly limits
        self.blocked_until = {}  # APIs blocked until timestamp
        
        # Initialize token buckets
        for api_id, config in self.FREE_TIER_LIMITS.items():
            refill_rate = config.calls_per_minute / 60.0  # Convert to per second
            self.buckets[api_id] = TokenBucket(
                capacity=config.burst_size,
                refill_rate=refill_rate
            )
            self.call_history[api_id] = deque()
    
    async def acquire(self, api_id: str, tokens: int = 1) -> bool:
        """
        Acquire permission to make API call(s).
        Returns True if allowed, False if rate limited.
        """
        # Check if API is in cooldown
        if api_id in self.blocked_until:
            if datetime.now() < self.blocked_until[api_id]:
                wait_time = (self.blocked_until[api_id] - datetime.now()).total_seconds()
                logger.warning(f"{api_id} blocked for {wait_time:.1f}s")
                return False
            else:
                del self.blocked_until[api_id]
        
        config = self.FREE_TIER_LIMITS.get(api_id)
        if not config:
            logger.warning(f"No rate limit config for {api_id}")
            return True
        
        # Check daily limit
        if config.calls_per_day:
            if not self._check_time_window_limit(
                api_id, config.calls_per_day, timedelta(days=1)
            ):
                logger.warning(f"{api_id} daily limit reached")
                self._set_cooldown(api_id, 3600)  # 1 hour cooldown
                return False
        
        # Check monthly limit
        if config.calls_per_month:
            if not self._check_time_window_limit(
                api_id, config.calls_per_month, timedelta(days=30)
            ):
                logger.warning(f"{api_id} monthly limit reached")
                self._set_cooldown(api_id, 86400)  # 24 hour cooldown
                return False
        
        # Check token bucket for rate limiting
        bucket = self.buckets.get(api_id)
        if bucket and bucket.consume(tokens):
            self._record_call(api_id)
            return True
        
        # Calculate wait time
        wait_time = bucket.time_until_tokens(tokens) if bucket else 0
        logger.info(f"{api_id} rate limited, need to wait {wait_time:.1f}s")
        return False
    
    async def acquire_with_wait(self, api_id: str, tokens: int = 1, max_wait: float = 10) -> bool:
        """
        Acquire permission to make API call(s), waiting if necessary.
        """
        start_time = datetime.now()
        
        while True:
            if await self.acquire(api_id, tokens):
                return True
            
            # Check if we've waited too long
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed >= max_wait:
                return False
            
            # Wait a bit before retrying
            bucket = self.buckets.get(api_id)
            if bucket:
                wait_time = min(bucket.time_until_tokens(tokens), max_wait - elapsed)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
            else:
                await asyncio.sleep(0.1)
    
    def _check_time_window_limit(
        self, 
        api_id: str, 
        limit: int, 
        window: timedelta
    ) -> bool:
        """Check if we're within limits for a time window."""
        history = self.call_history.get(api_id, deque())
        cutoff = datetime.now() - window
        
        # Remove old entries
        while history and history[0] < cutoff:
            history.popleft()
        
        return len(history) < limit
    
    def _record_call(self, api_id: str):
        """Record an API call in history."""
        if api_id not in self.call_history:
            self.call_history[api_id] = deque()
        
        self.call_history[api_id].append(datetime.now())
        
        # Limit history size to prevent memory issues
        max_history = 10000
        if len(self.call_history[api_id]) > max_history:
            self.call_history[api_id].popleft()
    
    def _set_cooldown(self, api_id: str, seconds: int):
        """Set a cooldown period for an API."""
        self.blocked_until[api_id] = datetime.now() + timedelta(seconds=seconds)
        logger.info(f"{api_id} blocked for {seconds}s")
    
    async def execute_with_fallback(
        self, 
        api_calls: Dict[str, Callable],
        timeout: float = 30
    ) -> Optional[any]:
        """
        Execute API calls with automatic fallback.
        Tries APIs in order until one succeeds.
        """
        for api_id, call_func in api_calls.items():
            if await self.acquire(api_id):
                try:
                    result = await asyncio.wait_for(call_func(), timeout=timeout)
                    if result:
                        return result
                except asyncio.TimeoutError:
                    logger.error(f"{api_id} call timed out")
                except Exception as e:
                    logger.error(f"{api_id} call failed: {e}")
        
        logger.error("All API calls failed")
        return None
    
    def get_status(self) -> Dict:
        """Get current rate limiter status."""
        status = {
            "apis": {},
            "blocked": [],
            "total_calls": 0
        }
        
        for api_id, config in self.FREE_TIER_LIMITS.items():
            bucket = self.buckets.get(api_id)
            history = self.call_history.get(api_id, deque())
            
            # Calculate usage percentages
            minute_usage = len([c for c in history 
                              if c > datetime.now() - timedelta(minutes=1)])
            day_usage = len([c for c in history 
                           if c > datetime.now() - timedelta(days=1)])
            
            api_status = {
                "name": config.name,
                "tokens_available": bucket.tokens if bucket else 0,
                "calls_last_minute": minute_usage,
                "calls_last_day": day_usage,
                "minute_usage_pct": (minute_usage / config.calls_per_minute * 100) 
                                  if config.calls_per_minute else 0,
                "day_usage_pct": (day_usage / config.calls_per_day * 100) 
                               if config.calls_per_day else 0
            }
            
            # Check if blocked
            if api_id in self.blocked_until:
                if datetime.now() < self.blocked_until[api_id]:
                    api_status["blocked_until"] = self.blocked_until[api_id].isoformat()
                    status["blocked"].append(api_id)
            
            status["apis"][api_id] = api_status
            status["total_calls"] += day_usage
        
        return status
    
    def optimize_api_selection(self, required_calls: int) -> Optional[str]:
        """
        Select the best API for making calls based on availability.
        Returns API ID with most available capacity.
        """
        best_api = None
        best_score = -1
        
        for api_id, config in self.FREE_TIER_LIMITS.items():
            # Skip blocked APIs
            if api_id in self.blocked_until:
                if datetime.now() < self.blocked_until[api_id]:
                    continue
            
            bucket = self.buckets.get(api_id)
            if not bucket:
                continue
            
            # Calculate availability score
            tokens = bucket.tokens
            capacity = config.calls_per_minute
            
            # Prefer APIs with more available tokens and higher capacity
            score = (tokens / required_calls) * (capacity / 60)
            
            # Bonus for APIs without daily limits
            if not config.calls_per_day:
                score *= 1.5
            
            if score > best_score:
                best_score = score
                best_api = api_id
        
        return best_api