"""Fundamental analysis service for evaluating company financials and valuation."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

from ..models import Asset

logger = logging.getLogger(__name__)


class FundamentalAnalysis:
    """Service for calculating fundamental analysis metrics."""
    
    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db
    
    @staticmethod
    def calculate_pe_ratio(price: float, earnings_per_share: float) -> Optional[float]:
        """
        Calculate Price-to-Earnings ratio.
        
        Args:
            price: Current stock price
            earnings_per_share: Earnings per share (EPS)
            
        Returns:
            P/E ratio or None if EPS is zero/negative
        """
        if earnings_per_share <= 0:
            return None
        return price / earnings_per_share
    
    @staticmethod
    def calculate_peg_ratio(pe_ratio: float, growth_rate: float) -> Optional[float]:
        """
        Calculate Price/Earnings-to-Growth ratio.
        
        Args:
            pe_ratio: P/E ratio
            growth_rate: Expected earnings growth rate (as percentage)
            
        Returns:
            PEG ratio or None if growth rate is zero/negative
        """
        if not pe_ratio or growth_rate <= 0:
            return None
        return pe_ratio / growth_rate
    
    @staticmethod
    def calculate_price_to_book(price: float, book_value_per_share: float) -> Optional[float]:
        """
        Calculate Price-to-Book ratio.
        
        Args:
            price: Current stock price
            book_value_per_share: Book value per share
            
        Returns:
            P/B ratio or None if book value is zero/negative
        """
        if book_value_per_share <= 0:
            return None
        return price / book_value_per_share
    
    @staticmethod
    def calculate_price_to_sales(market_cap: float, revenue: float) -> Optional[float]:
        """
        Calculate Price-to-Sales ratio.
        
        Args:
            market_cap: Market capitalization
            revenue: Annual revenue
            
        Returns:
            P/S ratio or None if revenue is zero/negative
        """
        if revenue <= 0:
            return None
        return market_cap / revenue
    
    @staticmethod
    def calculate_ev_to_ebitda(enterprise_value: float, ebitda: float) -> Optional[float]:
        """
        Calculate Enterprise Value to EBITDA ratio.
        
        Args:
            enterprise_value: Enterprise value (market cap + debt - cash)
            ebitda: Earnings before interest, taxes, depreciation, and amortization
            
        Returns:
            EV/EBITDA ratio or None if EBITDA is zero/negative
        """
        if ebitda <= 0:
            return None
        return enterprise_value / ebitda
    
    @staticmethod
    def calculate_debt_to_equity(total_debt: float, total_equity: float) -> Optional[float]:
        """
        Calculate Debt-to-Equity ratio.
        
        Args:
            total_debt: Total debt
            total_equity: Total shareholder equity
            
        Returns:
            D/E ratio or None if equity is zero/negative
        """
        if total_equity <= 0:
            return None
        return total_debt / total_equity
    
    @staticmethod
    def calculate_current_ratio(current_assets: float, current_liabilities: float) -> Optional[float]:
        """
        Calculate Current Ratio (liquidity measure).
        
        Args:
            current_assets: Current assets
            current_liabilities: Current liabilities
            
        Returns:
            Current ratio or None if liabilities is zero
        """
        if current_liabilities <= 0:
            return None
        return current_assets / current_liabilities
    
    @staticmethod
    def calculate_quick_ratio(current_assets: float, inventory: float, current_liabilities: float) -> Optional[float]:
        """
        Calculate Quick Ratio (acid-test ratio).
        
        Args:
            current_assets: Current assets
            inventory: Inventory value
            current_liabilities: Current liabilities
            
        Returns:
            Quick ratio or None if liabilities is zero
        """
        if current_liabilities <= 0:
            return None
        return (current_assets - inventory) / current_liabilities
    
    @staticmethod
    def calculate_roe(net_income: float, shareholder_equity: float) -> Optional[float]:
        """
        Calculate Return on Equity.
        
        Args:
            net_income: Net income
            shareholder_equity: Average shareholder equity
            
        Returns:
            ROE as percentage or None if equity is zero/negative
        """
        if shareholder_equity <= 0:
            return None
        return (net_income / shareholder_equity) * 100
    
    @staticmethod
    def calculate_roa(net_income: float, total_assets: float) -> Optional[float]:
        """
        Calculate Return on Assets.
        
        Args:
            net_income: Net income
            total_assets: Average total assets
            
        Returns:
            ROA as percentage or None if assets is zero/negative
        """
        if total_assets <= 0:
            return None
        return (net_income / total_assets) * 100
    
    @staticmethod
    def calculate_roic(nopat: float, invested_capital: float) -> Optional[float]:
        """
        Calculate Return on Invested Capital.
        
        Args:
            nopat: Net operating profit after tax
            invested_capital: Invested capital (debt + equity - cash)
            
        Returns:
            ROIC as percentage or None if invested capital is zero/negative
        """
        if invested_capital <= 0:
            return None
        return (nopat / invested_capital) * 100
    
    @staticmethod
    def calculate_gross_margin(revenue: float, cost_of_goods: float) -> Optional[float]:
        """
        Calculate Gross Profit Margin.
        
        Args:
            revenue: Total revenue
            cost_of_goods: Cost of goods sold
            
        Returns:
            Gross margin as percentage or None if revenue is zero
        """
        if revenue <= 0:
            return None
        return ((revenue - cost_of_goods) / revenue) * 100
    
    @staticmethod
    def calculate_operating_margin(operating_income: float, revenue: float) -> Optional[float]:
        """
        Calculate Operating Margin.
        
        Args:
            operating_income: Operating income (EBIT)
            revenue: Total revenue
            
        Returns:
            Operating margin as percentage or None if revenue is zero
        """
        if revenue <= 0:
            return None
        return (operating_income / revenue) * 100
    
    @staticmethod
    def calculate_net_margin(net_income: float, revenue: float) -> Optional[float]:
        """
        Calculate Net Profit Margin.
        
        Args:
            net_income: Net income
            revenue: Total revenue
            
        Returns:
            Net margin as percentage or None if revenue is zero
        """
        if revenue <= 0:
            return None
        return (net_income / revenue) * 100
    
    @staticmethod
    def calculate_free_cash_flow(operating_cash_flow: float, capital_expenditures: float) -> float:
        """
        Calculate Free Cash Flow.
        
        Args:
            operating_cash_flow: Cash flow from operations
            capital_expenditures: Capital expenditures
            
        Returns:
            Free cash flow
        """
        return operating_cash_flow - capital_expenditures
    
    @staticmethod
    def calculate_dividend_yield(annual_dividend: float, price: float) -> Optional[float]:
        """
        Calculate Dividend Yield.
        
        Args:
            annual_dividend: Annual dividend per share
            price: Current stock price
            
        Returns:
            Dividend yield as percentage or None if price is zero
        """
        if price <= 0:
            return None
        return (annual_dividend / price) * 100
    
    @staticmethod
    def calculate_dividend_payout_ratio(dividends_per_share: float, earnings_per_share: float) -> Optional[float]:
        """
        Calculate Dividend Payout Ratio.
        
        Args:
            dividends_per_share: Dividends per share
            earnings_per_share: Earnings per share
            
        Returns:
            Payout ratio as percentage or None if EPS is zero/negative
        """
        if earnings_per_share <= 0:
            return None
        return (dividends_per_share / earnings_per_share) * 100
    
    @staticmethod
    def calculate_revenue_growth(current_revenue: float, previous_revenue: float) -> Optional[float]:
        """
        Calculate Year-over-Year Revenue Growth.
        
        Args:
            current_revenue: Current period revenue
            previous_revenue: Previous period revenue
            
        Returns:
            Growth rate as percentage or None if previous revenue is zero
        """
        if previous_revenue <= 0:
            return None
        return ((current_revenue - previous_revenue) / previous_revenue) * 100
    
    @staticmethod
    def calculate_earnings_growth(current_earnings: float, previous_earnings: float) -> Optional[float]:
        """
        Calculate Year-over-Year Earnings Growth.
        
        Args:
            current_earnings: Current period earnings
            previous_earnings: Previous period earnings
            
        Returns:
            Growth rate as percentage or None if previous earnings is zero
        """
        if previous_earnings == 0:
            return None if current_earnings == 0 else float('inf')
        return ((current_earnings - previous_earnings) / abs(previous_earnings)) * 100
    
    @staticmethod
    def calculate_dcf_value(free_cash_flows: List[float], 
                          terminal_growth_rate: float = 0.03,
                          discount_rate: float = 0.10,
                          shares_outstanding: float = 1000000) -> Optional[float]:
        """
        Calculate intrinsic value using Discounted Cash Flow model.
        
        Args:
            free_cash_flows: List of projected free cash flows
            terminal_growth_rate: Perpetual growth rate for terminal value
            discount_rate: Weighted average cost of capital (WACC)
            shares_outstanding: Number of shares outstanding
            
        Returns:
            Intrinsic value per share or None if calculation fails
        """
        try:
            # Calculate present value of projected cash flows
            pv_cash_flows = sum(
                fcf / ((1 + discount_rate) ** (i + 1))
                for i, fcf in enumerate(free_cash_flows)
            )
            
            # Calculate terminal value
            terminal_fcf = free_cash_flows[-1] * (1 + terminal_growth_rate)
            terminal_value = terminal_fcf / (discount_rate - terminal_growth_rate)
            pv_terminal_value = terminal_value / ((1 + discount_rate) ** len(free_cash_flows))
            
            # Calculate intrinsic value per share
            enterprise_value = pv_cash_flows + pv_terminal_value
            intrinsic_value = enterprise_value / shares_outstanding
            
            return intrinsic_value
            
        except Exception as e:
            logger.error(f"Error calculating DCF value: {e}")
            return None
    
    @staticmethod
    def evaluate_financial_health(metrics: Dict[str, float]) -> Dict[str, str]:
        """
        Evaluate overall financial health based on key metrics.
        
        Args:
            metrics: Dictionary of financial metrics
            
        Returns:
            Dictionary with health assessment for each category
        """
        health = {}
        
        # Evaluate profitability
        roe = metrics.get('roe', 0)
        if roe > 15:
            health['profitability'] = 'strong'
        elif roe > 10:
            health['profitability'] = 'good'
        elif roe > 5:
            health['profitability'] = 'moderate'
        else:
            health['profitability'] = 'weak'
        
        # Evaluate liquidity
        current_ratio = metrics.get('current_ratio', 0)
        if current_ratio > 2:
            health['liquidity'] = 'strong'
        elif current_ratio > 1.5:
            health['liquidity'] = 'good'
        elif current_ratio > 1:
            health['liquidity'] = 'adequate'
        else:
            health['liquidity'] = 'poor'
        
        # Evaluate leverage
        debt_to_equity = metrics.get('debt_to_equity', 0)
        if debt_to_equity < 0.5:
            health['leverage'] = 'conservative'
        elif debt_to_equity < 1:
            health['leverage'] = 'moderate'
        elif debt_to_equity < 2:
            health['leverage'] = 'aggressive'
        else:
            health['leverage'] = 'high_risk'
        
        # Evaluate valuation
        pe_ratio = metrics.get('pe_ratio', 0)
        if 10 <= pe_ratio <= 20:
            health['valuation'] = 'fair'
        elif pe_ratio < 10:
            health['valuation'] = 'undervalued'
        elif pe_ratio > 30:
            health['valuation'] = 'overvalued'
        else:
            health['valuation'] = 'moderate'
        
        # Evaluate growth
        revenue_growth = metrics.get('revenue_growth', 0)
        if revenue_growth > 20:
            health['growth'] = 'high'
        elif revenue_growth > 10:
            health['growth'] = 'good'
        elif revenue_growth > 0:
            health['growth'] = 'stable'
        else:
            health['growth'] = 'declining'
        
        # Overall assessment
        positive_indicators = sum(1 for v in health.values() if v in ['strong', 'good', 'conservative', 'fair', 'high'])
        
        if positive_indicators >= 4:
            health['overall'] = 'excellent'
        elif positive_indicators >= 3:
            health['overall'] = 'good'
        elif positive_indicators >= 2:
            health['overall'] = 'moderate'
        else:
            health['overall'] = 'poor'
        
        return health
    
    def get_asset_fundamentals(self, symbol: str) -> Dict[str, any]:
        """
        Get fundamental analysis for a specific asset.
        
        Args:
            symbol: Asset symbol
            
        Returns:
            Dictionary with fundamental metrics and analysis
        """
        asset = self.db.query(Asset).filter(Asset.symbol == symbol.upper()).first()
        
        if not asset:
            return {'error': f'Asset {symbol} not found'}
        
        # In production, these would come from financial data APIs
        # For now, return mock data based on asset properties
        fundamentals = {
            'symbol': asset.symbol,
            'name': asset.name,
            'market_cap': asset.market_cap,
            'pe_ratio': asset.pe_ratio,
            'dividend_yield': asset.dividend_yield,
            'sector': asset.sector,
            'industry': asset.industry,
            'esg_score': asset.esg_score,
            'volatility_30d': asset.volatility_30d
        }
        
        # Add calculated health metrics if we have the data
        if asset.pe_ratio:
            metrics = {
                'pe_ratio': asset.pe_ratio,
                'dividend_yield': asset.dividend_yield or 0,
                'current_ratio': 1.5,  # Mock data
                'debt_to_equity': 0.8,  # Mock data
                'roe': 12,  # Mock data
                'revenue_growth': 15  # Mock data
            }
            fundamentals['health_assessment'] = self.evaluate_financial_health(metrics)
        
        return fundamentals