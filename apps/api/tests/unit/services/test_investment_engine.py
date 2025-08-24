"""Tests for investment decision engine."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import pandas as pd

from app.services.investment_engine import (
    InvestmentDecisionEngine,
    InvestmentSignal,
    InvestmentRecommendation,
    SignalStrength,
    InvestmentHorizon
)
from app.models import Asset, Price


class TestInvestmentEngine:
    """Test suite for investment decision engine."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def investment_engine(self, mock_db_session):
        """Create an investment engine instance."""
        with patch('app.services.investment_engine.FundamentalAnalysis'), \
             patch('app.services.investment_engine.StrategyService'):
            return InvestmentDecisionEngine(mock_db_session)
    
    @pytest.fixture
    def mock_asset(self):
        """Create a mock asset with test data."""
        asset = Mock(spec=Asset)
        asset.id = 1
        asset.symbol = 'AAPL'
        asset.name = 'Apple Inc.'
        asset.sector = 'Technology'
        asset.market_cap = 3000000000000
        asset.pe_ratio = 25.0
        asset.dividend_yield = 0.5
        asset.esg_score = 75
        asset.volatility_30d = 0.25
        return asset
    
    def test_analyze_investment_opportunity_success(self, investment_engine, mock_db_session, mock_asset):
        """Test successful investment opportunity analysis."""
        # Setup mocks
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_asset
        
        # Mock price data
        mock_prices = [
            Mock(close=150.0, date=datetime.now() - timedelta(days=i))
            for i in range(200)
        ]
        mock_db_session.query(Price).filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_prices
        
        # Mock fundamental analysis
        with patch.object(investment_engine, '_analyze_fundamentals') as mock_fundamentals:
            mock_fundamentals.return_value = InvestmentSignal(
                source='fundamental',
                strength=SignalStrength.BUY,
                confidence=0.8,
                rationale='Good fundamentals'
            )
            
            # Execute
            result = investment_engine.analyze_investment_opportunity('AAPL', InvestmentHorizon.LONG)
        
        # Verify
        assert isinstance(result, InvestmentRecommendation)
        assert result.symbol == 'AAPL'
        assert result.horizon == InvestmentHorizon.LONG
        assert len(result.signals) > 0
    
    def test_analyze_investment_opportunity_asset_not_found(self, investment_engine, mock_db_session):
        """Test analysis when asset is not found."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="Asset INVALID not found"):
            investment_engine.analyze_investment_opportunity('INVALID', InvestmentHorizon.LONG)
    
    def test_analyze_fundamentals_strong_buy(self, investment_engine, mock_asset):
        """Test fundamental analysis generating strong buy signal."""
        # Set favorable fundamentals
        mock_asset.pe_ratio = 12.0
        mock_asset.dividend_yield = 4.0
        mock_asset.esg_score = 85
        
        # Mock health assessment
        with patch.object(investment_engine.fundamental_analyzer, 'get_asset_fundamentals') as mock_get:
            mock_get.return_value = {
                'health_assessment': {'overall': 'excellent'}
            }
            
            signal = investment_engine._analyze_fundamentals(mock_asset)
        
        assert signal is not None
        assert signal.source == 'fundamental'
        assert signal.strength == SignalStrength.STRONG_BUY
        assert signal.confidence > 0.7
    
    def test_analyze_fundamentals_sell_signal(self, investment_engine, mock_asset):
        """Test fundamental analysis generating sell signal."""
        # Set poor fundamentals
        mock_asset.pe_ratio = 50.0
        mock_asset.dividend_yield = 0.0
        mock_asset.esg_score = 30
        
        with patch.object(investment_engine.fundamental_analyzer, 'get_asset_fundamentals') as mock_get:
            mock_get.return_value = {
                'health_assessment': {'overall': 'poor'}
            }
            
            signal = investment_engine._analyze_fundamentals(mock_asset)
        
        assert signal is not None
        assert signal.strength in [SignalStrength.SELL, SignalStrength.STRONG_SELL]
    
    def test_analyze_technicals_oversold(self, investment_engine, mock_asset, mock_db_session):
        """Test technical analysis detecting oversold condition."""
        # Mock price data showing decline
        prices = [Mock(close=100 - i*2, date=datetime.now() - timedelta(days=i)) for i in range(200)]
        mock_db_session.query(Price).filter.return_value.order_by.return_value.limit.return_value.all.return_value = prices
        
        with patch('app.services.investment_engine.TechnicalIndicators') as mock_indicators:
            # Mock RSI showing oversold
            mock_rsi = pd.Series([25] * 200)
            mock_indicators.calculate_rsi.return_value = mock_rsi
            
            # Mock other indicators
            mock_indicators.calculate_macd.return_value = {
                'macd': pd.Series([0.5] * 200),
                'signal': pd.Series([0.3] * 200),
                'histogram': pd.Series([0.2, 0.1] + [0.3] * 198)
            }
            mock_indicators.calculate_bollinger_bands.return_value = {
                'upper': pd.Series([110] * 200),
                'middle': pd.Series([100] * 200),
                'lower': pd.Series([90] * 200)
            }
            mock_indicators.calculate_sma.return_value = pd.Series([100] * 200)
            
            signal = investment_engine._analyze_technicals(mock_asset)
        
        assert signal is not None
        assert signal.strength in [SignalStrength.BUY, SignalStrength.STRONG_BUY]
        assert 'Oversold' in signal.rationale
    
    def test_analyze_sentiment(self, investment_engine, mock_asset):
        """Test sentiment analysis."""
        mock_asset.sector = 'Technology'
        mock_asset.market_cap = 50000000000
        
        signal = investment_engine._analyze_sentiment(mock_asset)
        
        assert signal is not None
        assert signal.source == 'sentiment'
        assert signal.strength == SignalStrength.BUY  # Tech sector is bullish
    
    def test_analyze_momentum_positive(self, investment_engine, mock_asset, mock_db_session):
        """Test momentum analysis with positive trend."""
        # Mock prices showing upward trend
        prices = [
            Mock(close=100 + i*0.5, date=datetime.now() - timedelta(days=60-i))
            for i in range(60)
        ]
        mock_db_session.query(Price).filter.return_value.order_by.return_value.limit.return_value.all.return_value = prices
        
        signal = investment_engine._analyze_momentum(mock_asset)
        
        assert signal is not None
        assert signal.source == 'momentum'
        assert signal.strength in [SignalStrength.BUY, SignalStrength.HOLD]
    
    def test_analyze_risk_low_volatility(self, investment_engine, mock_asset):
        """Test risk analysis with low volatility."""
        mock_asset.volatility_30d = 0.15
        mock_asset.pe_ratio = 20
        
        signal = investment_engine._analyze_risk(mock_asset)
        
        assert signal is not None
        assert signal.source == 'risk'
        assert signal.strength == SignalStrength.BUY
        assert 'Low volatility' in signal.rationale
    
    def test_analyze_risk_high_volatility(self, investment_engine, mock_asset):
        """Test risk analysis with high volatility."""
        mock_asset.volatility_30d = 0.6
        mock_asset.pe_ratio = 45
        
        signal = investment_engine._analyze_risk(mock_asset)
        
        assert signal is not None
        assert 'High volatility' in str(signal.data_points.get('risk_factors', []))
    
    def test_aggregate_signals_strong_buy(self, investment_engine, mock_asset):
        """Test signal aggregation resulting in strong buy."""
        signals = [
            InvestmentSignal('fundamental', SignalStrength.STRONG_BUY, 0.9, 'Great fundamentals'),
            InvestmentSignal('technical', SignalStrength.BUY, 0.7, 'Oversold'),
            InvestmentSignal('sentiment', SignalStrength.BUY, 0.6, 'Positive sentiment'),
            InvestmentSignal('momentum', SignalStrength.BUY, 0.5, 'Upward trend'),
            InvestmentSignal('risk', SignalStrength.BUY, 0.8, 'Low risk')
        ]
        
        # Mock price
        with patch.object(investment_engine.db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.order_by.return_value.first.return_value = Mock(close=100)
            
            recommendation = investment_engine._aggregate_signals(
                mock_asset,
                signals,
                InvestmentHorizon.LONG
            )
        
        assert recommendation.action == SignalStrength.STRONG_BUY
        assert recommendation.investment_score > 70
        assert recommendation.target_allocation > 0
    
    def test_aggregate_signals_hold(self, investment_engine, mock_asset):
        """Test signal aggregation resulting in hold."""
        signals = [
            InvestmentSignal('fundamental', SignalStrength.HOLD, 0.5, 'Neutral'),
            InvestmentSignal('technical', SignalStrength.SELL, 0.6, 'Overbought'),
            InvestmentSignal('sentiment', SignalStrength.BUY, 0.4, 'Mixed'),
            InvestmentSignal('momentum', SignalStrength.HOLD, 0.5, 'Sideways'),
            InvestmentSignal('risk', SignalStrength.HOLD, 0.5, 'Moderate risk')
        ]
        
        with patch.object(investment_engine.db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.order_by.return_value.first.return_value = Mock(close=100)
            
            recommendation = investment_engine._aggregate_signals(
                mock_asset,
                signals,
                InvestmentHorizon.MEDIUM
            )
        
        assert recommendation.action == SignalStrength.HOLD
        assert recommendation.target_allocation == 0
    
    def test_generate_rationale(self, investment_engine, mock_asset):
        """Test investment rationale generation."""
        signals = [
            InvestmentSignal('fundamental', SignalStrength.BUY, 0.8, 'Strong earnings growth'),
            InvestmentSignal('technical', SignalStrength.BUY, 0.7, 'Breaking resistance')
        ]
        
        rationale = investment_engine._generate_rationale(
            mock_asset,
            signals,
            SignalStrength.BUY,
            75.0
        )
        
        assert 'Buy recommendation' in rationale
        assert 'AAPL' in rationale
        assert '75%' in rationale
    
    def test_identify_risks(self, investment_engine, mock_asset):
        """Test risk identification."""
        mock_asset.pe_ratio = 40
        mock_asset.volatility_30d = 0.5
        mock_asset.dividend_yield = 0
        
        signals = [
            InvestmentSignal(
                'risk',
                SignalStrength.HOLD,
                0.5,
                'High risk',
                {'risk_factors': ['Market volatility', 'Sector rotation']}
            )
        ]
        
        risks = investment_engine._identify_risks(mock_asset, signals)
        
        assert 'High valuation multiple' in risks
        assert 'High price volatility' in risks
        assert 'No significant dividend support' in risks
        assert 'Market volatility' in risks
    
    def test_identify_catalysts(self, investment_engine, mock_asset):
        """Test catalyst identification."""
        mock_asset.sector = 'Technology'
        mock_asset.esg_score = 85
        
        signals = [
            InvestmentSignal('technical', SignalStrength.BUY, 0.7, 'Oversold conditions'),
            InvestmentSignal('fundamental', SignalStrength.BUY, 0.8, 'Strong dividend yield')
        ]
        
        catalysts = investment_engine._identify_catalysts(mock_asset, signals)
        
        assert 'Technology sector growth trends' in catalysts
        assert 'Strong ESG credentials' in catalysts
        assert 'Technical oversold bounce potential' in catalysts
    
    def test_screen_opportunities(self, investment_engine, mock_db_session):
        """Test opportunity screening."""
        # Mock assets
        mock_assets = [
            Mock(symbol='AAPL', sector='Technology', market_cap=3000000000000, pe_ratio=25, dividend_yield=0.5),
            Mock(symbol='MSFT', sector='Technology', market_cap=2500000000000, pe_ratio=30, dividend_yield=1.0),
            Mock(symbol='JNJ', sector='Healthcare', market_cap=400000000000, pe_ratio=18, dividend_yield=3.0)
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value.all.return_value = mock_assets
        mock_db_session.query.return_value = mock_query
        
        # Mock analyze_investment_opportunity
        with patch.object(investment_engine, 'analyze_investment_opportunity') as mock_analyze:
            mock_rec = Mock()
            mock_rec.symbol = 'AAPL'
            mock_rec.investment_score = 75
            mock_rec.action = SignalStrength.BUY
            mock_analyze.return_value = mock_rec
            
            filters = {
                'sectors': ['Technology'],
                'max_pe': 35,
                'min_investment_score': 60
            }
            
            results = investment_engine.screen_opportunities(filters, limit=2)
        
        assert len(results) <= 2
        assert all(r.investment_score >= 60 for r in results)