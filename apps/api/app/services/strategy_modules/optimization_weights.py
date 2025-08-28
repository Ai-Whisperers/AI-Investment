"""
Optimization-based weight calculation strategies.
Handles maximum Sharpe ratio and other advanced optimization techniques.
"""

import logging
from typing import Dict, List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class OptimizationWeightCalculator:
    """Calculate optimized portfolio weights."""

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
                return {
                    asset: float(weight) 
                    for asset, weight in zip(assets, result.x, strict=False)
                }
            else:
                logger.warning(
                    f"Sharpe optimization failed: {result.message}, using equal weights"
                )
                return {asset: 1.0/len(assets) for asset in assets}

        except ImportError:
            logger.warning("scipy not available, using equal weights")
            return {asset: 1.0/len(assets) for asset in assets}
        except Exception as e:
            logger.error(f"Error in Sharpe ratio optimization: {e}")
            return {asset: 1.0/len(assets) for asset in assets}

    @staticmethod
    def calculate_mean_variance_weights(
        returns: pd.DataFrame,
        lookback: int = 60,
        target_return: float = 0.10
    ) -> Dict[str, float]:
        """
        Calculate mean-variance optimized weights for target return.

        Args:
            returns: DataFrame of returns
            lookback: Lookback period
            target_return: Target annual return

        Returns:
            Dictionary of weights
        """
        if returns.empty or len(returns) < lookback:
            return {}

        try:
            from scipy.optimize import minimize

            # Prepare data
            asset_returns = returns.tail(lookback)
            mean_returns = asset_returns.mean().values * 252  # Annualized
            cov_matrix = asset_returns.cov().values * 252  # Annualized
            n_assets = len(returns.columns)
            assets = returns.columns.tolist()

            # Objective: minimize portfolio variance
            def portfolio_variance(weights):
                return weights @ cov_matrix @ weights

            # Constraints
            constraints = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                {'type': 'eq', 'fun': lambda x: np.sum(mean_returns * x) - target_return}
            ]

            # Bounds
            bounds = tuple((0, 1) for _ in range(n_assets))
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
                return {
                    asset: float(weight) 
                    for asset, weight in zip(assets, result.x, strict=False)
                }
            else:
                logger.warning("Mean-variance optimization failed, using equal weights")
                return {asset: 1.0/len(assets) for asset in assets}

        except ImportError:
            logger.warning("scipy not available, using equal weights")
            return dict.fromkeys(returns.columns, 1.0 / len(returns.columns))
        except Exception as e:
            logger.error(f"Error in mean-variance optimization: {e}")
            return dict.fromkeys(returns.columns, 1.0 / len(returns.columns))

    @staticmethod
    def calculate_kelly_weights(
        returns: pd.DataFrame,
        lookback: int = 60,
        kelly_fraction: float = 0.25
    ) -> Dict[str, float]:
        """
        Calculate Kelly criterion based weights.

        Args:
            returns: DataFrame of returns
            lookback: Lookback period
            kelly_fraction: Fraction of Kelly to use (for safety)

        Returns:
            Dictionary of weights
        """
        if returns.empty or len(returns) < lookback:
            return {}

        try:
            # Calculate mean returns and covariance
            asset_returns = returns.tail(lookback)
            mean_returns = asset_returns.mean()
            cov_matrix = asset_returns.cov()

            # Calculate inverse covariance
            inv_cov = np.linalg.inv(cov_matrix.values)

            # Kelly weights (simplified for multiple assets)
            raw_weights = inv_cov @ mean_returns.values

            # Apply Kelly fraction for safety
            kelly_weights = raw_weights * kelly_fraction

            # Normalize to sum to 1 and ensure non-negative
            kelly_weights = np.maximum(kelly_weights, 0)
            if kelly_weights.sum() > 0:
                kelly_weights = kelly_weights / kelly_weights.sum()
            else:
                kelly_weights = np.ones(len(returns.columns)) / len(returns.columns)

            return {
                asset: float(weight) 
                for asset, weight in zip(returns.columns, kelly_weights, strict=False)
            }

        except np.linalg.LinAlgError:
            logger.warning("Singular covariance matrix, using equal weights")
            return dict.fromkeys(returns.columns, 1.0 / len(returns.columns))
        except Exception as e:
            logger.error(f"Error in Kelly optimization: {e}")
            return dict.fromkeys(returns.columns, 1.0 / len(returns.columns))