"""
Data cleanup background tasks.
Handles removing old data and maintaining database health.
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any

from ..core.celery_app import celery_app
from ..utils.cache_utils import CacheManager
from ..models.asset import Price
from ..models.index import IndexValue, Allocation
from .base import DatabaseTask, create_success_response, create_error_response

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, base=DatabaseTask, name="cleanup_old_data")
def cleanup_old_data(
    self, 
    days_to_keep: int = 365, 
    db=None
) -> Dict[str, Any]:
    """
    Clean up old data from the database.

    Args:
        days_to_keep: Number of days of data to retain
        db: Database session (injected by DatabaseTask)

    Returns:
        Cleanup statistics
    """
    try:
        start_time = datetime.utcnow()
        logger.info(f"Starting data cleanup, keeping {days_to_keep} days")

        self.update_state(
            state="PROGRESS", 
            meta={"status": "Cleaning up old data..."}
        )

        cutoff_date = date.today() - timedelta(days=days_to_keep)

        # Count records to delete
        old_prices = db.query(Price).filter(Price.date < cutoff_date).count()
        old_index_values = (
            db.query(IndexValue)
            .filter(IndexValue.date < cutoff_date)
            .count()
        )
        old_allocations = (
            db.query(Allocation)
            .filter(Allocation.date < cutoff_date)
            .count()
        )

        # Delete old records
        if old_prices > 0:
            db.query(Price).filter(Price.date < cutoff_date).delete()
        if old_index_values > 0:
            db.query(IndexValue).filter(IndexValue.date < cutoff_date).delete()
        if old_allocations > 0:
            db.query(Allocation).filter(Allocation.date < cutoff_date).delete()

        db.commit()

        # Invalidate caches
        CacheManager.invalidate_all()

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        result = create_success_response(
            duration=duration,
            start_time=start_time,
            end_time=end_time,
            cutoff_date=cutoff_date.isoformat(),
            deleted={
                "prices": old_prices,
                "index_values": old_index_values,
                "allocations": old_allocations,
                "total": old_prices + old_index_values + old_allocations
            }
        )

        logger.info(f"Data cleanup completed in {duration:.2f} seconds")
        return result

    except Exception as e:
        logger.error(f"Data cleanup failed: {e}")
        return create_error_response(e)


@celery_app.task(bind=True, base=DatabaseTask, name="optimize_database")
def optimize_database(self, db=None) -> Dict[str, Any]:
    """
    Optimize database by running maintenance operations.

    Args:
        db: Database session (injected by DatabaseTask)

    Returns:
        Optimization statistics
    """
    try:
        start_time = datetime.utcnow()
        logger.info("Starting database optimization")

        self.update_state(
            state="PROGRESS",
            meta={"status": "Optimizing database..."}
        )

        # Run ANALYZE on tables for better query planning
        tables = ["prices", "index_values", "allocations", "assets"]
        
        for table in tables:
            try:
                db.execute(f"ANALYZE {table}")
            except Exception as e:
                logger.warning(f"Failed to analyze table {table}: {e}")

        # Get database statistics
        table_stats = {}
        for table in tables:
            try:
                result = db.execute(
                    f"SELECT COUNT(*) as count FROM {table}"
                ).first()
                table_stats[table] = result.count if result else 0
            except Exception as e:
                logger.warning(f"Failed to get stats for {table}: {e}")
                table_stats[table] = "error"

        db.commit()

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        result = create_success_response(
            duration=duration,
            start_time=start_time,
            end_time=end_time,
            tables_analyzed=len(tables),
            table_statistics=table_stats
        )

        logger.info(f"Database optimization completed in {duration:.2f} seconds")
        return result

    except Exception as e:
        logger.error(f"Database optimization failed: {e}")
        return create_error_response(e)


@celery_app.task(bind=True, base=DatabaseTask, name="cleanup_orphaned_records")
def cleanup_orphaned_records(self, db=None) -> Dict[str, Any]:
    """
    Clean up orphaned records that have no parent references.

    Args:
        db: Database session (injected by DatabaseTask)

    Returns:
        Cleanup statistics
    """
    try:
        start_time = datetime.utcnow()
        logger.info("Starting orphaned records cleanup")

        self.update_state(
            state="PROGRESS",
            meta={"status": "Cleaning orphaned records..."}
        )

        deleted_counts = {}

        # Clean orphaned prices (prices for non-existent assets)
        from ..models.asset import Asset
        
        orphaned_prices = (
            db.query(Price)
            .outerjoin(Asset, Price.asset_id == Asset.id)
            .filter(Asset.id.is_(None))
            .count()
        )
        
        if orphaned_prices > 0:
            db.query(Price).filter(
                ~Price.asset_id.in_(db.query(Asset.id))
            ).delete(synchronize_session=False)
            deleted_counts["orphaned_prices"] = orphaned_prices

        # Clean orphaned allocations
        orphaned_allocations = (
            db.query(Allocation)
            .outerjoin(Asset, Allocation.asset_id == Asset.id)
            .filter(Asset.id.is_(None))
            .count()
        )
        
        if orphaned_allocations > 0:
            db.query(Allocation).filter(
                ~Allocation.asset_id.in_(db.query(Asset.id))
            ).delete(synchronize_session=False)
            deleted_counts["orphaned_allocations"] = orphaned_allocations

        db.commit()

        # Invalidate caches if we deleted anything
        if deleted_counts:
            CacheManager.invalidate_all()

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        result = create_success_response(
            duration=duration,
            start_time=start_time,
            end_time=end_time,
            deleted=deleted_counts,
            total_deleted=sum(deleted_counts.values())
        )

        logger.info(f"Orphaned records cleanup completed in {duration:.2f} seconds")
        return result

    except Exception as e:
        logger.error(f"Orphaned records cleanup failed: {e}")
        return create_error_response(e)