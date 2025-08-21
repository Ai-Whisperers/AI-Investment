"""
Risk metrics calculations for portfolio performance.
Includes Sharpe ratio, Sortino ratio, Calmar ratio, volatility, and drawdown metrics.
"""

import logging

import numpy as np

logger = logging.getLogger(__name__)

# Annual trading days
TRADING_DAYS_PER_YEAR = 252
# Default risk-free rate (annual)
DEFAULT_RISK_FREE_RATE = 0.05


class RiskMetricsCalculator:
    """Calculate risk-adjusted performance metrics."""

    @staticmethod
    def sharpe_ratio(
        returns: np.ndarray,
        risk_free_rate: float = DEFAULT_RISK_FREE_RATE
    ) -> float:
        """
        Calculate Sharpe ratio.

        Args:
            returns: Daily returns
            risk_free_rate: Annual risk-free rate

        Returns:
            Annualized Sharpe ratio
        """
        if len(returns) == 0:
            return 0.0

        # Convert annual risk-free rate to daily
        daily_rf = risk_free_rate / TRADING_DAYS_PER_YEAR

        # Calculate excess returns
        excess_returns = returns - daily_rf

        # Handle zero volatility
        if excess_returns.std() == 0:
            return 0.0

        # Annualized Sharpe ratio
        sharpe = (excess_returns.mean() / excess_returns.std()) * np.sqrt(
            TRADING_DAYS_PER_YEAR
        )
        return float(sharpe)

    @staticmethod
    def sortino_ratio(
        returns: np.ndarray,
        risk_free_rate: float = DEFAULT_RISK_FREE_RATE,
        target_return: float = 0.0
    ) -> float:
        """
        Calculate Sortino ratio (Sharpe ratio using only downside volatility).

        Args:
            returns: Daily returns
            risk_free_rate: Annual risk-free rate
            target_return: Target return for downside deviation

        Returns:
            Annualized Sortino ratio
        """
        if len(returns) == 0:
            return 0.0

        # Convert annual risk-free rate to daily
        daily_rf = risk_free_rate / TRADING_DAYS_PER_YEAR

        # Calculate excess returns
        excess_returns = returns - daily_rf

        # Calculate downside deviation (only negative returns)
        downside_returns = excess_returns[excess_returns < target_return]

        if len(downside_returns) == 0:
            # No negative returns, return a high value
            return 10.0

        downside_std = np.sqrt(np.mean(downside_returns**2))

        if downside_std == 0:
            return 0.0

        sortino = (excess_returns.mean() / downside_std) * np.sqrt(
            TRADING_DAYS_PER_YEAR
        )
        return float(sortino)

    @staticmethod
    def volatility(
        returns: np.ndarray,
        annualized: bool = True
    ) -> float:
        """
        Calculate volatility (standard deviation of returns).

        Args:
            returns: Daily returns
            annualized: Whether to annualize the volatility

        Returns:
            Volatility (annualized if requested)
        """
        if len(returns) == 0:
            return 0.0

        vol = returns.std()

        if annualized:
            vol *= np.sqrt(TRADING_DAYS_PER_YEAR)

        return float(vol)

    @staticmethod
    def max_drawdown(values: list[float]) -> tuple[float, int, int]:
        """
        Calculate maximum drawdown.

        Args:
            values: Price series

        Returns:
            Tuple of (max_drawdown_percentage, peak_index, trough_index)
        """
        if len(values) < 2:
            return 0.0, 0, 0

        prices = np.array(values)
        cumulative_returns = prices / prices[0]
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / running_max

        max_dd = drawdown.min()
        trough_idx = drawdown.argmin()

        # Find the peak before the trough
        peak_idx = running_max[:trough_idx + 1].argmax() if trough_idx > 0 else 0

        return float(max_dd * 100), int(peak_idx), int(trough_idx)

    @staticmethod
    def current_drawdown(values: list[float]) -> float:
        """
        Calculate current drawdown from peak.

        Args:
            values: Price series

        Returns:
            Current drawdown as percentage
        """
        if len(values) == 0:
            return 0.0

        current_value = values[-1]
        running_max = max(values)

        if running_max <= 0:
            return 0.0

        return ((current_value - running_max) / running_max) * 100

    @staticmethod
    def calmar_ratio(
        returns: np.ndarray,
        max_dd: float
    ) -> float:
        """
        Calculate Calmar ratio (annual return / max drawdown).

        Args:
            returns: Daily returns
            max_dd: Maximum drawdown (as decimal, e.g., -0.20 for 20%)

        Returns:
            Calmar ratio
        """
        if len(returns) == 0 or max_dd == 0:
            return 0.0

        # Annualized return
        annual_return = (1 + returns.mean()) ** TRADING_DAYS_PER_YEAR - 1

        # Calmar ratio
        calmar = annual_return / abs(max_dd)
        return float(calmar)

    @staticmethod
    def value_at_risk(
        returns: np.ndarray,
        confidence_level: float = 0.95,
        periods: int = 1
    ) -> float:
        """
        Calculate Value at Risk (VaR).

        Args:
            returns: Daily returns
            confidence_level: Confidence level (e.g., 0.95 for 95%)
            periods: Number of periods for VaR calculation

        Returns:
            VaR as percentage
        """
        if len(returns) == 0:
            return 0.0

        # Sort returns
        sorted_returns = np.sort(returns)

        # Find the percentile
        index = int((1 - confidence_level) * len(sorted_returns))

        if index >= len(sorted_returns):
            index = len(sorted_returns) - 1

        var_daily = sorted_returns[index]

        # Scale to multiple periods if needed
        var_scaled = var_daily * np.sqrt(periods)

        return float(var_scaled * 100)

    @staticmethod
    def conditional_value_at_risk(
        returns: np.ndarray,
        confidence_level: float = 0.95
    ) -> float:
        """
        Calculate Conditional Value at Risk (CVaR), also known as Expected Shortfall.

        Args:
            returns: Daily returns
            confidence_level: Confidence level (e.g., 0.95 for 95%)

        Returns:
            CVaR as percentage
        """
        if len(returns) == 0:
            return 0.0

        # Sort returns
        sorted_returns = np.sort(returns)

        # Find the VaR threshold
        var_index = int((1 - confidence_level) * len(sorted_returns))

        if var_index >= len(sorted_returns):
            var_index = len(sorted_returns) - 1

        # Calculate mean of returns below VaR
        cvar = sorted_returns[:var_index + 1].mean()

        return float(cvar * 100)

    @staticmethod
    def downside_deviation(
        returns: np.ndarray,
        target_return: float = 0.0
    ) -> float:
        """
        Calculate downside deviation.

        Args:
            returns: Daily returns
            target_return: Target return threshold

        Returns:
            Annualized downside deviation
        """
        if len(returns) == 0:
            return 0.0

        # Filter returns below target
        downside_returns = returns[returns < target_return]

        if len(downside_returns) == 0:
            return 0.0

        # Calculate downside deviation
        downside_std = np.sqrt(np.mean((downside_returns - target_return) ** 2))

        # Annualize
        return float(downside_std * np.sqrt(TRADING_DAYS_PER_YEAR))
