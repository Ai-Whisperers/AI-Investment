"""
Risk metrics calculation for portfolio performance analysis.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# Risk-free rate for Sharpe ratio calculation (3-month T-bill rate)
RISK_FREE_RATE = 0.05  # 5% annual


class RiskCalculator:
    """Calculates risk metrics for the index."""

    @staticmethod
    def calculate_sharpe_ratio(
        returns: pd.Series, risk_free_rate: float = RISK_FREE_RATE
    ) -> float:
        """Calculate Sharpe ratio."""
        if len(returns) < 2:
            return 0.0

        # Annualize returns and volatility
        annual_return = (1 + returns.mean()) ** 252 - 1
        annual_vol = returns.std() * np.sqrt(252)

        if annual_vol == 0:
            return 0.0

        return (annual_return - risk_free_rate) / annual_vol

    @staticmethod
    def calculate_sortino_ratio(
        returns: pd.Series, risk_free_rate: float = RISK_FREE_RATE
    ) -> float:
        """Calculate Sortino ratio (uses downside deviation)."""
        if len(returns) < 2:
            return 0.0

        # Annualize returns
        annual_return = (1 + returns.mean()) ** 252 - 1

        # Calculate downside deviation
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0:
            return float('inf')  # No downside risk

        downside_std = downside_returns.std() * np.sqrt(252)

        if downside_std == 0:
            return float('inf')

        return (annual_return - risk_free_rate) / downside_std

    @staticmethod
    def calculate_max_drawdown(values: pd.Series) -> Tuple[float, pd.Timestamp, pd.Timestamp]:
        """
        Calculate maximum drawdown and dates.

        Args:
            values: Series of portfolio values

        Returns:
            Tuple of (max_drawdown, peak_date, trough_date)
        """
        if len(values) < 2:
            return 0.0, pd.Timestamp.now(), pd.Timestamp.now()

        # Calculate cumulative max
        cummax = values.cummax()

        # Calculate drawdown
        drawdown = (values - cummax) / cummax

        # Find maximum drawdown
        max_dd = drawdown.min()

        # Find peak and trough dates
        if max_dd == 0:
            return 0.0, values.index[0], values.index[0]

        trough_idx = drawdown.idxmin()
        peak_idx = values[:trough_idx].idxmax()

        return abs(max_dd), peak_idx, trough_idx

    @staticmethod
    def calculate_calmar_ratio(returns: pd.Series, values: pd.Series) -> float:
        """
        Calculate Calmar ratio (annual return / max drawdown).

        Args:
            returns: Series of returns
            values: Series of portfolio values

        Returns:
            Calmar ratio
        """
        if len(returns) < 252:  # Need at least 1 year of data
            return 0.0

        annual_return = (1 + returns.mean()) ** 252 - 1
        max_dd, _, _ = RiskCalculator.calculate_max_drawdown(values)

        if max_dd == 0:
            return float('inf')

        return annual_return / max_dd

    @staticmethod
    def calculate_volatility(returns: pd.Series, annualize: bool = True) -> float:
        """
        Calculate volatility (standard deviation of returns).

        Args:
            returns: Series of returns
            annualize: Whether to annualize the volatility

        Returns:
            Volatility
        """
        if len(returns) < 2:
            return 0.0

        vol = returns.std()

        if annualize:
            vol = vol * np.sqrt(252)

        return vol

    @staticmethod
    def calculate_beta(
        asset_returns: pd.Series, 
        market_returns: pd.Series
    ) -> float:
        """
        Calculate beta relative to market.

        Args:
            asset_returns: Series of asset returns
            market_returns: Series of market returns

        Returns:
            Beta coefficient
        """
        if len(asset_returns) < 2 or len(market_returns) < 2:
            return 1.0

        # Align series
        aligned = pd.DataFrame({
            'asset': asset_returns,
            'market': market_returns
        }).dropna()

        if len(aligned) < 2:
            return 1.0

        covariance = aligned['asset'].cov(aligned['market'])
        market_variance = aligned['market'].var()

        if market_variance == 0:
            return 1.0

        return covariance / market_variance

    @staticmethod
    def calculate_correlation(
        returns1: pd.Series, 
        returns2: pd.Series
    ) -> float:
        """
        Calculate correlation between two return series.

        Args:
            returns1: First return series
            returns2: Second return series

        Returns:
            Correlation coefficient
        """
        if len(returns1) < 2 or len(returns2) < 2:
            return 0.0

        # Align series
        aligned = pd.DataFrame({
            'r1': returns1,
            'r2': returns2
        }).dropna()

        if len(aligned) < 2:
            return 0.0

        return aligned['r1'].corr(aligned['r2'])

    @staticmethod
    def calculate_var(
        returns: pd.Series, 
        confidence_level: float = 0.95
    ) -> float:
        """
        Calculate Value at Risk (VaR).

        Args:
            returns: Series of returns
            confidence_level: Confidence level (e.g., 0.95 for 95%)

        Returns:
            VaR value
        """
        if len(returns) < 20:  # Need sufficient data
            return 0.0

        # Calculate percentile
        var_percentile = (1 - confidence_level) * 100
        return np.percentile(returns, var_percentile)

    @staticmethod
    def calculate_cvar(
        returns: pd.Series, 
        confidence_level: float = 0.95
    ) -> float:
        """
        Calculate Conditional Value at Risk (CVaR).

        Args:
            returns: Series of returns
            confidence_level: Confidence level

        Returns:
            CVaR value
        """
        var = RiskCalculator.calculate_var(returns, confidence_level)
        
        # Calculate mean of returns worse than VaR
        tail_returns = returns[returns <= var]
        
        if len(tail_returns) == 0:
            return var
        
        return tail_returns.mean()

    @staticmethod
    def calculate_information_ratio(
        portfolio_returns: pd.Series,
        benchmark_returns: pd.Series
    ) -> float:
        """
        Calculate Information Ratio.

        Args:
            portfolio_returns: Portfolio return series
            benchmark_returns: Benchmark return series

        Returns:
            Information ratio
        """
        if len(portfolio_returns) < 2 or len(benchmark_returns) < 2:
            return 0.0

        # Calculate excess returns
        excess_returns = portfolio_returns - benchmark_returns

        # Annualize
        annual_excess_return = (1 + excess_returns.mean()) ** 252 - 1
        tracking_error = excess_returns.std() * np.sqrt(252)

        if tracking_error == 0:
            return 0.0

        return annual_excess_return / tracking_error