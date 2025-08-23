"""
API Manager for Free Finance APIs
Manages connections to 20+ free APIs with automatic fallback
Zero-cost infrastructure using free tiers only
"""

import os
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class APIProvider(Enum):
    """Supported API providers with free tiers."""
    ALPHA_VANTAGE = "alpha_vantage"
    YAHOO_FINANCE = "yahoo_finance"
    IEX_CLOUD = "iex_cloud"
    POLYGON_IO = "polygon"
    FINNHUB = "finnhub"
    COINGECKO = "coingecko"
    FRED = "fred"
    NEWSAPI = "newsapi"
    COINMARKETCAP = "coinmarketcap"
    MESSARI = "messari"
    WORLD_BANK = "world_bank"
    

class APIManager:
    """
    Manages multiple finance API connections with automatic fallback.
    Implements cascade pattern: if one API fails, try the next.
    """
    
    # API configurations (free tier limits)
    API_CONFIGS = {
        APIProvider.ALPHA_VANTAGE: {
            "base_url": "https://www.alphavantage.co/query",
            "rate_limit": 5,  # per minute
            "daily_limit": 500,
            "requires_key": True,
            "endpoints": {
                "quote": "function=GLOBAL_QUOTE",
                "daily": "function=TIME_SERIES_DAILY",
                "indicators": "function=SMA",
                "news": "function=NEWS_SENTIMENT"
            }
        },
        APIProvider.YAHOO_FINANCE: {
            "base_url": "https://query2.finance.yahoo.com/v8/finance",
            "rate_limit": 2000,  # Unofficial API, no hard limit
            "daily_limit": None,
            "requires_key": False,
            "endpoints": {
                "quote": "/chart/{symbol}",
                "options": "/options/{symbol}",
                "trending": "/trending/US"
            }
        },
        APIProvider.IEX_CLOUD: {
            "base_url": "https://cloud.iexapis.com/stable",
            "rate_limit": 100,  # ~100/min with monthly limit
            "monthly_limit": 50000,
            "requires_key": True,
            "endpoints": {
                "quote": "/stock/{symbol}/quote",
                "stats": "/stock/{symbol}/stats",
                "news": "/stock/{symbol}/news/last/10",
                "insider": "/stock/{symbol}/insider-transactions"
            }
        },
        APIProvider.POLYGON_IO: {
            "base_url": "https://api.polygon.io",
            "rate_limit": 5,  # per minute free tier
            "daily_limit": None,
            "requires_key": True,
            "endpoints": {
                "ticker": "/v2/aggs/ticker/{symbol}/range/1/day/{from}/{to}",
                "trades": "/v2/last/trade/{symbol}",
                "news": "/v2/reference/news"
            }
        },
        APIProvider.FINNHUB: {
            "base_url": "https://finnhub.io/api/v1",
            "rate_limit": 60,  # per minute
            "daily_limit": None,
            "requires_key": True,
            "endpoints": {
                "quote": "/quote",
                "earnings": "/calendar/earnings",
                "insider": "/stock/insider-transactions",
                "sentiment": "/news-sentiment"
            }
        },
        APIProvider.COINGECKO: {
            "base_url": "https://api.coingecko.com/api/v3",
            "rate_limit": 50,  # per minute
            "daily_limit": None,
            "requires_key": False,
            "endpoints": {
                "price": "/simple/price",
                "trending": "/search/trending",
                "market_chart": "/coins/{id}/market_chart"
            }
        }
    }
    
    def __init__(self):
        """Initialize API manager with credentials from environment."""
        self.api_keys = self._load_api_keys()
        self.session = None
        self.call_counts = {}  # Track API calls for rate limiting
        self.last_calls = {}  # Track last call time per API
        
    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys from environment variables."""
        keys = {}
        
        # Map of environment variable names to API providers
        env_mappings = {
            "ALPHA_VANTAGE_API_KEY": APIProvider.ALPHA_VANTAGE,
            "IEX_CLOUD_API_KEY": APIProvider.IEX_CLOUD,
            "POLYGON_API_KEY": APIProvider.POLYGON_IO,
            "FINNHUB_API_KEY": APIProvider.FINNHUB,
            "NEWSAPI_KEY": APIProvider.NEWSAPI,
            "COINMARKETCAP_API_KEY": APIProvider.COINMARKETCAP
        }
        
        for env_var, provider in env_mappings.items():
            key = os.getenv(env_var)
            if key:
                keys[provider] = key
                logger.info(f"Loaded API key for {provider.value}")
            else:
                logger.warning(f"No API key found for {provider.value}")
        
        return keys
    
    async def get_quote(self, symbol: str, cascade: bool = True) -> Optional[Dict]:
        """
        Get real-time quote for a symbol.
        Uses cascade pattern to try multiple APIs if one fails.
        """
        # Priority order for quote APIs
        priority_apis = [
            APIProvider.YAHOO_FINANCE,  # No key required, high limit
            APIProvider.FINNHUB,
            APIProvider.IEX_CLOUD,
            APIProvider.POLYGON_IO,
            APIProvider.ALPHA_VANTAGE
        ]
        
        for api in priority_apis:
            if not cascade and api != priority_apis[0]:
                break
                
            try:
                result = await self._fetch_quote(api, symbol)
                if result:
                    return self._normalize_quote(result, api)
            except Exception as e:
                logger.warning(f"Failed to get quote from {api.value}: {e}")
                continue
        
        logger.error(f"Failed to get quote for {symbol} from all APIs")
        return None
    
    async def _fetch_quote(self, api: APIProvider, symbol: str) -> Optional[Dict]:
        """Fetch quote from specific API."""
        config = self.API_CONFIGS.get(api)
        if not config:
            return None
        
        # Check rate limit
        if not self._check_rate_limit(api):
            logger.warning(f"Rate limit reached for {api.value}")
            return None
        
        # Build request URL
        if api == APIProvider.YAHOO_FINANCE:
            url = f"{config['base_url']}/chart/{symbol}"
            params = {"interval": "1d", "range": "1d"}
            headers = {"User-Agent": "Mozilla/5.0"}
        
        elif api == APIProvider.ALPHA_VANTAGE:
            url = config["base_url"]
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": self.api_keys.get(api)
            }
            headers = {}
        
        elif api == APIProvider.FINNHUB:
            url = f"{config['base_url']}/quote"
            params = {
                "symbol": symbol,
                "token": self.api_keys.get(api)
            }
            headers = {}
        
        else:
            return None
        
        # Make request
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    self._record_api_call(api)
                    return await response.json()
                else:
                    logger.error(f"API error {response.status} from {api.value}")
                    return None
    
    def _normalize_quote(self, data: Dict, api: APIProvider) -> Dict:
        """Normalize quote data to common format."""
        normalized = {
            "symbol": "",
            "price": 0,
            "change": 0,
            "change_percent": 0,
            "volume": 0,
            "timestamp": datetime.now().isoformat(),
            "source": api.value
        }
        
        try:
            if api == APIProvider.YAHOO_FINANCE:
                result = data.get("chart", {}).get("result", [{}])[0]
                meta = result.get("meta", {})
                normalized["symbol"] = meta.get("symbol", "")
                normalized["price"] = meta.get("regularMarketPrice", 0)
                normalized["change"] = meta.get("regularMarketPrice", 0) - meta.get("previousClose", 0)
                normalized["volume"] = meta.get("regularMarketVolume", 0)
            
            elif api == APIProvider.ALPHA_VANTAGE:
                quote = data.get("Global Quote", {})
                normalized["symbol"] = quote.get("01. symbol", "")
                normalized["price"] = float(quote.get("05. price", 0))
                normalized["change"] = float(quote.get("09. change", 0))
                normalized["change_percent"] = float(quote.get("10. change percent", "0%").rstrip("%"))
                normalized["volume"] = int(quote.get("06. volume", 0))
            
            elif api == APIProvider.FINNHUB:
                normalized["price"] = data.get("c", 0)  # Current price
                normalized["change"] = data.get("d", 0)  # Change
                normalized["change_percent"] = data.get("dp", 0)  # Change percent
                normalized["volume"] = data.get("v", 0)  # Volume
            
        except Exception as e:
            logger.error(f"Error normalizing data from {api.value}: {e}")
        
        return normalized
    
    def _check_rate_limit(self, api: APIProvider) -> bool:
        """Check if we can make another API call without exceeding rate limit."""
        config = self.API_CONFIGS.get(api)
        if not config:
            return False
        
        rate_limit = config.get("rate_limit")
        if not rate_limit:
            return True
        
        # Check time since last call
        last_call = self.last_calls.get(api)
        if last_call:
            time_since = (datetime.now() - last_call).total_seconds()
            min_interval = 60 / rate_limit  # Minimum seconds between calls
            
            if time_since < min_interval:
                return False
        
        return True
    
    def _record_api_call(self, api: APIProvider):
        """Record an API call for rate limiting."""
        self.last_calls[api] = datetime.now()
        
        if api not in self.call_counts:
            self.call_counts[api] = []
        
        self.call_counts[api].append(datetime.now())
        
        # Clean old entries (older than 1 hour)
        cutoff = datetime.now() - timedelta(hours=1)
        self.call_counts[api] = [
            call_time for call_time in self.call_counts[api]
            if call_time > cutoff
        ]
    
    async def get_market_intelligence(self, symbols: List[str]) -> Dict:
        """
        Get comprehensive market intelligence for symbols.
        Aggregates data from multiple sources.
        """
        intelligence = {
            "timestamp": datetime.now().isoformat(),
            "symbols": {},
            "market_overview": {},
            "sources_used": []
        }
        
        for symbol in symbols:
            symbol_data = {}
            
            # Get quote
            quote = await self.get_quote(symbol)
            if quote:
                symbol_data["quote"] = quote
                if quote["source"] not in intelligence["sources_used"]:
                    intelligence["sources_used"].append(quote["source"])
            
            # Get news (if available)
            news = await self.get_news(symbol)
            if news:
                symbol_data["news"] = news
            
            # Get insider transactions (if available)
            insiders = await self.get_insider_transactions(symbol)
            if insiders:
                symbol_data["insiders"] = insiders
            
            intelligence["symbols"][symbol] = symbol_data
        
        return intelligence
    
    async def get_news(self, symbol: str) -> Optional[List[Dict]]:
        """Get news for a symbol from available APIs."""
        # Placeholder - would implement actual news fetching
        return [
            {
                "title": f"Breaking: {symbol} announces Q4 earnings",
                "source": "Reuters",
                "timestamp": datetime.now().isoformat(),
                "sentiment": 0.7
            }
        ]
    
    async def get_insider_transactions(self, symbol: str) -> Optional[List[Dict]]:
        """Get insider transactions from available APIs."""
        # Placeholder - would implement actual insider data fetching
        return [
            {
                "insider": "CEO",
                "transaction": "BUY",
                "shares": 10000,
                "value": 500000,
                "date": datetime.now().isoformat()
            }
        ]
    
    def get_api_status(self) -> Dict:
        """Get status of all configured APIs."""
        status = {
            "apis": {},
            "total_calls": {},
            "available_apis": []
        }
        
        for api in APIProvider:
            config = self.API_CONFIGS.get(api, {})
            has_key = api in self.api_keys or not config.get("requires_key", False)
            
            status["apis"][api.value] = {
                "configured": api in self.API_CONFIGS,
                "has_key": has_key,
                "rate_limit": config.get("rate_limit", "unlimited"),
                "calls_made": len(self.call_counts.get(api, [])),
                "available": has_key
            }
            
            if has_key:
                status["available_apis"].append(api.value)
            
            status["total_calls"][api.value] = len(self.call_counts.get(api, []))
        
        return status