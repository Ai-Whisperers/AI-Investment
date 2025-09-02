"""
Waardhaven Mathematical Engine
Pure computational core for investment intelligence.

This module provides the lowest abstraction mathematical operations
for financial modeling, optimization, and prediction. Designed for
high performance and WebAssembly compilation.
"""

from .core import (
    FinancialConstants,
    ComputationalLimits,
    Scalar, Vector, Matrix,
    Price, Return, Weight,
    PriceSeries, ReturnSeries, WeightVector,
)

from .financial import (
    simple_return,
    log_return,
    simple_returns_series,
    log_returns_series,
    cumulative_return,
    annualized_return,
    calculate_return_statistics,
)

from .prediction import (
    linear_trend_prediction,
    ensemble_trend_prediction,
    trend_strength,
)

# Version and metadata
__version__ = "0.1.0"
__author__ = "Waardhaven AI"
__description__ = "Pure mathematical engine for investment intelligence"

# Main engine class for organized access
class MathEngine:
    """
    Main mathematical engine interface.
    Provides organized access to all mathematical operations.
    """
    
    # Constants
    CONSTANTS = FinancialConstants
    LIMITS = ComputationalLimits
    
    # Financial mathematics
    @staticmethod
    def calculate_simple_return(start: Price, end: Price) -> Return:
        """Calculate simple return between two prices."""
        return simple_return(start, end)
    
    @staticmethod
    def calculate_returns_series(prices: PriceSeries) -> ReturnSeries:
        """Calculate return series from prices."""
        return simple_returns_series(prices)
    
    @staticmethod
    def calculate_cumulative_return(returns: ReturnSeries) -> Return:
        """Calculate cumulative return from series."""
        return cumulative_return(returns)
    
    @staticmethod
    def predict_trend(prices: PriceSeries, periods: int = 1) -> List[PredictionResult]:
        """Predict future prices using ensemble trend analysis."""
        return ensemble_trend_prediction(prices, periods)
    
    @staticmethod
    def analyze_trend_strength(prices: PriceSeries) -> float:
        """Analyze mathematical trend strength (0-1)."""
        return trend_strength(prices)


# Export main interface and key functions
__all__ = [
    # Main engine
    "MathEngine",
    
    # Constants and types
    "FinancialConstants", 
    "ComputationalLimits",
    "Scalar", "Vector", "Matrix",
    "Price", "Return", "Weight",
    "PriceSeries", "ReturnSeries", "WeightVector",
    
    # Core functions
    "simple_return",
    "simple_returns_series", 
    "cumulative_return",
    "annualized_return",
    
    # Prediction functions
    "linear_trend_prediction",
    "ensemble_trend_prediction",
    "trend_strength",
    
    # Statistics
    "calculate_return_statistics",
    
    # Version info
    "__version__",
    "__author__", 
    "__description__",
]