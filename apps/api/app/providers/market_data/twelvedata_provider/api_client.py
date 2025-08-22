"""
Core TwelveData API client.
Handles low-level API communication and response processing.
"""

import logging
from typing import Any

import pandas as pd
from twelvedata import TDClient
from twelvedata.exceptions import TwelveDataError

from ....core.config import settings
from ...base import APIError, retry_with_backoff

logger = logging.getLogger(__name__)


class TwelveDataAPIClient:
    """
    Low-level TwelveData API client.
    Handles direct API communication.
    """

    def __init__(self, api_key: str | None = None):
        """
        Initialize API client.

        Args:
            api_key: TwelveData API key
        """
        self.api_key = api_key or settings.TWELVEDATA_API_KEY

        if not self.api_key:
            raise ValueError("TwelveData API key not configured")

        self.client = TDClient(apikey=self.api_key)

    @retry_with_backoff(max_retries=3)
    def get_time_series(
        self,
        symbols: list[str],
        start_date: str,
        end_date: str,
        interval: str = "1day",
        outputsize: int = 5000
    ) -> Any:
        """
        Fetch time series data from TwelveData.

        Args:
            symbols: List of symbols or single symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            interval: Data interval
            outputsize: Maximum number of data points

        Returns:
            Time series response
        """
        try:
            if len(symbols) == 1:
                # Single symbol request
                ts = self.client.time_series(
                    symbol=symbols[0],
                    interval=interval,
                    start_date=start_date,
                    end_date=end_date,
                    outputsize=outputsize,
                    timezone="America/New_York",
                    order="asc",
                    dp=4
                )
            else:
                # Batch request
                ts = self.client.time_series(
                    symbol=symbols,
                    interval=interval,
                    start_date=start_date,
                    end_date=end_date,
                    outputsize=outputsize,
                    timezone="America/New_York",
                    order="asc",
                    dp=4
                )

            return ts

        except TwelveDataError as e:
            logger.error(f"TwelveData API error: {e}")
            raise APIError(f"TwelveData API error: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error fetching time series: {e}")
            raise

    @retry_with_backoff(max_retries=3)
    def get_quote(self, symbols: list[str]) -> Any:
        """
        Get real-time quotes.

        Args:
            symbols: List of symbols

        Returns:
            Quote data
        """
        try:
            if len(symbols) == 1:
                return self.client.quote(symbol=symbols[0])
            else:
                return self.client.quote(symbol=symbols)

        except TwelveDataError as e:
            logger.error(f"Quote fetch error: {e}")
            raise APIError(f"Failed to fetch quotes: {e}") from e

    @retry_with_backoff(max_retries=3)
    def get_exchange_rate(
        self,
        from_currency: str,
        to_currency: str
    ) -> float | None:
        """
        Get forex exchange rate.

        Args:
            from_currency: Source currency
            to_currency: Target currency

        Returns:
            Exchange rate or None
        """
        try:
            result = self.client.exchange_rate(
                symbol=f"{from_currency}/{to_currency}"
            )

            if result:
                data = result.as_json()
                if data and "rate" in data:
                    return float(data["rate"])

        except Exception as e:
            logger.error(f"Exchange rate fetch error: {e}")

        return None

    @retry_with_backoff(max_retries=2)
    def get_technical_indicator(
        self,
        symbol: str,
        indicator: str,
        interval: str = "1day",
        **kwargs
    ) -> pd.DataFrame:
        """
        Get technical indicator data.

        Args:
            symbol: Stock symbol
            indicator: Indicator name (e.g., 'sma', 'rsi')
            interval: Data interval
            **kwargs: Additional indicator parameters

        Returns:
            DataFrame with indicator values
        """
        try:
            # Map common indicator names
            indicator_map = {
                'sma': 'sma',
                'ema': 'ema',
                'rsi': 'rsi',
                'macd': 'macd',
                'bollinger': 'bbands',
                'stochastic': 'stoch'
            }

            td_indicator = indicator_map.get(indicator.lower(), indicator.lower())

            # Get indicator function
            indicator_func = getattr(self.client, td_indicator, None)
            if not indicator_func:
                raise ValueError(f"Unknown indicator: {indicator}")

            # Call indicator
            result = indicator_func(
                symbol=symbol,
                interval=interval,
                **kwargs
            )

            return result.as_pandas() if result else pd.DataFrame()

        except Exception as e:
            logger.error(f"Technical indicator error: {e}")
            return pd.DataFrame()

    def get_api_usage(self) -> dict:
        """
        Get API usage statistics.

        Returns:
            API usage information
        """
        try:
            usage = self.client.api_usage()
            if usage:
                return usage.as_json()
        except Exception as e:
            logger.error(f"Failed to get API usage: {e}")

        return {}
