"""
Unified return calculator that orchestrates specialized return calculation services.
Refactored to follow Single Responsibility Principle with focused service classes.
"""

import logging
from datetime import datetime

import numpy as np
import pandas as pd

from .basic_returns import BasicReturnCalculator
from .period_returns import PeriodReturnCalculator
from .benchmark_returns import BenchmarkReturnCalculator
from .advanced_returns import AdvancedReturnCalculator

logger = logging.getLogger(__name__)

# Annual trading days
TRADING_DAYS_PER_YEAR = 252


class ReturnCalculator:
    """
    Orchestrator for return calculations.
    Delegates to specialized calculators for different return types.
    """

    def __init__(self):
        """Initialize with specialized calculators."""
        self.basic = BasicReturnCalculator()
        self.period = PeriodReturnCalculator()
        self.benchmark = BenchmarkReturnCalculator()
        self.advanced = AdvancedReturnCalculator()

    # Basic return calculations
    @staticmethod
    def calculate_returns(values: list[float]) -> np.ndarray:
        """Calculate daily returns from price series."""
        return BasicReturnCalculator.calculate_returns(values)

    @staticmethod
    def total_return(values: list[float]) -> float:
        """Calculate total return over the period."""
        return BasicReturnCalculator.total_return(values)

    @staticmethod
    def calculate_simple_return(start_value: float, end_value: float) -> float:
        """Calculate simple return between two values."""
        return BasicReturnCalculator.calculate_simple_return(start_value, end_value)

    @staticmethod
    def calculate_log_returns(prices: list[float]) -> np.ndarray:
        """Calculate logarithmic returns from price series."""
        return BasicReturnCalculator.calculate_log_returns(prices)

    @staticmethod
    def calculate_compound_return(returns: list[float]) -> float:
        """Calculate compound return from series of returns."""
        return BasicReturnCalculator.calculate_compound_return(returns)

    @staticmethod
    def cumulative_returns(values: list[float]) -> np.ndarray:
        """Calculate cumulative returns series."""
        return BasicReturnCalculator.cumulative_returns(values)

    @staticmethod
    def calculate_cumulative_returns(returns: pd.Series) -> pd.Series:
        """Calculate cumulative returns from return series."""
        return BasicReturnCalculator.calculate_cumulative_returns(returns)

    # Period-based return calculations
    @staticmethod
    def annualized_return(values: list[float], days: int | None = None) -> float:
        """Calculate annualized return."""
        return PeriodReturnCalculator.annualized_return(values, days)

    @staticmethod
    def calculate_annualized_return(total_return: float, days: int) -> float:
        """Calculate annualized return from total return."""
        return PeriodReturnCalculator.calculate_annualized_return(total_return, days)

    @staticmethod
    def calculate_daily_returns(prices: pd.Series) -> pd.Series:
        """Calculate daily returns from price series."""
        return PeriodReturnCalculator.calculate_daily_returns(prices)

    @staticmethod
    def calculate_monthly_returns(prices: pd.Series) -> pd.Series:
        """Calculate monthly returns from price series."""
        return PeriodReturnCalculator.calculate_monthly_returns(prices)

    @staticmethod
    def calculate_ytd_return(
        prices: pd.Series,
        current_date: datetime | None = None,
        year: int | None = None
    ) -> float:
        """Calculate year-to-date return."""
        return PeriodReturnCalculator.calculate_ytd_return(prices, current_date, year)

    @staticmethod
    def calculate_period_returns(prices: pd.Series, period: str = 'daily') -> pd.Series:
        """Calculate returns for different periods."""
        return PeriodReturnCalculator.calculate_period_returns(prices, period)

    @staticmethod
    def rolling_returns(values: list[float], window: int = 30) -> list[tuple[int, float]]:
        """Calculate rolling returns over specified window."""
        return PeriodReturnCalculator.rolling_returns(values, window)

    @staticmethod
    def calculate_rolling_returns(prices: pd.Series, window: int = 30) -> pd.Series:
        """Calculate rolling returns over specified window."""
        return PeriodReturnCalculator.calculate_rolling_returns(prices, window)

    # Benchmark comparison calculations
    @staticmethod
    def excess_returns(
        portfolio_returns: np.ndarray,
        benchmark_returns: np.ndarray
    ) -> np.ndarray:
        """Calculate excess returns over benchmark."""
        return BenchmarkReturnCalculator.excess_returns(portfolio_returns, benchmark_returns)

    @staticmethod
    def active_returns(
        portfolio_returns: np.ndarray,
        benchmark_returns: np.ndarray
    ) -> tuple[np.ndarray, float, float]:
        """Calculate active returns and tracking statistics."""
        return BenchmarkReturnCalculator.active_returns(portfolio_returns, benchmark_returns)

    @staticmethod
    def calculate_active_return(
        portfolio_return: float,
        benchmark_return: float
    ) -> float:
        """Calculate active return vs benchmark."""
        return BenchmarkReturnCalculator.calculate_active_return(
            portfolio_return,
            benchmark_return
        )

    @staticmethod
    def calculate_tracking_error(
        portfolio_returns: pd.Series,
        benchmark_returns: pd.Series,
        annualized: bool = True
    ) -> float:
        """Calculate tracking error vs benchmark."""
        return BenchmarkReturnCalculator.calculate_tracking_error(
            portfolio_returns,
            benchmark_returns,
            annualized
        )

    @staticmethod
    def calculate_excess_returns(
        portfolio_returns: np.ndarray,
        benchmark_returns: np.ndarray
    ) -> np.ndarray:
        """Wrapper for excess_returns with consistent naming."""
        return BenchmarkReturnCalculator.calculate_excess_returns(
            portfolio_returns,
            benchmark_returns
        )

    # Advanced return calculations
    @staticmethod
    def calculate_time_weighted_return(
        values: list[float],
        dates: pd.DatetimeIndex,
        cash_flows: list[tuple[pd.Timestamp, float]]
    ) -> float:
        """Calculate time-weighted return accounting for cash flows."""
        return AdvancedReturnCalculator.calculate_time_weighted_return(
            values,
            dates,
            cash_flows
        )

    @staticmethod
    def calculate_money_weighted_return(
        cash_flows: list[tuple[float, datetime]]
    ) -> float:
        """Calculate money-weighted return (IRR) using numerical optimization."""
        return AdvancedReturnCalculator.calculate_money_weighted_return(cash_flows)

    @staticmethod
    def calculate_return_distribution_metrics(returns: np.ndarray) -> dict[str, float]:
        """Calculate return distribution metrics."""
        return AdvancedReturnCalculator.calculate_return_distribution_metrics(returns)

    @staticmethod
    def analyze_return_distribution(returns: pd.Series) -> dict[str, float]:
        """Analyze return distribution metrics."""
        return AdvancedReturnCalculator.analyze_return_distribution(returns)