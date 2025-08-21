"""
Return calculations for portfolio performance analysis.
Handles daily returns, annualized returns, and cumulative returns.
"""

import logging
from datetime import datetime

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Annual trading days
TRADING_DAYS_PER_YEAR = 252


class ReturnCalculator:
    """Calculate various return metrics for portfolios."""

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
        active = ReturnCalculator.excess_returns(portfolio_returns, benchmark_returns)

        if len(active) == 0:
            return np.array([]), 0.0, 0.0

        tracking_error = active.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
        active_return = active.mean() * TRADING_DAYS_PER_YEAR

        return active, float(tracking_error), float(active_return)

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
            ret = ReturnCalculator.total_return(window_values)
            rolling.append((i - 1, ret))

        return rolling

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
    def calculate_ytd_return(prices: pd.Series, current_date: datetime | None = None, year: int | None = None) -> float:
        """
        Calculate year-to-date return.

        Args:
            prices: Pandas Series of prices with date index
            current_date: Current date for YTD calculation

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
    def calculate_return_distribution_metrics(returns: np.ndarray) -> dict[str, float]:
        """
        Calculate return distribution metrics.

        Args:
            returns: Array of returns

        Returns:
            Dictionary with distribution metrics
        """
        if len(returns) == 0:
            return {
                'mean': 0.0,
                'std': 0.0,
                'skewness': 0.0,
                'kurtosis': 0.0,
                'min': 0.0,
                'max': 0.0
            }

        from scipy import stats

        return {
            'mean': float(np.mean(returns)),
            'std': float(np.std(returns)),
            'skewness': float(stats.skew(returns)),
            'kurtosis': float(stats.kurtosis(returns)),
            'min': float(np.min(returns)),
            'max': float(np.max(returns))
        }

    @staticmethod
    def calculate_time_weighted_return(
        values: list[float],
        dates: pd.DatetimeIndex,
        cash_flows: list[tuple[pd.Timestamp, float]]
    ) -> float:
        """
        Calculate time-weighted return accounting for cash flows.
        Segments periods by cash flows and compounds sub-period returns.

        Args:
            values: Portfolio values at each date
            dates: Dates corresponding to values
            cash_flows: List of (date, amount) tuples for cash flows

        Returns:
            Time-weighted return as decimal
        """
        if len(values) < 2:
            return 0.0

        # Create DataFrame for easier manipulation
        df = pd.DataFrame({'value': values}, index=dates)

        # If no cash flows, simple return
        if not cash_flows:
            return (values[-1] / values[0]) - 1

        # Sort cash flows by date
        sorted_cf = sorted(cash_flows, key=lambda x: x[0])

        # Segment periods by cash flows
        segments = []
        start_idx = 0

        for cf_date, _cf_amount in sorted_cf:
            # Find the index closest to cash flow date
            cf_idx = df.index.get_indexer([cf_date], method='nearest')[0]

            if cf_idx > start_idx:
                # Calculate return for this segment
                segment_return = (df.iloc[cf_idx]['value'] / df.iloc[start_idx]['value']) - 1
                segments.append(1 + segment_return)
                start_idx = cf_idx

        # Final segment from last cash flow to end
        if start_idx < len(df) - 1:
            final_return = (df.iloc[-1]['value'] / df.iloc[start_idx]['value']) - 1
            segments.append(1 + final_return)

        # Compound all segment returns
        if not segments:
            return (values[-1] / values[0]) - 1

        twr = np.prod(segments) - 1
        return float(twr)

    @staticmethod
    def calculate_money_weighted_return(cash_flows: list[tuple[float, datetime]]) -> float:
        """
        Calculate money-weighted return (IRR) using numerical optimization.

        Args:
            cash_flows: List of (amount, date) tuples

        Returns:
            IRR as decimal annual rate
        """
        if len(cash_flows) < 2:
            return 0.0

        try:
            from scipy.optimize import minimize_scalar
        except ImportError:
            logger.warning("scipy not available, using simplified IRR calculation")
            # Fallback to simple calculation if scipy not available
            total_invested = sum(cf[0] for cf in cash_flows if cf[0] < 0)
            total_returned = sum(cf[0] for cf in cash_flows if cf[0] > 0)

            if total_invested == 0:
                return 0.0

            simple_return = (total_returned / abs(total_invested)) - 1
            first_date = min(cf[1] for cf in cash_flows)
            last_date = max(cf[1] for cf in cash_flows)
            years = (last_date - first_date).days / 365.0

            if years <= 0:
                return simple_return

            return (1 + simple_return) ** (1 / years) - 1

        # Sort cash flows by date
        sorted_cf = sorted(cash_flows, key=lambda x: x[1])

        # Get the first date as reference
        first_date = sorted_cf[0][1]

        # Convert cash flows to (amount, years_from_start) format
        cf_values = []
        cf_times = []
        for amount, date in sorted_cf:
            years_from_start = (date - first_date).days / 365.0
            cf_values.append(amount)
            cf_times.append(years_from_start)

        # Define NPV function
        def npv(rate):
            """Calculate NPV at given rate."""
            total = 0
            for amount, t in zip(cf_values, cf_times, strict=False):
                if t == 0:
                    total += amount
                else:
                    total += amount / ((1 + rate) ** t)
            return total

        # Define objective function (squared NPV for minimization)
        def objective(rate):
            """Objective function to minimize (squared NPV)."""
            return npv(rate) ** 2

        # Try to find IRR using optimization
        # Search between -99% and 300% annual return
        result = minimize_scalar(objective, bounds=(-0.99, 3.0), method='bounded')

        if result.success and abs(npv(result.x)) < 0.01:  # Check if NPV is close to 0
            return float(result.x)

        # If optimization fails, try different initial guesses
        for guess in [0.0, 0.1, -0.1, 0.5, -0.5]:
            result = minimize_scalar(
                objective,
                bounds=(guess - 0.5, guess + 0.5),
                method='bounded'
            )
            if result.success and abs(npv(result.x)) < 0.01:
                return float(result.x)

        # Fallback to simple approximation if optimization fails
        logger.warning("IRR optimization failed, using approximation")
        total_invested = sum(cf[0] for cf in cash_flows if cf[0] < 0)
        total_returned = sum(cf[0] for cf in cash_flows if cf[0] > 0)

        if total_invested == 0:
            return 0.0

        simple_return = (total_returned / abs(total_invested)) - 1
        years = cf_times[-1] if cf_times else 1.0

        if years <= 0:
            return simple_return

        return (1 + simple_return) ** (1 / years) - 1

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

    @staticmethod
    def analyze_return_distribution(returns: pd.Series) -> dict[str, float]:
        """
        Analyze return distribution metrics.

        Args:
            returns: Series of returns

        Returns:
            Dictionary with distribution metrics
        """
        if len(returns) == 0:
            return {
                'mean': 0.0,
                'median': 0.0,
                'std': 0.0,
                'skew': 0.0,
                'kurtosis': 0.0,
                'min': 0.0,
                'max': 0.0,
                'percentile_5': 0.0,
                'percentile_95': 0.0
            }

        from scipy import stats

        return {
            'mean': float(returns.mean()),
            'median': float(returns.median()),
            'std': float(returns.std()),
            'skew': float(stats.skew(returns)),
            'kurtosis': float(stats.kurtosis(returns)),
            'min': float(returns.min()),
            'max': float(returns.max()),
            'percentile_5': float(returns.quantile(0.05)),
            'percentile_95': float(returns.quantile(0.95))
        }

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
        return ReturnCalculator.excess_returns(portfolio_returns, benchmark_returns)
