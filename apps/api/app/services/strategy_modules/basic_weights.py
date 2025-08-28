"""
Basic weight calculation strategies for portfolio allocation.
Handles equal weighting, market cap weighting, and simple calculations.
"""

import logging
from typing import Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class BasicWeightCalculator:
    """Calculate basic portfolio weights."""

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
    def calculate_equal_weights(
        assets: List[str], 
        precision: Optional[int] = None
    ) -> Dict[str, float]:
        """
        Calculate equal weights for all assets.

        Args:
            assets: List of asset symbols
            precision: Number of decimal places to round to (optional)

        Returns:
            Dictionary of asset: weight pairs
        """
        if not assets:
            return {}

        weight = 1.0 / len(assets)
        if precision is not None:
            weight = round(weight, precision)
        return dict.fromkeys(assets, weight)

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
    def calculate_market_cap_weights(
        market_caps: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate market cap weighted allocation.

        Args:
            market_caps: Dictionary of market caps

        Returns:
            Dictionary of weights
        """
        if not market_caps:
            return {}

        total_cap = sum(market_caps.values())

        if total_cap == 0:
            return {asset: 1.0/len(market_caps) for asset in market_caps}

        return {asset: cap/total_cap for asset, cap in market_caps.items()}

    @staticmethod
    def calculate_volatility_adjusted_weights(
        volatilities: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate inverse volatility weights.

        Args:
            volatilities: Dictionary of asset volatilities

        Returns:
            Dictionary of weights
        """
        if not volatilities:
            return {}

        # Inverse volatility weighting
        inv_vols = {asset: 1.0/vol for asset, vol in volatilities.items() if vol > 0}
        total = sum(inv_vols.values())

        if total == 0:
            return {asset: 1.0/len(volatilities) for asset in volatilities}

        return {asset: iv/total for asset, iv in inv_vols.items()}

    @staticmethod
    def calculate_position_sizes(
        weights: Dict[str, float],
        total_value: float,
        min_position_size: float = 0
    ) -> Dict[str, float]:
        """
        Calculate position sizes with minimum thresholds.

        Args:
            weights: Dictionary of weights
            total_value: Total portfolio value
            min_position_size: Minimum position size

        Returns:
            Dictionary of position sizes
        """
        positions = {}

        for asset, weight in weights.items():
            position = weight * total_value
            if position < min_position_size:
                positions[asset] = 0
            else:
                positions[asset] = position

        return positions

    @staticmethod
    def calculate_rebalancing_trades(
        current_weights: Dict[str, float],
        target_weights: Dict[str, float],
        portfolio_value: float
    ) -> Dict[str, float]:
        """
        Calculate trades needed to rebalance portfolio.

        Args:
            current_weights: Current portfolio weights
            target_weights: Target portfolio weights
            portfolio_value: Total portfolio value

        Returns:
            Dictionary of trade amounts
        """
        trades = {}

        for asset in set(current_weights.keys()) | set(target_weights.keys()):
            current = current_weights.get(asset, 0.0)
            target = target_weights.get(asset, 0.0)
            trades[asset] = (target - current) * portfolio_value

        return trades