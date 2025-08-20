"""
Risk metrics calculation for portfolio performance analysis.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional, Dict, Any
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
        returns: pd.Series,
        risk_free_rate: float = RISK_FREE_RATE,
        target_return: float = 0.0
    ) -> float:
        """Calculate Sortino ratio (uses downside deviation)."""
        if len(returns) < 2:
            return 0.0

        # Annualize returns
        annual_return = (1 + returns.mean()) ** 252 - 1

        # Calculate downside deviation (returns below target)
        downside_returns = returns[returns < target_return]
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
            raise ValueError("Insufficient data for drawdown calculation")

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

        return max_dd, peak_idx, trough_idx  # Return negative value as expected

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
        if len(returns) < 2:
            return 0.0

        annual_return = (1 + returns.mean()) ** 252 - 1
        
        try:
            max_dd, _, _ = RiskCalculator.calculate_max_drawdown(values)
        except ValueError:
            # If insufficient data for drawdown, return high value for positive returns
            if annual_return > 0:
                return float('inf')
            return 0.0

        if max_dd == 0:
            return float('inf')

        return annual_return / abs(max_dd)  # Use absolute value for ratio

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
        if len(returns) == 0:
            raise ValueError("Empty series")
        if len(returns) < 2:
            return 0.0

        vol = returns.std()
        
        # Handle case where all values are the same (floating point precision)
        if pd.isna(vol) or vol < 1e-10:
            return 0.0

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
        confidence: float = 0.95,
        periods: int = 1,
        method: str = 'historical'
    ) -> float:
        """
        Calculate Value at Risk (VaR).
        
        Args:
            returns: Series of returns
            confidence: Confidence level (e.g., 0.95 for 95%)
            periods: Number of periods for VaR calculation
            method: 'historical' or 'parametric'
            
        Returns:
            VaR as a negative number (potential loss)
        """
        if len(returns) < 2:
            return 0.0
        
        if method == 'historical':
            # Calculate the percentile
            alpha = 1 - confidence
            var = np.percentile(returns, alpha * 100)
        elif method == 'parametric':
            # Parametric VaR using normal distribution
            from scipy import stats
            mean = returns.mean()
            std = returns.std()
            alpha = 1 - confidence
            var = mean + std * stats.norm.ppf(alpha)
        else:
            raise ValueError(f"Unknown VaR method: {method}")
        
        # Scale by number of periods
        if periods > 1:
            var = var * np.sqrt(periods)
        
        return var  # Return negative value representing loss
    
    @staticmethod
    def calculate_cvar(
        returns: pd.Series,
        confidence: float = 0.95,
        periods: int = 1
    ) -> float:
        """
        Calculate Conditional Value at Risk (CVaR) / Expected Shortfall.
        
        Args:
            returns: Series of returns
            confidence: Confidence level
            periods: Number of periods
            
        Returns:
            CVaR as a negative number
        """
        if len(returns) < 2:
            return 0.0
        
        # Calculate VaR threshold
        var = RiskCalculator.calculate_var(returns, confidence, 1)
        
        # Get returns worse than VaR
        tail_returns = returns[returns <= var]
        
        if len(tail_returns) == 0:
            return var
        
        # Calculate mean of tail returns
        cvar = tail_returns.mean()
        
        # Scale by periods
        if periods > 1:
            cvar = cvar * np.sqrt(periods)
        
        return cvar  # Return negative value
    
    @staticmethod
    def calculate_rolling_volatility(
        returns: pd.Series,
        window: int = 60
    ) -> pd.Series:
        """
        Calculate rolling volatility.
        
        Args:
            returns: Series of returns
            window: Rolling window size
            
        Returns:
            Series of rolling volatility
        """
        rolling_vol = returns.rolling(window=window, min_periods=1).std()
        # Fill any remaining NaN values with 0
        return rolling_vol.fillna(0)
    
    @staticmethod
    def calculate_kurtosis(returns: pd.Series) -> float:
        """
        Calculate kurtosis (measure of tail heaviness).
        
        Args:
            returns: Series of returns
            
        Returns:
            Kurtosis (excess kurtosis, where normal = 0)
        """
        from scipy import stats
        return float(stats.kurtosis(returns))
    
    @staticmethod
    def calculate_skewness(returns: pd.Series) -> float:
        """
        Calculate skewness (measure of asymmetry).
        
        Args:
            returns: Series of returns
            
        Returns:
            Skewness
        """
        from scipy import stats
        return float(stats.skew(returns))
    
    @staticmethod
    def calculate_tail_ratio(returns: pd.Series, percentile: float = 0.05) -> float:
        """
        Calculate tail ratio (ratio of gains to losses in tails).
        
        Args:
            returns: Series of returns
            percentile: Percentile for tail definition
            
        Returns:
            Tail ratio
        """
        upper_tail = np.percentile(returns, 100 * (1 - percentile))
        lower_tail = np.percentile(returns, 100 * percentile)
        
        if lower_tail == 0:
            return float('inf')
        
        return abs(upper_tail / lower_tail)
    
    @staticmethod
    def calculate_risk_adjusted_metrics(
        returns: pd.Series,
        prices: pd.Series,
        risk_free_rate: float = RISK_FREE_RATE
    ) -> Dict[str, float]:
        """
        Calculate comprehensive risk-adjusted metrics.
        
        Args:
            returns: Series of returns
            prices: Series of prices
            risk_free_rate: Risk-free rate
            
        Returns:
            Dictionary of risk metrics
        """
        max_dd, _, _ = RiskCalculator.calculate_max_drawdown(prices)
        
        return {
            'sharpe_ratio': RiskCalculator.calculate_sharpe_ratio(returns, risk_free_rate),
            'sortino_ratio': RiskCalculator.calculate_sortino_ratio(returns, risk_free_rate),
            'calmar_ratio': RiskCalculator.calculate_calmar_ratio(returns, prices),
            'max_drawdown': max_dd,
            'volatility': RiskCalculator.calculate_volatility(returns),
            'var_95': RiskCalculator.calculate_var(returns, 0.95),
            'cvar_95': RiskCalculator.calculate_cvar(returns, 0.95)
        }
    
    @staticmethod
    def calculate_portfolio_risk(
        returns: pd.DataFrame,
        weights: np.ndarray
    ) -> float:
        """
        Calculate portfolio risk given weights.
        
        Args:
            returns: DataFrame of asset returns
            weights: Array of portfolio weights
            
        Returns:
            Portfolio risk (standard deviation)
        """
        # Calculate covariance matrix
        cov_matrix = returns.cov()
        
        # Calculate portfolio variance
        portfolio_variance = weights @ cov_matrix.values @ weights
        
        # Return portfolio standard deviation
        return np.sqrt(portfolio_variance)
    
    @staticmethod
    def apply_stress_scenarios(
        returns: pd.Series,
        scenarios: Dict[str, float]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Apply stress test scenarios.
        
        Args:
            returns: Series of returns
            scenarios: Dictionary of scenario names and stress factors
            
        Returns:
            Dictionary of stress test results
        """
        base_var = RiskCalculator.calculate_var(returns, 0.95)
        results = {}
        
        for scenario_name, stress_factor in scenarios.items():
            if scenario_name == 'volatility_spike':
                # Multiply volatility
                stressed_returns = returns * stress_factor
                new_var = RiskCalculator.calculate_var(stressed_returns, 0.95)
                results[scenario_name] = {
                    'base_var': base_var,
                    'new_var': new_var,
                    'portfolio_impact': 0.0  # Placeholder
                }
            else:
                # Apply direct shock
                results[scenario_name] = {
                    'portfolio_impact': stress_factor,
                    'base_var': base_var,
                    'new_var': base_var + stress_factor
                }
        
        return results
    
    @staticmethod
    def _clean_series(series: pd.Series) -> pd.Series:
        """
        Clean series by removing NaN values.
        
        Args:
            series: Series to clean
            
        Returns:
            Cleaned series
        """
        return series.dropna()