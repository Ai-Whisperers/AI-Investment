"""
Metrics endpoints for system monitoring and performance tracking.
Provides cache statistics, API usage metrics, and performance indicators.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import traceback

from ..core.database import get_db
from ..core.config import settings
from ..models.user import User
from ..utils.token_dep import get_current_user, require_admin
from ..utils.cache_utils import CacheManager
from ..core.redis_client import get_redis_client

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/cache-status")
def check_cache_status():
    """Check Redis cache status and statistics."""
    try:
        redis_client = get_redis_client()

        # Basic connection check
        is_connected = redis_client.health_check()

        if not is_connected:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "disconnected",
                "message": "Redis cache is not available. Running without cache.",
                "stats": {},
            }

        # Get detailed stats
        stats = CacheManager.get_cache_stats()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "connected",
            "stats": stats,
            "message": f"Cache is operational with {stats.get('total_entries', 0)} entries",
        }

    except Exception as e:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc(),
        }


@router.post("/cache-invalidate")
def invalidate_cache(pattern: str = "*"):
    """Invalidate cache entries matching pattern."""
    try:
        if pattern == "*":
            count = CacheManager.invalidate_all()
            message = f"Invalidated all {count} cache entries"
        elif pattern == "index":
            count = CacheManager.invalidate_index_data()
            message = f"Invalidated {count} index-related cache entries"
        elif pattern == "market":
            count = CacheManager.invalidate_market_data()
            message = f"Invalidated {count} market data cache entries"
        else:
            from ..utils.cache_utils import invalidate_pattern
            count = invalidate_pattern(pattern)
            message = f"Invalidated {count} entries matching pattern: {pattern}"

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
            "invalidated_count": count,
            "message": message,
        }

    except Exception as e:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc(),
        }


@router.post("/clear-market-cache")
def clear_market_cache(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Clear all market data cache (admin only)."""
    try:
        redis_client = get_redis_client()

        if not redis_client.is_connected:
            return {"status": "error", "message": "Redis not connected"}

        # Clear specific cache patterns
        patterns = ["prices:*", "quote:*", "forex:*", "twelvedata:*"]
        total_deleted = 0

        for pattern in patterns:
            keys = redis_client.client.keys(pattern)
            if keys:
                deleted = redis_client.client.delete(*keys)
                total_deleted += deleted

        # Also clear via CacheManager
        CacheManager.invalidate_market_data()

        return {
            "status": "success",
            "message": f"Cleared {total_deleted} cache entries",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc(),
        }


@router.get("/twelvedata-status")
def get_twelvedata_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get TwelveData API status including usage, rate limits, and cache statistics."""
    try:
        from ..services.twelvedata import get_twelvedata_service

        service = get_twelvedata_service()
        redis_client = get_redis_client()

        # Get API usage from TwelveData
        api_usage = service.get_api_usage()

        # Get rate limiter status
        rate_limit_info = {
            "credits_per_minute": service.rate_limiter.credits_per_minute,
            "credits_used_last_minute": len(service.rate_limiter.credits_used),
            "credits_available": service.rate_limiter.credits_per_minute - len(service.rate_limiter.credits_used),
        }

        # Get cache statistics if Redis is available
        cache_stats = {
            "enabled": service.cache_enabled,
            "redis_connected": redis_client.is_connected,
        }

        if redis_client.is_connected:
            try:
                # Get cache keys count
                cache_keys = redis_client.client.keys("prices:*")
                quote_keys = redis_client.client.keys("quote:*")
                forex_keys = redis_client.client.keys("forex:*")

                cache_stats.update({
                    "price_cache_entries": len(cache_keys),
                    "quote_cache_entries": len(quote_keys),
                    "forex_cache_entries": len(forex_keys),
                    "total_cache_entries": len(cache_keys) + len(quote_keys) + len(forex_keys),
                })
            except Exception as e:
                cache_stats["error"] = str(e)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy",
            "api_usage": api_usage,
            "rate_limit": rate_limit_info,
            "cache": cache_stats,
            "configuration": {
                "plan": settings.TWELVEDATA_PLAN,
                "rate_limit": settings.TWELVEDATA_RATE_LIMIT,
                "refresh_mode": settings.REFRESH_MODE,
                "cache_enabled": settings.ENABLE_MARKET_DATA_CACHE,
            },
        }

    except Exception as e:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc(),
        }


@router.get("/performance")
def get_performance_metrics(db: Session = Depends(get_db)):
    """Get system performance metrics."""
    try:
        from ..services.performance import calculate_portfolio_metrics

        # Calculate current performance metrics
        metrics = calculate_portfolio_metrics(db)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
            "metrics": metrics
        }

    except Exception as e:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }