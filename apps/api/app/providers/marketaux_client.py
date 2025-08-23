"""
MarketAux News API Client
Provides real-time financial news with sentiment analysis
Free tier: 100 requests/day
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import requests
from urllib.parse import urlencode

from ..core.config import settings

logger = logging.getLogger(__name__)


class MarketAuxClient:
    """Client for MarketAux News API with rate limiting and caching."""
    
    def __init__(self):
        """Initialize MarketAux client with API configuration."""
        self.api_key = settings.MARKETAUX_API_KEY
        self.base_url = "https://api.marketaux.com/v1"
        self.rate_limit = settings.MARKETAUX_RATE_LIMIT  # 100 requests/day for free tier
        self.cache_ttl = settings.NEWS_REFRESH_INTERVAL  # 15 minutes default
        self._request_count = 0
        self._last_reset = datetime.now()
        
    def _check_rate_limit(self):
        """Check if we're within rate limits."""
        # Reset counter daily
        if datetime.now() - self._last_reset > timedelta(days=1):
            self._request_count = 0
            self._last_reset = datetime.now()
            
        if self._request_count >= self.rate_limit:
            logger.warning(f"MarketAux rate limit reached ({self.rate_limit} requests/day)")
            return False
        
        return True
    
    def get_news(
        self,
        symbols: Optional[List[str]] = None,
        keywords: Optional[str] = None,
        from_date: Optional[datetime] = None,
        limit: int = 10,
        countries: Optional[List[str]] = None,
        filter_entities: bool = True,
        domains: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Fetch news articles from MarketAux API.
        
        Args:
            symbols: List of stock symbols to filter by
            keywords: Keywords to search for
            from_date: Get news from this date onwards
            limit: Maximum number of articles to return
            countries: Filter by country codes (e.g., ['us', 'gb'])
            filter_entities: Filter for articles with entity tags
            domains: Specific news domains to include
            
        Returns:
            Dictionary with news articles and metadata
        """
        if not self.api_key:
            logger.warning("MarketAux API key not configured, returning empty results")
            return {"data": [], "meta": {"found": 0}}
        
        if not self._check_rate_limit():
            return {"data": [], "meta": {"found": 0, "error": "Rate limit exceeded"}}
        
        # Build query parameters
        params = {
            "api_token": self.api_key,
            "limit": min(limit, 100),  # Max 100 per request
            "language": "en"
        }
        
        # Add optional filters
        if symbols:
            params["symbols"] = ",".join(symbols)
            
        if keywords:
            params["search"] = keywords
            
        if from_date:
            # MarketAux expects ISO format
            params["published_after"] = from_date.isoformat()
            
        if countries:
            params["countries"] = ",".join(countries)
            
        if filter_entities:
            params["filter_entities"] = "true"
            
        if domains:
            params["domains"] = ",".join(domains)
        
        try:
            # Make API request
            response = requests.get(
                f"{self.base_url}/news/all",
                params=params,
                timeout=10
            )
            
            self._request_count += 1
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Fetched {len(data.get('data', []))} news articles from MarketAux")
                return data
            elif response.status_code == 401:
                logger.error("MarketAux API key invalid")
                return {"data": [], "meta": {"error": "Invalid API key"}}
            elif response.status_code == 429:
                logger.warning("MarketAux rate limit exceeded")
                return {"data": [], "meta": {"error": "Rate limit exceeded"}}
            else:
                logger.error(f"MarketAux API error: {response.status_code}")
                return {"data": [], "meta": {"error": f"API error: {response.status_code}"}}
                
        except requests.exceptions.Timeout:
            logger.error("MarketAux API request timeout")
            return {"data": [], "meta": {"error": "Request timeout"}}
        except Exception as e:
            logger.error(f"Error fetching news from MarketAux: {e}")
            return {"data": [], "meta": {"error": str(e)}}
    
    def get_news_by_symbol(
        self,
        symbol: str,
        days_back: int = 7,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get news for a specific symbol.
        
        Args:
            symbol: Stock symbol
            days_back: Number of days of news to fetch
            limit: Maximum articles to return
            
        Returns:
            List of news articles
        """
        from_date = datetime.now() - timedelta(days=days_back)
        result = self.get_news(
            symbols=[symbol],
            from_date=from_date,
            limit=limit
        )
        return result.get("data", [])
    
    def get_market_sentiment(
        self,
        symbols: Optional[List[str]] = None,
        hours_back: int = 24
    ) -> Dict[str, Any]:
        """
        Get aggregated market sentiment from recent news.
        
        Args:
            symbols: Symbols to analyze (None for market-wide)
            hours_back: Hours of news to analyze
            
        Returns:
            Sentiment analysis results
        """
        from_date = datetime.now() - timedelta(hours=hours_back)
        
        # Fetch recent news
        result = self.get_news(
            symbols=symbols,
            from_date=from_date,
            limit=100
        )
        
        articles = result.get("data", [])
        
        if not articles:
            return {
                "sentiment": "neutral",
                "score": 0,
                "article_count": 0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0
            }
        
        # Analyze sentiment distribution
        positive = 0
        negative = 0
        neutral = 0
        
        for article in articles:
            # MarketAux provides sentiment in entities
            entities = article.get("entities", [])
            for entity in entities:
                sentiment = entity.get("sentiment_score", 0)
                if sentiment > 0.1:
                    positive += 1
                elif sentiment < -0.1:
                    negative += 1
                else:
                    neutral += 1
        
        total = positive + negative + neutral
        
        # Calculate aggregate sentiment
        if total == 0:
            sentiment_score = 0
            sentiment_label = "neutral"
        else:
            sentiment_score = (positive - negative) / total
            
            if sentiment_score > 0.2:
                sentiment_label = "bullish"
            elif sentiment_score < -0.2:
                sentiment_label = "bearish"
            else:
                sentiment_label = "neutral"
        
        return {
            "sentiment": sentiment_label,
            "score": sentiment_score,
            "article_count": len(articles),
            "positive_count": positive,
            "negative_count": negative,
            "neutral_count": neutral,
            "symbols": symbols,
            "time_range_hours": hours_back
        }
    
    def parse_article_for_tickers(self, article: Dict[str, Any]) -> List[str]:
        """
        Extract stock tickers mentioned in a news article.
        
        Args:
            article: MarketAux article object
            
        Returns:
            List of ticker symbols
        """
        tickers = set()
        
        # Extract from entities
        entities = article.get("entities", [])
        for entity in entities:
            symbol = entity.get("symbol")
            if symbol:
                tickers.add(symbol)
        
        # Extract from highlighted entities
        highlights = article.get("highlight", {})
        highlight_entities = highlights.get("entities", [])
        for entity in highlight_entities:
            symbol = entity.get("symbol")
            if symbol:
                tickers.add(symbol)
        
        return list(tickers)
    
    def format_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format MarketAux article for our system.
        
        Args:
            article: Raw MarketAux article
            
        Returns:
            Formatted article dictionary
        """
        # Extract primary image
        image_url = article.get("image_url", "")
        
        # Parse entities for sentiment
        entities = article.get("entities", [])
        avg_sentiment = 0
        if entities:
            sentiments = [e.get("sentiment_score", 0) for e in entities]
            avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
        
        return {
            "title": article.get("title", ""),
            "description": article.get("description", ""),
            "url": article.get("url", ""),
            "source": article.get("source", ""),
            "published_at": article.get("published_at", ""),
            "image_url": image_url,
            "tickers": self.parse_article_for_tickers(article),
            "sentiment_score": avg_sentiment,
            "entities": entities,
            "relevance_score": article.get("relevance_score", 0)
        }
    
    def get_trending_topics(
        self,
        hours_back: int = 24,
        min_mentions: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Identify trending topics from recent news.
        
        Args:
            hours_back: Hours of news to analyze
            min_mentions: Minimum mentions to be considered trending
            
        Returns:
            List of trending topics with counts
        """
        from_date = datetime.now() - timedelta(hours=hours_back)
        
        # Fetch recent news
        result = self.get_news(
            from_date=from_date,
            limit=100
        )
        
        articles = result.get("data", [])
        
        # Count entity mentions
        entity_counts = {}
        
        for article in articles:
            entities = article.get("entities", [])
            for entity in entities:
                name = entity.get("name", "")
                symbol = entity.get("symbol", "")
                key = f"{symbol}:{name}" if symbol else name
                
                if key:
                    if key not in entity_counts:
                        entity_counts[key] = {
                            "name": name,
                            "symbol": symbol,
                            "count": 0,
                            "sentiment_sum": 0,
                            "articles": []
                        }
                    
                    entity_counts[key]["count"] += 1
                    entity_counts[key]["sentiment_sum"] += entity.get("sentiment_score", 0)
                    entity_counts[key]["articles"].append(article.get("title", ""))
        
        # Filter and sort trending topics
        trending = []
        for key, data in entity_counts.items():
            if data["count"] >= min_mentions:
                avg_sentiment = data["sentiment_sum"] / data["count"]
                trending.append({
                    "name": data["name"],
                    "symbol": data["symbol"],
                    "mention_count": data["count"],
                    "avg_sentiment": avg_sentiment,
                    "sample_headlines": data["articles"][:3]
                })
        
        # Sort by mention count
        trending.sort(key=lambda x: x["mention_count"], reverse=True)
        
        return trending[:20]  # Top 20 trending topics
    
    def get_breaking_news(self, minutes_back: int = 30) -> List[Dict[str, Any]]:
        """
        Get breaking news from the last N minutes.
        
        Args:
            minutes_back: How far back to look for breaking news
            
        Returns:
            List of breaking news articles
        """
        from_date = datetime.now() - timedelta(minutes=minutes_back)
        
        result = self.get_news(
            from_date=from_date,
            limit=20
        )
        
        articles = result.get("data", [])
        
        # Format and return
        breaking = []
        for article in articles:
            formatted = self.format_article(article)
            # Mark as breaking if highly relevant
            if formatted["relevance_score"] > 0.7:
                formatted["is_breaking"] = True
                breaking.append(formatted)
        
        return breaking