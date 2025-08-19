"""
Background tasks module for async processing.
Provides Celery tasks for market data refresh, index computation, report generation, and cleanup.
"""

from .base import DatabaseTask, get_task_status
from .market_refresh import refresh_market_data, refresh_specific_symbols
from .index_computation import compute_index, rebalance_portfolio
from .report_generation import generate_report, generate_comprehensive_report
from .cleanup import cleanup_old_data, optimize_database, cleanup_orphaned_records

__all__ = [
    # Base utilities
    "DatabaseTask",
    "get_task_status",
    
    # Market refresh tasks
    "refresh_market_data",
    "refresh_specific_symbols",
    
    # Index computation tasks
    "compute_index",
    "rebalance_portfolio",
    
    # Report generation tasks
    "generate_report",
    "generate_comprehensive_report",
    
    # Cleanup tasks
    "cleanup_old_data",
    "optimize_database",
    "cleanup_orphaned_records"
]