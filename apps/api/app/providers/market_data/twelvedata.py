"""
TwelveData provider implementation.
Implements MarketDataProvider interface using modularized components.
"""

import logging
from datetime import date, datetime

import pandas as pd

from ...core.config import settings
from ..base import ProviderStatus
from .interface import ExchangeRate, MarketDataProvider, QuoteData
from .twelvedata_provider import (
    TwelveDataAPIClient,
    TwelveDataCacheManager,
    TwelveDataProcessor,
    TwelveDataRateLimiter,
)

logger = logging.getLogger(__name__)


class TwelveDataProvider(MarketDataProvider):
    """
    TwelveData API provider implementation.
    Orchestrates data fetching using modular components.
    """

    def __init__(self, api_key: str | None = None, cache_enabled: bool = True):
        """
        Initialize TwelveData provider.
        
        Args:
            api_key: TwelveData API key
            cache_enabled: Whether to enable caching
        """
        super().__init__(api_key or settings.TWELVEDATA_API_KEY, cache_enabled)

        # Initialize components
        self.client = TwelveDataAPIClient(self.api_key)
        self.rate_limiter = TwelveDataRateLimiter()
        self.cache_manager = TwelveDataCacheManager(cache_enabled)
        self.processor = TwelveDataProcessor()

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "TwelveData"

    def validate_config(self) -> bool:
        """Validate API key and configuration."""
        return bool(self.api_key)

    def health_check(self) -> ProviderStatus:
        """Check TwelveData API health."""
        try:
            self.rate_limiter.wait_if_needed(1)
            usage = self.client.get_api_usage()

            if usage:
                return ProviderStatus.HEALTHY
            else:
                return ProviderStatus.DEGRADED
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return ProviderStatus.UNHEALTHY

    def fetch_historical_prices(
        self,
        symbols: list[str],
        start_date: date,
        end_date: date | None = None,
        interval: str = "1day"
    ) -> pd.DataFrame:
        """
        Fetch historical prices with caching and batching.
        
        Args:
            symbols: List of stock symbols
            start_date: Start date for historical data
            end_date: End date (defaults to today)
            interval: Data interval
            
        Returns:
            DataFrame with price data
        """
        if not symbols:
            return pd.DataFrame()

        end_date = end_date or date.today()
        all_data = {}

        # Process in batches
        batch_size = min(8, settings.TWELVEDATA_RATE_LIMIT)

        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]

            # Check cache for each symbol
            uncached_symbols = []
            for symbol in batch:
                cached_df = self.cache_manager.get_price_data(
                    symbol,
                    start_date.isoformat(),
                    end_date.isoformat(),
                    interval
                )

                if cached_df is not None:
                    all_data[symbol] = cached_df
                else:
                    uncached_symbols.append(symbol)

            if not uncached_symbols:
                continue

            # Rate limit
            self.rate_limiter.wait_if_needed(len(uncached_symbols))

            # Fetch from API
            logger.info(f"Fetching prices for {','.join(uncached_symbols)}")

            ts = self.client.get_time_series(
                uncached_symbols,
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
                interval
            )

            # Process response
            if len(uncached_symbols) == 1:
                # Single symbol
                df = ts.as_pandas()
                if df is not None and not df.empty:
                    df = self.processor.process_price_data(df, uncached_symbols[0])
                    if not df.empty:
                        all_data[uncached_symbols[0]] = df
                        # Cache it
                        self.cache_manager.set_price_data(
                            uncached_symbols[0],
                            start_date.isoformat(),
                            end_date.isoformat(),
                            interval,
                            df
                        )
            else:
                # Batch response
                batch_data = ts.as_json()
                if batch_data:
                    processed = self.processor.process_batch_response(
                        batch_data,
                        uncached_symbols
                    )

                    for symbol, df in processed.items():
                        all_data[symbol] = df
                        # Cache it
                        self.cache_manager.set_price_data(
                            symbol,
                            start_date.isoformat(),
                            end_date.isoformat(),
                            interval,
                            df
                        )

        if not all_data:
            return pd.DataFrame()

        # Combine all data
        return self.processor.combine_dataframes(all_data)

    def get_quote(self, symbols: list[str]) -> list[QuoteData]:
        """
        Get real-time quotes for symbols.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            List of quote data
        """
        quotes = []

        # Check cache first
        uncached_symbols = []
        for symbol in symbols:
            cached_quote = self.cache_manager.get_quote(symbol)
            if cached_quote:
                quotes.append(QuoteData(**cached_quote))
            else:
                uncached_symbols.append(symbol)

        if not uncached_symbols:
            return quotes

        # Rate limit
        self.rate_limiter.wait_if_needed(len(uncached_symbols))

        # Fetch from API
        quote_response = self.client.get_quote(uncached_symbols)

        if quote_response:
            if len(uncached_symbols) == 1:
                # Single quote
                processed = self.processor.process_quote_response(quote_response)
                if processed:
                    quotes.append(QuoteData(**processed))
                    self.cache_manager.set_quote(uncached_symbols[0], processed)
            else:
                # Multiple quotes
                quote_data = quote_response.as_json()
                if quote_data:
                    for symbol in uncached_symbols:
                        if symbol in quote_data:
                            processed = self.processor.process_quote_response(
                                quote_data[symbol]
                            )
                            if processed:
                                quotes.append(QuoteData(**processed))
                                self.cache_manager.set_quote(symbol, processed)

        return quotes

    def get_exchange_rate(
        self,
        from_currency: str,
        to_currency: str
    ) -> ExchangeRate | None:
        """
        Get forex exchange rate.
        
        Args:
            from_currency: Source currency
            to_currency: Target currency
            
        Returns:
            Exchange rate data or None
        """
        # Check cache
        cached_rate = self.cache_manager.get_forex_rate(from_currency, to_currency)
        if cached_rate:
            return ExchangeRate(
                from_currency=from_currency,
                to_currency=to_currency,
                rate=cached_rate,
                timestamp=datetime.now()
            )

        # Rate limit
        self.rate_limiter.wait_if_needed(1)

        # Fetch from API
        rate = self.client.get_exchange_rate(from_currency, to_currency)

        if rate:
            # Cache it
            self.cache_manager.set_forex_rate(from_currency, to_currency, rate)

            return ExchangeRate(
                from_currency=from_currency,
                to_currency=to_currency,
                rate=rate,
                timestamp=datetime.now()
            )

        return None

    def get_technical_indicators(
        self,
        symbol: str,
        indicators: list[str],
        interval: str = "1day",
        **kwargs
    ) -> pd.DataFrame:
        """
        Get technical indicators for a symbol.
        
        Args:
            symbol: Stock symbol
            indicators: List of indicator names
            interval: Data interval
            **kwargs: Additional indicator parameters
            
        Returns:
            DataFrame with indicator values
        """
        results = {}

        for indicator in indicators:
            # Rate limit
            self.rate_limiter.wait_if_needed(1)

            # Fetch indicator
            df = self.client.get_technical_indicator(
                symbol,
                indicator,
                interval,
                **kwargs
            )

            if not df.empty:
                results[indicator] = df

        if results:
            return pd.concat(results, axis=1)

        return pd.DataFrame()

    def get_api_usage(self) -> dict:
        """
        Get API usage statistics.
        
        Returns:
            API usage information including rate limits
        """
        usage = self.client.get_api_usage()

        # Add rate limiter info
        usage["rate_limit"] = {
            "credits_per_minute": self.rate_limiter.credits_per_minute,
            "credits_available": self.rate_limiter.get_available_credits()
        }

        return usage


# Legacy export for backward compatibility
TwelveDataRateLimiter = TwelveDataRateLimiter
