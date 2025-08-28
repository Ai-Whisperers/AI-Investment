"""
Period-based return calculations for portfolio performance analysis.
Handles annualized, rolling, and time-period specific returns.
"""

import logging
from datetime import datetime

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Annual trading days
TRADING_DAYS_PER_YEAR = 252


class PeriodReturnCalculator:
    """Calculate period-specific return metrics."""

    @staticmethod
    def annualized_return(values: list[float], days: int | None = None) -> float:
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
    def calculate_annualized_return(total_return: float, days: int) -> float:
        """
        Calculate annualized return from total return.

        Args:
            total_return: Total return as decimal
            days: Number of days in period

        Returns:
            Annualized return as decimal
        """
        if days <= 0:
            return 0.0

        years = days / 365.0
        if years <= 0:
            return 0.0

        return (1 + total_return) ** (1 / years) - 1

    @staticmethod
    def calculate_daily_returns(prices: pd.Series) -> pd.Series:
        """
        Calculate daily returns from price series.

        Args:
            prices: Pandas Series of prices with date index

        Returns:
            Series of daily returns
        """
        return prices.pct_change().dropna()

    @staticmethod
    def calculate_monthly_returns(prices: pd.Series) -> pd.Series:
        """
        Calculate monthly returns from price series.

        Args:
            prices: Pandas Series of prices with date index

        Returns:
            Series of monthly returns
        """
        monthly_prices = prices.resample('ME').last()
        return monthly_prices.pct_change().dropna()

    @staticmethod
    def calculate_ytd_return(
        prices: pd.Series, 
        current_date: datetime | None = None, 
        year: int | None = None
    ) -> float:
        """
        Calculate year-to-date return.

        Args:
            prices: Pandas Series of prices with date index
            current_date: Current date for YTD calculation
            year: Specific year to calculate YTD for

        Returns:
            YTD return as decimal
        """
        if len(prices) == 0:
            return 0.0

        if current_date is None:
            current_date = prices.index[-1]

        # If year is specified, use it instead of current_date's year
        target_year = year if year is not None else current_date.year
        year_start = pd.Timestamp(target_year, 1, 1)
        ytd_prices = prices[prices.index >= year_start]

        if len(ytd_prices) < 2:
            return 0.0

        return (ytd_prices.iloc[-1] / ytd_prices.iloc[0]) - 1

    @staticmethod
    def calculate_period_returns(
        prices: pd.Series,
        period: str = 'daily'
    ) -> pd.Series:
        """
        Calculate returns for different periods.

        Args:
            prices: Series of prices with date index
            period: Period type ('daily', 'weekly', 'monthly', 'quarterly', 'yearly')

        Returns:
            Series of period returns
        """
        if period == 'daily':
            return prices.pct_change().dropna()
        elif period == 'weekly':
            weekly_prices = prices.resample('W').last()
            return weekly_prices.pct_change().dropna()
        elif period == 'monthly':
            monthly_prices = prices.resample('ME').last()
            return monthly_prices.pct_change().dropna()
        elif period == 'quarterly':
            quarterly_prices = prices.resample('QE').last()
            return quarterly_prices.pct_change().dropna()
        elif period == 'yearly':
            yearly_prices = prices.resample('YE').last()
            return yearly_prices.pct_change().dropna()
        else:
            raise ValueError(f"Unknown period: {period}")

    @staticmethod
    def rolling_returns(
        values: list[float],
        window: int = 30
    ) -> list[tuple[int, float]]:
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
            # Simple total return calculation
            ret = ((window_values[-1] / window_values[0]) - 1) * 100
            rolling.append((i - 1, ret))

        return rolling

    @staticmethod
    def calculate_rolling_returns(
        prices: pd.Series,
        window: int = 30
    ) -> pd.Series:
        """
        Calculate rolling returns over specified window.

        Args:
            prices: Series of prices
            window: Rolling window size in periods

        Returns:
            Series of rolling returns
        """
        if len(prices) < window:
            return pd.Series(dtype=float)

        # Calculate rolling returns
        rolling = prices.rolling(window=window).apply(
            lambda x: (x.iloc[-1] / x.iloc[0] - 1) if len(x) == window else np.nan
        )

        return rolling