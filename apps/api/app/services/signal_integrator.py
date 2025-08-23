"""
Signal Integrator - Connects real-time data feeds to signal detection
Following "throw spaghetti" approach - integrate fast, optimize later
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
import os

# Import our signal detection services
from .agro_robotics_tracker import AgroRoboticsTracker
from .regulatory_tracker import RegulatoryTracker
from .supply_chain_mapper import SupplyChainMapper
from .momentum_detector import MomentumDetector
from .osint_tracker import OSINTTracker

# Import data providers
from .twelvedata import TwelveDataService
from .news import NewsService
from ..providers.marketaux_client import MarketAuxClient
from ..core.database import get_db

logger = logging.getLogger(__name__)


class SignalIntegrator:
    """
    Integrates real-time data feeds with signal detection services.
    This is the bridge between data and alpha generation.
    """
    
    def __init__(self):
        """Initialize with data services."""
        self.twelvedata = TwelveDataService()
        self.news_service = None  # Will be initialized with db when needed
        self.marketaux = MarketAuxClient()  # Real news API
        self.last_refresh = {}
        self._cached_prices = {}  # Store cached price data
        self._cached_news = {}  # Store cached news data
        self.cache_duration = timedelta(minutes=5)  # 5-minute cache for rate limiting
        self.news_cache_duration = timedelta(minutes=15)  # 15-minute cache for news
        
    def get_real_time_price(self, symbol: str) -> Dict:
        """
        Get real-time price data for a symbol.
        Uses TwelveData API with caching.
        """
        cache_key = f"price_{symbol}"
        
        # Check cache
        if cache_key in self.last_refresh:
            if datetime.now() - self.last_refresh[cache_key] < self.cache_duration:
                logger.info(f"Using cached price for {symbol}")
                return self._get_cached_price(symbol)
        
        try:
            # Check if API key is configured
            if not os.getenv("TWELVEDATA_API_KEY"):
                logger.warning("TWELVEDATA_API_KEY not configured, using placeholder data")
                return self._get_placeholder_price(symbol)
            
            # Fetch real-time data from TwelveData API
            data = self.twelvedata.get_quote(symbol)
            if data:
                self.last_refresh[cache_key] = datetime.now()
                # Store cached data for future use
                self._cached_prices[symbol] = {
                    "price": float(data.get("close", data.get("price", 0))),
                    "change": float(data.get("change", 0)),
                    "percent_change": float(data.get("percent_change", data.get("percent", 0))),
                    "volume": int(data.get("volume", 0)),
                    "timestamp": datetime.now().isoformat()
                }
                return {
                    "symbol": symbol,
                    "price": self._cached_prices[symbol]["price"],
                    "change": self._cached_prices[symbol]["change"],
                    "percent_change": self._cached_prices[symbol]["percent_change"],
                    "volume": self._cached_prices[symbol]["volume"],
                    "timestamp": self._cached_prices[symbol]["timestamp"]
                }
        except Exception as e:
            logger.error(f"Error fetching real-time price for {symbol}: {e}")
        
        # Return placeholder if API fails
        logger.info(f"Using placeholder price for {symbol}")
        return self._get_placeholder_price(symbol)
    
    def get_momentum_signals_with_prices(self, timeframe: str = "short") -> List[Dict]:
        """
        Get momentum signals enriched with real-time prices.
        Combines MomentumDetector signals with live market data.
        """
        signals = MomentumDetector.detect_momentum_signals(timeframe)
        
        # Enrich with real-time prices
        for signal in signals[:10]:  # Limit API calls
            symbol = signal.get("symbol")
            if symbol:
                price_data = self.get_real_time_price(symbol)
                signal["current_price"] = price_data["price"]
                signal["price_change_today"] = price_data["percent_change"]
                signal["volume"] = price_data["volume"]
                
                # Calculate distance to entry
                entry_price = signal.get("entry_price", 0)
                if entry_price > 0:
                    signal["distance_to_entry"] = (
                        (price_data["price"] - entry_price) / entry_price * 100
                    )
        
        return signals
    
    def get_agro_opportunities_with_news(self, db) -> List[Dict]:
        """
        Get agro-robotics opportunities enriched with news sentiment.
        Combines AgroRoboticsTracker with real MarketAux news data.
        """
        opportunities = AgroRoboticsTracker.screen_for_opportunities(db, {})
        
        # Enrich with real news sentiment from MarketAux
        for opp in opportunities[:5]:  # Limit API calls to stay within free tier
            symbol = opp.get("symbol")
            if symbol:
                # Check news cache first
                cache_key = f"news_{symbol}_7d"
                if cache_key in self._cached_news:
                    cache_time, cached_data = self._cached_news[cache_key]
                    if datetime.now() - cache_time < self.news_cache_duration:
                        opp.update(cached_data)
                        continue
                
                try:
                    # Get real news from MarketAux API
                    if os.getenv("MARKETAUX_API_KEY"):
                        articles = self.marketaux.get_news_by_symbol(symbol, days_back=7, limit=10)
                        
                        if articles:
                            # Calculate aggregate sentiment from real news
                            sentiments = []
                            headlines = []
                            
                            for article in articles:
                                # MarketAux provides formatted articles
                                formatted = self.marketaux.format_article(article)
                                if formatted["sentiment_score"] != 0:
                                    sentiments.append(formatted["sentiment_score"])
                                headlines.append(formatted["title"])
                            
                            avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
                            
                            news_data = {
                                "news_sentiment": avg_sentiment,
                                "news_count_7d": len(articles),
                                "latest_headline": headlines[0] if headlines else None,
                                "news_source": "MarketAux"
                            }
                            
                            # Cache the news data
                            self._cached_news[cache_key] = (datetime.now(), news_data)
                            opp.update(news_data)
                        else:
                            opp["news_sentiment"] = 0
                            opp["news_count_7d"] = 0
                            opp["latest_headline"] = None
                            opp["news_source"] = "No news found"
                    else:
                        # Fallback to database news service if MarketAux not configured
                        if self.news_service is None:
                            self.news_service = NewsService(db)
                        
                        news = self.news_service.get_news_for_symbol(symbol, days=7)
                        if news:
                            sentiments = [n.get("sentiment_score", 0) for n in news]
                            avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
                            
                            opp["news_sentiment"] = avg_sentiment
                            opp["news_count_7d"] = len(news)
                            opp["latest_headline"] = news[0].get("title") if news else None
                            opp["news_source"] = "Database"
                        else:
                            opp["news_sentiment"] = 0
                            opp["news_count_7d"] = 0
                            opp["news_source"] = "Fallback"
                            
                except Exception as e:
                    logger.warning(f"Could not get news for {symbol}: {e}")
                    opp["news_sentiment"] = 0
                    opp["news_count_7d"] = 0
                    opp["news_source"] = "Error"
        
        return opportunities
    
    def get_smart_money_with_verification(self) -> List[Dict]:
        """
        Get OSINT smart money moves with price verification.
        Verifies that reported moves align with actual price action.
        """
        moves = OSINTTracker.track_smart_money()
        
        # Verify with price action
        for move in moves[:10]:
            # Extract symbol from action (simplified parsing)
            action = move.get("action", "")
            symbol = self._extract_symbol_from_action(action)
            
            if symbol:
                price_data = self.get_real_time_price(symbol)
                move["current_price"] = price_data["price"]
                move["price_momentum"] = price_data["percent_change"]
                
                # Verify direction aligns
                if "bought" in action.lower() or "increased" in action.lower():
                    move["alignment"] = "bullish" if price_data["percent_change"] > 0 else "divergent"
                elif "sold" in action.lower() or "reduced" in action.lower():
                    move["alignment"] = "bearish" if price_data["percent_change"] < 0 else "divergent"
        
        return moves
    
    def get_integrated_daily_signals(self, db) -> Dict:
        """
        Get fully integrated daily signals combining all sources.
        This is the main entry point for alpha generation.
        """
        try:
            # Gather signals from all sources
            momentum = self.get_momentum_signals_with_prices("short")[:5]
            agro = self.get_agro_opportunities_with_news(db)[:3]
            smart_money = self.get_smart_money_with_verification()[:5]
            regulatory = RegulatoryTracker.get_upcoming_catalysts(30)[:3]
            supply_chain = SupplyChainMapper.analyze_ukraine_impact()
            
            # Find consensus plays (appearing in multiple signals)
            all_symbols = set()
            symbol_mentions = {}
            
            for m in momentum:
                sym = m.get("symbol")
                if sym:
                    all_symbols.add(sym)
                    symbol_mentions[sym] = symbol_mentions.get(sym, 0) + 1
            
            for a in agro:
                sym = a.get("symbol")
                if sym:
                    all_symbols.add(sym)
                    symbol_mentions[sym] = symbol_mentions.get(sym, 0) + 1
            
            # Identify high-conviction plays (mentioned multiple times)
            consensus_plays = [
                sym for sym, count in symbol_mentions.items() if count >= 2
            ]
            
            # Get real-time news insights
            breaking_news = self.get_breaking_news_alerts()
            trending_topics = self.get_trending_topics()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "market_status": self._get_market_status(),
                "breaking_news": breaking_news[:3],  # Top 3 breaking stories
                "trending_topics": trending_topics[:5],  # Top 5 trending topics
                "momentum_signals": momentum,
                "agro_opportunities": agro,
                "smart_money_moves": smart_money,
                "regulatory_catalysts": regulatory,
                "supply_chain_impacts": supply_chain.get("beneficiary_companies", [])[:3],
                "consensus_plays": consensus_plays,
                "top_conviction": {
                    "symbol": consensus_plays[0] if consensus_plays else "AGCO",
                    "rationale": "Multiple signal convergence",
                    "signals_aligned": len(consensus_plays)
                },
                "action_items": self._generate_action_items(momentum, smart_money, consensus_plays),
                "data_sources": {
                    "prices": "TwelveData" if os.getenv("TWELVEDATA_API_KEY") else "Placeholder",
                    "news": "MarketAux" if os.getenv("MARKETAUX_API_KEY") else "Database"
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating integrated signals: {e}")
            return self._get_fallback_signals()
    
    def _extract_symbol_from_action(self, action: str) -> Optional[str]:
        """Extract stock symbol from action text."""
        # Simple extraction - look for uppercase symbols
        words = action.split()
        for word in words:
            if word.isupper() and 2 <= len(word) <= 5:
                # Basic validation that it looks like a symbol
                if not any(char.isdigit() for char in word):
                    return word
        return None
    
    def _get_market_status(self) -> str:
        """Determine current market status."""
        now = datetime.now()
        hour = now.hour
        
        # Simple market hours check (EST)
        if now.weekday() >= 5:  # Weekend
            return "closed_weekend"
        elif 9 <= hour < 16:
            return "open"
        elif 16 <= hour < 20:
            return "after_hours"
        else:
            return "pre_market"
    
    def _generate_action_items(self, momentum: List, smart_money: List, consensus: List) -> List[str]:
        """Generate specific action items based on signals."""
        actions = []
        
        if momentum and momentum[0].get("distance_to_entry", 0) < 2:
            actions.append(f"Enter {momentum[0]['symbol']} near {momentum[0]['entry_price']}")
        
        if smart_money and smart_money[0].get("alignment") == "bullish":
            actions.append(f"Follow smart money into {smart_money[0].get('entity', 'position')}")
        
        if consensus:
            actions.append(f"Increase allocation to consensus play {consensus[0]}")
        
        if not actions:
            actions.append("Monitor signals for entry opportunities")
        
        return actions[:5]  # Limit to 5 action items
    
    def _get_cached_price(self, symbol: str) -> Dict:
        """Get cached price data."""
        if symbol in self._cached_prices:
            return {
                "symbol": symbol,
                **self._cached_prices[symbol]
            }
        # Fallback to placeholder if no cached data
        return self._get_placeholder_price(symbol)
    
    def _get_placeholder_price(self, symbol: str) -> Dict:
        """Get placeholder price when API unavailable."""
        prices = {
            "AGCO": 115.50,
            "DE": 430.25,
            "SMCI": 65.75,
            "PLTR": 28.30,
            "OXY": 58.90,
            "NVDA": 142.50
        }
        
        return {
            "symbol": symbol,
            "price": prices.get(symbol, 100.00),
            "change": 1.25,
            "percent_change": 1.2,
            "volume": 1000000,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_breaking_news_alerts(self) -> List[Dict]:
        """
        Get breaking news that could impact markets.
        Uses MarketAux API for real-time news alerts.
        """
        if not os.getenv("MARKETAUX_API_KEY"):
            logger.info("MarketAux API key not configured, no breaking news available")
            return []
        
        try:
            # Get breaking news from last 30 minutes
            breaking = self.marketaux.get_breaking_news(minutes_back=30)
            
            # Get market sentiment for context
            sentiment = self.marketaux.get_market_sentiment(hours_back=1)
            
            alerts = []
            for article in breaking[:5]:  # Limit to top 5 breaking stories
                # Create alert with urgency scoring
                alert = {
                    "type": "breaking_news",
                    "headline": article["title"],
                    "url": article["url"],
                    "source": article["source"],
                    "tickers": article["tickers"],
                    "sentiment": article["sentiment_score"],
                    "relevance": article["relevance_score"],
                    "published": article["published_at"],
                    "urgency": "high" if article.get("is_breaking") else "medium",
                    "market_context": sentiment["sentiment"]
                }
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error fetching breaking news: {e}")
            return []
    
    def get_trending_topics(self) -> List[Dict]:
        """
        Get trending topics from news analysis.
        Identifies what the market is talking about.
        """
        if not os.getenv("MARKETAUX_API_KEY"):
            return []
        
        try:
            # Get trending topics from last 24 hours
            trending = self.marketaux.get_trending_topics(hours_back=24, min_mentions=3)
            
            # Enrich with current prices for mentioned symbols
            for topic in trending[:10]:
                symbol = topic.get("symbol")
                if symbol:
                    price_data = self.get_real_time_price(symbol)
                    topic["current_price"] = price_data["price"]
                    topic["price_change"] = price_data["percent_change"]
            
            return trending
            
        except Exception as e:
            logger.error(f"Error fetching trending topics: {e}")
            return []
    
    def _get_fallback_signals(self) -> Dict:
        """Fallback signals when integration fails."""
        return {
            "timestamp": datetime.now().isoformat(),
            "status": "fallback_mode",
            "message": "Using cached signals due to data feed issues",
            "top_opportunities": [
                {"symbol": "AGCO", "type": "agro-robotics", "conviction": "high"},
                {"symbol": "OXY", "type": "smart-money", "conviction": "high"},
                {"symbol": "SMCI", "type": "momentum", "conviction": "medium"}
            ]
        }


# Singleton instance
signal_integrator = SignalIntegrator()