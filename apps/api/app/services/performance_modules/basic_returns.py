"""
Basic return calculations for portfolio performance analysis.
Handles simple returns, total returns, and compound returns.
"""

import logging
from datetime import datetime

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Annual trading days
TRADING_DAYS_PER_YEAR = 252


class BasicReturnCalculator:
    """Calculate basic return metrics for portfolios."""

    @staticmethod
    def calculate_returns(values: list[float]) -> np.ndarray:
        """
        Calculate daily returns from price series.

        Args:
            values: List of prices/values

        Returns:
            Array of daily returns
        """
        if len(values) == 0:
            raise ValueError("Empty series")
        if len(values) < 2:
            return np.array([])

        prices = np.array(values)
        returns = (prices[1:] - prices[:-1]) / prices[:-1]
        return returns

    @staticmethod
    def total_return(values: list[float]) -> float:
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
    def calculate_simple_return(start_value: float, end_value: float) -> float:
        """
        Calculate simple return between two values.

        Args:
            start_value: Starting value
            end_value: Ending value

        Returns:
            Simple return as decimal (0.1 for 10%)
        """
        if start_value == 0:
            return 0.0
        return (end_value - start_value) / start_value

    @staticmethod
    def calculate_log_returns(prices: list[float]) -> np.ndarray:
        """
        Calculate logarithmic returns from price series.

        Args:
            prices: List of prices

        Returns:
            Array of log returns
        """
        if len(prices) < 2:
            return np.array([])

        prices_array = np.array(prices)

        # Check for negative prices
        if np.any(prices_array <= 0):
            raise ValueError("Negative or zero prices not allowed for log returns")

        return np.log(prices_array[1:] / prices_array[:-1])

    @staticmethod
    def calculate_compound_return(returns: list[float]) -> float:
        """
        Calculate compound return from series of returns.

        Args:
            returns: List of period returns

        Returns:
            Compound return as decimal
        """
        if len(returns) == 0:
            return 0.0

        return np.prod([1 + r for r in returns]) - 1

    @staticmethod
    def cumulative_returns(values: list[float]) -> np.ndarray:
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
    def calculate_cumulative_returns(returns: pd.Series) -> pd.Series:
        """
        Calculate cumulative returns from return series.

        Args:
            returns: Series of period returns

        Returns:
            Series of cumulative returns
        """
        if len(returns) == 0:
            return pd.Series(dtype=float)

        # Convert returns to growth factors and calculate cumulative product
        growth_factors = 1 + returns
        cum_returns = growth_factors.cumprod() - 1
        return cum_returns