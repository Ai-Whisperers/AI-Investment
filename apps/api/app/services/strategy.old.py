"""
Enhanced AutoIndex strategy with dynamic weighting and comprehensive risk management.
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from ..models.asset import Asset, Price
from ..models.index import IndexValue, Allocation
from ..core.config import settings

logger = logging.getLogger(__name__)

# Risk-free rate for Sharpe ratio calculation (3-month T-bill rate)
RISK_FREE_RATE = 0.05  # 5% annual


class DataValidator:
    """Validates and cleans price data."""

    @staticmethod
    def clean_price_data(
        df: pd.DataFrame, min_price: float = 1.0, max_forward_fill: int = 2
    ) -> pd.DataFrame:
        """
        Clean and validate price data.

        Args:
            df: DataFrame with price data (columns = symbols, index = dates)
            min_price: Minimum valid price threshold
            max_forward_fill: Maximum days to forward-fill missing data

        Returns:
            Cleaned DataFrame
        """
        logger.info(f"Cleaning price data: {len(df)} rows, {len(df.columns)} assets")

        # Replace prices below threshold with NaN
        df_clean = df.copy()
        df_clean[df_clean < min_price] = np.nan

        # Forward fill missing values up to max_forward_fill days
        df_clean = df_clean.fillna(method="ffill", limit=max_forward_fill)

        # Drop columns (assets) with too many missing values (>10%)
        missing_pct = df_clean.isnull().sum() / len(df_clean)
        valid_assets = missing_pct[missing_pct < 0.1].index
        df_clean = df_clean[valid_assets]

        # Drop rows where all values are NaN
        df_clean = df_clean.dropna(how="all")

        logger.info(
            f"After cleaning: {len(df_clean)} rows, {len(df_clean.columns)} assets"
        )
        return df_clean

    @staticmethod
    def cap_returns(
        returns: pd.DataFrame, max_return: float = 0.5, min_return: float = -0.5
    ) -> pd.DataFrame:
        """
        Cap extreme returns to prevent data errors from inflating the index.

        Args:
            returns: DataFrame of returns
            max_return: Maximum allowed daily return (e.g., 0.5 = 50%)
            min_return: Minimum allowed daily return (e.g., -0.5 = -50%)

        Returns:
            Capped returns DataFrame
        """
        return returns.clip(lower=min_return, upper=max_return)

    @staticmethod
    def detect_outliers(returns: pd.DataFrame, n_std: float = 3.0) -> pd.DataFrame:
        """
        Detect and handle outliers using z-score method.

        Args:
            returns: DataFrame of returns
            n_std: Number of standard deviations for outlier threshold

        Returns:
            DataFrame with outliers replaced by median
        """
        z_scores = np.abs((returns - returns.mean()) / returns.std())
        outliers = z_scores > n_std

        # Replace outliers with median return for that asset
        for col in returns.columns:
            median_return = returns[col].median()
            returns.loc[outliers[col], col] = median_return

        return returns


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
        returns: pd.Series, risk_free_rate: float = RISK_FREE_RATE
    ) -> float:
        """Calculate Sortino ratio (uses downside deviation)."""
        if len(returns) < 2:
            return 0.0

        # Annualize returns
        annual_return = (1 + returns.mean()) ** 252 - 1

        # Calculate downside deviation
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0:
            return float("inf")  # No downside risk

        downside_dev = downside_returns.std() * np.sqrt(252)

        if downside_dev == 0:
            return 0.0

        return (annual_return - risk_free_rate) / downside_dev

    @staticmethod
    def calculate_max_drawdown(values: pd.Series) -> Tuple[float, float]:
        """
        Calculate maximum drawdown and current drawdown.

        Returns:
            Tuple of (max_drawdown, current_drawdown)
        """
        if len(values) < 2:
            return 0.0, 0.0

        # Calculate running maximum
        running_max = values.expanding().max()

        # Calculate drawdown
        drawdown = (values - running_max) / running_max

        max_dd = drawdown.min()
        current_dd = drawdown.iloc[-1]

        return max_dd, current_dd

    @staticmethod
    def calculate_var(
        returns: pd.Series, confidence_levels: List[float] = [0.95, 0.99]
    ) -> Dict[str, float]:
        """
        Calculate Value at Risk at different confidence levels.

        Args:
            returns: Series of returns
            confidence_levels: List of confidence levels

        Returns:
            Dictionary of VaR values
        """
        var_dict = {}
        for level in confidence_levels:
            var_dict[f"var_{int(level*100)}"] = returns.quantile(1 - level)
        return var_dict

    @staticmethod
    def calculate_beta_correlation(
        index_returns: pd.Series, benchmark_returns: pd.Series
    ) -> Tuple[float, float]:
        """
        Calculate beta and correlation relative to benchmark.

        Returns:
            Tuple of (beta, correlation)
        """
        if len(index_returns) < 2 or len(benchmark_returns) < 2:
            return 1.0, 0.0

        # Align series
        aligned = pd.DataFrame(
            {"index": index_returns, "benchmark": benchmark_returns}
        ).dropna()

        if len(aligned) < 2:
            return 1.0, 0.0

        # Calculate correlation
        correlation = aligned["index"].corr(aligned["benchmark"])

        # Calculate beta
        covariance = aligned["index"].cov(aligned["benchmark"])
        benchmark_var = aligned["benchmark"].var()

        if benchmark_var == 0:
            beta = 1.0
        else:
            beta = covariance / benchmark_var

        return beta, correlation


def compute_index_and_allocations(db: Session, config: Optional[Dict] = None):
    """
    Compute index values using dynamic weighted strategy.

    Args:
        db: Database session
        config: Strategy configuration dictionary
    """
    if config is None:
        config = {
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
        }

    logger.info("Starting dynamic index computation with config: %s", config)

    # Load prices into DataFrame
    prices = db.query(Price).all()
    if not prices:
        logger.warning("No price data available")
        return

    # Map asset_id -> symbol
    assets = {a.id: a for a in db.query(Asset).all()}

    # Create DataFrame: rows=date, columns=symbol, values=close
    records = [
        (p.date, assets[p.asset_id].symbol, p.close)
        for p in prices
        if p.asset_id in assets and assets[p.asset_id].symbol != "^GSPC"
    ]

    df = pd.DataFrame(records, columns=["date", "symbol", "close"])
    pivot = df.pivot_table(index="date", columns="symbol", values="close").sort_index()

    # Clean and validate data
    validator = DataValidator()
    pivot_clean = validator.clean_price_data(
        pivot,
        min_price=config["min_price"],
        max_forward_fill=config["max_forward_fill_days"],
    )

    # Calculate returns
    returns = pivot_clean.pct_change()

    # Cap extreme returns
    returns = validator.cap_returns(
        returns,
        max_return=config["max_daily_return"],
        min_return=config["min_daily_return"],
    )

    # Handle outliers
    returns = validator.detect_outliers(returns, n_std=config["outlier_std_threshold"])

    # Initialize calculators
    weight_calc = WeightCalculator()
    risk_calc = RiskCalculator()

    # Initialize index tracking
    index_values = []
    allocations = []
    risk_metrics = []

    # Starting value (will be normalized to 100)
    portfolio_value = 1.0
    last_rebalance = None
    current_weights = None

    # Get market cap data if available (placeholder for now)
    # In production, this would fetch actual market cap data
    market_caps = pd.Series(1.0, index=pivot_clean.columns)  # Equal market cap for now

    # Process each trading day
    for dt, daily_returns in returns.iterrows():
        if pd.isna(daily_returns).all():
            continue

        # Check if rebalancing is needed
        should_rebalance = False

        if last_rebalance is None:
            should_rebalance = True
        elif config["rebalance_frequency"] == "daily":
            should_rebalance = True
        elif config["rebalance_frequency"] == "weekly":
            should_rebalance = (dt - last_rebalance).days >= 7
        elif config["rebalance_frequency"] == "monthly":
            should_rebalance = (dt - last_rebalance).days >= 30

        # Calculate new weights if rebalancing
        if should_rebalance:
            # Get recent returns for calculations
            recent_returns = returns.loc[:dt].tail(60)  # Last 60 days

            # Calculate weights for each strategy
            momentum_w = weight_calc.momentum_weights(
                recent_returns, threshold=config.get("daily_drop_threshold", -0.01)
            )
            market_cap_w = weight_calc.market_cap_weights(market_caps)
            risk_parity_w = weight_calc.risk_parity_weights(recent_returns)

            # Combine weights
            current_weights = weight_calc.combine_weights(
                momentum_w, market_cap_w, risk_parity_w, config
            )

            last_rebalance = dt

            # Save allocations
            for symbol, weight in current_weights.items():
                if weight > 0:
                    asset = next(
                        (a for a in assets.values() if a.symbol == symbol), None
                    )
                    if asset:
                        allocations.append((dt, asset.id, float(weight)))

        # Calculate portfolio return for the day
        if current_weights is not None:
            # Weight-adjusted returns
            portfolio_return = (daily_returns * current_weights).sum()

            # Handle NaN (if all weights are on missing assets)
            if pd.isna(portfolio_return):
                portfolio_return = 0.0
        else:
            portfolio_return = 0.0

        # Update portfolio value
        portfolio_value *= 1 + portfolio_return

        # Store index value
        index_values.append((dt, float(portfolio_value)))

        # Calculate risk metrics periodically (weekly)
        if dt == returns.index[-1] or (
            last_rebalance and (dt - last_rebalance).days % 7 == 0
        ):
            # Get returns up to current date
            index_returns = (
                pd.Series([v[1] for v in index_values]).pct_change().dropna()
            )

            if len(index_returns) > 20:  # Need minimum data for metrics
                metrics = {
                    "date": dt,
                    "total_return": (portfolio_value - 1.0) * 100,
                    "sharpe_ratio": risk_calc.calculate_sharpe_ratio(index_returns),
                    "sortino_ratio": risk_calc.calculate_sortino_ratio(index_returns),
                }

                # Calculate drawdown
                index_series = pd.Series([v[1] for v in index_values])
                max_dd, current_dd = risk_calc.calculate_max_drawdown(index_series)
                metrics["max_drawdown"] = max_dd
                metrics["current_drawdown"] = current_dd

                # Calculate VaR
                var_metrics = risk_calc.calculate_var(index_returns)
                metrics.update(var_metrics)

                risk_metrics.append(metrics)

    # Normalize index values to base 100
    if index_values:
        first_value = index_values[0][1]
        normalized_index_values = [
            (dt, (val / first_value) * 100.0) for dt, val in index_values
        ]
    else:
        normalized_index_values = []

    # Safe upsert with transaction and backup

    # Create backup of existing data before modifications
    existing_index_values = db.query(IndexValue).all()
    existing_allocations = db.query(Allocation).all()

    backup_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "index_values": [
            (iv.date.isoformat(), iv.value) for iv in existing_index_values
        ],
        "allocations": [
            (a.date.isoformat(), a.asset_id, a.weight) for a in existing_allocations
        ],
    }

    # Log backup for recovery if needed
    logger.info(
        f"Backed up {len(existing_index_values)} index values and {len(existing_allocations)} allocations"
    )

    try:
        # Begin transaction
        db.begin_nested() if hasattr(db, "begin_nested") else None

        # Track dates for cleanup
        new_dates = set()

        # Upsert index values
        for dt, val in normalized_index_values:
            new_dates.add(dt)
            existing = db.query(IndexValue).filter(IndexValue.date == dt).first()
            if existing:
                existing.value = val
            else:
                db.add(IndexValue(date=dt, value=val))

        # Upsert allocations
        allocation_dates = set()
        for dt, asset_id, weight in allocations:
            allocation_dates.add(dt)
            existing = (
                db.query(Allocation)
                .filter(Allocation.date == dt, Allocation.asset_id == asset_id)
                .first()
            )
            if existing:
                existing.weight = weight
            else:
                db.add(Allocation(date=dt, asset_id=asset_id, weight=weight))

        # Optional: Remove outdated entries (older than strategy start date)
        if normalized_index_values:
            oldest_date = min(new_dates)
            # Only remove very old data (>1 year before oldest new date)
            cutoff_date = oldest_date - timedelta(days=365)
            db.query(IndexValue).filter(IndexValue.date < cutoff_date).delete()
            db.query(Allocation).filter(Allocation.date < cutoff_date).delete()

        db.commit()

    except Exception as e:
        logger.error(f"Failed to update index/allocations: {e}")
        db.rollback()

        # Attempt to restore from backup if critical failure
        logger.info("Attempting to restore from backup...")
        try:
            # Clear corrupted data
            db.query(IndexValue).delete()
            db.query(Allocation).delete()

            # Restore from backup
            for date_str, value in backup_data["index_values"]:
                db.add(
                    IndexValue(
                        date=datetime.fromisoformat(date_str).date(), value=value
                    )
                )

            for date_str, asset_id, weight in backup_data["allocations"]:
                db.add(
                    Allocation(
                        date=datetime.fromisoformat(date_str).date(),
                        asset_id=asset_id,
                        weight=weight,
                    )
                )

            db.commit()
            logger.info("Successfully restored from backup")
        except Exception as restore_error:
            logger.critical(f"Failed to restore from backup: {restore_error}")
            db.rollback()

        raise e

    logger.info(
        f"Index computation complete. {len(normalized_index_values)} values, {len(allocations)} allocations"
    )

    # Log final metrics
    if risk_metrics:
        final_metrics = risk_metrics[-1]
        logger.info(
            f"Final metrics - Total Return: {final_metrics['total_return']:.2f}%, "
            f"Sharpe: {final_metrics['sharpe_ratio']:.2f}, "
            f"Max Drawdown: {final_metrics['max_drawdown']:.2%}"
        )

    return normalized_index_values, risk_metrics
