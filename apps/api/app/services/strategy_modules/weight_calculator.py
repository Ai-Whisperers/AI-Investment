"""
Unified weight calculator that orchestrates specialized weight calculation services.
Refactored to follow Single Responsibility Principle with focused service classes.
"""

import logging
from typing import Dict, List, Optional

import pandas as pd

from .basic_weights import BasicWeightCalculator
from .momentum_weights import MomentumWeightCalculator
from .risk_weights import RiskWeightCalculator
from .optimization_weights import OptimizationWeightCalculator
from .constraint_weights import ConstraintWeightManager

logger = logging.getLogger(__name__)


class WeightCalculator:
    """
    Orchestrator for weight calculations.
    Delegates to specialized calculators for different weighting strategies.
    """

    def __init__(self):
        """Initialize with specialized calculators."""
        self.basic = BasicWeightCalculator()
        self.momentum = MomentumWeightCalculator()
        self.risk = RiskWeightCalculator()
        self.optimization = OptimizationWeightCalculator()
        self.constraints = ConstraintWeightManager()

    # Basic weight calculations
    @staticmethod
    def equal_weights(assets: pd.Index) -> pd.Series:
        """Calculate equal weights for all assets."""
        return BasicWeightCalculator.equal_weights(assets)

    @staticmethod
    def calculate_equal_weights(
        assets: List[str], 
        precision: Optional[int] = None
    ) -> Dict[str, float]:
        """Calculate equal weights for all assets."""
        return BasicWeightCalculator.calculate_equal_weights(assets, precision)

    @staticmethod
    def market_cap_weights(market_caps: pd.Series) -> pd.Series:
        """Calculate market cap weighted allocation."""
        return BasicWeightCalculator.market_cap_weights(market_caps)

    @staticmethod
    def calculate_market_cap_weights(
        market_caps: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate market cap weighted allocation."""
        return BasicWeightCalculator.calculate_market_cap_weights(market_caps)

    @staticmethod
    def calculate_volatility_adjusted_weights(
        volatilities: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate inverse volatility weights."""
        return BasicWeightCalculator.calculate_volatility_adjusted_weights(volatilities)

    @staticmethod
    def calculate_position_sizes(
        weights: Dict[str, float],
        total_value: float,
        min_position_size: float = 0
    ) -> Dict[str, float]:
        """Calculate position sizes with minimum thresholds."""
        return BasicWeightCalculator.calculate_position_sizes(
            weights, total_value, min_position_size
        )

    @staticmethod
    def calculate_rebalancing_trades(
        current_weights: Dict[str, float],
        target_weights: Dict[str, float],
        portfolio_value: float
    ) -> Dict[str, float]:
        """Calculate trades needed to rebalance portfolio."""
        return BasicWeightCalculator.calculate_rebalancing_trades(
            current_weights, target_weights, portfolio_value
        )

    # Momentum-based weight calculations
    @staticmethod
    def momentum_weights(
        returns: pd.DataFrame, 
        lookback: int = 20, 
        threshold: float = -0.01
    ) -> pd.Series:
        """Calculate momentum-based weights."""
        return MomentumWeightCalculator.momentum_weights(returns, lookback, threshold)

    @staticmethod
    def calculate_momentum_weights(
        data: pd.DataFrame,
        lookback: int = 20
    ) -> Dict[str, float]:
        """Calculate momentum-based weights."""
        return MomentumWeightCalculator.calculate_momentum_weights(data, lookback)

    # Risk-based weight calculations
    @staticmethod
    def risk_parity_weights(
        returns: pd.DataFrame, 
        lookback: int = 60
    ) -> pd.Series:
        """Calculate risk parity weights."""
        return RiskWeightCalculator.risk_parity_weights(returns, lookback)

    @staticmethod
    def calculate_risk_parity_weights(
        data: pd.DataFrame,
        lookback: int = 60
    ) -> Dict[str, float]:
        """Calculate risk parity weights."""
        return RiskWeightCalculator.calculate_risk_parity_weights(data, lookback)

    @staticmethod
    def minimum_variance_weights(
        returns: pd.DataFrame, 
        lookback: int = 60
    ) -> pd.Series:
        """Calculate minimum variance portfolio weights."""
        return RiskWeightCalculator.minimum_variance_weights(returns, lookback)

    @staticmethod
    def calculate_minimum_variance_weights(
        data: pd.DataFrame,
        lookback: int = 60
    ) -> Dict[str, float]:
        """Calculate minimum variance portfolio weights."""
        return RiskWeightCalculator.calculate_minimum_variance_weights(data, lookback)

    # Optimization-based weight calculations
    @staticmethod
    def calculate_maximum_sharpe_weights(
        assets: List[str],
        returns: pd.DataFrame,
        lookback: int = 60,
        risk_free_rate: float = 0.05
    ) -> Dict[str, float]:
        """Calculate maximum Sharpe ratio portfolio weights."""
        return OptimizationWeightCalculator.calculate_maximum_sharpe_weights(
            assets, returns, lookback, risk_free_rate
        )

    # Constraint management
    @staticmethod
    def apply_weight_constraints(
        weights: Dict[str, float],
        min_weight: float = 0.0,
        max_weight: float = 1.0,
        total_weight: float = 1.0
    ) -> Dict[str, float]:
        """Apply constraints to portfolio weights."""
        return ConstraintWeightManager.apply_weight_constraints(
            weights, min_weight, max_weight, total_weight
        )

    @staticmethod
    def apply_constraints(
        weights,
        constraints: Optional[Dict] = None
    ):
        """Apply portfolio constraints to weights."""
        return ConstraintWeightManager.apply_constraints(weights, constraints)

    @staticmethod
    def combine_weights(
        momentum_w: pd.Series,
        market_cap_w: pd.Series,
        risk_parity_w: pd.Series,
        config: Dict,
    ) -> pd.Series:
        """Combine different weighting strategies."""
        return ConstraintWeightManager.combine_weights(
            momentum_w, market_cap_w, risk_parity_w, config
        )

    # Utility method for calculating weights
    @staticmethod
    def calculate_weights(
        data: pd.DataFrame,
        method: str = 'equal'
    ) -> Dict[str, float]:
        """
        Calculate weights using specified method.

        Args:
            data: DataFrame of prices
            method: Weight calculation method

        Returns:
            Dictionary of weights
        """
        if data.empty:
            raise ValueError("Empty data")

        if method == 'equal':
            return {asset: 1.0/len(data.columns) for asset in data.columns}
        elif method == 'momentum':
            return WeightCalculator.calculate_momentum_weights(data)
        elif method == 'volatility':
            return WeightCalculator.calculate_risk_parity_weights(data)
        else:
            raise ValueError(f"Unknown method: {method}")