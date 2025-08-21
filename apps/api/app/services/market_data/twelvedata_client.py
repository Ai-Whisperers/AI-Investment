"""
TwelveData API client module.
"""

import logging
from datetime import date
from typing import Any

import pandas as pd
from twelvedata import TDClient
from twelvedata.exceptions import TwelveDataError

from ...core.config import settings

logger = logging.getLogger(__name__)


class TwelveDataClient:
    """Pure API client for TwelveData service."""

    def __init__(self, api_key: str | None = None):
        """
        Initialize TwelveData client.

        Args:
            api_key: TwelveData API key (uses settings if not provided)
        """
        self.api_key = api_key or getattr(settings, "TWELVEDATA_API_KEY", None)
        if not self.api_key:
            raise ValueError("TWELVEDATA_API_KEY not configured")

        self.client = TDClient(apikey=self.api_key)
        self.base_params = {
            'timezone': 'America/New_York',
            'outputsize': 5000  # Maximum for free tier
        }

    def get_time_series(
        self,
        symbol: str,
        interval: str = "1day",
        start_date: date | None = None,
        end_date: date | None = None,
        outputsize: int | None = None
    ) -> pd.DataFrame:
        """
        Get time series data for a symbol.

        Args:
            symbol: Stock symbol
            interval: Time interval (1min, 5min, 15min, 30min, 45min, 1h, 2h, 4h, 1day, 1week, 1month)
            start_date: Start date for data
            end_date: End date for data
            outputsize: Number of data points to return

        Returns:
            DataFrame with time series data
        """
        try:
            params = self.base_params.copy()
            params['interval'] = interval

            if start_date:
                params['start_date'] = start_date.isoformat()
            if end_date:
                params['end_date'] = end_date.isoformat()
            if outputsize:
                params['outputsize'] = outputsize

            ts = self.client.time_series(
                symbol=symbol,
                **params
            )

            df = ts.as_pandas()

            if df.empty:
                logger.warning(f"No data returned for {symbol}")
                return pd.DataFrame()

            return df

        except TwelveDataError as e:
            logger.error(f"TwelveData API error for {symbol}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to fetch time series for {symbol}: {e}")
            raise

    def get_quote(self, symbols: list[str]) -> dict[str, Any]:
        """
        Get real-time quotes for symbols.

        Args:
            symbols: List of stock symbols

        Returns:
            Dictionary with quote data
        """
        try:
            quote = self.client.quote(
                symbol=','.join(symbols),
                timezone=self.base_params['timezone']
            )

            result = quote.as_json()

            # Handle single symbol vs multiple
            if len(symbols) == 1:
                return {symbols[0]: result}

            return result

        except TwelveDataError as e:
            logger.error(f"TwelveData API error for quotes: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to fetch quotes: {e}")
            raise

    def get_exchange_rate(
        self,
        from_currency: str,
        to_currency: str
    ) -> float:
        """
        Get exchange rate between two currencies.

        Args:
            from_currency: Source currency code
            to_currency: Target currency code

        Returns:
            Exchange rate
        """
        try:
            result = self.client.exchange_rate(
                symbol=f"{from_currency}/{to_currency}"
            ).as_json()

            return float(result.get('rate', 0))

        except TwelveDataError as e:
            logger.error(f"TwelveData API error for exchange rate: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to fetch exchange rate: {e}")
            raise

    def get_fundamentals(
        self,
        symbol: str,
        module: str = 'overview'
    ) -> dict[str, Any]:
        """
        Get fundamental data for a symbol.

        Args:
            symbol: Stock symbol
            module: Type of fundamental data (overview, dividends, earnings, etc.)

        Returns:
            Dictionary with fundamental data
        """
        try:
            # Map module names to TwelveData API methods
            module_map = {
                'overview': 'statistics',
                'dividends': 'dividends',
                'earnings': 'earnings',
                'balance_sheet': 'balance_sheet',
                'income_statement': 'income_statement',
                'cash_flow': 'cash_flow'
            }

            method_name = module_map.get(module, 'statistics')
            method = getattr(self.client, method_name)

            result = method(symbol=symbol).as_json()

            return result

        except TwelveDataError as e:
            logger.error(f"TwelveData API error for fundamentals: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to fetch fundamentals for {symbol}: {e}")
            raise

    def get_technical_indicators(
        self,
        symbol: str,
        indicator: str,
        interval: str = "1day",
        **indicator_params
    ) -> pd.DataFrame:
        """
        Get technical indicator data.

        Args:
            symbol: Stock symbol
            indicator: Indicator name (sma, ema, rsi, macd, etc.)
            interval: Time interval
            **indicator_params: Additional parameters for the indicator

        Returns:
            DataFrame with indicator data
        """
        try:
            params = self.base_params.copy()
            params['interval'] = interval
            params.update(indicator_params)

            # Get the indicator method
            indicator_method = getattr(self.client, indicator.lower(), None)
            if not indicator_method:
                raise ValueError(f"Unknown indicator: {indicator}")

            result = indicator_method(
                symbol=symbol,
                **params
            )

            df = result.as_pandas()

            if df.empty:
                logger.warning(f"No indicator data returned for {symbol}")
                return pd.DataFrame()

            return df

        except TwelveDataError as e:
            logger.error(f"TwelveData API error for indicator: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to fetch indicator for {symbol}: {e}")
            raise

    def search_symbols(
        self,
        query: str,
        exchange: str | None = None,
        instrument_type: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Search for symbols.

        Args:
            query: Search query
            exchange: Filter by exchange
            instrument_type: Filter by instrument type

        Returns:
            List of matching symbols
        """
        try:
            params = {'symbol': query}

            if exchange:
                params['exchange'] = exchange
            if instrument_type:
                params['type'] = instrument_type

            result = self.client.symbol_search(**params).as_json()

            return result.get('data', [])

        except TwelveDataError as e:
            logger.error(f"TwelveData API error for symbol search: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to search symbols: {e}")
            raise
