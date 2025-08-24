"""Tests for news processing modules."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import pandas as pd

from app.services.news_modules import (
    NewsProcessor,
    NewsAggregator,
    EntityExtractor,
    SentimentAnalyzer
)


class TestNewsProcessor:
    """Test suite for NewsProcessor."""

    @patch('app.services.news_modules.news_processor.NewsAggregator')
    @patch('app.services.news_modules.news_processor.EntityExtractor')
    def test_process_news_success(self, mock_extractor_class, mock_aggregator_class):
        """Test successful news processing."""
        # Setup mocks
        mock_aggregator = Mock()
        mock_aggregator_class.return_value = mock_aggregator
        
        mock_news_data = [
            {
                'title': 'Tech stocks surge',
                'description': 'Major tech companies report strong earnings',
                'published_at': '2024-01-15T10:00:00Z',
                'url': 'https://example.com/news1'
            },
            {
                'title': 'Market volatility increases',
                'description': 'Investors concerned about inflation',
                'published_at': '2024-01-15T11:00:00Z',
                'url': 'https://example.com/news2'
            }
        ]
        mock_aggregator.aggregate_news.return_value = mock_news_data
        
        mock_extractor = Mock()
        mock_extractor_class.return_value = mock_extractor
        mock_extractor.extract_entities.return_value = {
            'sentiment': 'neutral',
            'relevance_score': 0.75,
            'key_entities': ['AAPL', 'GOOGL', 'MSFT']
        }
        
        # Create processor
        processor = NewsProcessor()
        
        # Execute
        result = processor.process_news(['AAPL', 'GOOGL'])
        
        # Verify
        assert 'news_items' in result
        assert 'analysis' in result
        assert len(result['news_items']) == 2
        mock_fetcher.fetch_news.assert_called_once()
        mock_analyzer.analyze.assert_called()

    @patch('app.services.news_modules.news_processor.NewsFetcher')
    def test_process_news_no_data(self, mock_fetcher_class):
        """Test news processing with no data."""
        # Setup mock
        mock_fetcher = Mock()
        mock_fetcher_class.return_value = mock_fetcher
        mock_fetcher.fetch_news.return_value = []
        
        # Create processor
        processor = NewsProcessor()
        
        # Execute
        result = processor.process_news(['AAPL'])
        
        # Verify
        assert result == {'news_items': [], 'analysis': None}
        mock_fetcher.fetch_news.assert_called_once()

    def test_filter_by_date(self):
        """Test news filtering by date."""
        processor = NewsProcessor()
        
        news_items = [
            {
                'title': 'Old news',
                'published_at': '2024-01-01T10:00:00Z'
            },
            {
                'title': 'Recent news',
                'published_at': datetime.now().isoformat()
            }
        ]
        
        # Filter for last 7 days
        filtered = processor.filter_by_date(news_items, days=7)
        
        assert len(filtered) == 1
        assert filtered[0]['title'] == 'Recent news'


class TestNewsFetcher:
    """Test suite for NewsFetcher."""

    @patch('app.services.news_modules.news_fetcher.requests')
    def test_fetch_news_success(self, mock_requests):
        """Test successful news fetching."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {
                    'title': 'Market Update',
                    'description': 'Daily market summary',
                    'published_at': '2024-01-15T10:00:00Z',
                    'url': 'https://example.com/news'
                }
            ]
        }
        mock_requests.get.return_value = mock_response
        
        # Create fetcher
        fetcher = NewsFetcher(api_key='test_key')
        
        # Execute
        result = fetcher.fetch_news(symbols=['AAPL'])
        
        # Verify
        assert len(result) == 1
        assert result[0]['title'] == 'Market Update'
        mock_requests.get.assert_called_once()

    @patch('app.services.news_modules.news_fetcher.requests')
    def test_fetch_news_api_error(self, mock_requests):
        """Test news fetching with API error."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_requests.get.return_value = mock_response
        
        # Create fetcher
        fetcher = NewsFetcher(api_key='test_key')
        
        # Execute
        result = fetcher.fetch_news(symbols=['AAPL'])
        
        # Verify
        assert result == []
        mock_requests.get.assert_called_once()

    @patch('app.services.news_modules.news_fetcher.requests')
    def test_fetch_news_with_pagination(self, mock_requests):
        """Test news fetching with pagination."""
        # Setup mock responses for multiple pages
        page1_response = Mock()
        page1_response.status_code = 200
        page1_response.json.return_value = {
            'data': [{'title': f'News {i}'} for i in range(100)],
            'next_page': 'page2_token'
        }
        
        page2_response = Mock()
        page2_response.status_code = 200
        page2_response.json.return_value = {
            'data': [{'title': f'News {i}'} for i in range(100, 150)],
            'next_page': None
        }
        
        mock_requests.get.side_effect = [page1_response, page2_response]
        
        # Create fetcher
        fetcher = NewsFetcher(api_key='test_key')
        
        # Execute
        result = fetcher.fetch_news(symbols=['AAPL'], max_pages=2)
        
        # Verify
        assert len(result) == 150
        assert mock_requests.get.call_count == 2


class TestSentimentAnalyzer:
    """Test suite for SentimentAnalyzer."""

    def test_analyze_sentiment_positive(self):
        """Test positive sentiment analysis."""
        analyzer = SentimentAnalyzer()
        
        text = "Excellent earnings report! Company profits soar. Strong growth expected."
        result = analyzer.analyze_sentiment(text)
        
        assert result['sentiment'] == 'positive'
        assert result['score'] > 0.5

    def test_analyze_sentiment_negative(self):
        """Test negative sentiment analysis."""
        analyzer = SentimentAnalyzer()
        
        text = "Disappointing results. Losses mount. Outlook remains bleak."
        result = analyzer.analyze_sentiment(text)
        
        assert result['sentiment'] == 'negative'
        assert result['score'] < -0.5

    def test_analyze_sentiment_neutral(self):
        """Test neutral sentiment analysis."""
        analyzer = SentimentAnalyzer()
        
        text = "The company reported quarterly results today."
        result = analyzer.analyze_sentiment(text)
        
        assert result['sentiment'] == 'neutral'
        assert -0.5 <= result['score'] <= 0.5

    def test_extract_entities(self):
        """Test entity extraction from text."""
        analyzer = SentimentAnalyzer()
        
        text = "Apple and Microsoft announced partnership with Google."
        entities = analyzer.extract_entities(text)
        
        assert 'AAPL' in entities or 'Apple' in entities
        assert 'MSFT' in entities or 'Microsoft' in entities
        assert 'GOOGL' in entities or 'Google' in entities

    def test_calculate_relevance_score(self):
        """Test relevance score calculation."""
        analyzer = SentimentAnalyzer()
        
        text = "Stock market technology earnings report financial analysis"
        keywords = ['stock', 'market', 'earnings']
        
        score = analyzer.calculate_relevance_score(text, keywords)
        
        assert 0 <= score <= 1
        assert score > 0.5  # High relevance due to keyword matches


class TestNewsAnalyzer:
    """Test suite for NewsAnalyzer."""

    @patch('app.services.news_modules.news_analyzer.SentimentAnalyzer')
    def test_analyze_news_batch(self, mock_sentiment_class):
        """Test batch news analysis."""
        # Setup mock
        mock_sentiment = Mock()
        mock_sentiment_class.return_value = mock_sentiment
        mock_sentiment.analyze_sentiment.return_value = {
            'sentiment': 'positive',
            'score': 0.7
        }
        
        # Create analyzer
        analyzer = NewsAnalyzer()
        
        # Test data
        news_items = [
            {'title': 'News 1', 'description': 'Description 1'},
            {'title': 'News 2', 'description': 'Description 2'}
        ]
        
        # Execute
        result = analyzer.analyze_batch(news_items)
        
        # Verify
        assert 'overall_sentiment' in result
        assert 'sentiment_distribution' in result
        assert 'analyzed_count' in result
        assert result['analyzed_count'] == 2

    def test_aggregate_sentiments(self):
        """Test sentiment aggregation."""
        analyzer = NewsAnalyzer()
        
        sentiments = [
            {'sentiment': 'positive', 'score': 0.8},
            {'sentiment': 'positive', 'score': 0.6},
            {'sentiment': 'negative', 'score': -0.3},
            {'sentiment': 'neutral', 'score': 0.1}
        ]
        
        result = analyzer.aggregate_sentiments(sentiments)
        
        assert result['average_score'] == 0.3
        assert result['dominant_sentiment'] == 'positive'
        assert result['positive_count'] == 2
        assert result['negative_count'] == 1
        assert result['neutral_count'] == 1

    def test_identify_trends(self):
        """Test trend identification in news."""
        analyzer = NewsAnalyzer()
        
        news_items = [
            {'title': 'AI technology breakthrough', 'published_at': '2024-01-15'},
            {'title': 'Another AI advancement', 'published_at': '2024-01-16'},
            {'title': 'AI market growth', 'published_at': '2024-01-17'},
            {'title': 'Unrelated news', 'published_at': '2024-01-18'}
        ]
        
        trends = analyzer.identify_trends(news_items)
        
        assert 'AI' in trends or 'ai' in trends or 'artificial intelligence' in trends
        assert trends[0]['frequency'] >= 3