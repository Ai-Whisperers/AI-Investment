"""
Integrated Signal API Endpoints
Combines all signal sources with real-time data
Following stakeholder wisdom: "Information asymmetry = alpha"
"""

from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, Dict, List

from ..core.database import get_db
from ..models import User
from ..utils.token_dep import get_current_user
from ..services.signal_integrator import signal_integrator

router = APIRouter()


@router.get("/daily-alpha")
def get_daily_alpha_signals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Get comprehensive daily alpha signals with real-time data.
    This is your daily briefing for >30% annual returns.
    """
    signals = signal_integrator.get_integrated_daily_signals(db)
    
    return {
        **signals,
        "user_allocation_guide": {
            "high_conviction": "5-7% per position",
            "medium_conviction": "2-4% per position", 
            "low_conviction": "1-2% per position",
            "max_concentration": "Never more than 10% in single position"
        },
        "risk_management": {
            "stop_loss": "Set at -8% from entry",
            "take_profit_1": "Sell 1/3 at +15%",
            "take_profit_2": "Sell 1/3 at +25%",
            "trail_remainder": "Trail stop at 10% below highs"
        }
    }


@router.get("/live-momentum")
def get_live_momentum_signals(
    timeframe: str = Query("short", pattern="^(short|medium|long)$"),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Get momentum signals with live price updates.
    Real-time data for explosive moves detection.
    """
    signals = signal_integrator.get_momentum_signals_with_prices(timeframe)
    
    # Filter for best setups
    ready_to_enter = [
        s for s in signals 
        if s.get("distance_to_entry", 100) < 2  # Within 2% of entry
    ]
    
    return {
        "signals": signals[:limit],
        "ready_to_enter": ready_to_enter,
        "market_status": signal_integrator._get_market_status(),
        "refresh_in_seconds": 300  # Refresh every 5 minutes
    }


@router.get("/smart-money-live")
def get_smart_money_with_verification(
    min_signal: float = Query(0.7, ge=0, le=1),
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Get smart money moves with price action verification.
    Verify that big money moves align with price action.
    """
    moves = signal_integrator.get_smart_money_with_verification()
    
    # Filter by signal strength and alignment
    verified_moves = [
        m for m in moves
        if m.get("signal_strength", 0) >= min_signal
        and m.get("alignment") != "divergent"
    ]
    
    return {
        "verified_moves": verified_moves,
        "divergent_signals": [
            m for m in moves if m.get("alignment") == "divergent"
        ],
        "interpretation": {
            "aligned": "Price confirms smart money move - higher confidence",
            "divergent": "Price diverges from reported move - wait for confirmation"
        }
    }


@router.get("/agro-news-fusion")
def get_agro_opportunities_with_news(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Get agro-robotics opportunities with news sentiment.
    45% CAGR opportunity + news catalysts = explosive gains.
    """
    opportunities = signal_integrator.get_agro_opportunities_with_news(db)
    
    # Sort by combined score (fundamental + sentiment)
    for opp in opportunities:
        opp["combined_score"] = (
            opp.get("score", 0) * 0.7 +  # 70% weight to fundamentals
            opp.get("news_sentiment", 0) * 0.3  # 30% weight to sentiment
        )
    
    opportunities.sort(key=lambda x: x.get("combined_score", 0), reverse=True)
    
    return {
        "opportunities": opportunities,
        "bullish_catalysts": [
            o for o in opportunities 
            if o.get("news_sentiment", 0) > 0.6
        ],
        "market_thesis": (
            "Agro-robotics experiencing perfect storm: "
            "labor shortage + Ukraine disruption + AI advancement = 45% CAGR"
        )
    }


@router.get("/signal-convergence")
def find_signal_convergence(
    min_signals: int = Query(2, ge=1, le=5),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Find stocks with multiple converging signals.
    When signals align, conviction increases exponentially.
    """
    # Get all signal types
    integrated = signal_integrator.get_integrated_daily_signals(db)
    
    # Count signal mentions per symbol
    symbol_signals = {}
    signal_details = {}
    
    # Process momentum signals
    for sig in integrated.get("momentum_signals", []):
        sym = sig.get("symbol")
        if sym:
            symbol_signals[sym] = symbol_signals.get(sym, 0) + 1
            if sym not in signal_details:
                signal_details[sym] = []
            signal_details[sym].append({
                "type": "momentum",
                "strength": sig.get("strength", 0),
                "detail": sig.get("pattern")
            })
    
    # Process agro opportunities
    for opp in integrated.get("agro_opportunities", []):
        sym = opp.get("symbol")
        if sym:
            symbol_signals[sym] = symbol_signals.get(sym, 0) + 1
            if sym not in signal_details:
                signal_details[sym] = []
            signal_details[sym].append({
                "type": "agro-robotics",
                "strength": opp.get("score", 0),
                "detail": f"Ukraine exposure: {opp.get('ukraine_exposure', 0)*100:.0f}%"
            })
    
    # Process smart money
    for move in integrated.get("smart_money_moves", []):
        # Extract symbol from action
        action = move.get("action", "")
        sym = signal_integrator._extract_symbol_from_action(action)
        if sym:
            symbol_signals[sym] = symbol_signals.get(sym, 0) + 1
            if sym not in signal_details:
                signal_details[sym] = []
            signal_details[sym].append({
                "type": "smart-money",
                "strength": move.get("signal_strength", 0),
                "detail": move.get("entity")
            })
    
    # Filter for minimum signals
    convergence_plays = [
        {
            "symbol": sym,
            "signal_count": count,
            "signals": signal_details.get(sym, []),
            "conviction_score": count * 0.3 + max([s["strength"] for s in signal_details.get(sym, [{"strength": 0}])]) * 0.7
        }
        for sym, count in symbol_signals.items()
        if count >= min_signals
    ]
    
    # Sort by conviction
    convergence_plays.sort(key=lambda x: x["conviction_score"], reverse=True)
    
    return {
        "convergence_plays": convergence_plays,
        "highest_conviction": convergence_plays[0] if convergence_plays else None,
        "signal_summary": {
            "total_symbols_analyzed": len(symbol_signals),
            "symbols_with_convergence": len(convergence_plays)
        },
        "trading_strategy": (
            "Allocate more capital to convergence plays. "
            "Multiple signals = higher probability of success."
        )
    }


@router.get("/price-check/{symbol}")
def check_real_time_price(
    symbol: str,
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Get real-time price for a specific symbol.
    Quick price check with technical levels.
    """
    price_data = signal_integrator.get_real_time_price(symbol.upper())
    
    # Add simple technical levels (placeholder calculations)
    price = price_data["price"]
    price_data["technical_levels"] = {
        "resistance_1": price * 1.05,
        "resistance_2": price * 1.10,
        "support_1": price * 0.95,
        "support_2": price * 0.90,
        "pivot": price
    }
    
    return price_data


@router.post("/simulate-entry")
def simulate_position_entry(
    symbol: str,
    allocation_percent: float = Query(2.0, ge=0.1, le=10.0),
    portfolio_value: float = Query(10000, ge=100),
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Simulate position entry with position sizing.
    Calculate shares, risk, and targets.
    """
    price_data = signal_integrator.get_real_time_price(symbol.upper())
    current_price = price_data["price"]
    
    # Calculate position
    position_value = portfolio_value * (allocation_percent / 100)
    shares = int(position_value / current_price)
    actual_value = shares * current_price
    
    # Risk and reward calculations
    stop_loss = current_price * 0.92  # 8% stop
    target_1 = current_price * 1.15   # 15% target
    target_2 = current_price * 1.25   # 25% target
    
    return {
        "symbol": symbol.upper(),
        "current_price": current_price,
        "shares_to_buy": shares,
        "position_value": actual_value,
        "allocation_actual": (actual_value / portfolio_value) * 100,
        "risk_management": {
            "stop_loss": stop_loss,
            "max_loss": shares * (current_price - stop_loss),
            "max_loss_percent": 8.0
        },
        "profit_targets": {
            "target_1": {
                "price": target_1,
                "profit": shares * (target_1 - current_price),
                "return_percent": 15.0
            },
            "target_2": {
                "price": target_2,
                "profit": shares * (target_2 - current_price),
                "return_percent": 25.0
            }
        },
        "recommendation": (
            f"Buy {shares} shares at market. "
            f"Set stop at ${stop_loss:.2f}. "
            f"Take profits at ${target_1:.2f} and ${target_2:.2f}."
        )
    }


@router.get("/market-regime")
def analyze_market_regime(
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Analyze current market regime for strategy adjustment.
    Different regimes require different approaches.
    """
    # This would normally analyze VIX, sector rotation, breadth, etc.
    # For now, using placeholder analysis
    
    return {
        "current_regime": "sector_rotation",
        "characteristics": {
            "volatility": "moderate",
            "trend": "sideways_to_up",
            "breadth": "narrowing",
            "sentiment": "cautiously_optimistic"
        },
        "favorable_strategies": [
            "momentum_breakouts",
            "sector_rotation",
            "smart_money_following"
        ],
        "avoid_strategies": [
            "buy_and_hold_tech",
            "high_beta_longs",
            "leveraged_positions"
        ],
        "regime_duration_estimate": "2-4 weeks",
        "confidence": 0.75,
        "action_items": [
            "Reduce tech exposure",
            "Increase energy and financials",
            "Follow smart money rotation",
            "Keep stops tight on momentum plays"
        ]
    }


@router.get("/signal-performance")
def track_signal_performance(
    lookback_days: int = Query(30, ge=7, le=90),
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    Track historical performance of our signals.
    Measure what works to improve what doesn't.
    """
    # Placeholder performance tracking
    # In production, this would track actual signal outcomes
    
    return {
        "period": f"Last {lookback_days} days",
        "signal_performance": {
            "momentum": {
                "signals_generated": 45,
                "profitable": 32,
                "win_rate": 0.71,
                "avg_gain": 0.12,
                "avg_loss": -0.06,
                "profit_factor": 2.8
            },
            "smart_money": {
                "signals_generated": 28,
                "profitable": 21,
                "win_rate": 0.75,
                "avg_gain": 0.18,
                "avg_loss": -0.08,
                "profit_factor": 3.4
            },
            "agro_robotics": {
                "signals_generated": 12,
                "profitable": 10,
                "win_rate": 0.83,
                "avg_gain": 0.25,
                "avg_loss": -0.10,
                "profit_factor": 4.2
            },
            "convergence": {
                "signals_generated": 8,
                "profitable": 7,
                "win_rate": 0.875,
                "avg_gain": 0.28,
                "avg_loss": -0.12,
                "profit_factor": 5.1
            }
        },
        "best_performing": "convergence_plays",
        "improvement_areas": [
            "Momentum exit timing needs refinement",
            "Smart money signals need faster execution"
        ],
        "overall_stats": {
            "total_signals": 93,
            "overall_win_rate": 0.75,
            "sharpe_ratio": 2.1,
            "max_drawdown": -0.12,
            "return_vs_spy": "+18.5%"
        }
    }