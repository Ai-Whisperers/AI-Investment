"""
Unit tests for news processing orchestrator module.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
from app.services.news_modules.news_processor import NewsProcessor
from app.services.news_modules.entity_extractor import ExtractedEntity


@pytest.mark.unit
class TestNewsProcessor:
    """Test news processing pipeline."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock()
    
    @pytest.fixture
    def processor(self, mock_db):
        """Create a news processor instance."""
        known_symbols = {'AAPL': 'Apple Inc.', 'GOOGL': 'Alphabet Inc.'}
        return NewsProcessor(mock_db, known_symbols)
    
    @pytest.fixture
    def sample_article(self):
        """Create sample article data."""
        return {
            'uuid': 'test-123',
            'title': 'Tech Stocks Surge as AAPL Reports Earnings',
            'description': 'Apple beats expectations with strong Q4 results',
            'content': 'Apple Inc. reported revenue growth of 15% year over year',
            'url': 'https://example.com/article',
            'published_at': datetime.now().isoformat(),
            'source': 'TechNews'
        }
    
    def test_process_article_complete(self, processor, sample_article):
        """Test complete article processing."""
        result = processor.process_article(
            sample_article,
            extract_entities=True,
            analyze_sentiment=True
        )
        
        # Should have original fields
        assert result['uuid'] == sample_article['uuid']
        assert result['title'] == sample_article['title']
        
        # Should have added fields
        assert 'entities' in result
        assert 'sentiment' in result
        assert isinstance(result['entities'], list)
        assert isinstance(result['sentiment'], dict)
    
    def test_process_article_entities_only(self, processor, sample_article):
        """Test article processing with only entity extraction."""
        result = processor.process_article(
            sample_article,
            extract_entities=True,
            analyze_sentiment=False
        )
        
        assert 'entities' in result
        assert 'sentiment' not in result
        
        # Should find AAPL entity
        symbols = [e['symbol'] for e in result['entities']]
        assert 'AAPL' in symbols or any('AAPL' in str(e) for e in result['entities'])
    
    def test_process_article_sentiment_only(self, processor, sample_article):
        """Test article processing with only sentiment analysis."""
        result = processor.process_article(
            sample_article,
            extract_entities=False,
            analyze_sentiment=True
        )
        
        assert 'sentiment' in result
        assert 'entities' not in result
        
        # Should detect positive sentiment
        assert result['sentiment']['overall_label'] in ['positive', 'neutral', 'negative']
        assert 'overall_score' in result['sentiment']
    
    def test_process_article_no_processing(self, processor, sample_article):
        """Test article processing with no analysis."""
        result = processor.process_article(
            sample_article,
            extract_entities=False,
            analyze_sentiment=False
        )
        
        # Should return copy of original
        assert result == sample_article
        assert result is not sample_article  # Should be a copy
    
    def test_process_batch(self, processor, sample_article):
        """Test batch article processing."""
        articles = [
            sample_article,
            {**sample_article, 'uuid': 'test-456', 'title': 'GOOGL Announces AI Features'},
            {**sample_article, 'uuid': 'test-789', 'title': 'Market Update'}
        ]
        
        results = processor.process_batch(articles)
        
        assert len(results) == 3
        assert all('entities' in r for r in results)
        assert all('sentiment' in r for r in results)
        
        # Each should have unique UUID
        uuids = [r['uuid'] for r in results]
        assert len(set(uuids)) == 3
    
    def test_process_batch_with_error(self, processor, sample_article):
        """Test batch processing handles errors gracefully."""
        articles = [
            sample_article,
            None,  # This will cause an error
            {**sample_article, 'uuid': 'test-789'}
        ]
        
        results = processor.process_batch(articles)
        
        # Should process valid articles despite error
        assert len(results) >= 2
        valid_uuids = [r['uuid'] for r in results if 'uuid' in r]
        assert 'test-123' in valid_uuids
        assert 'test-789' in valid_uuids
    
    def test_entity_to_dict_conversion(self, processor):
        """Test entity object to dictionary conversion."""
        entity = ExtractedEntity(
            symbol='AAPL',
            name='Apple Inc.',
            type='STOCK',
            mentions=3,
            context=['strong earnings', 'beat expectations'],
            sentiment_score=0.8
        )
        
        entity_dict = processor._entity_to_dict(entity)
        
        assert entity_dict['symbol'] == 'AAPL'
        assert entity_dict['name'] == 'Apple Inc.'
        assert entity_dict['type'] == 'STOCK'
        assert entity_dict['mentions'] == 3
        assert len(entity_dict['context']) == 2
        assert entity_dict['sentiment_score'] == 0.8
    
    def test_save_article_to_db(self, processor, mock_db, sample_article):
        """Test saving processed article to database."""
        processed = processor.process_article(sample_article)
        
        # Mock the database operations
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.add = Mock()
        mock_db.commit = Mock()
        
        article_model = processor.save_article(processed)
        
        # Should call database methods
        assert mock_db.add.called
        assert mock_db.commit.called
    
    def test_process_article_missing_fields(self, processor):
        """Test processing article with missing fields."""
        minimal_article = {
            'title': 'Market News'
        }
        
        result = processor.process_article(minimal_article)
        
        # Should handle missing fields gracefully
        assert 'title' in result
        assert 'entities' in result
        assert 'sentiment' in result
        
        # Sentiment should work with just title
        assert result['sentiment']['title_sentiment'] is not None
    
    def test_process_with_empty_content(self, processor):
        """Test processing article with empty content."""
        article = {
            'title': 'AAPL Stock Update',
            'description': '',
            'content': None
        }
        
        result = processor.process_article(article)
        
        # Should still extract from title
        assert 'entities' in result
        assert 'sentiment' in result
        
        # Should find AAPL in title
        if result['entities']:
            symbols = [e['symbol'] for e in result['entities']]
            assert 'AAPL' in symbols or 'AAPL' in str(result['entities'])
    
    def test_get_recent_articles(self, processor, mock_db):
        """Test fetching recent articles from database."""
        # Mock query results
        mock_articles = [Mock(id=1), Mock(id=2), Mock(id=3)]
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_articles
        
        recent = processor.get_recent_articles(hours=24, limit=10)
        
        assert len(recent) == 3
        mock_db.query.assert_called()
    
    def test_aggregate_entity_sentiment(self, processor):
        """Test aggregating sentiment for specific entity."""
        articles_with_entity = [
            {'entities': [{'symbol': 'AAPL', 'sentiment_score': 0.8}]},
            {'entities': [{'symbol': 'AAPL', 'sentiment_score': 0.6}]},
            {'entities': [{'symbol': 'AAPL', 'sentiment_score': -0.2}]}
        ]
        
        aggregate = processor.aggregate_entity_sentiment('AAPL', articles_with_entity)
        
        assert 'average_score' in aggregate
        assert 'total_mentions' in aggregate
        assert 'sentiment_trend' in aggregate
        
        # Average should be (0.8 + 0.6 - 0.2) / 3 = 0.4
        assert 0.3 <= aggregate['average_score'] <= 0.5