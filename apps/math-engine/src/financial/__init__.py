"""
Financial mathematics module for investment calculations.
Pure mathematical operations without business logic.
"""

from .returns import (
    simple_return,
    log_return,
    simple_returns_series,
    log_returns_series,
    cumulative_return,
    annualized_return,
    rolling_returns,
    excess_returns,
    returns_to_prices,
    normalize_returns,
    returns_percentiles,
    compound_returns_matrix,
    calculate_return_statistics,
)

# Export all financial calculation functions
__all__ = [
    "simple_return",
    "log_return", 
    "simple_returns_series",
    "log_returns_series",
    "cumulative_return",
    "annualized_return",
    "rolling_returns",
    "excess_returns",
    "returns_to_prices",
    "normalize_returns", 
    "returns_percentiles",
    "compound_returns_matrix",
    "calculate_return_statistics",
]