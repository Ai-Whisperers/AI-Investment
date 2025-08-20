"""
News service for handling news data and sentiment analysis.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from ..models.news import (
    NewsArticle as NewsArticleModel,
    NewsSentiment as NewsSentimentModel,
    NewsEntity as NewsEntityModel,
    NewsSource as NewsSourceModel,
    EntitySentimentHistory,
    asset_news_association,
)
from ..models.asset import Asset
from ..providers.news import MarketauxProvider, NewsSearchParams
from ..core.redis_client import get_redis_client

# Import modular components
from .news_modules.sentiment_analyzer import SentimentAnalyzer
from .news_modules.entity_extractor import EntityExtractor
from .news_modules.news_aggregator import NewsAggregator
from .news_modules.news_processor import NewsProcessor

logger = logging.getLogger(__name__)


class NewsService:
    """Service for managing news data and sentiment analysis."""

    def __init__(self, db: Session):
        self.db = db
        self.provider = MarketauxProvider()
        self.redis_client = get_redis_client()
        
        # Initialize components
        self._init_components()

    def _init_components(self):
        """Initialize modular components."""
        # Get known symbols for entity extraction
        known_symbols = self._get_known_symbols()
        
        # Initialize components
        self.sentiment_analyzer = SentimentAnalyzer()
        self.entity_extractor = EntityExtractor(known_symbols)
        self.news_aggregator = NewsAggregator()
        self.news_processor = NewsProcessor(self.db, known_symbols)

    def _get_known_symbols(self) -> Dict[str, str]:
        """Get mapping of known symbols to company names."""
        assets = self.db.query(Asset).all()
        return {asset.symbol: asset.name for asset in assets}

    def search_news(
        self,
        symbols: Optional[List[str]] = None,
        keywords: Optional[str] = None,
        sentiment_min: Optional[float] = None,
        sentiment_max: Optional[float] = None,
        published_after: Optional[datetime] = None,
        published_before: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Search for news articles in database and fetch new ones if needed."""
        
        # First, check database
        query = self.db.query(NewsArticleModel)

        if symbols:
            query = query.join(NewsEntityModel).filter(
                NewsEntityModel.symbol.in_(symbols)
            )

        if keywords:
            search_pattern = f"%{keywords}%"
            query = query.filter(
                NewsArticleModel.title.ilike(search_pattern)
                | NewsArticleModel.description.ilike(search_pattern)
            )

        if sentiment_min is not None or sentiment_max is not None:
            query = query.join(NewsSentimentModel)
            if sentiment_min is not None:
                query = query.filter(
                    NewsSentimentModel.sentiment_score >= sentiment_min
                )
            if sentiment_max is not None:
                query = query.filter(
                    NewsSentimentModel.sentiment_score <= sentiment_max
                )

        if published_after:
            query = query.filter(NewsArticleModel.published_at >= published_after)

        if published_before:
            query = query.filter(NewsArticleModel.published_at <= published_before)

        # Apply pagination
        query = query.order_by(desc(NewsArticleModel.published_at))
        query = query.offset(offset).limit(limit)

        articles = query.all()

        # If not enough articles in DB, fetch from provider
        if len(articles) < limit and symbols:
            logger.info(f"Fetching fresh news for symbols: {symbols}")
            self._fetch_and_store_news(symbols, limit - len(articles))
            articles = query.all()

        # Convert to response format
        return [self._article_to_dict(article) for article in articles]

    def get_article(self, article_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific article by ID."""
        article = (
            self.db.query(NewsArticleModel)
            .filter(NewsArticleModel.external_id == article_id)
            .first()
        )
        return self._article_to_dict(article) if article else None

    def get_sentiment_analysis(
        self, 
        symbol: str, 
        days: int = 30
    ) -> Dict[str, Any]:
        """Get sentiment analysis for a symbol."""
        # Calculate sentiment history
        history = self.news_processor.calculate_entity_sentiment_history(symbol, days)
        
        # Get current sentiment from recent articles
        recent_articles = (
            self.db.query(NewsArticleModel)
            .join(NewsEntityModel)
            .filter(
                NewsEntityModel.symbol == symbol,
                NewsArticleModel.published_at >= datetime.now() - timedelta(hours=24)
            )
            .all()
        )
        
        current_sentiment = 0.0
        if recent_articles:
            sentiments = [
                a.sentiment.sentiment_score for a in recent_articles if a.sentiment
            ]
            current_sentiment = self.sentiment_analyzer.calculate_aggregate_sentiment(sentiments)

        # Classify trend
        sentiment_history = [(datetime.fromisoformat(h['date']), h['sentiment_score']) for h in history]
        trend = self.sentiment_analyzer.classify_sentiment_trend(sentiment_history)

        return {
            "symbol": symbol,
            "current_sentiment": current_sentiment,
            "sentiment_trend": trend,
            "history": history,
            "total_articles": sum(h['article_count'] for h in history)
        }

    def get_trending_entities(
        self, 
        entity_type: Optional[str] = None, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get trending entities from news."""
        # Get recent articles
        recent_articles = (
            self.db.query(NewsArticleModel)
            .filter(NewsArticleModel.published_at >= datetime.now() - timedelta(days=7))
            .all()
        )
        
        # Convert to dict format
        articles_data = [self._article_to_dict(a) for a in recent_articles]
        
        # Use aggregator to find trending
        aggregated = self.news_aggregator.aggregate_by_symbol(
            articles_data,
            self._get_known_symbols().keys()
        )
        
        # Calculate trending scores
        trending = []
        for symbol, symbol_articles in aggregated.items():
            if len(symbol_articles) < 2:
                continue
            
            # Calculate metrics
            sentiment_scores = []
            for article in symbol_articles:
                if article.get('sentiment'):
                    sentiment_scores.append(article['sentiment']['sentiment_score'])
            
            avg_sentiment = self.sentiment_analyzer.calculate_aggregate_sentiment(sentiment_scores)
            
            # Get most recent article time
            recent_time = max(
                datetime.fromisoformat(a['published_at'].replace('Z', '+00:00'))
                for a in symbol_articles
            )
            recency_hours = (datetime.now() - recent_time).total_seconds() / 3600
            
            # Calculate trending score
            score = self.news_aggregator.calculate_trending_score(
                len(symbol_articles),
                avg_sentiment,
                recency_hours
            )
            
            trending.append({
                'symbol': symbol,
                'name': self._get_known_symbols().get(symbol, symbol),
                'article_count': len(symbol_articles),
                'average_sentiment': avg_sentiment,
                'trend_score': score
            })
        
        # Sort by trend score and return top results
        trending.sort(key=lambda x: x['trend_score'], reverse=True)
        return trending[:limit]

    def refresh_news(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """Refresh news data for specified symbols."""
        if not symbols:
            # Get top assets by default
            symbols = (
                self.db.query(Asset.symbol)
                .limit(10)
                .all()
            )
            symbols = [s[0] for s in symbols]

        articles_processed = 0
        errors = []

        for symbol in symbols:
            try:
                # Fetch from provider
                news_data = self.provider.fetch_news(
                    NewsSearchParams(symbols=[symbol], limit=20)
                )
                
                if news_data and news_data.get("data"):
                    # Process articles
                    processed = self.news_processor.process_batch(
                        news_data["data"],
                        extract_entities=True,
                        analyze_sentiment=True
                    )
                    
                    # Store in database
                    for article in processed:
                        result = self.news_processor.store_processed_article(article)
                        if result:
                            articles_processed += 1
                            
            except Exception as e:
                logger.error(f"Failed to refresh news for {symbol}: {e}")
                errors.append(f"{symbol}: {str(e)}")

        return {
            "status": "completed" if not errors else "partial",
            "articles_processed": articles_processed,
            "symbols_refreshed": len(symbols) - len(errors),
            "errors": errors
        }

    def _fetch_and_store_news(self, symbols: List[str], limit: int):
        """Fetch and store news from provider."""
        for symbol in symbols:
            try:
                news_data = self.provider.fetch_news(
                    NewsSearchParams(symbols=[symbol], limit=limit)
                )
                
                if news_data and news_data.get("data"):
                    processed = self.news_processor.process_batch(
                        news_data["data"],
                        extract_entities=True,
                        analyze_sentiment=True
                    )
                    
                    for article in processed:
                        self.news_processor.store_processed_article(article)
                        
            except Exception as e:
                logger.error(f"Failed to fetch news for {symbol}: {e}")

    def _article_to_dict(self, article: NewsArticleModel) -> Dict[str, Any]:
        """Convert article model to dictionary."""
        if not article:
            return None

        result = {
            "id": article.external_id,
            "title": article.title,
            "description": article.description,
            "url": article.url,
            "published_at": article.published_at.isoformat() if article.published_at else None,
            "source": {
                "name": article.source.name if article.source else None,
                "url": article.source.url if article.source else None
            }
        }

        # Add sentiment if available
        if article.sentiment:
            result["sentiment"] = {
                "sentiment_score": article.sentiment.sentiment_score,
                "sentiment_label": article.sentiment.sentiment_label,
                "confidence": article.sentiment.confidence
            }

        # Add entities if available
        if article.entities:
            result["entities"] = [
                {
                    "symbol": entity.symbol,
                    "name": entity.name,
                    "type": entity.type,
                    "mentions": entity.mentions
                }
                for entity in article.entities
            ]

        return result