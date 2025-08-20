"""
Portfolio performance metrics calculation service.
This is now a facade that delegates to the modular performance components.
"""

from typing import Dict, List, Optional
from sqlalchemy.orm import Session
import logging

from .performance_modules import (
    PerformanceTracker,
    PerformanceCalculator,  # Legacy alias for RiskMetricsCalculator
    TRADING_DAYS_PER_YEAR,
    RISK_FREE_RATE
)

logger = logging.getLogger(__name__)


def calculate_portfolio_metrics(
    db: Session, 
    lookback_days: Optional[int] = None
) -> Dict:
    """
    Calculate comprehensive portfolio performance metrics.
    
    This function maintains backward compatibility with the original API.
    
    Args:
        db: Database session
        lookback_days: Number of days to look back (None for all history)
        
    Returns:
        Dictionary of performance metrics
    """
    tracker = PerformanceTracker(db)
    metrics = tracker.calculate_comprehensive_metrics(lookback_days)
    
    # Save metrics to database
    if metrics:
        tracker.save_metrics_to_database(metrics)
    
    return metrics


def get_rolling_metrics(db: Session, window: int = 30) -> List[Dict]:
    """
    Calculate rolling performance metrics.
    
    This function maintains backward compatibility with the original API.
    
    Args:
        db: Database session
        window: Rolling window size in days
        
    Returns:
        List of metrics for each window
    """
    tracker = PerformanceTracker(db)
    return tracker.get_rolling_metrics(window)


# Re-export the PerformanceCalculator class for backward compatibility
__all__ = [
    "calculate_portfolio_metrics",
    "get_rolling_metrics",
    "PerformanceCalculator",
    "TRADING_DAYS_PER_YEAR",
    "RISK_FREE_RATE"
]