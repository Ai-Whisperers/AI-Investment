"""
Performance service module for portfolio metrics calculation.
Provides comprehensive performance analysis including returns, risk metrics, and benchmark comparisons.
"""

from .return_calculator import ReturnCalculator
from .risk_metrics import RiskMetricsCalculator, TRADING_DAYS_PER_YEAR, DEFAULT_RISK_FREE_RATE
from .benchmark_comparison import BenchmarkComparison
from .performance_tracker import PerformanceTracker

# Legacy imports for backward compatibility
from .risk_metrics import RiskMetricsCalculator as PerformanceCalculator

# Functions from parent performance.py will be imported separately to avoid circular imports

# Re-export commonly used constants
RISK_FREE_RATE = DEFAULT_RISK_FREE_RATE

__all__ = [
    "ReturnCalculator",
    "RiskMetricsCalculator",
    "BenchmarkComparison",
    "PerformanceTracker",
    "PerformanceCalculator",  # Legacy alias
    "TRADING_DAYS_PER_YEAR",
    "RISK_FREE_RATE",
    "DEFAULT_RISK_FREE_RATE"
]