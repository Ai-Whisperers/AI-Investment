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

logger = logging.getLogger(__name__)


class NewsService:
    """Service for managing news data and sentiment analysis."""

    def __init__(self, db: Session):
        self.db = db
        self.provider = MarketauxProvider()
        self.redis_client = get_redis_client()

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
            # Join with entities to filter by symbols
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

            # Re-query to get fresh data
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

        if not article:
            # Try to fetch from provider
            provider_article = self.provider.get_article(article_id)
            if provider_article:
                article = self._store_article(provider_article)

        return self._article_to_dict(article) if article else None

    def get_similar_articles(
        self, article_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get similar articles."""
        # Try provider first
        try:
            similar = self.provider.get_similar_articles(article_id, limit)

            # Store in database
            for article_data in similar:
                self._store_article(article_data)

            return [article.to_dict() for article in similar]
        except Exception as e:
            logger.error(f"Failed to get similar articles: {e}")

            # Fallback to database search based on entities
            base_article = (
                self.db.query(NewsArticleModel)
                .filter(NewsArticleModel.external_id == article_id)
                .first()
            )

            if not base_article:
                return []

            # Find articles with similar entities
            entity_symbols = [e.symbol for e in base_article.entities if e.symbol]

            if entity_symbols:
                similar_articles = (
                    self.db.query(NewsArticleModel)
                    .join(NewsEntityModel)
                    .filter(
                        NewsEntityModel.symbol.in_(entity_symbols),
                        NewsArticleModel.id != base_article.id,
                    )
                    .order_by(desc(NewsArticleModel.published_at))
                    .limit(limit)
                    .all()
                )

                return [self._article_to_dict(article) for article in similar_articles]

            return []

    def get_entity_sentiment(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get sentiment analysis for an entity over time."""

        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # Get sentiment history
        history = (
            self.db.query(EntitySentimentHistory)
            .filter(
                EntitySentimentHistory.symbol == symbol,
                EntitySentimentHistory.date >= start_date,
                EntitySentimentHistory.date <= end_date,
            )
            .order_by(EntitySentimentHistory.date)
            .all()
        )

        # If no history, calculate from articles
        if not history:
            history = self._calculate_sentiment_history(symbol, start_date, end_date)

        # Get current sentiment
        recent_articles = (
            self.db.query(NewsArticleModel)
            .join(NewsEntityModel)
            .filter(
                NewsEntityModel.symbol == symbol,
                NewsArticleModel.published_at >= end_date - timedelta(days=1),
            )
            .all()
        )

        current_sentiment = 0.0
        if recent_articles:
            sentiments = [
                a.sentiment.sentiment_score for a in recent_articles if a.sentiment
            ]
            current_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0

        # Calculate averages
        total_articles = sum(h.article_count for h in history)
        average_sentiment = sum(
            h.sentiment_score * h.article_count for h in history
        ) / max(total_articles, 1)

        # Get top sources
        top_sources = (
            self.db.query(
                NewsSourceModel.name, func.count(NewsArticleModel.id).label("count")
            )
            .join(NewsArticleModel)
            .join(NewsEntityModel)
            .filter(
                NewsEntityModel.symbol == symbol,
                NewsArticleModel.published_at >= start_date,
            )
            .group_by(NewsSourceModel.name)
            .order_by(desc("count"))
            .limit(5)
            .all()
        )

        return {
            "symbol": symbol,
            "current_sentiment": current_sentiment,
            "average_sentiment": average_sentiment,
            "total_articles": total_articles,
            "sentiment_trend": [
                {
                    "date": h.date,
                    "sentiment_score": h.sentiment_score,
                    "article_count": h.article_count,
                    "positive_count": h.positive_count,
                    "negative_count": h.negative_count,
                    "neutral_count": h.neutral_count,
                }
                for h in history
            ],
            "top_sources": [
                {"name": source.name, "count": source.count} for source in top_sources
            ],
        }

    def get_trending_entities(
        self, entity_type: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get trending entities from news."""

        # Try provider first
        try:
            trending = self.provider.get_trending_entities(entity_type, limit)
            return trending
        except Exception as e:
            logger.error(f"Failed to get trending from provider: {e}")

        # Fallback to database
        query = self.db.query(
            NewsEntityModel.symbol,
            NewsEntityModel.name,
            NewsEntityModel.type,
            func.count(NewsEntityModel.id).label("mention_count"),
            func.avg(NewsEntityModel.sentiment_score).label("avg_sentiment"),
        ).filter(NewsEntityModel.created_at >= datetime.now() - timedelta(days=7))

        if entity_type:
            query = query.filter(NewsEntityModel.type == entity_type)

        trending = (
            query.group_by(
                NewsEntityModel.symbol, NewsEntityModel.name, NewsEntityModel.type
            )
            .order_by(desc("mention_count"))
            .limit(limit)
            .all()
        )

        return [
            {
                "symbol": t.symbol,
                "name": t.name,
                "type": t.type,
                "mention_count": t.mention_count,
                "average_sentiment": t.avg_sentiment or 0.0,
                "article_count": t.mention_count,
                "trend_score": t.mention_count * (1 + (t.avg_sentiment or 0)),
            }
            for t in trending
        ]

    def refresh_news(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """Refresh news data for specified symbols."""

        if not symbols:
            # Get all active asset symbols
            assets = self.db.query(Asset).all()
            symbols = [a.symbol for a in assets]

        articles_fetched = 0

        for symbol in symbols:
            try:
                count = self._fetch_and_store_news([symbol], limit=20)
                articles_fetched += count
            except Exception as e:
                logger.error(f"Failed to refresh news for {symbol}: {e}")

        return {"articles_fetched": articles_fetched, "symbols_processed": len(symbols)}

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about news data."""

        total_articles = self.db.query(func.count(NewsArticleModel.id)).scalar()
        total_sources = self.db.query(func.count(NewsSourceModel.id)).scalar()

        # Articles by sentiment
        sentiment_stats = (
            self.db.query(
                NewsSentimentModel.sentiment_label,
                func.count(NewsSentimentModel.id).label("count"),
            )
            .group_by(NewsSentimentModel.sentiment_label)
            .all()
        )

        # Recent activity
        recent_count = (
            self.db.query(func.count(NewsArticleModel.id))
            .filter(NewsArticleModel.published_at >= datetime.now() - timedelta(days=1))
            .scalar()
        )

        return {
            "total_articles": total_articles,
            "total_sources": total_sources,
            "articles_last_24h": recent_count,
            "sentiment_distribution": {
                s.sentiment_label: s.count for s in sentiment_stats
            },
        }

    def _fetch_and_store_news(self, symbols: List[str], limit: int = 50) -> int:
        """Fetch news from provider and store in database."""

        params = NewsSearchParams(
            symbols=symbols,
            limit=limit,
            published_after=datetime.now() - timedelta(days=7),
        )

        articles = self.provider.search_news(params)

        stored_count = 0
        for article in articles:
            if self._store_article(article):
                stored_count += 1

        self.db.commit()

        return stored_count

    def _store_article(self, article_data) -> Optional[NewsArticleModel]:
        """Store article in database."""

        # Check if already exists
        existing = (
            self.db.query(NewsArticleModel)
            .filter(NewsArticleModel.external_id == article_data.uuid)
            .first()
        )

        if existing:
            return existing

        try:
            # Get or create source
            source = self._get_or_create_source(article_data.source)

            # Create article
            article = NewsArticleModel(
                external_id=article_data.uuid,
                title=article_data.title,
                description=article_data.description,
                content=article_data.content,
                url=article_data.url,
                image_url=article_data.image_url,
                source_id=source.id if source else None,
                source_name=article_data.source,
                language=article_data.language,
                country=article_data.country,
                published_at=article_data.published_at,
                categories=article_data.categories,
                keywords=article_data.keywords,
            )

            self.db.add(article)
            self.db.flush()

            # Add sentiment
            if article_data.sentiment:
                sentiment = NewsSentimentModel(
                    article_id=article.id,
                    sentiment_score=article_data.sentiment.score,
                    sentiment_label=article_data.sentiment.label.value,
                    confidence=article_data.sentiment.confidence,
                    provider="marketaux",
                )
                self.db.add(sentiment)

            # Add entities
            for entity_data in article_data.entities:
                entity = NewsEntityModel(
                    article_id=article.id,
                    symbol=entity_data.symbol,
                    name=entity_data.name,
                    type=entity_data.type,
                    exchange=entity_data.exchange,
                    country=entity_data.country,
                    industry=entity_data.industry,
                    match_score=entity_data.match_score,
                    sentiment_score=entity_data.sentiment_score,
                )
                self.db.add(entity)

                # Link to asset if exists
                if entity_data.symbol:
                    asset = (
                        self.db.query(Asset)
                        .filter(Asset.symbol == entity_data.symbol)
                        .first()
                    )

                    if asset:
                        # Add to association table
                        self.db.execute(
                            asset_news_association.insert().values(
                                asset_id=asset.id,
                                article_id=article.id,
                                relevance_score=entity_data.match_score,
                                sentiment_score=entity_data.sentiment_score,
                            )
                        )

            return article

        except Exception as e:
            logger.error(f"Failed to store article: {e}")
            self.db.rollback()
            return None

    def _get_or_create_source(self, source_name: str) -> Optional[NewsSourceModel]:
        """Get or create news source."""

        source = (
            self.db.query(NewsSourceModel)
            .filter(NewsSourceModel.name == source_name)
            .first()
        )

        if not source:
            source = NewsSourceModel(name=source_name)
            self.db.add(source)
            self.db.flush()

        return source

    def _calculate_sentiment_history(
        self, symbol: str, start_date: datetime, end_date: datetime
    ) -> List[EntitySentimentHistory]:
        """Calculate sentiment history from articles."""

        # Group articles by day
        articles = (
            self.db.query(NewsArticleModel)
            .join(NewsEntityModel)
            .filter(
                NewsEntityModel.symbol == symbol,
                NewsArticleModel.published_at >= start_date,
                NewsArticleModel.published_at <= end_date,
            )
            .all()
        )

        # Group by date
        from collections import defaultdict

        daily_data = defaultdict(list)

        for article in articles:
            date_key = article.published_at.date()
            if article.sentiment:
                daily_data[date_key].append(article.sentiment.sentiment_score)

        # Create history records
        history = []
        for date_key, sentiments in daily_data.items():
            if sentiments:
                avg_sentiment = sum(sentiments) / len(sentiments)
                positive = len([s for s in sentiments if s > 0.2])
                negative = len([s for s in sentiments if s < -0.2])
                neutral = len(sentiments) - positive - negative

                hist = EntitySentimentHistory(
                    symbol=symbol,
                    date=datetime.combine(date_key, datetime.min.time()),
                    sentiment_score=avg_sentiment,
                    article_count=len(sentiments),
                    positive_count=positive,
                    negative_count=negative,
                    neutral_count=neutral,
                )

                self.db.add(hist)
                history.append(hist)

        self.db.commit()

        return history

    def _article_to_dict(
        self, article: Optional[NewsArticleModel]
    ) -> Optional[Dict[str, Any]]:
        """Convert article model to dictionary."""

        if not article:
            return None

        return {
            "id": article.external_id or str(article.id),
            "title": article.title,
            "description": article.description,
            "content": article.content,
            "url": article.url,
            "source": article.source_name,
            "published_at": article.published_at,
            "image_url": article.image_url,
            "language": article.language,
            "country": article.country,
            "categories": article.categories or [],
            "keywords": article.keywords or [],
            "entities": [
                {
                    "symbol": e.symbol,
                    "name": e.name,
                    "type": e.type,
                    "sentiment_score": e.sentiment_score,
                }
                for e in article.entities
            ],
            "sentiment": (
                {
                    "score": article.sentiment.sentiment_score,
                    "label": article.sentiment.sentiment_label,
                    "confidence": article.sentiment.confidence,
                }
                if article.sentiment
                else None
            ),
        }
