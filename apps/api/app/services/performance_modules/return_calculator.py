"""
Return calculations for portfolio performance analysis.
Handles daily returns, annualized returns, and cumulative returns.
"""

import numpy as np
import pandas as pd
from typing import List, Optional, Tuple, Dict
from datetime import datetime
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
    def calculate_log_returns(prices: List[float]) -> np.ndarray:
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
        return np.log(prices_array[1:] / prices_array[:-1])
    
    @staticmethod
    def calculate_cumulative_returns(returns: np.ndarray) -> np.ndarray:
        """
        Calculate cumulative returns from return series.
        
        Args:
            returns: Array of period returns
            
        Returns:
            Array of cumulative returns
        """
        if len(returns) == 0:
            return np.array([])
        
        # Convert returns to growth factors and calculate cumulative product
        growth_factors = 1 + returns
        cum_returns = np.cumprod(growth_factors) - 1
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
        monthly_prices = prices.resample('M').last()
        return monthly_prices.pct_change().dropna()
    
    @staticmethod
    def calculate_ytd_return(prices: pd.Series, current_date: Optional[datetime] = None) -> float:
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
        
        year_start = pd.Timestamp(current_date.year, 1, 1)
        ytd_prices = prices[prices.index >= year_start]
        
        if len(ytd_prices) < 2:
            return 0.0
        
        return (ytd_prices.iloc[-1] / ytd_prices.iloc[0]) - 1
    
    @staticmethod
    def calculate_compound_return(returns: np.ndarray) -> float:
        """
        Calculate compound return from series of returns.
        
        Args:
            returns: Array of period returns
            
        Returns:
            Compound return as decimal
        """
        if len(returns) == 0:
            return 0.0
        
        return np.prod(1 + returns) - 1
    
    @staticmethod
    def calculate_return_distribution_metrics(returns: np.ndarray) -> Dict[str, float]:
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
        values: List[float],
        dates: pd.DatetimeIndex,
        cash_flows: List[Tuple[pd.Timestamp, float]]
    ) -> float:
        """
        Calculate time-weighted return accounting for cash flows.
        Note: Simplified implementation - production would need more robust handling.
        
        Args:
            values: Portfolio values at each date
            dates: Dates corresponding to values
            cash_flows: List of (date, amount) tuples for cash flows
            
        Returns:
            Time-weighted return as decimal
        """
        if len(values) < 2:
            return 0.0
        
        # Simple approximation: calculate return ignoring cash flow timing
        # Full implementation would segment periods by cash flows
        total_return = (values[-1] / values[0]) - 1
        return total_return
    
    @staticmethod
    def calculate_money_weighted_return(cash_flows: List[Tuple[float, datetime]]) -> float:
        """
        Calculate money-weighted return (IRR).
        Note: Simplified implementation - production would use scipy.optimize.
        
        Args:
            cash_flows: List of (amount, date) tuples
            
        Returns:
            IRR as decimal annual rate
        """
        if len(cash_flows) < 2:
            return 0.0
        
        # Simple approximation: calculate based on total in/out
        total_invested = sum(cf[0] for cf in cash_flows if cf[0] < 0)
        total_returned = sum(cf[0] for cf in cash_flows if cf[0] > 0)
        
        if total_invested == 0:
            return 0.0
        
        # Simple return calculation - production would solve for IRR
        simple_return = (total_returned / abs(total_invested)) - 1
        
        # Approximate annualization based on time span
        first_date = min(cf[1] for cf in cash_flows)
        last_date = max(cf[1] for cf in cash_flows)
        years = (last_date - first_date).days / 365.0
        
        if years <= 0:
            return simple_return
        
        # Annualize the return
        return (1 + simple_return) ** (1 / years) - 1
    
    @staticmethod
    def calculate_active_return(
        portfolio_returns: np.ndarray,
        benchmark_returns: np.ndarray
    ) -> float:
        """
        Calculate active return vs benchmark.
        
        Args:
            portfolio_returns: Portfolio return series
            benchmark_returns: Benchmark return series
            
        Returns:
            Active return as decimal
        """
        active, _, active_return = ReturnCalculator.active_returns(
            portfolio_returns, benchmark_returns
        )
        return active_return
    
    @staticmethod
    def calculate_tracking_error(
        portfolio_returns: np.ndarray,
        benchmark_returns: np.ndarray
    ) -> float:
        """
        Calculate tracking error vs benchmark.
        
        Args:
            portfolio_returns: Portfolio return series
            benchmark_returns: Benchmark return series
            
        Returns:
            Tracking error as decimal
        """
        active, tracking_error, _ = ReturnCalculator.active_returns(
            portfolio_returns, benchmark_returns
        )
        return tracking_error
    
    @staticmethod
    def calculate_excess_returns(
        portfolio_returns: np.ndarray,
        benchmark_returns: np.ndarray
    ) -> np.ndarray:
        """
        Wrapper for excess_returns with consistent naming.
        """
        return ReturnCalculator.excess_returns(portfolio_returns, benchmark_returns)