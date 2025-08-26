"""
Enhanced AutoIndex strategy service with modular architecture.
"""

import logging
from datetime import datetime

import pandas as pd
from sqlalchemy.orm import Session, joinedload

from ..core.config import settings
from ..models.asset import Asset, Price
from ..models.index import Allocation, IndexValue

# Import modular components
from .strategy_modules.data_validator import DataValidator
from .strategy_modules.portfolio_optimizer import PortfolioOptimizer
from .strategy_modules.risk_calculator import RiskCalculator
from .strategy_modules.weight_calculator import WeightCalculator

logger = logging.getLogger(__name__)


class StrategyService:
    """Main strategy service for index computation and portfolio management."""

    def __init__(self, db: Session):
        self.db = db
        self.validator = DataValidator()
        self.weight_calc = WeightCalculator()
        self.risk_calc = RiskCalculator()
        self.optimizer = PortfolioOptimizer(db)

    def compute_index_and_allocations(self, config: dict | None = None):
        """
        Compute index values using dynamic weighted strategy.

        Args:
            config: Strategy configuration dictionary
        """
        if config is None:
            config = self._get_default_config()

        logger.info("Starting dynamic index computation with config: %s", config)

        # Load and prepare data
        prices_df = self._load_price_data()
        if prices_df.empty:
            logger.warning("No price data available")
            return

        # Clean and validate data
        prices_clean = self.validator.clean_price_data(
            prices_df,
            min_price=config["min_price"],
            max_forward_fill=config["max_forward_fill_days"]
        )

        # Calculate returns
        returns = prices_clean.pct_change()
        returns = self.validator.cap_returns(
            returns,
            max_return=config["max_daily_return"],
            min_return=config["min_daily_return"]
        )
        returns = self.validator.detect_outliers(
            returns,
            n_std=config["outlier_std_threshold"]
        )

        # Compute index values
        self._compute_index_values(prices_clean, returns, config)

    def _get_default_config(self) -> dict:
        """Get default strategy configuration."""
        return {
            "momentum_weight": 0.4,
            "market_cap_weight": 0.3,
            "risk_parity_weight": 0.3,
            "min_price": 1.0,
            "max_daily_return": 0.5,
            "min_daily_return": -0.5,
            "max_forward_fill_days": 2,
            "outlier_std_threshold": 3.0,
            "rebalance_frequency": "weekly",
            "daily_drop_threshold": settings.DAILY_DROP_THRESHOLD,
            "momentum_lookback": 20,
            "momentum_threshold": -0.01,
            "risk_lookback": 60,
            "min_weight": 0.01,
            "max_weight": 0.25,
            "max_positions": 30
        }

    def _load_price_data(self) -> pd.DataFrame:
        """Load price data from database into DataFrame.
        
        Uses eager loading to avoid N+1 queries.
        """
        # Use eager loading with joinedload to fetch prices with their assets in one query
        prices = (
            self.db.query(Price)
            .options(joinedload(Price.asset))  # Eager load the related asset
            .join(Asset)
            .filter(Asset.symbol != "^GSPC")  # Exclude S&P 500 benchmark
            .all()
        )
        
        if not prices:
            return pd.DataFrame()

        # Create DataFrame - asset is already loaded, no additional queries
        records = [
            (p.date, p.asset.symbol, p.close)
            for p in prices
        ]

        df = pd.DataFrame(records, columns=["date", "symbol", "close"])
        return df.pivot_table(index="date", columns="symbol", values="close").sort_index()

    def _compute_index_values(
        self,
        prices_df: pd.DataFrame,
        returns: pd.DataFrame,
        config: dict
    ):
        """Compute and store index values."""
        # Determine rebalance dates
        rebalance_dates = self._get_rebalance_dates(
            prices_df.index,
            config["rebalance_frequency"]
        )

        # Initialize
        index_values = []
        current_weights = pd.Series()
        base_value = 10000.0

        for date in prices_df.index:
            # Check if rebalancing needed
            if date in rebalance_dates:
                # Get market caps (simplified for now)
                market_caps = self._get_market_caps(prices_df.columns, date)

                # Optimize portfolio
                current_weights = self.optimizer.optimize_portfolio(
                    prices_df[:date],
                    market_caps,
                    config,
                    date
                )

                # Store allocations
                self._store_allocations(date, current_weights)

            # Calculate index value
            if not current_weights.empty and date > prices_df.index[0]:
                daily_return = (returns.loc[date] * current_weights).sum()
                base_value *= (1 + daily_return)

            index_values.append({
                'date': date,
                'value': base_value
            })

        # Store index values
        self._store_index_values(index_values)

    def _get_rebalance_dates(self, date_index, frequency: str):
        """Get rebalancing dates based on frequency."""
        if frequency == "daily":
            return date_index
        elif frequency == "weekly":
            return date_index[date_index.weekday == 0]  # Mondays
        elif frequency == "monthly":
            return date_index[date_index.day == 1]  # First of month
        else:
            return date_index[date_index.weekday == 0]  # Default to weekly

    def _get_market_caps(self, symbols, date) -> pd.Series:
        """Get market capitalizations for assets."""
        # Simplified - in production, fetch real market cap data
        # For now, use equal weights as fallback
        return pd.Series(1.0, index=symbols)

    def _store_allocations(self, date, weights: pd.Series):
        """Store portfolio allocations in database."""
        # Delete existing allocations for date
        self.db.query(Allocation).filter(Allocation.date == date).delete()

        # Get asset mapping
        assets = {a.symbol: a for a in self.db.query(Asset).all()}

        # Store new allocations
        for symbol, weight in weights.items():
            if symbol in assets and weight > 0:
                allocation = Allocation(
                    date=date,
                    asset_id=assets[symbol].id,
                    weight=float(weight)
                )
                self.db.add(allocation)

        self.db.commit()

    def _store_index_values(self, index_values: list[dict]):
        """Store index values in database."""
        for entry in index_values:
            # Check if value exists
            existing = self.db.query(IndexValue).filter(
                IndexValue.date == entry['date']
            ).first()

            if existing:
                existing.value = entry['value']
            else:
                index_value = IndexValue(
                    date=entry['date'],
                    value=entry['value']
                )
                self.db.add(index_value)

        self.db.commit()

    def calculate_risk_metrics(
        self,
        lookback_days: int = 30
    ) -> dict:
        """Calculate comprehensive risk metrics for the index."""
        # Get index values
        index_values = self.db.query(IndexValue).order_by(IndexValue.date).all()

        if len(index_values) < lookback_days:
            return {}

        # Convert to pandas Series
        values = pd.Series(
            [iv.value for iv in index_values[-lookback_days:]],
            index=[iv.date for iv in index_values[-lookback_days:]]
        )

        # Calculate returns
        returns = values.pct_change().dropna()

        # Calculate metrics
        metrics = {
            'sharpe_ratio': self.risk_calc.calculate_sharpe_ratio(returns),
            'sortino_ratio': self.risk_calc.calculate_sortino_ratio(returns),
            'volatility': self.risk_calc.calculate_volatility(returns),
            'var_95': self.risk_calc.calculate_var(returns, 0.95),
            'cvar_95': self.risk_calc.calculate_cvar(returns, 0.95)
        }

        # Add drawdown metrics
        max_dd, peak_date, trough_date = self.risk_calc.calculate_max_drawdown(values)
        metrics.update({
            'max_drawdown': max_dd,
            'drawdown_peak': peak_date.isoformat() if peak_date else None,
            'drawdown_trough': trough_date.isoformat() if trough_date else None
        })

        return metrics

    def trigger_rebalance(self, force: bool = False) -> dict:
        """Trigger portfolio rebalancing."""
        # Get current allocations
        latest_allocation = self.db.query(Allocation).order_by(
            Allocation.date.desc()
        ).first()

        if not latest_allocation and not force:
            return {"status": "No existing allocations found"}

        # Check if rebalance is needed
        if not force:
            days_since_last = (datetime.now().date() - latest_allocation.date).days
            if days_since_last < 7:  # Minimum 7 days between rebalances
                return {"status": f"Too soon to rebalance ({days_since_last} days)"}

        # Run rebalancing
        config = self._get_default_config()
        self.compute_index_and_allocations(config)

        return {"status": "Rebalancing complete"}


# Backward compatibility function
def compute_index_and_allocations(db: Session, config: dict | None = None):
    """Legacy function for backward compatibility."""
    service = StrategyService(db)
    service.compute_index_and_allocations(config)
