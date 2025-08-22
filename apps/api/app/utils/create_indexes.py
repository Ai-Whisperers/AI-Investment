"""
Script to create performance indexes on the database.
Can be run manually or as part of deployment.
"""

import logging

from sqlalchemy import text

from ..core.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_performance_indexes():
    """Create composite indexes for better query performance."""

    indexes = [
        # Composite index for price queries
        """CREATE INDEX IF NOT EXISTS idx_prices_asset_date
           ON prices(asset_id, date DESC)""",
        # Date-based indexes
        "CREATE INDEX IF NOT EXISTS idx_allocations_date ON allocations(date DESC)",
        "CREATE INDEX IF NOT EXISTS idx_index_values_date ON index_values(date DESC)",
        "CREATE INDEX IF NOT EXISTS idx_risk_metrics_date ON risk_metrics(date DESC)",
        # User email lookup (case-insensitive)
        "CREATE INDEX IF NOT EXISTS idx_users_email_lower ON users(LOWER(email))",
    ]

    with engine.connect() as conn:
        for index_sql in indexes:
            try:
                logger.info(f"Creating index: {index_sql[:50]}...")
                conn.execute(text(index_sql))
                conn.commit()
                logger.info("✓ Index created successfully")
            except Exception as e:
                logger.warning(f"Could not create index: {e}")

        # Update statistics for query planner
        try:
            logger.info("Updating table statistics...")
            conn.execute(text("ANALYZE prices"))
            conn.execute(text("ANALYZE allocations"))
            conn.execute(text("ANALYZE index_values"))
            conn.execute(text("ANALYZE assets"))
            conn.commit()
            logger.info("✓ Statistics updated")
        except Exception as e:
            logger.warning(f"Could not update statistics: {e}")

    logger.info("Index creation complete!")


if __name__ == "__main__":
    create_performance_indexes()
