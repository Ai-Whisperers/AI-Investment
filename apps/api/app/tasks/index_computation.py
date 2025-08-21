"""
Index computation background tasks.
Handles index value and allocation calculations asynchronously.
"""

import logging
from datetime import datetime
from typing import Any

from ..core.celery_app import celery_app
from ..models.index import Allocation, IndexValue
from ..services.performance import calculate_portfolio_metrics
from ..services.strategy import compute_index_and_allocations
from ..utils.cache_utils import CacheManager
from .base import DatabaseTask, create_error_response, create_success_response

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, base=DatabaseTask, name="compute_index")
def compute_index(
    self,
    strategy_config: dict | None = None,
    db=None
) -> dict[str, Any]:
    """
    Compute index and allocations in the background.

    Args:
        strategy_config: Optional strategy configuration override
        db: Database session (injected by DatabaseTask)

    Returns:
        Computation results
    """
    try:
        start_time = datetime.utcnow()
        logger.info("Starting index computation")

        # Update task state
        self.update_state(state="PROGRESS", meta={"status": "Computing index..."})

        # Run computation
        compute_index_and_allocations(db, config=strategy_config)

        # Calculate portfolio metrics
        self.update_state(state="PROGRESS", meta={"status": "Calculating metrics..."})
        metrics = calculate_portfolio_metrics(db)

        # Invalidate index cache
        CacheManager.invalidate_index_data()

        # Get statistics
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        index_count = db.query(IndexValue).count()
        allocation_count = db.query(Allocation).count()

        result = create_success_response(
            duration=duration,
            start_time=start_time,
            end_time=end_time,
            statistics={
                "index_values": index_count,
                "allocations": allocation_count,
            },
            metrics=metrics
        )

        logger.info(f"Index computation completed in {duration:.2f} seconds")
        return result

    except Exception as e:
        logger.error(f"Index computation failed: {e}")
        return create_error_response(e)


@celery_app.task(bind=True, base=DatabaseTask, name="rebalance_portfolio")
def rebalance_portfolio(
    self,
    force: bool = False,
    db=None
) -> dict[str, Any]:
    """
    Rebalance portfolio allocations.

    Args:
        force: Force rebalancing even if not scheduled
        db: Database session (injected by DatabaseTask)

    Returns:
        Rebalancing results
    """
    try:
        start_time = datetime.utcnow()
        logger.info(f"Starting portfolio rebalancing (force={force})")

        # Update task state
        self.update_state(
            state="PROGRESS",
            meta={"status": "Checking rebalancing conditions..."}
        )

        # Get current strategy config
        from ..models.strategy import StrategyConfig
        config = db.query(StrategyConfig).first()

        if not config:
            raise ValueError("No strategy configuration found")

        # Check if rebalancing is needed
        needs_rebalancing = force

        if not force:
            # Check based on frequency
            from datetime import date, timedelta

            if config.last_rebalance:
                days_since_rebalance = (date.today() - config.last_rebalance).days

                if config.rebalance_frequency == "daily":
                    needs_rebalancing = days_since_rebalance >= 1
                elif config.rebalance_frequency == "weekly":
                    needs_rebalancing = days_since_rebalance >= 7
                elif config.rebalance_frequency == "monthly":
                    needs_rebalancing = days_since_rebalance >= 30
            else:
                needs_rebalancing = True

        if not needs_rebalancing:
            return {
                "status": "skipped",
                "reason": "Rebalancing not yet due",
                "next_rebalance": config.last_rebalance + timedelta(
                    days=7 if config.rebalance_frequency == "weekly" else
                    30 if config.rebalance_frequency == "monthly" else 1
                )
            }

        # Perform rebalancing
        self.update_state(state="PROGRESS", meta={"status": "Rebalancing portfolio..."})

        # Recompute with current config
        compute_index_and_allocations(db)

        # Update last rebalance date
        config.last_rebalance = date.today()
        db.add(config)
        db.commit()

        # Invalidate caches
        CacheManager.invalidate_index_data()

        # Get new allocations
        latest_allocations = (
            db.query(Allocation)
            .filter(Allocation.date == date.today())
            .all()
        )

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        result = create_success_response(
            duration=duration,
            start_time=start_time,
            end_time=end_time,
            forced=force,
            allocations_updated=len(latest_allocations),
            next_rebalance=config.last_rebalance + timedelta(
                days=7 if config.rebalance_frequency == "weekly" else
                30 if config.rebalance_frequency == "monthly" else 1
            )
        )

        logger.info(f"Portfolio rebalancing completed in {duration:.2f} seconds")
        return result

    except Exception as e:
        logger.error(f"Portfolio rebalancing failed: {e}")
        return create_error_response(e)
