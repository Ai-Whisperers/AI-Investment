"""
Benchmark comparison and relative return calculations.
Handles active returns, tracking error, and excess returns.
"""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Annual trading days
TRADING_DAYS_PER_YEAR = 252


class BenchmarkReturnCalculator:
    """Calculate benchmark-relative return metrics."""

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
    ) -> tuple[np.ndarray, float, float]:
        """
        Calculate active returns and tracking statistics.

        Args:
            portfolio_returns: Portfolio return series
            benchmark_returns: Benchmark return series

        Returns:
            Tuple of (active_returns, tracking_error, active_return)
        """
        active = BenchmarkReturnCalculator.excess_returns(
            portfolio_returns, 
            benchmark_returns
        )

        if len(active) == 0:
            return np.array([]), 0.0, 0.0

        tracking_error = active.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
        active_return = active.mean() * TRADING_DAYS_PER_YEAR

        return active, float(tracking_error), float(active_return)

    @staticmethod
    def calculate_active_return(
        portfolio_return: float,
        benchmark_return: float
    ) -> float:
        """
        Calculate active return vs benchmark.

        Args:
            portfolio_return: Portfolio return (scalar)
            benchmark_return: Benchmark return (scalar)

        Returns:
            Active return as decimal
        """
        return portfolio_return - benchmark_return

    @staticmethod
    def calculate_tracking_error(
        portfolio_returns: pd.Series,
        benchmark_returns: pd.Series,
        annualized: bool = True
    ) -> float:
        """
        Calculate tracking error vs benchmark.

        Args:
            portfolio_returns: Portfolio return series
            benchmark_returns: Benchmark return series
            annualized: Whether to annualize the tracking error

        Returns:
            Tracking error as decimal
        """
        # Align the series
        aligned = pd.DataFrame({
            'portfolio': portfolio_returns,
            'benchmark': benchmark_returns
        }).dropna()

        if len(aligned) < 2:
            return 0.0

        # Calculate tracking error (std of excess returns)
        excess_returns = aligned['portfolio'] - aligned['benchmark']
        tracking_error = excess_returns.std()

        if annualized:
            tracking_error = tracking_error * np.sqrt(252)

        return float(tracking_error)

    @staticmethod
    def calculate_excess_returns(
        portfolio_returns: np.ndarray,
        benchmark_returns: np.ndarray
    ) -> np.ndarray:
        """
        Wrapper for excess_returns with consistent naming.
        """
        return BenchmarkReturnCalculator.excess_returns(
            portfolio_returns, 
            benchmark_returns
        )