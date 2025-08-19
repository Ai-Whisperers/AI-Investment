"""
Return calculations for portfolio performance analysis.
Handles daily returns, annualized returns, and cumulative returns.
"""

import numpy as np
from typing import List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Annual trading days
TRADING_DAYS_PER_YEAR = 252


class ReturnCalculator:
    """Calculate various return metrics for portfolios."""

    @staticmethod
    def calculate_returns(values: List[float]) -> np.ndarray:
        """
        Calculate daily returns from price series.
        
        Args:
            values: List of prices/values
            
        Returns:
            Array of daily returns
        """
        if len(values) < 2:
            return np.array([])

        prices = np.array(values)
        returns = (prices[1:] - prices[:-1]) / prices[:-1]
        return returns

    @staticmethod
    def total_return(values: List[float]) -> float:
        """
        Calculate total return over the period.
        
        Args:
            values: List of prices/values
            
        Returns:
            Total return as percentage
        """
        if len(values) < 2:
            return 0.0
        
        return ((values[-1] / values[0]) - 1) * 100

    @staticmethod
    def annualized_return(values: List[float], days: Optional[int] = None) -> float:
        """
        Calculate annualized return.
        
        Args:
            values: List of prices/values
            days: Number of days in the period (if None, uses len(values))
            
        Returns:
            Annualized return as percentage
        """
        if len(values) < 2:
            return 0.0
        
        if days is None:
            days = len(values)
        
        if days <= 0:
            return 0.0
        
        total_return = (values[-1] / values[0]) - 1
        years = days / 365.0
        
        if years <= 0:
            return 0.0
        
        annualized = (1 + total_return) ** (1 / years) - 1
        return annualized * 100

    @staticmethod
    def cumulative_returns(values: List[float]) -> np.ndarray:
        """
        Calculate cumulative returns series.
        
        Args:
            values: List of prices/values
            
        Returns:
            Array of cumulative returns
        """
        if len(values) == 0:
            return np.array([])
        
        prices = np.array(values)
        return prices / prices[0]

    @staticmethod
    def excess_returns(
        portfolio_returns: np.ndarray,
        benchmark_returns: np.ndarray
    ) -> np.ndarray:
        """
        Calculate excess returns over benchmark.
        
        Args:
            portfolio_returns: Portfolio return series
            benchmark_returns: Benchmark return series
            
        Returns:
            Array of excess returns
        """
        # Align returns to same length
        min_len = min(len(portfolio_returns), len(benchmark_returns))
        
        if min_len == 0:
            return np.array([])
        
        portfolio_aligned = portfolio_returns[:min_len]
        benchmark_aligned = benchmark_returns[:min_len]
        
        return portfolio_aligned - benchmark_aligned

    @staticmethod
    def active_returns(
        portfolio_returns: np.ndarray,
        benchmark_returns: np.ndarray
    ) -> Tuple[np.ndarray, float, float]:
        """
        Calculate active returns and tracking statistics.
        
        Args:
            portfolio_returns: Portfolio return series
            benchmark_returns: Benchmark return series
            
        Returns:
            Tuple of (active_returns, tracking_error, active_return)
        """
        active = ReturnCalculator.excess_returns(portfolio_returns, benchmark_returns)
        
        if len(active) == 0:
            return np.array([]), 0.0, 0.0
        
        tracking_error = active.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
        active_return = active.mean() * TRADING_DAYS_PER_YEAR
        
        return active, float(tracking_error), float(active_return)

    @staticmethod
    def rolling_returns(
        values: List[float],
        window: int = 30
    ) -> List[Tuple[int, float]]:
        """
        Calculate rolling returns over specified window.
        
        Args:
            values: List of prices/values
            window: Rolling window size in periods
            
        Returns:
            List of tuples (index, return) for each window
        """
        if len(values) < window or window < 2:
            return []
        
        rolling = []
        for i in range(window, len(values) + 1):
            window_values = values[i - window:i]
            ret = ReturnCalculator.total_return(window_values)
            rolling.append((i - 1, ret))
        
        return rolling