"""
Pure financial return calculations - lowest abstraction level.
Optimized for performance and WebAssembly compilation.
No dependencies beyond numpy/scipy.
"""

import numpy as np
from typing import List, Optional, Tuple, Union
from ..core.types import (
    Price, Return, PriceSeries, ReturnSeries, Scalar,
    FinancialConstants, ComputationalLimits
)


def simple_return(start_price: Price, end_price: Price) -> Return:
    """
    Calculate simple return between two prices.
    Pure mathematical operation - no business logic.
    
    Args:
        start_price: Starting price
        end_price: Ending price
        
    Returns:
        Simple return as decimal (0.1 = 10%)
    """
    if start_price <= 0:
        return Return(0.0)
    
    return Return((end_price / start_price) - 1.0)


def log_return(start_price: Price, end_price: Price) -> Return:
    """
    Calculate logarithmic return between two prices.
    Better for time series analysis and compounding.
    """
    if start_price <= 0 or end_price <= 0:
        return Return(0.0)
    
    return Return(np.log(end_price / start_price))


def simple_returns_series(prices: PriceSeries) -> ReturnSeries:
    """
    Calculate simple returns for entire price series.
    Vectorized for performance.
    """
    if len(prices) < 2:
        return []
    
    # Vectorized calculation for performance
    prices_array = np.array(prices, dtype=np.float64)
    
    # Handle zero prices
    prices_array = np.where(prices_array <= 0, np.finfo(float).eps, prices_array)
    
    # Calculate returns: (P[t] / P[t-1]) - 1
    returns = (prices_array[1:] / prices_array[:-1]) - 1.0
    
    return returns.tolist()


def log_returns_series(prices: PriceSeries) -> ReturnSeries:
    """
    Calculate logarithmic returns for entire price series.
    Preferred for statistical analysis.
    """
    if len(prices) < 2:
        return []
    
    prices_array = np.array(prices, dtype=np.float64)
    
    # Handle zero/negative prices
    prices_array = np.where(prices_array <= 0, np.finfo(float).eps, prices_array)
    
    # Calculate log returns: ln(P[t] / P[t-1])
    log_returns = np.log(prices_array[1:] / prices_array[:-1])
    
    return log_returns.tolist()


def cumulative_return(returns: ReturnSeries) -> Return:
    """
    Calculate cumulative return from return series.
    Uses compound return formula.
    """
    if not returns:
        return Return(0.0)
    
    # Compound returns: (1 + r1) * (1 + r2) * ... - 1
    cumulative = 1.0
    for ret in returns:
        cumulative *= (1.0 + ret)
    
    return Return(cumulative - 1.0)


def annualized_return(returns: ReturnSeries, 
                     periods_per_year: int = FinancialConstants.TRADING_DAYS_PER_YEAR) -> Return:
    """
    Calculate annualized return from return series.
    
    Args:
        returns: Series of period returns
        periods_per_year: Number of periods per year (252 for daily)
    """
    if not returns:
        return Return(0.0)
    
    cumulative = cumulative_return(returns)
    periods = len(returns)
    
    if periods <= 0:
        return Return(0.0)
    
    try:
        # Annualization: (1 + cumulative_return) ^ (periods_per_year / periods) - 1
        annualized = ((1.0 + cumulative) ** (periods_per_year / periods)) - 1.0
        return Return(annualized)
    except (OverflowError, ZeroDivisionError):
        return Return(0.0)


def rolling_returns(prices: PriceSeries, 
                   window: int, 
                   step: int = 1) -> List[Return]:
    """
    Calculate rolling returns over a moving window.
    
    Args:
        prices: Price series
        window: Size of rolling window
        step: Step size between windows
        
    Returns:
        List of rolling period returns
    """
    if len(prices) < window or window <= 0:
        return []
    
    rolling_rets = []
    for i in range(0, len(prices) - window + 1, step):
        window_prices = prices[i:i + window]
        period_return = simple_return(Price(window_prices[0]), Price(window_prices[-1]))
        rolling_rets.append(period_return)
    
    return rolling_rets


def excess_returns(asset_returns: ReturnSeries, 
                  benchmark_returns: ReturnSeries) -> ReturnSeries:
    """
    Calculate excess returns over benchmark.
    Pure mathematical operation - no interpretation.
    """
    if len(asset_returns) != len(benchmark_returns):
        return []
    
    return [asset - benchmark for asset, benchmark in zip(asset_returns, benchmark_returns)]


def returns_to_prices(returns: ReturnSeries, 
                     initial_price: Price = Price(100.0)) -> PriceSeries:
    """
    Convert return series back to price series.
    Useful for simulation and backtesting.
    """
    if not returns:
        return [initial_price]
    
    prices = [initial_price]
    current_price = initial_price
    
    for ret in returns:
        current_price = Price(current_price * (1.0 + ret))
        prices.append(current_price)
    
    return prices


def normalize_returns(returns: ReturnSeries) -> ReturnSeries:
    """
    Normalize returns to z-scores.
    Removes mean and scales by standard deviation.
    """
    if len(returns) < 2:
        return returns
    
    returns_array = np.array(returns)
    mean_return = np.mean(returns_array)
    std_return = np.std(returns_array, ddof=1)
    
    if std_return == 0:
        return [0.0] * len(returns)
    
    normalized = (returns_array - mean_return) / std_return
    return normalized.tolist()


def returns_percentiles(returns: ReturnSeries, 
                       percentiles: List[float] = [5, 25, 50, 75, 95]) -> List[Return]:
    """
    Calculate return percentiles for risk assessment.
    
    Args:
        returns: Return series
        percentiles: List of percentile levels (0-100)
        
    Returns:
        List of return values at specified percentiles
    """
    if not returns:
        return []
    
    returns_array = np.array(returns)
    percentile_values = np.percentile(returns_array, percentiles)
    return percentile_values.tolist()


def compound_returns_matrix(returns_matrix: ReturnsMatrix) -> ReturnSeries:
    """
    Compound returns across multiple assets.
    Each row represents an asset, each column a time period.
    """
    if returns_matrix.size == 0:
        return []
    
    # Calculate portfolio return as equal-weighted average
    equal_weights = 1.0 / returns_matrix.shape[0]
    portfolio_returns = np.mean(returns_matrix, axis=0) * equal_weights
    
    return portfolio_returns.tolist()


# Performance measurement utilities
def calculate_return_statistics(returns: ReturnSeries) -> dict:
    """
    Calculate comprehensive return statistics.
    Pure mathematical analysis without interpretation.
    """
    if not returns:
        return {}
    
    returns_array = np.array(returns)
    
    return {
        "mean": float(np.mean(returns_array)),
        "median": float(np.median(returns_array)),
        "std": float(np.std(returns_array, ddof=1)),
        "skewness": float(_calculate_skewness(returns_array)),
        "kurtosis": float(_calculate_kurtosis(returns_array)),
        "min": float(np.min(returns_array)),
        "max": float(np.max(returns_array)),
        "count": len(returns),
        "positive_periods": int(np.sum(returns_array > 0)),
        "negative_periods": int(np.sum(returns_array < 0)),
        "zero_periods": int(np.sum(returns_array == 0))
    }


def _calculate_skewness(returns: np.ndarray) -> float:
    """Calculate skewness of returns distribution."""
    if len(returns) < 3:
        return 0.0
    
    mean = np.mean(returns)
    std = np.std(returns, ddof=1)
    
    if std == 0:
        return 0.0
    
    normalized = (returns - mean) / std
    skewness = np.mean(normalized ** 3)
    
    return float(skewness)


def _calculate_kurtosis(returns: np.ndarray) -> float:
    """Calculate kurtosis of returns distribution."""
    if len(returns) < 4:
        return 0.0
    
    mean = np.mean(returns)
    std = np.std(returns, ddof=1)
    
    if std == 0:
        return 0.0
    
    normalized = (returns - mean) / std
    kurtosis = np.mean(normalized ** 4) - 3.0  # Excess kurtosis
    
    return float(kurtosis)