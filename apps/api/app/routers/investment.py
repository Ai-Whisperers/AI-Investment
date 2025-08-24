"""API endpoints for investment recommendations and backtesting."""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from ..core.database import get_db
from ..models import User
from ..utils.token_dep import get_current_user
from ..services.investment_engine import (
    InvestmentDecisionEngine,
    InvestmentHorizon,
    SignalStrength
)
from ..services.backtesting import BacktestEngine

router = APIRouter()


class InvestmentAnalysisRequest(BaseModel):
    """Request model for investment analysis."""
    symbol: str
    horizon: str = Field(default="long", pattern="^(short|medium|long)$")


class BacktestRequest(BaseModel):
    """Request model for backtesting."""
    symbols: List[str]
    start_date: datetime
    end_date: datetime
    initial_capital: float = 100000
    rebalance_frequency: str = Field(default="monthly", pattern="^(daily|weekly|monthly)$")
    strategy_params: Optional[Dict[str, Any]] = None


class ScreeningRequest(BaseModel):
    """Request model for opportunity screening."""
    sectors: Optional[List[str]] = None
    min_market_cap: Optional[int] = None
    max_pe: Optional[float] = None
    min_dividend: Optional[float] = None
    min_investment_score: Optional[float] = 60
    limit: int = Field(default=20, le=100)


@router.post("/analyze")
def analyze_investment(
    request: InvestmentAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive investment analysis and recommendation for a symbol.
    
    Returns detailed recommendation including:
    - Action (buy/sell/hold)
    - Confidence and investment scores
    - Entry/exit prices
    - Risk assessment
    - Investment rationale
    """
    engine = InvestmentDecisionEngine(db)
    
    # Convert horizon string to enum
    horizon_map = {
        'short': InvestmentHorizon.SHORT,
        'medium': InvestmentHorizon.MEDIUM,
        'long': InvestmentHorizon.LONG
    }
    horizon = horizon_map.get(request.horizon, InvestmentHorizon.LONG)
    
    try:
        recommendation = engine.analyze_investment_opportunity(
            request.symbol,
            horizon
        )
        
        # Convert to JSON-serializable format
        return {
            'symbol': recommendation.symbol,
            'action': recommendation.action.value,
            'confidence_score': recommendation.confidence_score,
            'investment_score': recommendation.investment_score,
            'risk_score': recommendation.risk_score,
            'horizon': recommendation.horizon.value,
            'target_allocation': recommendation.target_allocation,
            'entry_price_range': {
                'low': recommendation.entry_price_range[0],
                'high': recommendation.entry_price_range[1]
            },
            'exit_price_target': recommendation.exit_price_target,
            'stop_loss': recommendation.stop_loss,
            'rationale': recommendation.rationale,
            'risks': recommendation.risks,
            'catalysts': recommendation.catalysts,
            'signals': [
                {
                    'source': signal.source,
                    'strength': signal.strength.value,
                    'confidence': signal.confidence,
                    'rationale': signal.rationale
                }
                for signal in recommendation.signals
            ],
            'metadata': recommendation.metadata
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.post("/screen")
def screen_opportunities(
    request: ScreeningRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Screen for investment opportunities based on criteria.
    
    Returns top opportunities ranked by investment score.
    """
    engine = InvestmentDecisionEngine(db)
    
    filters = {
        'sectors': request.sectors,
        'min_market_cap': request.min_market_cap,
        'max_pe': request.max_pe,
        'min_dividend': request.min_dividend,
        'min_investment_score': request.min_investment_score
    }
    
    # Remove None values
    filters = {k: v for k, v in filters.items() if v is not None}
    
    try:
        recommendations = engine.screen_opportunities(filters, request.limit)
        
        # Convert to JSON-serializable format
        results = []
        for rec in recommendations:
            results.append({
                'symbol': rec.symbol,
                'action': rec.action.value,
                'investment_score': rec.investment_score,
                'risk_score': rec.risk_score,
                'target_allocation': rec.target_allocation,
                'rationale': rec.rationale[:200] + '...' if len(rec.rationale) > 200 else rec.rationale,
                'sector': rec.metadata.get('sector'),
                'market_cap': rec.metadata.get('market_cap')
            })
        
        return {
            'count': len(results),
            'opportunities': results,
            'filters_applied': filters
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Screening failed: {str(e)}"
        )


@router.post("/backtest")
def run_backtest(
    request: BacktestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Run backtest simulation for a strategy.
    
    Simulates portfolio performance over historical period.
    """
    if request.end_date <= request.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after start date"
        )
    
    if len(request.symbols) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one symbol required"
        )
    
    engine = BacktestEngine(db, request.initial_capital)
    
    try:
        result = engine.run_backtest(
            request.symbols,
            request.start_date,
            request.end_date,
            request.rebalance_frequency,
            request.strategy_params
        )
        
        # Convert to JSON-serializable format
        return {
            'performance': {
                'initial_capital': result.initial_capital,
                'final_value': result.final_value,
                'total_return': result.total_return,
                'total_return_pct': result.total_return_pct,
                'annualized_return': result.annualized_return,
                'max_drawdown': result.max_drawdown,
                'sharpe_ratio': result.sharpe_ratio,
                'benchmark_return': result.benchmark_return,
                'alpha': result.alpha
            },
            'trading_statistics': {
                'total_trades': result.total_trades,
                'winning_trades': result.winning_trades,
                'losing_trades': result.losing_trades,
                'win_rate': result.win_rate,
                'avg_win': result.avg_win,
                'avg_loss': result.avg_loss
            },
            'positions': [
                {
                    'symbol': pos.symbol,
                    'entry_price': pos.entry_price,
                    'entry_date': pos.entry_date.isoformat(),
                    'exit_price': pos.exit_price,
                    'exit_date': pos.exit_date.isoformat() if pos.exit_date else None,
                    'return_pct': pos.return_pct,
                    'is_open': pos.is_open
                }
                for pos in result.positions[:50]  # Limit to 50 positions
            ],
            'equity_curve': result.equity_curve.tolist()[-100:],  # Last 100 points
            'metadata': result.metadata
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backtest failed: {str(e)}"
        )


@router.get("/recommendations/portfolio")
def get_portfolio_recommendations(
    risk_tolerance: str = Query("moderate", pattern="^(conservative|moderate|aggressive)$"),
    investment_amount: float = Query(10000, ge=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get personalized portfolio recommendations based on risk profile.
    
    Returns diversified portfolio allocation suggestions.
    """
    engine = InvestmentDecisionEngine(db)
    
    # Define risk-based filters
    risk_filters = {
        'conservative': {
            'max_pe': 20,
            'min_dividend': 2,
            'min_market_cap': 10_000_000_000,
            'sectors': ['Consumer', 'Healthcare', 'Utilities']
        },
        'moderate': {
            'max_pe': 30,
            'min_dividend': 1,
            'min_market_cap': 1_000_000_000,
            'sectors': ['Technology', 'Consumer', 'Healthcare', 'Finance']
        },
        'aggressive': {
            'max_pe': 50,
            'min_market_cap': 100_000_000,
            'sectors': ['Technology', 'Consumer', 'Healthcare']
        }
    }
    
    filters = risk_filters.get(risk_tolerance, risk_filters['moderate'])
    
    try:
        # Get top opportunities
        recommendations = engine.screen_opportunities(filters, limit=10)
        
        # Build portfolio allocation
        portfolio = []
        remaining_allocation = 1.0
        
        for rec in recommendations:
            if remaining_allocation <= 0:
                break
            
            allocation = min(rec.target_allocation, remaining_allocation)
            portfolio.append({
                'symbol': rec.symbol,
                'allocation_pct': allocation * 100,
                'investment_amount': investment_amount * allocation,
                'action': rec.action.value,
                'investment_score': rec.investment_score,
                'rationale': rec.rationale[:150] + '...' if len(rec.rationale) > 150 else rec.rationale
            })
            remaining_allocation -= allocation
        
        # Add cash position if not fully allocated
        if remaining_allocation > 0:
            portfolio.append({
                'symbol': 'CASH',
                'allocation_pct': remaining_allocation * 100,
                'investment_amount': investment_amount * remaining_allocation,
                'action': 'hold',
                'investment_score': 50,
                'rationale': 'Cash reserve for opportunities'
            })
        
        return {
            'risk_tolerance': risk_tolerance,
            'total_investment': investment_amount,
            'portfolio': portfolio,
            'expected_return': sum(p['investment_score'] * p['allocation_pct'] / 10000 for p in portfolio),
            'diversification_score': min(100, len([p for p in portfolio if p['symbol'] != 'CASH']) * 15)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Portfolio recommendation failed: {str(e)}"
        )


@router.get("/signals/{symbol}")
def get_investment_signals(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all investment signals for a symbol.
    
    Returns signals from technical, fundamental, and other sources.
    """
    engine = InvestmentDecisionEngine(db)
    
    try:
        # Get full analysis
        recommendation = engine.analyze_investment_opportunity(
            symbol,
            InvestmentHorizon.LONG
        )
        
        # Format signals with more detail
        signals_detail = []
        for signal in recommendation.signals:
            signals_detail.append({
                'source': signal.source,
                'strength': signal.strength.value,
                'confidence': signal.confidence,
                'confidence_pct': signal.confidence * 100,
                'rationale': signal.rationale,
                'data_points': signal.data_points,
                'signal_quality': 'high' if signal.confidence > 0.7 else 'medium' if signal.confidence > 0.5 else 'low'
            })
        
        # Aggregate signal summary
        buy_signals = sum(1 for s in recommendation.signals if s.strength.value in ['buy', 'strong_buy'])
        sell_signals = sum(1 for s in recommendation.signals if s.strength.value in ['sell', 'strong_sell'])
        
        return {
            'symbol': symbol,
            'signals': signals_detail,
            'summary': {
                'total_signals': len(recommendation.signals),
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'hold_signals': len(recommendation.signals) - buy_signals - sell_signals,
                'consensus': recommendation.action.value,
                'consensus_strength': recommendation.confidence_score
            },
            'recommendation': {
                'action': recommendation.action.value,
                'investment_score': recommendation.investment_score,
                'risk_score': recommendation.risk_score
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signal analysis failed: {str(e)}"
        )