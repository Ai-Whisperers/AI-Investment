"""
Market data refresh background tasks.
Handles fetching and updating market data asynchronously.
"""

import logging
from datetime import datetime
from typing import Dict, Any

from ..core.celery_app import celery_app
from ..services.refresh import refresh_all
from ..utils.cache_utils import CacheManager
from ..models.asset import Price
from ..models.index import IndexValue
from .base import DatabaseTask, create_success_response, create_error_response

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, base=DatabaseTask, name="refresh_market_data")
def refresh_market_data(self, mode: str = "smart", db=None) -> Dict[str, Any]:
    """
    Refresh market data in the background.

    Args:
        mode: Refresh mode (smart, full, minimal)
        db: Database session (injected by DatabaseTask)

    Returns:
        Status and statistics
    """
    try:
        start_time = datetime.utcnow()
        logger.info(f"Starting market data refresh in {mode} mode")

        # Update task state
        self.update_state(state="PROGRESS", meta={"status": "Fetching market data..."})

        # Run refresh
        refresh_all(db, smart_mode=(mode == "smart"))

        # Invalidate caches
        self.update_state(state="PROGRESS", meta={"status": "Invalidating caches..."})
        CacheManager.invalidate_market_data()
        CacheManager.invalidate_index_data()

        # Calculate metrics
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Get statistics
        price_count = db.query(Price).count()
        index_count = db.query(IndexValue).count()

        result = create_success_response(
            duration=duration,
            start_time=start_time,
            end_time=end_time,
            mode=mode,
            statistics={
                "total_prices": price_count,
                "total_index_values": index_count,
            }
        )

        logger.info(f"Market data refresh completed in {duration:.2f} seconds")
        return result

    except Exception as e:
        logger.error(f"Market data refresh failed: {e}")
        return create_error_response(e)


@celery_app.task(bind=True, base=DatabaseTask, name="refresh_specific_symbols")
def refresh_specific_symbols(
    self, 
    symbols: list, 
    lookback_days: int = 30,
    db=None
) -> Dict[str, Any]:
    """
    Refresh data for specific symbols only.

    Args:
        symbols: List of symbols to refresh
        lookback_days: Number of days to fetch
        db: Database session (injected by DatabaseTask)

    Returns:
        Status and statistics
    """
    try:
        start_time = datetime.utcnow()
        logger.info(f"Refreshing {len(symbols)} symbols with {lookback_days} days lookback")

        # Update task state
        self.update_state(
            state="PROGRESS", 
            meta={"status": f"Fetching data for {len(symbols)} symbols..."}
        )

        # Import here to avoid circular dependency
        from ..services.twelvedata import fetch_prices
        from datetime import date, timedelta

        # Calculate date range
        end_date = date.today()
        start_date = end_date - timedelta(days=lookback_days)

        # Fetch prices
        price_df = fetch_prices(symbols, start=start_date)

        # Store in database
        if not price_df.empty:
            from ..services.refresh import store_prices
            store_prices(db, price_df)

        # Invalidate cache for these symbols
        CacheManager.invalidate_market_data()

        # Statistics
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        result = create_success_response(
            duration=duration,
            start_time=start_time,
            end_time=end_time,
            symbols=symbols,
            lookback_days=lookback_days,
            rows_fetched=len(price_df) if not price_df.empty else 0
        )

        logger.info(f"Symbol refresh completed in {duration:.2f} seconds")
        return result

    except Exception as e:
        logger.error(f"Symbol refresh failed: {e}")
        return create_error_response(e)