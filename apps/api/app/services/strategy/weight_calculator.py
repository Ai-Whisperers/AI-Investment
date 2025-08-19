"""
Weight calculation strategies for portfolio allocation.
"""

import pandas as pd
import numpy as np
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class WeightCalculator:
    """Calculates weights for different strategies."""

    @staticmethod
    def momentum_weights(
        returns: pd.DataFrame, lookback: int = 20, threshold: float = -0.01
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
    def market_cap_weights(market_caps: pd.Series) -> pd.Series:
        """
        Calculate market cap weighted allocation.

        Args:
            market_caps: Series of market capitalizations

        Returns:
            Series of weights
        """
        if market_caps.empty or market_caps.sum() == 0:
            return pd.Series()

        return market_caps / market_caps.sum()

    @staticmethod
    def risk_parity_weights(returns: pd.DataFrame, lookback: int = 60) -> pd.Series:
        """
        Calculate risk parity weights (inverse volatility weighting).

        Args:
            returns: DataFrame of returns
            lookback: Number of days for volatility calculation

        Returns:
            Series of weights
        """
        # Calculate rolling volatility
        volatility = returns.tail(lookback).std()

        # Inverse volatility weighting
        if volatility.sum() == 0:
            return pd.Series(1.0 / len(volatility), index=volatility.index)

        inv_vol = 1.0 / volatility
        weights = inv_vol / inv_vol.sum()

        return weights

    @staticmethod
    def equal_weights(assets: pd.Index) -> pd.Series:
        """
        Calculate equal weights for all assets.

        Args:
            assets: Index of asset symbols

        Returns:
            Series of equal weights
        """
        if len(assets) == 0:
            return pd.Series()

        weight = 1.0 / len(assets)
        return pd.Series(weight, index=assets)

    @staticmethod
    def minimum_variance_weights(returns: pd.DataFrame, lookback: int = 60) -> pd.Series:
        """
        Calculate minimum variance portfolio weights.

        Args:
            returns: DataFrame of returns
            lookback: Number of days for covariance calculation

        Returns:
            Series of weights
        """
        try:
            # Calculate covariance matrix
            cov_matrix = returns.tail(lookback).cov()
            
            # Calculate inverse covariance matrix
            inv_cov = np.linalg.inv(cov_matrix.values)
            
            # Calculate minimum variance weights
            ones = np.ones(len(cov_matrix))
            weights = inv_cov @ ones / (ones @ inv_cov @ ones)
            
            return pd.Series(weights, index=cov_matrix.index)
        except np.linalg.LinAlgError:
            logger.warning("Covariance matrix is singular, using equal weights")
            return WeightCalculator.equal_weights(returns.columns)

    @staticmethod
    def combine_weights(
        momentum_w: pd.Series,
        market_cap_w: pd.Series,
        risk_parity_w: pd.Series,
        config: Dict,
    ) -> pd.Series:
        """
        Combine different weighting strategies based on configuration.

        Args:
            momentum_w: Momentum weights
            market_cap_w: Market cap weights
            risk_parity_w: Risk parity weights
            config: Configuration with weight allocations

        Returns:
            Combined weights
        """
        # Align all weight series to same index
        all_assets = momentum_w.index.union(market_cap_w.index).union(
            risk_parity_w.index
        )

        momentum_w = momentum_w.reindex(all_assets, fill_value=0)
        market_cap_w = market_cap_w.reindex(all_assets, fill_value=0)
        risk_parity_w = risk_parity_w.reindex(all_assets, fill_value=0)

        # Combine based on configuration weights
        combined = (
            momentum_w * config.get("momentum_weight", 0.4)
            + market_cap_w * config.get("market_cap_weight", 0.3)
            + risk_parity_w * config.get("risk_parity_weight", 0.3)
        )

        # Normalize to sum to 1
        if combined.sum() > 0:
            combined = combined / combined.sum()

        return combined

    @staticmethod
    def apply_constraints(
        weights: pd.Series,
        min_weight: float = 0.01,
        max_weight: float = 0.25,
        max_positions: int = 30
    ) -> pd.Series:
        """
        Apply portfolio constraints to weights.

        Args:
            weights: Series of weights
            min_weight: Minimum weight per position
            max_weight: Maximum weight per position
            max_positions: Maximum number of positions

        Returns:
            Constrained weights
        """
        # Apply max weight constraint
        weights = weights.clip(upper=max_weight)

        # Filter by minimum weight
        weights = weights[weights >= min_weight]

        # Limit number of positions
        if len(weights) > max_positions:
            weights = weights.nlargest(max_positions)

        # Renormalize
        if weights.sum() > 0:
            weights = weights / weights.sum()

        return weights