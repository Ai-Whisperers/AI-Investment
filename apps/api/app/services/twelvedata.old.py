"""
TwelveData API service with rate limiting, caching, and batch operations.
Implements best practices from the official TwelveData Python library.
"""

import time
import pandas as pd
from datetime import date
from typing import Optional, Dict, List, Any
import logging
import json
from twelvedata import TDClient
from twelvedata.exceptions import TwelveDataError

from ..core.config import settings
from ..core.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for TwelveData API calls."""

    def __init__(self, credits_per_minute: int = 8):
        self.credits_per_minute = credits_per_minute
        self.credits_used = []
        self.redis_client = get_redis_client()
        self.redis_key = "twelvedata:rate_limit"

    def wait_if_needed(self, credits_required: int = 1):
        """Wait if rate limit would be exceeded."""
        now = time.time()

        # Try to use Redis for distributed rate limiting
        if self.redis_client.is_connected:
            try:
                # Get credit usage from Redis
                usage_data = self.redis_client.get(self.redis_key)
                if usage_data:
                    self.credits_used = json.loads(usage_data)
            except Exception as e:
                logger.warning(f"Failed to get rate limit from Redis: {e}")

        # Remove credits older than 1 minute
        self.credits_used = [t for t in self.credits_used if now - t < 60]

        # Check if we need to wait
        if len(self.credits_used) + credits_required > self.credits_per_minute:
            # Calculate wait time
            oldest_credit = min(self.credits_used)
            wait_time = 60 - (now - oldest_credit) + 1
            logger.info(f"Rate limit reached. Waiting {wait_time:.1f} seconds...")
            time.sleep(wait_time)

            # Clean up old credits again
            now = time.time()
            self.credits_used = [t for t in self.credits_used if now - t < 60]

        # Record new credit usage
        for _ in range(credits_required):
            self.credits_used.append(now)

        # Update Redis
        if self.redis_client.is_connected:
            try:
                self.redis_client.set(
                    self.redis_key,
                    json.dumps(self.credits_used),
                    expire=120,  # Expire after 2 minutes
                )
            except Exception as e:
                logger.warning(f"Failed to update rate limit in Redis: {e}")


class TwelveDataService:
    """Enhanced TwelveData service with caching and rate limiting."""

    def __init__(self):
        self.api_key = getattr(settings, "TWELVEDATA_API_KEY", None)
        if not self.api_key:
            raise ValueError("TWELVEDATA_API_KEY not configured in settings")

        self.client = TDClient(apikey=self.api_key)
        self.rate_limiter = RateLimiter(settings.TWELVEDATA_RATE_LIMIT)
        self.redis_client = get_redis_client()
        self.cache_enabled = settings.ENABLE_MARKET_DATA_CACHE

        # Cache TTL settings
        self.price_cache_ttl = 3600  # 1 hour for historical prices
        self.quote_cache_ttl = 60  # 1 minute for real-time quotes
        self.forex_cache_ttl = 300  # 5 minutes for forex rates

    def _get_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate cache key from parameters."""
        key_parts = [prefix]
        for k, v in sorted(kwargs.items()):
            if v is not None:
                key_parts.append(f"{k}:{v}")
        return ":".join(key_parts)

    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get data from cache if available."""
        if not self.cache_enabled or not self.redis_client.is_connected:
            return None

        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit: {cache_key}")
                return (
                    json.loads(cached_data)
                    if isinstance(cached_data, str)
                    else cached_data
                )
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")

        return None

    def _set_cache(self, cache_key: str, data: Any, ttl: int):
        """Store data in cache."""
        if not self.cache_enabled or not self.redis_client.is_connected:
            return

        try:
            json_data = json.dumps(data) if not isinstance(data, str) else data
            self.redis_client.set(cache_key, json_data, expire=ttl)
            logger.debug(f"Cached: {cache_key}, TTL: {ttl}s")
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")

    def fetch_prices(
        self, symbols: List[str], start: date, end: Optional[date] = None
    ) -> pd.DataFrame:
        """
        Fetch historical prices using batch operations for efficiency.
        Implements caching and rate limiting.
        """
        if not symbols:
            return pd.DataFrame()

        end = end or date.today()
        all_data = {}

        # Process in batches to optimize API credits
        # TwelveData allows up to 120 symbols per request for time series
        batch_size = min(8, settings.TWELVEDATA_RATE_LIMIT)  # Limited by rate limit

        for i in range(0, len(symbols), batch_size):
            batch = symbols[i : i + batch_size]

            # Check cache first for each symbol
            uncached_symbols = []
            for symbol in batch:
                cache_key = self._get_cache_key(
                    "prices",
                    symbol=symbol,
                    start=start.isoformat(),
                    end=end.isoformat(),
                )

                cached_data = self._get_from_cache(cache_key)
                if cached_data:
                    # Convert cached JSON back to DataFrame
                    df = pd.DataFrame(cached_data)
                    df.index = pd.to_datetime(df.index)
                    all_data[symbol] = df
                else:
                    uncached_symbols.append(symbol)

            if not uncached_symbols:
                continue

            # Rate limit check
            self.rate_limiter.wait_if_needed(len(uncached_symbols))

            try:
                # Batch request for multiple symbols
                if len(uncached_symbols) == 1:
                    # Single symbol request
                    symbol = uncached_symbols[0]
                    logger.info(f"Fetching prices for {symbol}")

                    ts = self.client.time_series(
                        symbol=symbol,
                        interval="1day",
                        start_date=start.strftime("%Y-%m-%d"),
                        end_date=end.strftime("%Y-%m-%d"),
                        outputsize=5000,
                        timezone="America/New_York",
                        order="asc",
                        dp=4,  # 4 decimal places
                    )

                    df = ts.as_pandas()
                    if df is not None and not df.empty:
                        df = self._process_price_data(df, symbol)
                        if not df.empty:
                            all_data[symbol] = df
                            # Cache the result
                            cache_key = self._get_cache_key(
                                "prices",
                                symbol=symbol,
                                start=start.isoformat(),
                                end=end.isoformat(),
                            )
                            self._set_cache(
                                cache_key, df.to_json(), self.price_cache_ttl
                            )

                else:
                    # Batch request for multiple symbols
                    symbols_str = ",".join(uncached_symbols)
                    logger.info(f"Fetching batch prices for {symbols_str}")

                    ts = self.client.time_series(
                        symbol=uncached_symbols,  # Pass as list for batch
                        interval="1day",
                        start_date=start.strftime("%Y-%m-%d"),
                        end_date=end.strftime("%Y-%m-%d"),
                        outputsize=5000,
                        timezone="America/New_York",
                        order="asc",
                        dp=4,
                    )

                    # Process batch response
                    batch_data = ts.as_json()

                    if batch_data:
                        for symbol in uncached_symbols:
                            if symbol in batch_data:
                                symbol_data = batch_data[symbol]
                                if "values" in symbol_data:
                                    df = pd.DataFrame(symbol_data["values"])
                                    df["datetime"] = pd.to_datetime(df["datetime"])
                                    df.set_index("datetime", inplace=True)

                                    # Process and standardize
                                    df = self._process_price_data(df, symbol)
                                    if not df.empty:
                                        all_data[symbol] = df

                                        # Cache the result
                                        cache_key = self._get_cache_key(
                                            "prices",
                                            symbol=symbol,
                                            start=start.isoformat(),
                                            end=end.isoformat(),
                                        )
                                        self._set_cache(
                                            cache_key,
                                            df.to_json(),
                                            self.price_cache_ttl,
                                        )

            except TwelveDataError as e:
                logger.error(f"TwelveData API error: {e}")
                # Try individual requests as fallback
                for symbol in uncached_symbols:
                    try:
                        self.rate_limiter.wait_if_needed(1)
                        ts = self.client.time_series(
                            symbol=symbol,
                            interval="1day",
                            start_date=start.strftime("%Y-%m-%d"),
                            end_date=end.strftime("%Y-%m-%d"),
                            outputsize=5000,
                            timezone="America/New_York",
                            order="asc",
                            dp=4,
                        )
                        df = ts.as_pandas()
                        if df is not None and not df.empty:
                            df = self._process_price_data(df, symbol)
                            if not df.empty:
                                all_data[symbol] = df
                    except Exception as e2:
                        logger.error(f"Failed to fetch {symbol}: {e2}")

            except Exception as e:
                logger.error(f"Unexpected error fetching batch {uncached_symbols}: {e}")

        if not all_data:
            logger.warning("No data fetched for any symbols")
            return pd.DataFrame()

        # Combine all DataFrames into MultiIndex format
        result = pd.concat(all_data, axis=1)

        # Ensure datetime index
        if not isinstance(result.index, pd.DatetimeIndex):
            result.index = pd.to_datetime(result.index)

        return result

    def _process_price_data(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Process and validate price data."""
        # Standardize column names
        df = df.rename(
            columns={
                "close": "Close",
                "open": "Open",
                "high": "High",
                "low": "Low",
                "volume": "Volume",
            }
        )

        # Ensure numeric types
        for col in ["Close", "Open", "High", "Low", "Volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Data quality checks
        initial_len = len(df)

        # Remove invalid prices
        df = df[df["Close"].notna() & (df["Close"] > 0)]

        if len(df) < initial_len:
            logger.warning(f"{symbol}: Removed {initial_len - len(df)} invalid rows")

        # Check for extreme movements
        if len(df) > 1:
            returns = df["Close"].pct_change()
            extreme_returns = returns[(returns > 0.5) | (returns < -0.5)]
            if len(extreme_returns) > 0:
                logger.warning(
                    f"{symbol}: {len(extreme_returns)} extreme movements (>50%)"
                )

        return df

    def get_quotes(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Get real-time quotes for multiple symbols using batch operations.
        """
        if not symbols:
            return {}

        quotes = {}

        # Check cache first
        uncached_symbols = []
        for symbol in symbols:
            cache_key = self._get_cache_key("quote", symbol=symbol)
            cached_quote = self._get_from_cache(cache_key)
            if cached_quote:
                quotes[symbol] = cached_quote
            else:
                uncached_symbols.append(symbol)

        if not uncached_symbols:
            return quotes

        # Rate limit check - batch quotes count as 1 credit
        self.rate_limiter.wait_if_needed(1)

        try:
            # Batch quote request
            logger.info(f"Fetching quotes for {','.join(uncached_symbols)}")

            if len(uncached_symbols) == 1:
                # Single quote
                quote_data = self.client.quote(symbol=uncached_symbols[0]).as_json()
                if quote_data:
                    processed_quote = self._process_quote(quote_data)
                    quotes[uncached_symbols[0]] = processed_quote
                    # Cache it
                    cache_key = self._get_cache_key("quote", symbol=uncached_symbols[0])
                    self._set_cache(cache_key, processed_quote, self.quote_cache_ttl)
            else:
                # Batch quotes
                quote_data = self.client.quote(symbol=uncached_symbols).as_json()

                if quote_data:
                    for symbol in uncached_symbols:
                        if symbol in quote_data:
                            processed_quote = self._process_quote(quote_data[symbol])
                            quotes[symbol] = processed_quote
                            # Cache it
                            cache_key = self._get_cache_key("quote", symbol=symbol)
                            self._set_cache(
                                cache_key, processed_quote, self.quote_cache_ttl
                            )

        except Exception as e:
            logger.error(f"Error fetching quotes: {e}")

        return quotes

    def _process_quote(self, quote_data: Dict) -> Dict:
        """Process quote data into standard format."""
        return {
            "symbol": quote_data.get("symbol"),
            "price": float(quote_data.get("close", 0)),
            "change": float(quote_data.get("change", 0)),
            "percent_change": float(quote_data.get("percent_change", 0)),
            "volume": int(quote_data.get("volume", 0)),
            "timestamp": quote_data.get("timestamp"),
            "open": float(quote_data.get("open", 0)),
            "high": float(quote_data.get("high", 0)),
            "low": float(quote_data.get("low", 0)),
            "previous_close": float(quote_data.get("previous_close", 0)),
        }

    def get_exchange_rate(
        self, from_currency: str, to_currency: str = "USD"
    ) -> Optional[float]:
        """Get exchange rate with caching."""
        if from_currency == to_currency:
            return 1.0

        # Check cache
        cache_key = self._get_cache_key(
            "forex", from_curr=from_currency, to_curr=to_currency
        )
        cached_rate = self._get_from_cache(cache_key)
        if cached_rate:
            return float(cached_rate)

        # Rate limit check
        self.rate_limiter.wait_if_needed(1)

        try:
            # Direct rate
            symbol = f"{from_currency}/{to_currency}"
            logger.info(f"Fetching exchange rate: {symbol}")

            rate_data = self.client.exchange_rate(symbol=symbol).as_json()
            if rate_data and "rate" in rate_data:
                rate = float(rate_data["rate"])
                # Cache it
                self._set_cache(cache_key, rate, self.forex_cache_ttl)
                return rate

            # Try reverse rate
            if from_currency == "USD":
                symbol = f"{to_currency}/USD"
                rate_data = self.client.exchange_rate(symbol=symbol).as_json()
                if rate_data and "rate" in rate_data:
                    rate = 1.0 / float(rate_data["rate"])
                    self._set_cache(cache_key, rate, self.forex_cache_ttl)
                    return rate

            # Cross rate through USD
            if to_currency != "USD" and from_currency != "USD":
                rate_to_usd = self.get_exchange_rate(from_currency, "USD")
                rate_from_usd = self.get_exchange_rate("USD", to_currency)
                if rate_to_usd and rate_from_usd:
                    rate = rate_to_usd * rate_from_usd
                    self._set_cache(cache_key, rate, self.forex_cache_ttl)
                    return rate

        except Exception as e:
            logger.error(
                f"Error fetching exchange rate {from_currency}/{to_currency}: {e}"
            )

        return None

    def validate_symbols(self, symbols: List[str]) -> Dict[str, bool]:
        """Validate symbols availability."""
        results = {}

        # Check in batches
        batch_size = min(8, settings.TWELVEDATA_RATE_LIMIT)

        for i in range(0, len(symbols), batch_size):
            batch = symbols[i : i + batch_size]
            self.rate_limiter.wait_if_needed(len(batch))

            for symbol in batch:
                try:
                    # Try to fetch one data point
                    ts = self.client.time_series(
                        symbol=symbol, interval="1day", outputsize=1
                    )
                    data = ts.as_json()
                    results[symbol] = data is not None and "values" in data
                except Exception:
                    results[symbol] = False

        return results

    def get_api_usage(self) -> Optional[Dict]:
        """Get current API usage statistics."""
        try:
            self.rate_limiter.wait_if_needed(1)
            usage = self.client.api_usage().as_json()
            return usage
        except Exception as e:
            logger.error(f"Error fetching API usage: {e}")
            return None


# Global service instance
_service_instance = None


def get_twelvedata_service() -> TwelveDataService:
    """Get or create TwelveData service instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = TwelveDataService()
    return _service_instance


# Backward compatibility functions
def fetch_prices(
    symbols: List[str], start: date, end: Optional[date] = None
) -> pd.DataFrame:
    """Fetch historical prices (backward compatibility)."""
    service = get_twelvedata_service()
    return service.fetch_prices(symbols, start, end)


def get_exchange_rate(from_currency: str, to_currency: str = "USD") -> Optional[float]:
    """Get exchange rate (backward compatibility)."""
    service = get_twelvedata_service()
    return service.get_exchange_rate(from_currency, to_currency)


def get_quote(symbol: str) -> Optional[Dict]:
    """Get single quote (backward compatibility)."""
    service = get_twelvedata_service()
    quotes = service.get_quotes([symbol])
    return quotes.get(symbol)


def validate_symbols(symbols: List[str]) -> Dict[str, bool]:
    """Validate symbols (backward compatibility)."""
    service = get_twelvedata_service()
    return service.validate_symbols(symbols)
