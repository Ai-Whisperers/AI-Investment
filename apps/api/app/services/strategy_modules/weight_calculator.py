"""
Weight calculation strategies for portfolio allocation.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
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
    def calculate_equal_weights(assets: List[str], precision: int = None) -> Dict[str, float]:
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
        return {asset: weight for asset in assets}
    
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
    def calculate_risk_parity_weights(
        data: pd.DataFrame,
        lookback: int = 60
    ) -> Dict[str, float]:
        """
        Calculate risk parity weights (inverse volatility).
        
        Args:
            data: DataFrame of prices or returns
            lookback: Lookback period for volatility
            
        Returns:
            Dictionary of weights
        """
        if data.empty:
            return {}
        
        # Convert prices to returns if needed
        if (data > 0).all().all():  # Likely prices
            returns = data.pct_change().dropna()
        else:
            returns = data
        
        # Calculate volatilities
        vols = returns.tail(lookback).std()
        
        # Handle zero volatility
        vols = vols.replace(0, 1e-10)
        
        # Inverse volatility weighting
        inv_vols = 1.0 / vols
        weights = inv_vols / inv_vols.sum()
        
        return weights.to_dict()
    
    @staticmethod
    def calculate_minimum_variance_weights(
        data: pd.DataFrame,
        lookback: int = 60
    ) -> Dict[str, float]:
        """
        Calculate minimum variance portfolio weights using optimization.
        
        Args:
            data: DataFrame of prices or returns
            lookback: Lookback period
            
        Returns:
            Dictionary of weights
        """
        if data.empty:
            return {}
        
        try:
            from scipy.optimize import minimize
            
            # Convert prices to returns if needed
            if (data > 0).all().all():  # Likely prices
                returns = data.pct_change().dropna()
            else:
                returns = data
            
            # Get returns for the specified assets
            asset_returns = returns.tail(lookback)
            
            # Calculate covariance matrix
            cov_matrix = asset_returns.cov().values
            n_assets = len(data.columns)
            assets = data.columns.tolist()
            
            # Objective function: portfolio variance
            def portfolio_variance(weights):
                return weights @ cov_matrix @ weights
            
            # Constraints: weights sum to 1
            constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
            
            # Bounds: weights between 0 and 1 (long-only)
            bounds = tuple((0, 1) for _ in range(n_assets))
            
            # Initial guess: equal weights
            x0 = np.array([1.0/n_assets] * n_assets)
            
            # Optimize
            result = minimize(
                portfolio_variance,
                x0,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints
            )
            
            if result.success:
                return {asset: float(weight) for asset, weight in zip(assets, result.x)}
            else:
                logger.warning(f"Optimization failed: {result.message}, using equal weights")
                return {asset: 1.0/len(assets) for asset in assets}
                
        except ImportError:
            logger.warning("scipy not available, using risk parity as proxy")
            return WeightCalculator.calculate_risk_parity_weights(data, lookback)
        except Exception as e:
            logger.error(f"Error in minimum variance optimization: {e}")
            return {asset: 1.0/n_assets for asset in data.columns}
    
    @staticmethod
    def calculate_maximum_sharpe_weights(
        assets: List[str],
        returns: pd.DataFrame,
        lookback: int = 60,
        risk_free_rate: float = 0.05
    ) -> Dict[str, float]:
        """
        Calculate maximum Sharpe ratio portfolio weights using optimization.
        
        Args:
            assets: List of asset symbols
            returns: DataFrame of returns
            lookback: Lookback period
            risk_free_rate: Annual risk-free rate
            
        Returns:
            Dictionary of weights
        """
        if not assets or returns.empty:
            return {asset: 1.0/len(assets) for asset in assets} if assets else {}
        
        try:
            from scipy.optimize import minimize
            
            # Get returns for the specified assets
            asset_returns = returns[assets].tail(lookback)
            
            # Calculate expected returns and covariance
            mean_returns = asset_returns.mean().values
            cov_matrix = asset_returns.cov().values
            n_assets = len(assets)
            
            # Convert risk-free rate to daily
            daily_rf = (1 + risk_free_rate) ** (1/252) - 1
            
            # Objective function: negative Sharpe ratio (to minimize)
            def negative_sharpe(weights):
                portfolio_return = np.sum(mean_returns * weights)
                portfolio_std = np.sqrt(weights @ cov_matrix @ weights)
                if portfolio_std == 0:
                    return 0
                sharpe = (portfolio_return - daily_rf) / portfolio_std
                return -sharpe * np.sqrt(252)  # Annualized negative Sharpe
            
            # Constraints: weights sum to 1
            constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
            
            # Bounds: weights between 0 and 1 (long-only)
            bounds = tuple((0, 1) for _ in range(n_assets))
            
            # Initial guess: equal weights
            x0 = np.array([1.0/n_assets] * n_assets)
            
            # Optimize
            result = minimize(
                negative_sharpe,
                x0,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints
            )
            
            if result.success:
                return {asset: float(weight) for asset, weight in zip(assets, result.x)}
            else:
                logger.warning(f"Sharpe optimization failed: {result.message}, using equal weights")
                return {asset: 1.0/len(assets) for asset in assets}
                
        except ImportError:
            logger.warning("scipy not available, using equal weights")
            return {asset: 1.0/len(assets) for asset in assets}
        except Exception as e:
            logger.error(f"Error in Sharpe ratio optimization: {e}")
            return {asset: 1.0/len(assets) for asset in assets}
    
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
        result = {asset: 0.0 for asset in data.columns}
        result.update(weights.to_dict())
        
        return result
    
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
        weights,
        constraints: dict = None
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
        
        # Apply max weight constraint
        weights_series = weights_series.clip(upper=max_weight)

        # Filter by minimum weight
        weights_series = weights_series[weights_series >= min_weight]

        # Limit number of positions
        if len(weights_series) > max_positions:
            weights_series = weights_series.nlargest(max_positions)

        # Renormalize
        if weights_series.sum() > 0:
            weights_series = weights_series / weights_series.sum()

        # Return in the same format as input
        if return_dict:
            return weights_series.to_dict()
        return weights_series
    
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
        inv_vols = {asset: 1.0/vol for asset, vol in volatilities.items()}
        total = sum(inv_vols.values())
        
        if total == 0:
            return {asset: 1.0/len(volatilities) for asset in volatilities}
        
        return {asset: iv/total for asset, iv in inv_vols.items()}
    
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