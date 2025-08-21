"""
Portfolio optimization and rebalancing logic.
"""

import logging
from datetime import datetime

import pandas as pd
from sqlalchemy.orm import Session

from .data_validator import DataValidator
from .risk_calculator import RiskCalculator
from .weight_calculator import WeightCalculator

logger = logging.getLogger(__name__)


class PortfolioOptimizer:
    """Handles portfolio optimization and rebalancing."""

    def __init__(self, db: Session):
        self.db = db
        self.validator = DataValidator()
        self.weight_calc = WeightCalculator()
        self.risk_calc = RiskCalculator()

    def optimize_portfolio(
        self,
        prices_df: pd.DataFrame,
        market_caps: pd.Series,
        strategy_config: dict,
        current_date: datetime
    ) -> pd.Series:
        """
        Optimize portfolio weights based on strategy configuration.

        Args:
            prices_df: DataFrame of historical prices
            market_caps: Series of market capitalizations
            strategy_config: Strategy configuration dict
            current_date: Current date for optimization

        Returns:
            Series of optimized weights
        """
        # Validate data
        if not self.validator.validate_data_quality(prices_df):
            logger.warning("Data quality check failed, returning equal weights")
            return self.weight_calc.equal_weights(prices_df.columns)

        # Calculate returns
        returns = prices_df.pct_change().dropna()

        # Clean returns
        returns = self.validator.cap_returns(returns)
        returns = self.validator.detect_outliers(returns)

        # Calculate different weight strategies
        momentum_w = self.weight_calc.momentum_weights(
            returns,
            lookback=strategy_config.get("momentum_lookback", 20),
            threshold=strategy_config.get("momentum_threshold", -0.01)
        )

        market_cap_w = self.weight_calc.market_cap_weights(market_caps)

        risk_parity_w = self.weight_calc.risk_parity_weights(
            returns,
            lookback=strategy_config.get("risk_lookback", 60)
        )

        # Combine weights
        combined_weights = self.weight_calc.combine_weights(
            momentum_w, market_cap_w, risk_parity_w, strategy_config
        )

        # Apply constraints
        final_weights = self.weight_calc.apply_constraints(
            combined_weights,
            min_weight=strategy_config.get("min_weight", 0.01),
            max_weight=strategy_config.get("max_weight", 0.25),
            max_positions=strategy_config.get("max_positions", 30)
        )

        return final_weights

    def should_rebalance(
        self,
        current_weights: pd.Series,
        target_weights: pd.Series,
        threshold: float = 0.05,
        days_since_last: int = 0,
        min_days: int = 30
    ) -> bool:
        """
        Determine if portfolio should be rebalanced.

        Args:
            current_weights: Current portfolio weights
            target_weights: Target portfolio weights
            threshold: Deviation threshold for rebalancing
            days_since_last: Days since last rebalance
            min_days: Minimum days between rebalances

        Returns:
            True if should rebalance
        """
        # Check minimum time constraint
        if days_since_last < min_days:
            return False

        # Calculate weight deviations
        all_assets = current_weights.index.union(target_weights.index)
        current = current_weights.reindex(all_assets, fill_value=0)
        target = target_weights.reindex(all_assets, fill_value=0)

        deviations = abs(current - target)
        max_deviation = deviations.max()

        # Rebalance if any weight deviates more than threshold
        return max_deviation > threshold

    def calculate_turnover(
        self,
        old_weights: pd.Series,
        new_weights: pd.Series
    ) -> float:
        """
        Calculate portfolio turnover.

        Args:
            old_weights: Previous weights
            new_weights: New weights

        Returns:
            Turnover rate (0-2)
        """
        all_assets = old_weights.index.union(new_weights.index)
        old = old_weights.reindex(all_assets, fill_value=0)
        new = new_weights.reindex(all_assets, fill_value=0)

        return abs(new - old).sum()

    def calculate_transaction_costs(
        self,
        turnover: float,
        portfolio_value: float,
        cost_rate: float = 0.001  # 0.1% default
    ) -> float:
        """
        Estimate transaction costs from rebalancing.

        Args:
            turnover: Portfolio turnover rate
            portfolio_value: Total portfolio value
            cost_rate: Transaction cost rate

        Returns:
            Estimated transaction cost
        """
        return turnover * portfolio_value * cost_rate

    def get_rebalance_trades(
        self,
        current_holdings: dict[str, float],
        target_weights: pd.Series,
        portfolio_value: float
    ) -> list[dict]:
        """
        Calculate trades needed for rebalancing.

        Args:
            current_holdings: Dict of symbol -> value
            target_weights: Target portfolio weights
            portfolio_value: Total portfolio value

        Returns:
            List of trade orders
        """
        trades = []

        # Calculate target values
        target_values = target_weights * portfolio_value

        # Calculate trades for each asset
        all_assets = set(current_holdings.keys()).union(set(target_weights.index))

        for asset in all_assets:
            current_value = current_holdings.get(asset, 0)
            target_value = target_values.get(asset, 0)

            trade_value = target_value - current_value

            if abs(trade_value) > 10:  # Minimum trade size
                trades.append({
                    'symbol': asset,
                    'action': 'BUY' if trade_value > 0 else 'SELL',
                    'value': abs(trade_value),
                    'target_weight': target_weights.get(asset, 0)
                })

        # Sort by absolute value (execute larger trades first)
        trades.sort(key=lambda x: x['value'], reverse=True)

        return trades

    def backtest_strategy(
        self,
        prices_df: pd.DataFrame,
        strategy_config: dict,
        initial_value: float = 10000,
        rebalance_frequency: str = 'monthly'
    ) -> pd.DataFrame:
        """
        Backtest a strategy over historical data.

        Args:
            prices_df: Historical prices
            strategy_config: Strategy configuration
            initial_value: Initial portfolio value
            rebalance_frequency: How often to rebalance

        Returns:
            DataFrame with backtest results
        """
        results = []
        portfolio_value = initial_value
        current_weights = pd.Series()

        # Determine rebalance dates
        if rebalance_frequency == 'monthly':
            rebalance_dates = pd.date_range(
                start=prices_df.index[0],
                end=prices_df.index[-1],
                freq='MS'
            )
        elif rebalance_frequency == 'quarterly':
            rebalance_dates = pd.date_range(
                start=prices_df.index[0],
                end=prices_df.index[-1],
                freq='QS'
            )
        else:  # daily
            rebalance_dates = prices_df.index

        for date in prices_df.index:
            # Check if rebalance needed
            if date in rebalance_dates:
                # Get market caps (simplified - use equal caps for backtest)
                market_caps = pd.Series(1.0, index=prices_df.columns)

                # Optimize portfolio
                current_weights = self.optimize_portfolio(
                    prices_df[:date],
                    market_caps,
                    strategy_config,
                    date
                )

            # Calculate portfolio value
            if not current_weights.empty:
                # Get returns for this date
                if date > prices_df.index[0]:
                    returns = prices_df.loc[date] / prices_df.shift(1).loc[date] - 1
                    portfolio_return = (current_weights * returns).sum()
                    portfolio_value *= (1 + portfolio_return)

            results.append({
                'date': date,
                'value': portfolio_value,
                'weights': current_weights.to_dict() if not current_weights.empty else {}
            })

        return pd.DataFrame(results).set_index('date')
