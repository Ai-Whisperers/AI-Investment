"""
Data transformation module for market data.
"""

import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class MarketDataTransformer:
    """Transforms market data between different formats."""

    @staticmethod
    def transform_time_series(
        df: pd.DataFrame,
        symbol: str,
        include_volume: bool = True
    ) -> list[dict[str, Any]]:
        """
        Transform time series DataFrame to list of price records.

        Args:
            df: DataFrame with OHLCV data
            symbol: Stock symbol
            include_volume: Whether to include volume data

        Returns:
            List of price dictionaries
        """
        if df.empty:
            return []

        records = []

        for timestamp, row in df.iterrows():
            record = {
                'symbol': symbol,
                'date': timestamp.date() if hasattr(timestamp, 'date') else timestamp,
                'open': float(row.get('open', 0)),
                'high': float(row.get('high', 0)),
                'low': float(row.get('low', 0)),
                'close': float(row.get('close', 0))
            }

            if include_volume and 'volume' in row:
                record['volume'] = int(row.get('volume', 0))

            records.append(record)

        return records

    @staticmethod
    def transform_quote(
        quote_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Transform quote data to standardized format.

        Args:
            quote_data: Raw quote data from API

        Returns:
            Standardized quote dictionary
        """
        return {
            'symbol': quote_data.get('symbol'),
            'name': quote_data.get('name'),
            'exchange': quote_data.get('exchange'),
            'currency': quote_data.get('currency'),
            'price': float(quote_data.get('close', 0)),
            'change': float(quote_data.get('change', 0)),
            'percent_change': float(quote_data.get('percent_change', 0)),
            'volume': int(quote_data.get('volume', 0)),
            'open': float(quote_data.get('open', 0)),
            'high': float(quote_data.get('high', 0)),
            'low': float(quote_data.get('low', 0)),
            'previous_close': float(quote_data.get('previous_close', 0)),
            'timestamp': quote_data.get('datetime')
        }

    @staticmethod
    def transform_fundamentals(
        fundamental_data: dict[str, Any],
        data_type: str
    ) -> dict[str, Any]:
        """
        Transform fundamental data to standardized format.

        Args:
            fundamental_data: Raw fundamental data
            data_type: Type of fundamental data

        Returns:
            Standardized fundamental dictionary
        """
        if data_type == 'overview':
            return {
                'market_cap': fundamental_data.get('market_capitalization'),
                'pe_ratio': fundamental_data.get('pe_ratio'),
                'dividend_yield': fundamental_data.get('dividend_yield'),
                'eps': fundamental_data.get('earnings_per_share'),
                'beta': fundamental_data.get('beta'),
                '52_week_high': fundamental_data.get('fifty_two_week_high'),
                '52_week_low': fundamental_data.get('fifty_two_week_low'),
                'shares_outstanding': fundamental_data.get('shares_outstanding')
            }

        elif data_type == 'dividends':
            dividends = []
            for div in fundamental_data.get('dividends', []):
                dividends.append({
                    'ex_date': div.get('ex_date'),
                    'payment_date': div.get('payment_date'),
                    'amount': float(div.get('amount', 0))
                })
            return {'dividends': dividends}

        else:
            # Return raw data for other types
            return fundamental_data

    @staticmethod
    def calculate_returns(
        prices: pd.Series,
        period: int = 1
    ) -> pd.Series:
        """
        Calculate returns from price series.

        Args:
            prices: Series of prices
            period: Period for return calculation

        Returns:
            Series of returns
        """
        if len(prices) < period + 1:
            return pd.Series()

        return prices.pct_change(period)

    @staticmethod
    def calculate_volatility(
        returns: pd.Series,
        window: int = 20,
        annualize: bool = True
    ) -> pd.Series:
        """
        Calculate rolling volatility.

        Args:
            returns: Series of returns
            window: Rolling window size
            annualize: Whether to annualize volatility

        Returns:
            Series of volatility values
        """
        volatility = returns.rolling(window=window).std()

        if annualize:
            # Assume 252 trading days per year
            volatility = volatility * np.sqrt(252)

        return volatility

    @staticmethod
    def normalize_prices(
        df: pd.DataFrame,
        base_value: float = 100.0
    ) -> pd.DataFrame:
        """
        Normalize prices to a base value.

        Args:
            df: DataFrame with price data
            base_value: Base value for normalization

        Returns:
            DataFrame with normalized prices
        """
        if df.empty:
            return df

        normalized = df.copy()

        # Get first valid value for each column
        first_values = normalized.iloc[0]

        # Normalize each column
        for col in normalized.columns:
            if first_values[col] != 0:
                normalized[col] = (normalized[col] / first_values[col]) * base_value

        return normalized

    @staticmethod
    def aggregate_ohlcv(
        df: pd.DataFrame,
        target_interval: str
    ) -> pd.DataFrame:
        """
        Aggregate OHLCV data to a different interval.

        Args:
            df: DataFrame with OHLCV data
            target_interval: Target interval (e.g., '1W', '1M')

        Returns:
            Aggregated DataFrame
        """
        if df.empty:
            return df

        # Define aggregation rules
        agg_rules = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }

        # Resample based on target interval
        resampled = df.resample(target_interval).agg(agg_rules)

        # Remove rows with all NaN values
        resampled = resampled.dropna(how='all')

        return resampled

    @staticmethod
    def fill_missing_data(
        df: pd.DataFrame,
        method: str = 'ffill',
        limit: int = 5
    ) -> pd.DataFrame:
        """
        Fill missing data in DataFrame.

        Args:
            df: DataFrame with potential missing data
            method: Fill method ('ffill', 'bfill', 'interpolate')
            limit: Maximum number of consecutive NaNs to fill

        Returns:
            DataFrame with filled data
        """
        if df.empty:
            return df

        filled = df.copy()

        if method == 'interpolate':
            filled = filled.interpolate(method='linear', limit=limit)
        else:
            filled = filled.fillna(method=method, limit=limit)

        return filled

    @staticmethod
    def detect_outliers(
        df: pd.DataFrame,
        n_std: float = 3.0
    ) -> pd.DataFrame:
        """
        Detect outliers in price data.

        Args:
            df: DataFrame with price data
            n_std: Number of standard deviations for outlier threshold

        Returns:
            DataFrame with outlier flags
        """
        if df.empty:
            return pd.DataFrame()

        outliers = pd.DataFrame(index=df.index)

        for col in df.columns:
            if col == 'volume':
                continue  # Skip volume column

            # Calculate returns
            returns = df[col].pct_change()

            # Calculate z-scores
            z_scores = np.abs((returns - returns.mean()) / returns.std())

            # Flag outliers
            outliers[f'{col}_outlier'] = z_scores > n_std

        return outliers
