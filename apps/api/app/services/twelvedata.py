"""
TwelveData API service with rate limiting, caching, and batch operations.
"""

import logging
from datetime import date
from typing import Any

import pandas as pd

from ..core.config import settings
from .market_data.data_transformer import MarketDataTransformer
from .market_data.market_cache import MarketDataCache

# Import modular components
from .market_data.rate_limiter import BatchRateLimiter, RateLimiter
from .market_data.twelvedata_client import TwelveDataClient

logger = logging.getLogger(__name__)


class TwelveDataService:
    """Enhanced TwelveData service with caching and rate limiting."""

    def __init__(self):
        """Initialize TwelveData service with all components."""
        # Initialize components
        self.client = TwelveDataClient()
        self.rate_limiter = RateLimiter(
            credits_per_minute=settings.TWELVEDATA_RATE_LIMIT,
            redis_key_prefix="twelvedata:rate_limit"
        )
        self.batch_limiter = BatchRateLimiter(
            credits_per_minute=settings.TWELVEDATA_RATE_LIMIT,
            redis_key_prefix="twelvedata:batch_limit"
        )
        self.cache = MarketDataCache(
            cache_enabled=settings.ENABLE_MARKET_DATA_CACHE
        )
        self.transformer = MarketDataTransformer()

    def get_stock_prices(
        self,
        symbol: str,
        start_date: date | None = None,
        end_date: date | None = None,
        interval: str = "1day"
    ) -> list[dict[str, Any]]:
        """
        Get historical stock prices with caching and rate limiting.

        Args:
            symbol: Stock symbol
            start_date: Start date for data
            end_date: End date for data
            interval: Time interval

        Returns:
            List of price records
        """
        # Check cache first
        cached_data = self.cache.get(
            'price',
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            interval=interval
        )

        if cached_data is not None:
            return cached_data

        # Apply rate limiting
        self.rate_limiter.wait_if_needed()

        try:
            # Fetch from API
            df = self.client.get_time_series(
                symbol=symbol,
                interval=interval,
                start_date=start_date,
                end_date=end_date
            )

            if df.empty:
                logger.warning(f"No price data for {symbol}")
                return []

            # Transform data
            records = self.transformer.transform_time_series(df, symbol)

            # Cache the results
            self.cache.set(
                records,
                'price',
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                interval=interval
            )

            return records

        except Exception as e:
            logger.error(f"Failed to get prices for {symbol}: {e}")
            return []

    def get_batch_prices(
        self,
        symbols: list[str],
        start_date: date | None = None,
        end_date: date | None = None
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Get prices for multiple symbols efficiently.

        Args:
            symbols: List of stock symbols
            start_date: Start date for data
            end_date: End date for data

        Returns:
            Dictionary mapping symbols to price records
        """
        results = {}

        # Apply batch rate limiting
        self.batch_limiter.wait_for_batch(len(symbols))

        for symbol in symbols:
            try:
                prices = self.get_stock_prices(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date
                )
                results[symbol] = prices
            except Exception as e:
                logger.error(f"Failed to get prices for {symbol}: {e}")
                results[symbol] = []

        return results

    def get_real_time_quote(
        self,
        symbols: list[str]
    ) -> dict[str, dict[str, Any]]:
        """
        Get real-time quotes for symbols.

        Args:
            symbols: List of stock symbols

        Returns:
            Dictionary with quote data
        """
        # Check cache for each symbol
        cached_quotes = {}
        uncached_symbols = []

        for symbol in symbols:
            cached = self.cache.get('quote', symbol=symbol)
            if cached:
                cached_quotes[symbol] = cached
            else:
                uncached_symbols.append(symbol)

        if not uncached_symbols:
            return cached_quotes

        # Apply rate limiting
        self.rate_limiter.wait_if_needed()

        try:
            # Fetch uncached quotes
            raw_quotes = self.client.get_quote(uncached_symbols)

            # Transform and cache each quote
            for symbol, quote_data in raw_quotes.items():
                transformed = self.transformer.transform_quote(quote_data)
                cached_quotes[symbol] = transformed

                # Cache with short TTL
                self.cache.set(
                    transformed,
                    'quote',
                    ttl=60,  # 1 minute cache
                    symbol=symbol
                )

            return cached_quotes

        except Exception as e:
            logger.error(f"Failed to get quotes: {e}")
            return cached_quotes

    def get_forex_rate(
        self,
        from_currency: str,
        to_currency: str
    ) -> float | None:
        """
        Get exchange rate between currencies.

        Args:
            from_currency: Source currency code
            to_currency: Target currency code

        Returns:
            Exchange rate or None if failed
        """
        # Check cache
        cached_rate = self.cache.get(
            'forex',
            from_currency=from_currency,
            to_currency=to_currency
        )

        if cached_rate is not None:
            return cached_rate

        # Apply rate limiting
        self.rate_limiter.wait_if_needed()

        try:
            rate = self.client.get_exchange_rate(from_currency, to_currency)

            # Cache the rate
            self.cache.set(
                rate,
                'forex',
                ttl=300,  # 5 minutes cache
                from_currency=from_currency,
                to_currency=to_currency
            )

            return rate

        except Exception as e:
            logger.error(f"Failed to get forex rate {from_currency}/{to_currency}: {e}")
            return None

    def get_fundamentals(
        self,
        symbol: str,
        module: str = 'overview'
    ) -> dict[str, Any]:
        """
        Get fundamental data for a symbol.

        Args:
            symbol: Stock symbol
            module: Type of fundamental data

        Returns:
            Fundamental data dictionary
        """
        # Check cache
        cached_data = self.cache.get(
            'fundamentals',
            symbol=symbol,
            module=module
        )

        if cached_data is not None:
            return cached_data

        # Apply rate limiting
        self.rate_limiter.wait_if_needed()

        try:
            raw_data = self.client.get_fundamentals(symbol, module)

            # Transform data
            transformed = self.transformer.transform_fundamentals(raw_data, module)

            # Cache with long TTL
            self.cache.set(
                transformed,
                'fundamentals',
                ttl=86400,  # 24 hours cache
                symbol=symbol,
                module=module
            )

            return transformed

        except Exception as e:
            logger.error(f"Failed to get fundamentals for {symbol}: {e}")
            return {}

    def get_technical_indicator(
        self,
        symbol: str,
        indicator: str,
        interval: str = "1day",
        **params
    ) -> pd.DataFrame:
        """
        Get technical indicator data.

        Args:
            symbol: Stock symbol
            indicator: Indicator name
            interval: Time interval
            **params: Additional indicator parameters

        Returns:
            DataFrame with indicator values
        """
        # Apply rate limiting
        self.rate_limiter.wait_if_needed()

        try:
            df = self.client.get_technical_indicators(
                symbol=symbol,
                indicator=indicator,
                interval=interval,
                **params
            )

            return df

        except Exception as e:
            logger.error(f"Failed to get {indicator} for {symbol}: {e}")
            return pd.DataFrame()

    def search_symbols(
        self,
        query: str,
        exchange: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Search for symbols.

        Args:
            query: Search query
            exchange: Filter by exchange

        Returns:
            List of matching symbols
        """
        # Apply rate limiting
        self.rate_limiter.wait_if_needed()

        try:
            results = self.client.search_symbols(
                query=query,
                exchange=exchange
            )

            return results

        except Exception as e:
            logger.error(f"Failed to search symbols: {e}")
            return []

    def invalidate_cache(self, pattern: str | None = None):
        """
        Invalidate cache entries.

        Args:
            pattern: Pattern to match for invalidation
        """
        if pattern:
            count = self.cache.invalidate_pattern(pattern)
            logger.info(f"Invalidated {count} cache entries")
        else:
            # Invalidate all market data cache
            count = self.cache.invalidate_pattern("market_data:*")
            logger.info(f"Invalidated all {count} market data cache entries")

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return self.cache.get_stats()

    def get_rate_limit_status(self) -> dict[str, Any]:
        """Get rate limit status."""
        return {
            'remaining_credits': self.rate_limiter.get_remaining_credits(),
            'credits_per_minute': self.rate_limiter.credits_per_minute
        }

    def get_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        """
        Get exchange rate between two currencies.
        Wrapper for get_forex_rate for backward compatibility.

        Args:
            from_currency: Source currency code
            to_currency: Target currency code

        Returns:
            Exchange rate
        """
        rate = self.get_forex_rate(from_currency, to_currency)
        if rate is None:
            raise ValueError(f"Failed to get exchange rate for {from_currency}/{to_currency}")
        return rate


# Create singleton instance
_service_instance = TwelveDataService()

# Export functions for backward compatibility
def get_exchange_rate(from_currency: str, to_currency: str) -> float:
    """Module-level function for backward compatibility."""
    return _service_instance.get_exchange_rate(from_currency, to_currency)
