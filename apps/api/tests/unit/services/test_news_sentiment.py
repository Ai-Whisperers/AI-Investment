"""
Unit tests for news sentiment analysis module.
"""

import pytest
from app.services.news_modules.sentiment_analyzer import SentimentAnalyzer


@pytest.mark.unit
class TestSentimentAnalyzer:
    """Test sentiment analysis functionality."""
    
    @pytest.fixture
    def analyzer(self):
        """Create a sentiment analyzer instance."""
        return SentimentAnalyzer()
    
    def test_calculate_sentiment_score_positive(self, analyzer):
        """Test sentiment scoring for positive text."""
        text = "The stock market shows strong growth and bullish momentum with record profits"
        score, label = analyzer.calculate_sentiment_score(text)
        
        assert score > 0.2
        assert label == 'positive'
        assert -1.0 <= score <= 1.0
    
    def test_calculate_sentiment_score_negative(self, analyzer):
        """Test sentiment scoring for negative text."""
        text = "Market crash fears rise as stocks plunge amid weak earnings and concerns"
        score, label = analyzer.calculate_sentiment_score(text)
        
        assert score < -0.2
        assert label == 'negative'
        assert -1.0 <= score <= 1.0
    
    def test_calculate_sentiment_score_neutral(self, analyzer):
        """Test sentiment scoring for neutral text."""
        text = "The market remains unchanged and stable with steady trading volume"
        score, label = analyzer.calculate_sentiment_score(text)
        
        assert -0.2 <= score <= 0.2
        assert label == 'neutral'
    
    def test_calculate_sentiment_score_empty_text(self, analyzer):
        """Test sentiment scoring with empty text."""
        score, label = analyzer.calculate_sentiment_score("")
        
        assert score == 0.0
        assert label == 'neutral'
    
    def test_calculate_sentiment_score_no_sentiment_words(self, analyzer):
        """Test sentiment scoring with text containing no sentiment words."""
        text = "The company announced their quarterly report today"
        score, label = analyzer.calculate_sentiment_score(text)
        
        assert score == 0.0
        assert label == 'neutral'
    
    def test_analyze_article_sentiment_complete(self, analyzer):
        """Test complete article sentiment analysis."""
        result = analyzer.analyze_article_sentiment(
            title="Tech Stocks Surge to Record Highs",
            description="Major technology companies beat earnings expectations",
            content="Apple and Microsoft reported strong quarterly results with significant growth"
        )
        
        assert 'title_sentiment' in result
        assert 'description_sentiment' in result
        assert 'content_sentiment' in result
        assert 'overall_score' in result
        assert 'overall_label' in result
        assert 'confidence' in result
        
        # Should be positive overall
        assert result['overall_score'] > 0
        assert result['overall_label'] == 'positive'
    
    def test_analyze_article_sentiment_title_only(self, analyzer):
        """Test article sentiment with only title."""
        result = analyzer.analyze_article_sentiment(
            title="Market Crash Fears Intensify"
        )
        
        assert result['title_sentiment']['label'] == 'negative'
        assert result['overall_label'] == 'negative'
        assert result['confidence'] <= 0.5  # Low confidence with just title
    
    def test_analyze_article_sentiment_mixed(self, analyzer):
        """Test article sentiment with mixed signals."""
        result = analyzer.analyze_article_sentiment(
            title="Market Shows Mixed Signals",
            description="Gains in tech offset by losses in energy sector",
            content="While technology stocks surge, energy companies face declining profits"
        )
        
        # Should handle mixed sentiment appropriately
        assert 'overall_score' in result
        assert -0.5 <= result['overall_score'] <= 0.5
    
    def test_sentiment_boundary_conditions(self, analyzer):
        """Test sentiment score boundary conditions."""
        # Extremely positive text
        very_positive = " ".join(["bullish surge profit growth"] * 10)
        score, label = analyzer.calculate_sentiment_score(very_positive)
        assert score <= 1.0  # Should be clamped
        assert label == 'positive'
        
        # Extremely negative text
        very_negative = " ".join(["bearish crash loss decline"] * 10)
        score, label = analyzer.calculate_sentiment_score(very_negative)
        assert score >= -1.0  # Should be clamped
        assert label == 'negative'
    
    def test_aggregate_sentiment_multiple_entities(self, analyzer):
        """Test sentiment aggregation for multiple entities."""
        entity_sentiments = [
            {'symbol': 'AAPL', 'score': 0.8, 'label': 'positive'},
            {'symbol': 'GOOGL', 'score': -0.3, 'label': 'negative'},
            {'symbol': 'MSFT', 'score': 0.5, 'label': 'positive'}
        ]
        
        result = analyzer.aggregate_entity_sentiments(entity_sentiments)
        
        assert 'average_score' in result
        assert 'dominant_sentiment' in result
        assert 'positive_count' in result
        assert 'negative_count' in result
        assert 'neutral_count' in result
        
        assert result['positive_count'] == 2
        assert result['negative_count'] == 1
        assert result['dominant_sentiment'] == 'positive'
    
    def test_sentiment_with_special_characters(self, analyzer):
        """Test sentiment analysis with special characters and punctuation."""
        text = "Profits surge!!! Stock SOARS 🚀 #bullish @market"
        score, label = analyzer.calculate_sentiment_score(text)
        
        assert score > 0  # Should still detect positive sentiment
        assert label == 'positive'
    
    def test_case_insensitive_sentiment(self, analyzer):
        """Test that sentiment analysis is case insensitive."""
        text1 = "BULLISH GROWTH PROFIT"
        text2 = "bullish growth profit"
        text3 = "BuLLiSh GrOwTh PrOfIt"
        
        score1, _ = analyzer.calculate_sentiment_score(text1)
        score2, _ = analyzer.calculate_sentiment_score(text2)
        score3, _ = analyzer.calculate_sentiment_score(text3)
        
        # All should have the same score
        assert score1 == score2 == score3