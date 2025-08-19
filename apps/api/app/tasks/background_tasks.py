"""
Background tasks facade for backward compatibility.
Re-exports tasks from modularized task modules.
"""

# Re-export all tasks for backward compatibility
from .base import DatabaseTask, get_task_status
from .market_refresh import refresh_market_data, refresh_specific_symbols
from .index_computation import compute_index, rebalance_portfolio
from .report_generation import generate_report, generate_comprehensive_report
from .cleanup import cleanup_old_data, optimize_database, cleanup_orphaned_records

__all__ = [
    "DatabaseTask",
    "get_task_status",
    "refresh_market_data",
    "refresh_specific_symbols",
    "compute_index",
    "rebalance_portfolio",
    "generate_report",
    "generate_comprehensive_report",
    "cleanup_old_data",
    "optimize_database",
    "cleanup_orphaned_records"
]