"""
Momentum-based weight calculation strategies.
Handles momentum weighting and trend-following strategies.
"""

import logging
from typing import Dict

import pandas as pd

logger = logging.getLogger(__name__)


class MomentumWeightCalculator:
    """Calculate momentum-based portfolio weights."""

    @staticmethod
    def momentum_weights(
        returns: pd.DataFrame, 
        lookback: int = 20, 
        threshold: float = -0.01
    ) -> pd.Series:
        """
        Calculate momentum-based weights.

        Args:
            returns: DataFrame of returns
            lookback: Number of days to look back for momentum
            threshold: Minimum return threshold

        Returns:
            Series of weights for each asset
        """
        # Calculate rolling momentum (cumulative return over lookback period)
        momentum = (1 + returns.tail(lookback)).prod() - 1

        # Filter assets above threshold
        valid_assets = momentum[momentum > threshold]

        if len(valid_assets) == 0:
            # If no assets meet criteria, equal weight all
            return pd.Series(1.0 / len(momentum), index=momentum.index)

        # Weight by relative momentum (positive momentum only)
        positive_momentum = valid_assets.clip(lower=0)
        weights = positive_momentum / positive_momentum.sum()

        # Fill zeros for excluded assets
        all_weights = pd.Series(0, index=momentum.index)
        all_weights[weights.index] = weights

        return all_weights

    @staticmethod
    def calculate_momentum_weights(
        data: pd.DataFrame,
        lookback: int = 20
    ) -> Dict[str, float]:
        """
        Calculate momentum-based weights.

        Args:
            data: DataFrame of prices
            lookback: Momentum lookback period

        Returns:
            Dictionary of weights
        """
        if data.empty or len(data) < lookback:
            return {}

        # Calculate momentum (price change over lookback)
        momentum = (data.iloc[-1] / data.iloc[-lookback] - 1)

        # Only use positive momentum
        positive_momentum = momentum[momentum > 0]

        if positive_momentum.empty:
            return {asset: 1.0/len(data.columns) for asset in data.columns}

        # Weight by relative momentum
        weights = positive_momentum / positive_momentum.sum()

        # Fill zeros for negative momentum assets
        result = dict.fromkeys(data.columns, 0.0)
        result.update(weights.to_dict())

        return result

    @staticmethod
    def calculate_trend_following_weights(
        prices: pd.DataFrame,
        short_window: int = 10,
        long_window: int = 30
    ) -> Dict[str, float]:
        """
        Calculate trend-following weights based on moving average crossover.

        Args:
            prices: DataFrame of prices
            short_window: Short moving average period
            long_window: Long moving average period

        Returns:
            Dictionary of weights
        """
        if prices.empty or len(prices) < long_window:
            return {}

        weights = {}
        
        for asset in prices.columns:
            # Calculate moving averages
            short_ma = prices[asset].rolling(window=short_window).mean().iloc[-1]
            long_ma = prices[asset].rolling(window=long_window).mean().iloc[-1]
            
            # Bullish signal when short MA > long MA
            if short_ma > long_ma:
                # Weight proportional to MA difference
                weights[asset] = (short_ma / long_ma - 1)
            else:
                weights[asset] = 0.0

        # Normalize weights
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}
        else:
            # Equal weight if no bullish signals
            weights = {asset: 1.0/len(prices.columns) for asset in prices.columns}

        return weights

    @staticmethod
    def calculate_relative_strength_weights(
        prices: pd.DataFrame,
        lookback: int = 20,
        top_n: int = 10
    ) -> Dict[str, float]:
        """
        Calculate weights based on relative strength ranking.

        Args:
            prices: DataFrame of prices
            lookback: Period for calculating returns
            top_n: Number of top performers to include

        Returns:
            Dictionary of weights
        """
        if prices.empty or len(prices) < lookback:
            return {}

        # Calculate returns over lookback period
        returns = (prices.iloc[-1] / prices.iloc[-lookback] - 1)
        
        # Sort by performance and select top N
        top_performers = returns.nlargest(min(top_n, len(returns)))
        
        if top_performers.empty or (top_performers <= 0).all():
            return {asset: 1.0/len(prices.columns) for asset in prices.columns}
        
        # Only include positive performers
        positive_performers = top_performers[top_performers > 0]
        
        if positive_performers.empty:
            return {asset: 1.0/len(prices.columns) for asset in prices.columns}
        
        # Weight proportionally to performance
        weights = positive_performers / positive_performers.sum()
        
        # Create full weight dictionary with zeros for excluded assets
        result = dict.fromkeys(prices.columns, 0.0)
        result.update(weights.to_dict())
        
        return result