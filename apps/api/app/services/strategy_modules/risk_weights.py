"""
Risk-based weight calculation strategies.
Handles risk parity, minimum variance, and volatility-based weighting.
"""

import logging
from typing import Dict, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class RiskWeightCalculator:
    """Calculate risk-based portfolio weights."""

    @staticmethod
    def risk_parity_weights(
        returns: pd.DataFrame, 
        lookback: int = 60
    ) -> pd.Series:
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
    def minimum_variance_weights(
        returns: pd.DataFrame, 
        lookback: int = 60
    ) -> pd.Series:
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
            return pd.Series(1.0 / len(returns.columns), index=returns.columns)

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
                return {
                    asset: float(weight) 
                    for asset, weight in zip(assets, result.x, strict=False)
                }
            else:
                logger.warning(
                    f"Optimization failed: {result.message}, using equal weights"
                )
                return {asset: 1.0/len(assets) for asset in assets}

        except ImportError:
            logger.warning("scipy not available, using risk parity as proxy")
            return RiskWeightCalculator.calculate_risk_parity_weights(data, lookback)
        except Exception as e:
            logger.error(f"Error in minimum variance optimization: {e}")
            return dict.fromkeys(data.columns, 1.0 / len(data.columns))

    @staticmethod
    def calculate_max_diversification_weights(
        returns: pd.DataFrame,
        lookback: int = 60
    ) -> Dict[str, float]:
        """
        Calculate maximum diversification portfolio weights.

        Args:
            returns: DataFrame of returns
            lookback: Lookback period

        Returns:
            Dictionary of weights
        """
        if returns.empty or len(returns) < lookback:
            return {}

        try:
            from scipy.optimize import minimize

            # Calculate covariance matrix and volatilities
            asset_returns = returns.tail(lookback)
            cov_matrix = asset_returns.cov().values
            volatilities = asset_returns.std().values
            n_assets = len(returns.columns)
            assets = returns.columns.tolist()

            # Objective: maximize diversification ratio (negative for minimization)
            def negative_div_ratio(weights):
                portfolio_vol = np.sqrt(weights @ cov_matrix @ weights)
                weighted_avg_vol = weights @ volatilities
                if portfolio_vol == 0:
                    return 0
                return -weighted_avg_vol / portfolio_vol

            # Constraints and bounds
            constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
            bounds = tuple((0, 1) for _ in range(n_assets))
            x0 = np.array([1.0/n_assets] * n_assets)

            # Optimize
            result = minimize(
                negative_div_ratio,
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
                logger.warning("Max diversification optimization failed")
                return {asset: 1.0/len(assets) for asset in assets}

        except ImportError:
            logger.warning("scipy not available, using risk parity")
            return RiskWeightCalculator.calculate_risk_parity_weights(returns, lookback)
        except Exception as e:
            logger.error(f"Error in max diversification optimization: {e}")
            return dict.fromkeys(returns.columns, 1.0 / len(returns.columns))