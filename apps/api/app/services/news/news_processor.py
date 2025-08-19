"""
Main news processing orchestrator module.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from ..news import NewsArticle as NewsArticleModel
from ..news import NewsSentiment as NewsSentimentModel
from ..news import NewsEntity as NewsEntityModel
from ..news import NewsSource as NewsSourceModel
from .sentiment_analyzer import SentimentAnalyzer
from .entity_extractor import EntityExtractor, ExtractedEntity

logger = logging.getLogger(__name__)


class NewsProcessor:
    """Orchestrates news processing pipeline."""

    def __init__(self, db: Session, known_symbols: Optional[Dict[str, str]] = None):
        """
        Initialize news processor.
        
        Args:
            db: Database session
            known_symbols: Dict mapping symbols to company names
        """
        self.db = db
        self.sentiment_analyzer = SentimentAnalyzer()
        self.entity_extractor = EntityExtractor(known_symbols)

    def process_article(
        self,
        article_data: Dict[str, Any],
        extract_entities: bool = True,
        analyze_sentiment: bool = True
    ) -> Dict[str, Any]:
        """
        Process a single news article.
        
        Args:
            article_data: Raw article data
            extract_entities: Whether to extract entities
            analyze_sentiment: Whether to analyze sentiment
            
        Returns:
            Processed article data
        """
        processed = article_data.copy()
        
        # Extract entities if requested
        if extract_entities:
            entities = self.entity_extractor.extract_entities(
                text=article_data.get('description', '') + ' ' + article_data.get('content', ''),
                title=article_data.get('title')
            )
            processed['entities'] = [self._entity_to_dict(e) for e in entities]
        
        # Analyze sentiment if requested
        if analyze_sentiment:
            sentiment_result = self.sentiment_analyzer.analyze_article_sentiment(
                title=article_data.get('title'),
                description=article_data.get('description'),
                content=article_data.get('content')
            )
            processed['sentiment'] = sentiment_result
        
        return processed

    def process_batch(
        self,
        articles: List[Dict[str, Any]],
        extract_entities: bool = True,
        analyze_sentiment: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Process a batch of articles.
        
        Args:
            articles: List of raw article data
            extract_entities: Whether to extract entities
            analyze_sentiment: Whether to analyze sentiment
            
        Returns:
            List of processed articles
        """
        processed_articles = []
        
        for article in articles:
            try:
                processed = self.process_article(
                    article,
                    extract_entities=extract_entities,
                    analyze_sentiment=analyze_sentiment
                )
                processed_articles.append(processed)
            except Exception as e:
                logger.error(f"Failed to process article {article.get('id')}: {e}")
                # Add article anyway but mark as processing failed
                article['processing_error'] = str(e)
                processed_articles.append(article)
        
        return processed_articles

    def store_processed_article(
        self,
        processed_article: Dict[str, Any]
    ) -> Optional[NewsArticleModel]:
        """
        Store processed article in database.
        
        Args:
            processed_article: Processed article data
            
        Returns:
            Stored article model or None if failed
        """
        try:
            # Check if article already exists
            existing = self.db.query(NewsArticleModel).filter(
                NewsArticleModel.external_id == processed_article.get('id')
            ).first()
            
            if existing:
                logger.debug(f"Article {processed_article.get('id')} already exists")
                return existing
            
            # Get or create source
            source_data = processed_article.get('source', {})
            source = self._get_or_create_source(
                source_data.get('name', 'Unknown'),
                source_data.get('url')
            )
            
            # Create article
            article = NewsArticleModel(
                external_id=processed_article.get('id'),
                title=processed_article.get('title'),
                description=processed_article.get('description'),
                content=processed_article.get('content'),
                url=processed_article.get('url'),
                image_url=processed_article.get('image_url'),
                published_at=self._parse_datetime(processed_article.get('published_at')),
                source_id=source.id,
                raw_data=processed_article
            )
            self.db.add(article)
            self.db.flush()
            
            # Store sentiment if available
            sentiment_data = processed_article.get('sentiment')
            if sentiment_data:
                sentiment = NewsSentimentModel(
                    article_id=article.id,
                    sentiment_score=sentiment_data.get('sentiment_score', 0),
                    sentiment_label=sentiment_data.get('sentiment_label', 'neutral'),
                    confidence=sentiment_data.get('confidence', 0)
                )
                self.db.add(sentiment)
            
            # Store entities if available
            for entity_data in processed_article.get('entities', []):
                entity = NewsEntityModel(
                    article_id=article.id,
                    symbol=entity_data.get('symbol'),
                    name=entity_data.get('name'),
                    type=entity_data.get('type'),
                    sentiment_score=entity_data.get('sentiment_score'),
                    mentions=entity_data.get('mentions', 1)
                )
                self.db.add(entity)
            
            self.db.commit()
            return article
            
        except Exception as e:
            logger.error(f"Failed to store article: {e}")
            self.db.rollback()
            return None

    def _get_or_create_source(
        self,
        name: str,
        url: Optional[str] = None
    ) -> NewsSourceModel:
        """Get or create news source."""
        source = self.db.query(NewsSourceModel).filter(
            NewsSourceModel.name == name
        ).first()
        
        if not source:
            source = NewsSourceModel(
                name=name,
                url=url,
                is_trusted=True  # Default to trusted, can be updated later
            )
            self.db.add(source)
            self.db.flush()
        
        return source

    def _entity_to_dict(self, entity: ExtractedEntity) -> Dict[str, Any]:
        """Convert ExtractedEntity to dictionary."""
        return {
            'symbol': entity.symbol,
            'name': entity.name,
            'type': entity.type,
            'mentions': entity.mentions,
            'context': entity.context[:3] if entity.context else [],  # Limit context
            'sentiment_score': entity.sentiment_score
        }

    def _parse_datetime(self, date_str: Any) -> Optional[datetime]:
        """Parse datetime from various formats."""
        if not date_str:
            return None
        
        if isinstance(date_str, datetime):
            return date_str
        
        if isinstance(date_str, str):
            try:
                # Try ISO format
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except:
                try:
                    # Try other common formats
                    from dateutil import parser
                    return parser.parse(date_str)
                except:
                    logger.warning(f"Could not parse date: {date_str}")
                    return None
        
        return None

    def calculate_entity_sentiment_history(
        self,
        symbol: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Calculate sentiment history for an entity.
        
        Args:
            symbol: Entity symbol
            days: Number of days of history
            
        Returns:
            List of daily sentiment data
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Query articles with this entity
        articles = (
            self.db.query(NewsArticleModel)
            .join(NewsEntityModel)
            .filter(
                NewsEntityModel.symbol == symbol,
                NewsArticleModel.published_at >= start_date
            )
            .all()
        )
        
        # Group by day and calculate sentiment
        daily_sentiments = {}
        
        for article in articles:
            date_key = article.published_at.date()
            
            if date_key not in daily_sentiments:
                daily_sentiments[date_key] = {
                    'scores': [],
                    'positive': 0,
                    'negative': 0,
                    'neutral': 0,
                    'count': 0
                }
            
            day_data = daily_sentiments[date_key]
            
            # Get sentiment
            if article.sentiment:
                score = article.sentiment.sentiment_score
                label = article.sentiment.sentiment_label
                
                day_data['scores'].append(score)
                day_data['count'] += 1
                
                if label == 'positive':
                    day_data['positive'] += 1
                elif label == 'negative':
                    day_data['negative'] += 1
                else:
                    day_data['neutral'] += 1
        
        # Calculate daily averages
        history = []
        for date, data in sorted(daily_sentiments.items()):
            history.append({
                'date': date.isoformat(),
                'sentiment_score': sum(data['scores']) / len(data['scores']) if data['scores'] else 0,
                'article_count': data['count'],
                'positive_count': data['positive'],
                'negative_count': data['negative'],
                'neutral_count': data['neutral']
            })
        
        return history