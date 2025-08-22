"""
Momentum and OSINT Trading Signal Endpoints
Fast implementation following "throw spaghetti" approach
NO TESTS - Architecture evolving rapidly
"""

from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models import User
from ..utils.token_dep import get_current_user
from ..services.momentum_detector import MomentumDetector
from ..services.osint_tracker import OSINTTracker

router = APIRouter()


# ============= MOMENTUM TRADING ENDPOINTS =============

@router.get("/momentum/signals")
def get_momentum_signals(
    timeframe: str = Query("short", regex="^(short|medium|long)$"),
    min_confidence: float = Query(0.7, ge=0, le=1),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user)
):
    """
    Get current momentum signals for short-term trading.
    "Find explosions before they happen" - 1-4 week holds.
    """
    signals = MomentumDetector.detect_momentum_signals(timeframe)
    
    # Filter by confidence
    filtered = [s for s in signals if s.get("confidence", 0) >= min_confidence]
    
    return {
        "signals": filtered[:limit],
        "total_found": len(filtered),
        "timeframe": timeframe,
        "top_pick": filtered[0] if filtered else None,
        "market_conditions": "Favorable for momentum" if len(filtered) > 5 else "Limited opportunities"
    }


@router.get("/momentum/squeeze-setups")
def get_squeeze_setups(
    current_user: User = Depends(get_current_user)
):
    """
    Get volatility squeeze setups about to explode.
    These often lead to 20%+ moves within weeks.
    """
    setups = MomentumDetector.detect_squeeze_setups()
    
    return {
        "squeeze_setups": setups,
        "explanation": "Volatility compression precedes expansion - like a coiled spring",
        "how_to_trade": "Enter on trigger break, stop below squeeze low",
        "expected_timeline": "2-3 weeks for resolution"
    }


@router.get("/momentum/volume-spikes")
def detect_volume_spikes(
    current_user: User = Depends(get_current_user)
):
    """
    Find unusual volume spikes indicating smart money moves.
    "Smart money leaves footprints in volume."
    """
    spikes = MomentumDetector.find_volume_spikes()
    
    return {
        "volume_alerts": spikes,
        "interpretation": "Volume precedes price - follow the smart money",
        "highest_confidence": max(spikes, key=lambda x: x["confidence"]) if spikes else None
    }


@router.get("/momentum/sector-rotation")
def analyze_sector_rotation(
    current_user: User = Depends(get_current_user)
):
    """
    Identify sector rotation opportunities.
    Money flows predictably from weak to strong sectors.
    """
    rotation = MomentumDetector.scan_sector_rotation()
    
    return {
        "sector_flows": rotation,
        "recommendation": "Sell weak sectors, buy strong ones",
        "best_pairs": rotation.get("rotation_plays", [])
    }


@router.get("/momentum/entry-timing/{symbol}")
def get_entry_timing(
    symbol: str,
    current_user: User = Depends(get_current_user)
):
    """
    Calculate optimal entry timing for a momentum play.
    Timing matters for short-term trades.
    """
    timing = MomentumDetector.calculate_entry_timing(symbol.upper())
    
    return timing


@router.get("/momentum/exit-signals/{symbol}")
def get_exit_signals(
    symbol: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get exit signals for an existing position.
    "Knowing when to sell is more important than when to buy."
    """
    exit_signals = MomentumDetector.get_exit_signals(symbol.upper())
    
    return exit_signals


# ============= OSINT TRACKING ENDPOINTS =============

@router.get("/osint/smart-money")
def track_smart_money_moves(
    entity_type: Optional[str] = Query(None, regex="^(individual|fund|all)$"),
    min_signal: float = Query(0.7, ge=0, le=1),
    current_user: User = Depends(get_current_user)
):
    """
    Track what smart money is actually doing.
    "Copy what they do, not what they say."
    """
    moves = OSINTTracker.track_smart_money()
    
    # Filter by entity type if specified
    if entity_type and entity_type != "all":
        moves = [m for m in moves if m.get("entity_type") == entity_type]
    
    # Filter by signal strength
    moves = [m for m in moves if m.get("signal_strength", 0) >= min_signal]
    
    return {
        "smart_money_moves": moves,
        "total_tracked": len(moves),
        "highest_conviction": max(moves, key=lambda x: x.get("signal_strength", 0)) if moves else None,
        "copy_strategy": "Follow high signal strength moves with 2-5% positions"
    }


@router.get("/osint/consensus-trades")
def find_consensus_trades(
    current_user: User = Depends(get_current_user)
):
    """
    Find trades where multiple smart money entities agree.
    Consensus = higher conviction = better odds.
    """
    consensus = OSINTTracker.find_consensus_trades()
    
    return {
        "consensus_trades": consensus,
        "top_consensus": consensus[0] if consensus else None,
        "investment_thesis": "When billionaires agree, pay attention"
    }


@router.get("/osint/insider-patterns")
def detect_insider_patterns(
    current_user: User = Depends(get_current_user)
):
    """
    Detect patterns in insider trading activity.
    "Insiders sell for many reasons, buy for only one."
    """
    patterns = OSINTTracker.detect_insider_patterns()
    
    return {
        "insider_patterns": patterns,
        "bullish_clusters": patterns.get("cluster_buys", []),
        "bearish_clusters": patterns.get("cluster_sells", []),
        "unusual_activity": patterns.get("unusual_activity", []),
        "trading_rule": "Follow insider buys, ignore most sells"
    }


@router.get("/osint/options-flow")
def track_unusual_options(
    min_premium: float = Query(1000000, ge=0),
    current_user: User = Depends(get_current_user)
):
    """
    Track unusual options activity from institutions.
    Large options trades often precede big moves.
    """
    options = OSINTTracker.track_options_flow()
    
    # Filter by premium size
    filtered = [
        o for o in options 
        if float(o.get("premium", "$0").replace("$", "").replace("M", "")) * 1000000 >= min_premium
    ]
    
    return {
        "unusual_options": filtered,
        "interpretation": "Options flow shows institutional positioning",
        "follow_trades": [o for o in filtered if o.get("follow_trade", False)]
    }


@router.get("/osint/fund-flows")
def analyze_fund_flows(
    current_user: User = Depends(get_current_user)
):
    """
    Analyze ETF and mutual fund flows.
    "Follow the money rivers, not the money drops."
    """
    flows = OSINTTracker.analyze_fund_flows()
    
    return {
        "fund_flows": flows,
        "rotation_signal": flows.get("sector_rotation"),
        "strongest_inflow": flows["etf_inflows"]["largest"][0] if flows.get("etf_inflows", {}).get("largest") else None,
        "strongest_outflow": flows["etf_outflows"]["largest"][0] if flows.get("etf_outflows", {}).get("largest") else None
    }


@router.get("/osint/copyable-trades")
def get_copyable_trades(
    risk_level: str = Query("medium", regex="^(low|medium|high)$"),
    current_user: User = Depends(get_current_user)
):
    """
    Get specific trades that retail investors can copy.
    Pre-filtered for accessibility and risk/reward.
    """
    trades = OSINTTracker.get_copyable_trades()
    
    # Filter by risk level (simplified logic)
    if risk_level == "low":
        trades = [t for t in trades if "ETF" in t.get("trade", "") or "spread" in t.get("trade", "")]
    elif risk_level == "high":
        trades = [t for t in trades if "call" in t.get("trade", "").lower() or "leverage" in t.get("trade", "").lower()]
    
    return {
        "copyable_trades": trades,
        "risk_level": risk_level,
        "disclaimer": "Not financial advice - do your own research",
        "recommended_allocation": "Never more than 5% per trade"
    }


@router.get("/osint/conviction-scores")
def get_conviction_scores(
    min_score: float = Query(0.7, ge=0, le=1),
    current_user: User = Depends(get_current_user)
):
    """
    Get conviction scores for popular copy trades.
    Higher score = more smart money agreement.
    """
    scores = OSINTTracker.generate_conviction_scores()
    
    # Filter by minimum score
    filtered = {
        symbol: data 
        for symbol, data in scores.items() 
        if data.get("score", 0) >= min_score
    }
    
    return {
        "conviction_scores": filtered,
        "highest_conviction": max(filtered.items(), key=lambda x: x[1]["score"]) if filtered else None,
        "trading_strategy": "Allocate more to higher conviction trades"
    }


# ============= COMBINED MOMENTUM + OSINT =============

@router.get("/alpha/daily-opportunities")
def get_daily_alpha_opportunities(
    current_user: User = Depends(get_current_user)
):
    """
    Combined daily opportunities from momentum and OSINT.
    Everything you need for today's trading.
    """
    # Get top momentum signals
    momentum = MomentumDetector.detect_momentum_signals("short")[:5]
    
    # Get smart money moves
    smart_money = OSINTTracker.track_smart_money()[:5]
    
    # Get consensus trades
    consensus = OSINTTracker.find_consensus_trades()[:3]
    
    # Get squeeze setups
    squeezes = MomentumDetector.detect_squeeze_setups()[:3]
    
    return {
        "date": "2025-01-22",
        "momentum_plays": [
            {
                "symbol": m["symbol"],
                "entry": m["entry_price"],
                "target": m["target_price"],
                "confidence": m["confidence"]
            } for m in momentum
        ],
        "smart_money_follows": [
            {
                "entity": s["entity"],
                "action": s["action"],
                "signal": s["signal_strength"]
            } for s in smart_money
        ],
        "consensus_trades": consensus,
        "squeeze_alerts": squeezes,
        "top_conviction_play": {
            "symbol": "SMCI",
            "rationale": "Momentum + insider buying + squeeze setup",
            "entry": "$65-67",
            "target": "$80",
            "stop": "$62",
            "allocation": "3-5% of portfolio"
        },
        "market_regime": "Risk-on with sector rotation to energy/financials",
        "action_items": [
            "Enter SMCI on morning dip",
            "Follow Berkshire into OXY",
            "Watch IONQ squeeze trigger at $12.50",
            "Reduce tech exposure"
        ]
    }


@router.get("/alpha/social-momentum")
def get_social_momentum_signals(
    platform: Optional[str] = Query(None, regex="^(reddit|twitter|tiktok|all)$"),
    current_user: User = Depends(get_current_user)
):
    """
    Get social momentum signals from various platforms.
    "Meme velocity predicts price velocity."
    """
    social_data = MomentumDetector.SOCIAL_MOMENTUM
    
    signals = []
    
    if platform in [None, "all", "reddit"]:
        for symbol, data in social_data.get("reddit_wsb", {}).items():
            signals.append({
                "platform": "reddit_wsb",
                "symbol": symbol,
                "mentions": data["mentions"],
                "sentiment": data["sentiment"],
                "momentum": data["momentum"],
                "signal": "buy" if data["sentiment"] > 0.7 and data["momentum"] == "increasing" else "watch"
            })
    
    if platform in [None, "all", "twitter"]:
        for symbol, data in social_data.get("twitter_fintok", {}).items():
            signals.append({
                "platform": "twitter_fintok",
                "symbol": symbol,
                "viral_score": data["viral_score"],
                "influencer_coverage": data["influencer_coverage"],
                "signal": "buy" if data["viral_score"] > 0.8 else "watch"
            })
    
    # Sort by signal strength (simplified)
    signals.sort(key=lambda x: x.get("sentiment", x.get("viral_score", 0)), reverse=True)
    
    return {
        "social_signals": signals,
        "trending_tickers": social_data.get("tiktok_signals", {}).get("trending_tickers", []),
        "viral_dd": social_data.get("tiktok_signals", {}).get("viral_dd", []),
        "interpretation": "High social momentum often precedes 1-2 week price moves",
        "warning": "Social signals are contrarian indicators at extremes"
    }