"""
Data validation and cleaning utilities for strategy calculations.
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


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

    @staticmethod
    def validate_data_quality(df: pd.DataFrame, min_days: int = 30) -> bool:
        """
        Validate data quality for strategy calculations.

        Args:
            df: DataFrame with price data
            min_days: Minimum number of days required

        Returns:
            True if data passes quality checks
        """
        if df.empty:
            logger.warning("Empty DataFrame provided")
            return False

        if len(df) < min_days:
            logger.warning(f"Insufficient data: {len(df)} days < {min_days} required")
            return False

        if df.columns.empty:
            logger.warning("No assets in DataFrame")
            return False

        return True