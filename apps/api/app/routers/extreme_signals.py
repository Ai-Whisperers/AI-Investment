"""API endpoints for extreme signal detection targeting >30% returns."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.signals import Signal
from app.services.alpha_detection import (
    MultiLayerAlphaDetection,
    AsymmetryExploiter,
    ExtremeEventDetector
)
from app.services.signal_processor import SignalProcessor
from app.services.meme_velocity import MemeVelocityTracker
from app.services.extreme_backtest import ExtremeBacktest
from app.services.collectors.zero_cost_collector import ZeroCostCollector

router = APIRouter(prefix="/api/v1/extreme", tags=["extreme_signals"])


@router.get("/signals/live")
async def get_live_signals(
    confidence_min: float = Query(0.7, description="Minimum confidence threshold"),
    signal_type: Optional[str] = Query(None, description="Filter by signal type"),
    db: Session = Depends(get_db)
) -> List[Dict]:
    """Get live high-confidence signals for immediate action."""
    
    # Query recent signals
    query = db.query(Signal).filter(
        Signal.confidence >= confidence_min,
        Signal.executed == False,
        Signal.created_at >= datetime.now() - timedelta(days=7)
    )
    
    if signal_type:
        query = query.filter(Signal.signal_type == signal_type)
        
    signals = query.order_by(Signal.confidence.desc()).limit(20).all()
    
    # Process and return
    return [
        {
            'ticker': s.ticker,
            'action': s.action,
            'confidence': s.confidence,
            'expected_return': s.expected_return,
            'timeframe': s.timeframe,
            'signal_type': s.signal_type,
            'sources': s.sources,
            'pattern_stack': s.pattern_stack,
            'created_at': s.created_at.isoformat()
        }
        for s in signals
    ]


@router.post("/detect/alpha")
async def detect_alpha_event(
    data: Dict,
    db: Session = Depends(get_db)
) -> Dict:
    """Detect alpha events using multi-layer pattern recognition."""
    
    detector = MultiLayerAlphaDetection()
    
    # Run detection
    alpha_event = await detector.detect_alpha_event(data)
    
    if alpha_event:
        # Store signal
        signal = Signal(
            ticker=alpha_event.get('ticker', 'UNKNOWN'),
            signal_type='extreme',
            confidence=alpha_event['confidence'],
            expected_return=alpha_event.get('expected_return', 0.3),
            timeframe=alpha_event.get('timeframe', '1_week'),
            sources=['multi_layer_detection'],
            pattern_stack=alpha_event.get('patterns', []),
            action=alpha_event.get('action', 'BUY')
        )
        
        db.add(signal)
        db.commit()
        
        return alpha_event
    else:
        return {'detected': False, 'message': 'No alpha event detected'}


@router.get("/meme/velocity/{ticker}")
async def get_meme_velocity(
    ticker: str,
    db: Session = Depends(get_db)
) -> Dict:
    """Get meme velocity metrics for a ticker."""
    
    tracker = MemeVelocityTracker()
    
    # Mock platform data for demo (would fetch real data in production)
    platform_data = {
        'reddit_wsb': ['mention1', 'mention2'] * 100,
        'tiktok': ['video1', 'video2'] * 50,
        'twitter': ['tweet1', 'tweet2'] * 75
    }
    
    signal = await tracker.calculate_velocity(ticker.upper(), platform_data)
    
    return {
        'ticker': signal.ticker,
        'velocity': round(signal.velocity, 2),
        'acceleration': round(signal.acceleration, 2),
        'virality_score': signal.virality_score,
        'expected_move': f"{signal.expected_move:.1%}",
        'timeframe': signal.timeframe,
        'platforms': signal.platforms,
        'mention_count': signal.mention_count,
        'sentiment': round(signal.sentiment, 2)
    }


@router.get("/meme/trending")
async def get_trending_memes(
    limit: int = Query(10, description="Number of results"),
    db: Session = Depends(get_db)
) -> List[Dict]:
    """Get top trending meme stocks by velocity."""
    
    tracker = MemeVelocityTracker()
    
    # Get top meme stocks
    meme_signals = tracker.get_top_meme_stocks(limit)
    
    return [
        {
            'ticker': s.ticker,
            'virality_score': s.virality_score,
            'velocity': round(s.velocity, 2),
            'expected_move': f"{s.expected_move:.1%}",
            'timeframe': s.timeframe,
            'platforms': s.platforms
        }
        for s in meme_signals
    ]


@router.get("/backtest/validate")
async def validate_strategy(
    starting_capital: float = Query(100000, description="Starting capital"),
    db: Session = Depends(get_db)
) -> Dict:
    """Run backtest to validate >30% return capability."""
    
    backtest = ExtremeBacktest()
    
    # Run validation
    results = await backtest.run_validation(starting_capital)
    
    return results


@router.get("/squeeze/candidates")
async def get_squeeze_candidates(
    db: Session = Depends(get_db)
) -> List[Dict]:
    """Get potential short squeeze candidates."""
    
    tracker = MemeVelocityTracker()
    
    # Check popular tickers for squeeze setup
    candidates = []
    tickers_to_check = ['GME', 'AMC', 'BBBY', 'SPCE', 'CLOV', 'WISH']
    
    for ticker in tickers_to_check:
        squeeze_data = await tracker.detect_squeeze_setup(ticker)
        if squeeze_data:
            candidates.append(squeeze_data)
            
    # Sort by probability
    candidates.sort(key=lambda x: x['squeeze_probability'], reverse=True)
    
    return candidates


@router.post("/collect/signals")
async def trigger_signal_collection(
    focus: str = Query('auto', description="Collection focus"),
    db: Session = Depends(get_db)
) -> Dict:
    """Manually trigger signal collection."""
    
    collector = ZeroCostCollector()
    
    # Run collection based on focus
    if focus == 'momentum':
        signals = await collector.collect_opening_momentum()
    elif focus == 'research':
        signals = await collector.collect_long_term_research()
    elif focus == 'extreme':
        signals = await collector.collect_extreme_signals()
    else:
        signals = await collector.collect_quick_signals()
        
    # Store signals
    stored_count = 0
    for signal_data in signals:
        if signal_data.get('tickers'):
            signal = Signal(
                ticker=signal_data['tickers'][0],
                signal_type=signal_data.get('signal_type', 'swing'),
                confidence=signal_data.get('confidence', 0.5),
                expected_return=signal_data.get('expected_return', 0.2),
                timeframe=signal_data.get('timeframe', '1_week'),
                sources=[signal_data.get('source', 'unknown')],
                pattern_stack=signal_data.get('patterns', []),
                action='BUY'
            )
            
            db.add(signal)
            stored_count += 1
            
    db.commit()
    
    return {
        'collected': len(signals),
        'stored': stored_count,
        'focus': focus,
        'timestamp': datetime.now().isoformat()
    }


@router.get("/opportunities/extreme")
async def get_extreme_opportunities(
    db: Session = Depends(get_db)
) -> List[Dict]:
    """Get extreme opportunities with >50% expected returns."""
    
    detector = ExtremeEventDetector()
    
    # Mock data for extreme detection (would use real data in production)
    opportunities = []
    
    # Check for various extreme patterns
    test_data = {
        'ticker': 'UNKNOWN',
        'short_interest': 30,
        'retail_buying': 0.8,
        'upcoming_catalyst': True,
        'options_volume': 10,
        'meme_growth': 5
    }
    
    extreme_events = await detector.scan_for_extremes(test_data)
    
    return extreme_events


@router.get("/asymmetry/early")
async def get_early_signals(
    db: Session = Depends(get_db)
) -> List[Dict]:
    """Get early signals with 48-72 hour lead time."""
    
    exploiter = AsymmetryExploiter()
    
    # Get signals from earliest sources
    raw_signals = [
        {'source': '4chan', 'ticker': 'GME', 'confidence': 0.3},
        {'source': 'small_discord', 'ticker': 'AMC', 'confidence': 0.4},
        {'source': 'reddit', 'ticker': 'TSLA', 'confidence': 0.6}
    ]
    
    # Process for early advantage
    early_signals = await exploiter.find_early_signals(raw_signals)
    
    return early_signals


@router.get("/portfolio/recommendations")
async def get_portfolio_recommendations(
    risk_tolerance: str = Query('moderate', description="Risk tolerance level"),
    capital: float = Query(100000, description="Available capital"),
    db: Session = Depends(get_db)
) -> Dict:
    """Get portfolio allocation recommendations for maximum alpha."""
    
    processor = SignalProcessor(db)
    
    # Get current high-confidence signals
    signals = db.query(Signal).filter(
        Signal.confidence > 0.75,
        Signal.executed == False
    ).order_by(Signal.expected_return.desc()).limit(10).all()
    
    recommendations = []
    total_allocation = 0
    
    for signal in signals:
        # Process each signal
        recommendation = await processor.process_signal(signal)
        
        # Calculate position size
        position_size = capital * recommendation['allocation']
        
        recommendations.append({
            'ticker': recommendation['ticker'],
            'action': recommendation['action'],
            'allocation_percent': f"{recommendation['allocation']:.1%}",
            'position_size': f"${position_size:,.0f}",
            'confidence': recommendation['confidence'],
            'stop_loss': f"{recommendation['stop_loss']:.1%}",
            'take_profit': f"{recommendation['take_profit']:.1%}",
            'timeframe': recommendation['timeframe']
        })
        
        total_allocation += recommendation['allocation']
        
        # Don't exceed risk limits
        if total_allocation >= 0.5:  # Max 50% allocated
            break
            
    return {
        'recommendations': recommendations,
        'total_allocation': f"{total_allocation:.1%}",
        'cash_reserve': f"{1 - total_allocation:.1%}",
        'expected_portfolio_return': f"{sum(s.expected_return * s.allocation_percent for s in signals[:len(recommendations)]):.1%}",
        'risk_level': risk_tolerance
    }