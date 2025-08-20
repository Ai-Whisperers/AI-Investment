"""
Strategy factory for test data generation.
Single responsibility: Create strategy configuration test data.
"""

from typing import Dict, Any, Optional, List
from .base import BaseFactory


class StrategyFactory(BaseFactory):
    """Factory for creating strategy test data."""
    
    STRATEGIES = ["momentum", "value", "growth", "balanced", "defensive"]
    REBALANCE_FREQUENCIES = ["daily", "weekly", "monthly", "quarterly", "yearly"]
    
    @staticmethod
    def create_strategy_config(
        strategy_type: Optional[str] = None,
        rebalance_frequency: Optional[str] = None,
        min_weight: float = 0.01,
        max_weight: float = 0.30
    ) -> Dict[str, Any]:
        """Create strategy configuration for testing."""
        import random
        
        return {
            "strategy_type": strategy_type or random.choice(StrategyFactory.STRATEGIES),
            "rebalance_frequency": rebalance_frequency or random.choice(StrategyFactory.REBALANCE_FREQUENCIES),
            "min_weight": min_weight,
            "max_weight": max_weight,
            "target_volatility": random.uniform(0.10, 0.25),
            "max_drawdown": random.uniform(0.15, 0.30),
            "lookback_period": random.choice([20, 60, 120, 252])
        }
    
    @staticmethod
    def create_risk_parameters(
        risk_tolerance: str = "moderate"
    ) -> Dict[str, Any]:
        """Create risk parameters for testing."""
        risk_profiles = {
            "conservative": {
                "max_volatility": 0.10,
                "max_drawdown": 0.10,
                "sharpe_target": 0.5
            },
            "moderate": {
                "max_volatility": 0.15,
                "max_drawdown": 0.20,
                "sharpe_target": 1.0
            },
            "aggressive": {
                "max_volatility": 0.25,
                "max_drawdown": 0.35,
                "sharpe_target": 1.5
            }
        }
        return risk_profiles.get(risk_tolerance, risk_profiles["moderate"])
    
    @staticmethod
    def create_constraint_set() -> Dict[str, Any]:
        """Create portfolio constraints for testing."""
        return {
            "min_assets": 5,
            "max_assets": 20,
            "min_weight": 0.01,
            "max_weight": 0.30,
            "sector_limits": {
                "Technology": 0.40,
                "Finance": 0.30,
                "Healthcare": 0.30
            },
            "allow_shorts": False
        }