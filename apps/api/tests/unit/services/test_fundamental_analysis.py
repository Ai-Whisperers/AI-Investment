"""Tests for fundamental analysis service."""
import pytest
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session

from app.services.fundamental_analysis import FundamentalAnalysis
from app.models import Asset


class TestFundamentalAnalysis:
    """Test suite for fundamental analysis calculations."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def fundamental_service(self, mock_db_session):
        """Create a FundamentalAnalysis service instance."""
        return FundamentalAnalysis(mock_db_session)
    
    def test_calculate_pe_ratio_valid(self):
        """Test P/E ratio calculation with valid inputs."""
        pe = FundamentalAnalysis.calculate_pe_ratio(150.0, 5.0)
        assert pe == 30.0
    
    def test_calculate_pe_ratio_negative_earnings(self):
        """Test P/E ratio with negative earnings."""
        pe = FundamentalAnalysis.calculate_pe_ratio(150.0, -5.0)
        assert pe is None
    
    def test_calculate_pe_ratio_zero_earnings(self):
        """Test P/E ratio with zero earnings."""
        pe = FundamentalAnalysis.calculate_pe_ratio(150.0, 0.0)
        assert pe is None
    
    def test_calculate_peg_ratio_valid(self):
        """Test PEG ratio calculation with valid inputs."""
        peg = FundamentalAnalysis.calculate_peg_ratio(20.0, 15.0)
        assert abs(peg - 1.33) < 0.01
    
    def test_calculate_peg_ratio_no_growth(self):
        """Test PEG ratio with zero growth."""
        peg = FundamentalAnalysis.calculate_peg_ratio(20.0, 0.0)
        assert peg is None
    
    def test_calculate_peg_ratio_no_pe(self):
        """Test PEG ratio with no P/E ratio."""
        peg = FundamentalAnalysis.calculate_peg_ratio(None, 15.0)
        assert peg is None
    
    def test_calculate_price_to_book_valid(self):
        """Test Price-to-Book ratio calculation."""
        pb = FundamentalAnalysis.calculate_price_to_book(100.0, 25.0)
        assert pb == 4.0
    
    def test_calculate_price_to_book_negative_book(self):
        """Test P/B ratio with negative book value."""
        pb = FundamentalAnalysis.calculate_price_to_book(100.0, -25.0)
        assert pb is None
    
    def test_calculate_price_to_sales_valid(self):
        """Test Price-to-Sales ratio calculation."""
        ps = FundamentalAnalysis.calculate_price_to_sales(1000000000, 500000000)
        assert ps == 2.0
    
    def test_calculate_price_to_sales_no_revenue(self):
        """Test P/S ratio with zero revenue."""
        ps = FundamentalAnalysis.calculate_price_to_sales(1000000000, 0)
        assert ps is None
    
    def test_calculate_ev_to_ebitda_valid(self):
        """Test EV/EBITDA ratio calculation."""
        ev_ebitda = FundamentalAnalysis.calculate_ev_to_ebitda(5000000000, 500000000)
        assert ev_ebitda == 10.0
    
    def test_calculate_ev_to_ebitda_negative(self):
        """Test EV/EBITDA with negative EBITDA."""
        ev_ebitda = FundamentalAnalysis.calculate_ev_to_ebitda(5000000000, -500000000)
        assert ev_ebitda is None
    
    def test_calculate_debt_to_equity_valid(self):
        """Test Debt-to-Equity ratio calculation."""
        de = FundamentalAnalysis.calculate_debt_to_equity(500000000, 1000000000)
        assert de == 0.5
    
    def test_calculate_debt_to_equity_negative_equity(self):
        """Test D/E ratio with negative equity."""
        de = FundamentalAnalysis.calculate_debt_to_equity(500000000, -1000000000)
        assert de is None
    
    def test_calculate_current_ratio_valid(self):
        """Test Current Ratio calculation."""
        current = FundamentalAnalysis.calculate_current_ratio(2000000, 1000000)
        assert current == 2.0
    
    def test_calculate_current_ratio_no_liabilities(self):
        """Test Current Ratio with zero liabilities."""
        current = FundamentalAnalysis.calculate_current_ratio(2000000, 0)
        assert current is None
    
    def test_calculate_quick_ratio_valid(self):
        """Test Quick Ratio calculation."""
        quick = FundamentalAnalysis.calculate_quick_ratio(2000000, 500000, 1000000)
        assert quick == 1.5
    
    def test_calculate_quick_ratio_no_liabilities(self):
        """Test Quick Ratio with zero liabilities."""
        quick = FundamentalAnalysis.calculate_quick_ratio(2000000, 500000, 0)
        assert quick is None
    
    def test_calculate_roe_valid(self):
        """Test Return on Equity calculation."""
        roe = FundamentalAnalysis.calculate_roe(150000000, 1000000000)
        assert roe == 15.0
    
    def test_calculate_roe_negative_equity(self):
        """Test ROE with negative equity."""
        roe = FundamentalAnalysis.calculate_roe(150000000, -1000000000)
        assert roe is None
    
    def test_calculate_roa_valid(self):
        """Test Return on Assets calculation."""
        roa = FundamentalAnalysis.calculate_roa(100000000, 2000000000)
        assert roa == 5.0
    
    def test_calculate_roa_zero_assets(self):
        """Test ROA with zero assets."""
        roa = FundamentalAnalysis.calculate_roa(100000000, 0)
        assert roa is None
    
    def test_calculate_roic_valid(self):
        """Test Return on Invested Capital calculation."""
        roic = FundamentalAnalysis.calculate_roic(200000000, 1000000000)
        assert roic == 20.0
    
    def test_calculate_roic_no_capital(self):
        """Test ROIC with zero invested capital."""
        roic = FundamentalAnalysis.calculate_roic(200000000, 0)
        assert roic is None
    
    def test_calculate_gross_margin_valid(self):
        """Test Gross Margin calculation."""
        margin = FundamentalAnalysis.calculate_gross_margin(1000000, 600000)
        assert margin == 40.0
    
    def test_calculate_gross_margin_no_revenue(self):
        """Test Gross Margin with zero revenue."""
        margin = FundamentalAnalysis.calculate_gross_margin(0, 600000)
        assert margin is None
    
    def test_calculate_operating_margin_valid(self):
        """Test Operating Margin calculation."""
        margin = FundamentalAnalysis.calculate_operating_margin(300000, 1000000)
        assert margin == 30.0
    
    def test_calculate_net_margin_valid(self):
        """Test Net Margin calculation."""
        margin = FundamentalAnalysis.calculate_net_margin(150000, 1000000)
        assert margin == 15.0
    
    def test_calculate_free_cash_flow(self):
        """Test Free Cash Flow calculation."""
        fcf = FundamentalAnalysis.calculate_free_cash_flow(500000000, 100000000)
        assert fcf == 400000000
    
    def test_calculate_dividend_yield_valid(self):
        """Test Dividend Yield calculation."""
        yield_pct = FundamentalAnalysis.calculate_dividend_yield(3.0, 100.0)
        assert yield_pct == 3.0
    
    def test_calculate_dividend_yield_zero_price(self):
        """Test Dividend Yield with zero price."""
        yield_pct = FundamentalAnalysis.calculate_dividend_yield(3.0, 0.0)
        assert yield_pct is None
    
    def test_calculate_dividend_payout_ratio_valid(self):
        """Test Dividend Payout Ratio calculation."""
        payout = FundamentalAnalysis.calculate_dividend_payout_ratio(2.0, 5.0)
        assert payout == 40.0
    
    def test_calculate_dividend_payout_ratio_no_earnings(self):
        """Test Payout Ratio with zero earnings."""
        payout = FundamentalAnalysis.calculate_dividend_payout_ratio(2.0, 0.0)
        assert payout is None
    
    def test_calculate_revenue_growth_valid(self):
        """Test Revenue Growth calculation."""
        growth = FundamentalAnalysis.calculate_revenue_growth(1200000, 1000000)
        assert growth == 20.0
    
    def test_calculate_revenue_growth_from_zero(self):
        """Test Revenue Growth from zero base."""
        growth = FundamentalAnalysis.calculate_revenue_growth(1000000, 0)
        assert growth is None
    
    def test_calculate_earnings_growth_valid(self):
        """Test Earnings Growth calculation."""
        growth = FundamentalAnalysis.calculate_earnings_growth(150000, 100000)
        assert growth == 50.0
    
    def test_calculate_earnings_growth_from_negative(self):
        """Test Earnings Growth from negative base."""
        growth = FundamentalAnalysis.calculate_earnings_growth(100000, -50000)
        assert growth == -300.0  # Moving from loss to profit
    
    def test_calculate_earnings_growth_both_zero(self):
        """Test Earnings Growth when both are zero."""
        growth = FundamentalAnalysis.calculate_earnings_growth(0, 0)
        assert growth is None
    
    def test_calculate_dcf_value_valid(self):
        """Test DCF valuation calculation."""
        cash_flows = [100000000, 110000000, 121000000, 133100000, 146410000]
        dcf = FundamentalAnalysis.calculate_dcf_value(
            cash_flows,
            terminal_growth_rate=0.03,
            discount_rate=0.10,
            shares_outstanding=10000000
        )
        
        assert dcf is not None
        assert dcf > 0
        # Rough check - should be in reasonable range
        assert 20 < dcf < 200
    
    def test_calculate_dcf_value_error_handling(self):
        """Test DCF with invalid inputs."""
        # Terminal growth rate higher than discount rate
        cash_flows = [100000000]
        dcf = FundamentalAnalysis.calculate_dcf_value(
            cash_flows,
            terminal_growth_rate=0.15,
            discount_rate=0.10,
            shares_outstanding=10000000
        )
        assert dcf is None
    
    def test_evaluate_financial_health_strong(self):
        """Test financial health evaluation with strong metrics."""
        metrics = {
            'roe': 20,
            'current_ratio': 2.5,
            'debt_to_equity': 0.3,
            'pe_ratio': 15,
            'revenue_growth': 25
        }
        
        health = FundamentalAnalysis.evaluate_financial_health(metrics)
        
        assert health['profitability'] == 'strong'
        assert health['liquidity'] == 'strong'
        assert health['leverage'] == 'conservative'
        assert health['valuation'] == 'fair'
        assert health['growth'] == 'high'
        assert health['overall'] == 'excellent'
    
    def test_evaluate_financial_health_weak(self):
        """Test financial health evaluation with weak metrics."""
        metrics = {
            'roe': 3,
            'current_ratio': 0.8,
            'debt_to_equity': 3,
            'pe_ratio': 50,
            'revenue_growth': -5
        }
        
        health = FundamentalAnalysis.evaluate_financial_health(metrics)
        
        assert health['profitability'] == 'weak'
        assert health['liquidity'] == 'poor'
        assert health['leverage'] == 'high_risk'
        assert health['valuation'] == 'overvalued'
        assert health['growth'] == 'declining'
        assert health['overall'] == 'poor'
    
    def test_evaluate_financial_health_moderate(self):
        """Test financial health evaluation with moderate metrics."""
        metrics = {
            'roe': 12,
            'current_ratio': 1.6,
            'debt_to_equity': 0.8,
            'pe_ratio': 18,
            'revenue_growth': 8
        }
        
        health = FundamentalAnalysis.evaluate_financial_health(metrics)
        
        assert health['profitability'] == 'good'
        assert health['liquidity'] == 'good'
        assert health['leverage'] == 'moderate'
        assert health['valuation'] == 'fair'
        assert health['growth'] == 'stable'
        assert health['overall'] in ['good', 'moderate']
    
    def test_get_asset_fundamentals_found(self, fundamental_service, mock_db_session):
        """Test getting fundamentals for existing asset."""
        # Mock asset
        mock_asset = Mock(spec=Asset)
        mock_asset.symbol = 'AAPL'
        mock_asset.name = 'Apple Inc.'
        mock_asset.market_cap = 3000000000000
        mock_asset.pe_ratio = 28.5
        mock_asset.dividend_yield = 0.5
        mock_asset.sector = 'Technology'
        mock_asset.industry = 'Consumer Electronics'
        mock_asset.esg_score = 75
        mock_asset.volatility_30d = 0.25
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_asset
        
        result = fundamental_service.get_asset_fundamentals('AAPL')
        
        assert result['symbol'] == 'AAPL'
        assert result['name'] == 'Apple Inc.'
        assert result['market_cap'] == 3000000000000
        assert result['pe_ratio'] == 28.5
        assert 'health_assessment' in result
    
    def test_get_asset_fundamentals_not_found(self, fundamental_service, mock_db_session):
        """Test getting fundamentals for non-existent asset."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = fundamental_service.get_asset_fundamentals('INVALID')
        
        assert 'error' in result
        assert 'INVALID' in result['error']