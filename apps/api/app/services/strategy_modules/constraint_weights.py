"""
Weight constraint application and portfolio management.
Handles constraint application, weight combination, and portfolio adjustments.
"""

import logging
from typing import Dict, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class ConstraintWeightManager:
    """Manage portfolio weight constraints and adjustments."""

    @staticmethod
    def apply_weight_constraints(
        weights: Dict[str, float],
        min_weight: float = 0.0,
        max_weight: float = 1.0,
        total_weight: float = 1.0
    ) -> Dict[str, float]:
        """
        Apply constraints to portfolio weights.

        Args:
            weights: Dictionary of weights
            min_weight: Minimum weight per asset
            max_weight: Maximum weight per asset
            total_weight: Total portfolio weight

        Returns:
            Constrained weights
        """
        if not weights:
            return {}

        # Apply min/max constraints
        constrained = {}
        for asset, weight in weights.items():
            constrained[asset] = max(min_weight, min(max_weight, weight))

        # Normalize to sum to total_weight
        current_sum = sum(constrained.values())
        if current_sum > 0:
            factor = total_weight / current_sum
            constrained = {k: v * factor for k, v in constrained.items()}

        return constrained

    @staticmethod
    def apply_constraints(
        weights,
        constraints: Optional[Dict] = None
    ):
        """
        Apply portfolio constraints to weights.

        Args:
            weights: Dict or Series of weights
            constraints: Dict with constraint parameters

        Returns:
            Constrained weights as dict
        """
        # Handle both dict and Series inputs
        if isinstance(weights, dict):
            weights_series = pd.Series(weights)
            return_dict = True
        else:
            weights_series = weights
            return_dict = False

        # Extract constraints
        if constraints is None:
            constraints = {}
        min_weight = constraints.get('min_weight', 0.01)
        max_weight = constraints.get('max_weight', 0.25)
        max_positions = constraints.get('max_positions', 30)

        # Limit number of positions first
        if len(weights_series) > max_positions:
            weights_series = weights_series.nlargest(max_positions)

        # Check if constraint is mathematically feasible for full allocation
        n_assets = len(weights_series)
        if n_assets * max_weight < 1.0:
            # Cannot achieve full allocation with max_weight constraint
            # We need to relax the min_weight constraint
            required_min = 1.0 - (n_assets - 1) * max_weight
            min_weight = max(required_min, 0.0)
            logger.debug(f"Adjusting min_weight to {min_weight} for feasibility")

        # Apply iterative constraint satisfaction
        for _iteration in range(20):  # More iterations for convergence
            # First ensure min weight
            weights_series = weights_series.clip(lower=min_weight)

            # Normalize to sum to 1.0
            current_sum = weights_series.sum()
            if current_sum > 0:
                weights_series = weights_series / current_sum

            # Check if max weight is violated
            max_violation = weights_series.max() - max_weight
            if max_violation <= 1e-10:
                # All constraints satisfied
                break

            # If max weight is violated, clip and redistribute
            over_max = weights_series > max_weight
            if over_max.any():
                # Calculate excess weight
                excess = (weights_series[over_max] - max_weight).sum()
                # Clip to max weight
                weights_series[over_max] = max_weight
                # Redistribute excess to assets under max weight
                under_max = weights_series < max_weight
                if under_max.any():
                    # Distribute proportionally to current weights
                    available_space = (max_weight - weights_series[under_max]).sum()
                    if available_space > 0:
                        redistribution = min(excess, available_space)
                        weights_series[under_max] += redistribution * (
                            (max_weight - weights_series[under_max]) / available_space
                        )

        # Final normalization to ensure sum to 1.0
        if weights_series.sum() > 0:
            weights_series = weights_series / weights_series.sum()

        # Return in the same format as input
        if return_dict:
            return weights_series.to_dict()
        return weights_series

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
    def combine_weight_strategies(
        strategies: Dict[str, Dict[str, float]],
        strategy_weights: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Combine multiple weight strategies with given allocations.

        Args:
            strategies: Dict of strategy_name -> asset weights
            strategy_weights: Dict of strategy_name -> strategy weight

        Returns:
            Combined weights dictionary
        """
        if not strategies or not strategy_weights:
            return {}

        # Get all unique assets
        all_assets = set()
        for weights in strategies.values():
            all_assets.update(weights.keys())

        # Initialize combined weights
        combined = {asset: 0.0 for asset in all_assets}

        # Combine strategies
        for strategy_name, strategy_weight in strategy_weights.items():
            if strategy_name in strategies:
                asset_weights = strategies[strategy_name]
                for asset in all_assets:
                    combined[asset] += asset_weights.get(asset, 0.0) * strategy_weight

        # Normalize
        total = sum(combined.values())
        if total > 0:
            combined = {k: v / total for k, v in combined.items()}

        return combined

    @staticmethod
    def filter_minimum_positions(
        weights: Dict[str, float],
        min_weight_threshold: float = 0.01
    ) -> Dict[str, float]:
        """
        Filter out positions below minimum threshold and renormalize.

        Args:
            weights: Dictionary of weights
            min_weight_threshold: Minimum weight to keep

        Returns:
            Filtered and renormalized weights
        """
        if not weights:
            return {}

        # Filter positions above threshold
        filtered = {
            asset: weight 
            for asset, weight in weights.items() 
            if weight >= min_weight_threshold
        }

        # Renormalize
        total = sum(filtered.values())
        if total > 0:
            filtered = {k: v / total for k, v in filtered.items()}

        return filtered