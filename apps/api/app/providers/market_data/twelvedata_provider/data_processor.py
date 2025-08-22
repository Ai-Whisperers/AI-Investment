"""
Data processing utilities for TwelveData responses.
Handles data transformation, validation, and normalization.
"""

import logging
from datetime import datetime
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class TwelveDataProcessor:
    """
    Processes and transforms TwelveData API responses.
    """

    @staticmethod
    def process_price_data(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        Process raw price data from TwelveData.

        Args:
            df: Raw price DataFrame
            symbol: Stock symbol for logging

        Returns:
            Processed DataFrame
        """
        if df.empty:
            return df

        try:
            # Ensure numeric columns
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # Remove any rows with all NaN prices
            price_cols = ['open', 'high', 'low', 'close']
            existing_price_cols = [col for col in price_cols if col in df.columns]
            if existing_price_cols:
                df = df.dropna(subset=existing_price_cols, how='all')

            # Sort by date
            df = df.sort_index()

            # Add symbol column if not present
            if 'symbol' not in df.columns:
                df['symbol'] = symbol

            logger.debug(f"Processed {len(df)} rows for {symbol}")
            return df

        except Exception as e:
            logger.error(f"Error processing price data for {symbol}: {e}")
            return pd.DataFrame()

    @staticmethod
    def process_batch_response(
        batch_data: dict,
        symbols: list[str]
    ) -> dict[str, pd.DataFrame]:
        """
        Process batch time series response.

        Args:
            batch_data: Raw batch response from TwelveData
            symbols: List of requested symbols

        Returns:
            Dictionary of symbol -> DataFrame
        """
        processed_data = {}

        for symbol in symbols:
            if symbol not in batch_data:
                logger.warning(f"Symbol {symbol} not in batch response")
                continue

            symbol_data = batch_data[symbol]

            # Handle different response formats
            if isinstance(symbol_data, dict) and "values" in symbol_data:
                # Standard format with "values" key
                df = pd.DataFrame(symbol_data["values"])
            elif isinstance(symbol_data, list | tuple):
                # Batch format returns tuple/list of dicts
                df = pd.DataFrame(symbol_data)
            else:
                logger.warning(f"Unexpected data format for {symbol}")
                continue

            # Process datetime index
            if "datetime" in df.columns:
                df["datetime"] = pd.to_datetime(df["datetime"])
                df.set_index("datetime", inplace=True)

            # Process the data
            df = TwelveDataProcessor.process_price_data(df, symbol)

            if not df.empty:
                processed_data[symbol] = df

        return processed_data

    @staticmethod
    def process_quote_response(quote_data: Any) -> dict | None:
        """
        Process quote response from TwelveData.

        Args:
            quote_data: Raw quote response

        Returns:
            Processed quote dictionary
        """
        try:
            if hasattr(quote_data, 'as_json'):
                data = quote_data.as_json()
            else:
                data = quote_data

            if not data:
                return None

            # Ensure numeric fields
            numeric_fields = [
                'open', 'high', 'low', 'close', 'volume',
                'previous_close', 'change', 'percent_change',
                'average_volume', 'fifty_two_week_low',
                'fifty_two_week_high'
            ]

            for field in numeric_fields:
                if field in data:
                    try:
                        data[field] = float(data[field])
                    except (ValueError, TypeError):
                        pass

            # Add timestamp if not present
            if 'timestamp' not in data:
                data['timestamp'] = datetime.now().isoformat()

            return data

        except Exception as e:
            logger.error(f"Error processing quote response: {e}")
            return None

    @staticmethod
    def combine_dataframes(
        dataframes: dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Combine multiple symbol DataFrames into a single multi-index DataFrame.

        Args:
            dataframes: Dictionary of symbol -> DataFrame

        Returns:
            Combined multi-index DataFrame
        """
        if not dataframes:
            return pd.DataFrame()

        try:
            # Create multi-index columns
            combined = pd.concat(
                dataframes.values(),
                axis=1,
                keys=dataframes.keys(),
                names=['symbol', 'field']
            )

            return combined

        except Exception as e:
            logger.error(f"Error combining dataframes: {e}")
            return pd.DataFrame()

    @staticmethod
    def validate_data_quality(
        df: pd.DataFrame,
        min_rows: int = 10,
        max_null_pct: float = 0.1
    ) -> bool:
        """
        Validate data quality.

        Args:
            df: DataFrame to validate
            min_rows: Minimum required rows
            max_null_pct: Maximum allowed null percentage

        Returns:
            True if data passes quality checks
        """
        if df.empty or len(df) < min_rows:
            return False

        # Check null percentage for price columns
        price_cols = ['open', 'high', 'low', 'close']
        for col in price_cols:
            if col in df.columns:
                null_pct = df[col].isna().sum() / len(df)
                if null_pct > max_null_pct:
                    logger.warning(f"Column {col} has {null_pct:.1%} nulls")
                    return False

        return True
