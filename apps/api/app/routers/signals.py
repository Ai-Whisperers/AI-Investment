"""
Signal Detection API Endpoints
Exposes agro-robotics, regulatory, and supply chain signals
Following "throw spaghetti" approach - ship fast, iterate later
"""

from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models import User
from ..utils.token_dep import get_current_user
from ..services.agro_robotics_tracker import AgroRoboticsTracker
from ..services.regulatory_tracker import RegulatoryTracker
from ..services.supply_chain_mapper import SupplyChainMapper

router = APIRouter()


# ============= AGRO-ROBOTICS ENDPOINTS =============

@router.get("/agro-robotics/opportunities")
def get_agro_opportunities(
    limit: int = Query(10, ge=1, le=50),
    min_ukraine_exposure: Optional[float] = Query(None, ge=0, le=1),
    min_ai_exposure: Optional[float] = Query(None, ge=0, le=1),
    category: Optional[str] = Query(None, regex="^(established|diversified|emerging)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get top agro-robotics investment opportunities.
    This is our highest conviction play - 45% CAGR expected.
    """
    filters = {}
    if min_ukraine_exposure is not None:
        filters["min_ukraine_exposure"] = min_ukraine_exposure
    if min_ai_exposure is not None:
        filters["min_ai_exposure"] = min_ai_exposure
    if category:
        filters["category"] = category
    
    opportunities = AgroRoboticsTracker.screen_for_opportunities(db, filters)
    
    return {
        "opportunities": opportunities[:limit],
        "total_found": len(opportunities),
        "filters_applied": filters,
        "market_thesis": "Labor shortage + AI = 45% CAGR opportunity"
    }


@router.get("/agro-robotics/ukraine-analysis")
def analyze_ukraine_opportunity(
    current_user: User = Depends(get_current_user)
):
    """
    Analyze Ukraine agro-robotics opportunity.
    $150M FAO investment + war-driven adoption = alpha.
    """
    return AgroRoboticsTracker.analyze_ukraine_opportunity()


@router.get("/agro-robotics/catalysts")
def get_agro_catalysts(
    current_user: User = Depends(get_current_user)
):
    """Get upcoming catalyst events for agro-robotics sector."""
    return {
        "catalysts": AgroRoboticsTracker.get_catalyst_events(),
        "recommendation": "Position before Q2 2025 planting season"
    }


# ============= REGULATORY SIGNAL ENDPOINTS =============

@router.get("/regulatory/upcoming-catalysts")
def get_regulatory_catalysts(
    horizon_days: int = Query(90, ge=7, le=365),
    region: Optional[str] = Query(None, regex="^(US|EU|China)$"),
    current_user: User = Depends(get_current_user)
):
    """
    Get upcoming regulatory catalysts.
    Regulations = predictable gains. EU mandates especially powerful.
    """
    catalysts = RegulatoryTracker.get_upcoming_catalysts(horizon_days)
    
    if region:
        catalysts = [c for c in catalysts if c["region"] == region]
    
    return {
        "catalysts": catalysts,
        "total_events": len(catalysts),
        "investment_strategy": "Buy beneficiaries 30-60 days before implementation"
    }


@router.get("/regulatory/spending-opportunities")
def get_spending_opportunities(
    min_growth: float = Query(0.15, ge=0, le=1),
    current_user: User = Depends(get_current_user)
):
    """
    Track government spending opportunities.
    Follow the money from government to contractors.
    """
    opportunities = RegulatoryTracker.get_spending_opportunities(min_growth)
    
    return {
        "opportunities": opportunities,
        "total_budget": sum(
            RegulatoryTracker._parse_budget(o["budget"]) 
            for o in opportunities
        ),
        "top_pick": opportunities[0] if opportunities else None
    }


@router.get("/regulatory/policy-changes")
def track_policy_changes(
    current_user: User = Depends(get_current_user)
):
    """
    Track real-time policy changes.
    Early detection of policy shifts = alpha generation.
    """
    return {
        "recent_changes": RegulatoryTracker.track_policy_changes(),
        "monitoring_sources": ["EU Commission", "USDA", "SEC", "Congress"]
    }


# ============= SUPPLY CHAIN ENDPOINTS =============

@router.get("/supply-chain/map/{symbol}")
def map_supply_chain(
    symbol: str,
    current_user: User = Depends(get_current_user)
):
    """
    Map supply chain dependencies for a company.
    Understand dependencies = predict impacts.
    """
    dependencies = SupplyChainMapper.map_dependencies(symbol.upper())
    
    if "error" in dependencies:
        raise HTTPException(status_code=404, detail=dependencies["error"])
    
    return dependencies


@router.get("/supply-chain/ukraine-impact")
def analyze_ukraine_supply_impact(
    current_user: User = Depends(get_current_user)
):
    """
    Analyze Ukraine supply chain impacts.
    Disruption creates both risks and opportunities.
    """
    return SupplyChainMapper.analyze_ukraine_impact()


@router.post("/supply-chain/disruption-analysis")
def analyze_disruption(
    disrupted_entity: str,
    current_user: User = Depends(get_current_user)
):
    """
    Find beneficiaries of supply chain disruptions.
    One company's problem = another's opportunity.
    """
    beneficiaries = SupplyChainMapper.find_disruption_beneficiaries(disrupted_entity)
    cascade = SupplyChainMapper.predict_cascade_effects(disrupted_entity)
    
    return {
        "disrupted_entity": disrupted_entity,
        "beneficiaries": beneficiaries,
        "cascade_effects": cascade,
        "investment_thesis": f"Short affected companies, long beneficiaries"
    }


# ============= COMBINED SIGNAL ENDPOINTS =============

@router.get("/signals/top-opportunities")
def get_top_opportunities(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """
    Get top opportunities across all signal types.
    Combines agro, regulatory, and supply chain signals.
    """
    opportunities = []
    
    # Get agro opportunities
    agro = AgroRoboticsTracker.get_top_opportunities(limit=10)
    for opp in agro[:5]:
        opportunities.append({
            "type": "agro-robotics",
            "symbol": opp["symbol"],
            "score": opp["score"],
            "reason": f"Agro-robotics play with {opp.get('ukraine_exposure', 0)*100:.0f}% Ukraine exposure"
        })
    
    # Get regulatory opportunities  
    reg_catalysts = RegulatoryTracker.get_upcoming_catalysts(90)
    for catalyst in reg_catalysts[:5]:
        for beneficiary in catalyst.get("beneficiaries", [])[:2]:
            opportunities.append({
                "type": "regulatory",
                "symbol": beneficiary,
                "score": catalyst["confidence"],
                "reason": f"{catalyst['regulation']} in {catalyst['days_until']} days"
            })
    
    # Get supply chain opportunities
    ukraine_impact = SupplyChainMapper.analyze_ukraine_impact()
    for ben in ukraine_impact.get("beneficiary_companies", [])[:5]:
        opportunities.append({
            "type": "supply-chain",
            "symbol": ben["symbol"],
            "score": 0.7,  # Default score
            "reason": ben["reason"]
        })
    
    # Sort by score and deduplicate
    seen = set()
    unique_opportunities = []
    for opp in sorted(opportunities, key=lambda x: x["score"], reverse=True):
        if opp["symbol"] not in seen:
            seen.add(opp["symbol"])
            unique_opportunities.append(opp)
    
    return {
        "opportunities": unique_opportunities[:limit],
        "signal_mix": {
            "agro": len([o for o in unique_opportunities if o["type"] == "agro-robotics"]),
            "regulatory": len([o for o in unique_opportunities if o["type"] == "regulatory"]),
            "supply_chain": len([o for o in unique_opportunities if o["type"] == "supply-chain"])
        },
        "top_conviction": unique_opportunities[0] if unique_opportunities else None
    }


@router.get("/signals/daily-brief")
def get_daily_signal_brief(
    current_user: User = Depends(get_current_user)
):
    """
    Get daily signal brief with actionable insights.
    Everything you need to know in one call.
    """
    return {
        "date": "2025-01-22",
        "top_opportunities": get_top_opportunities(limit=5, current_user=current_user)["opportunities"],
        "ukraine_spotlight": {
            "agro": AgroRoboticsTracker.analyze_ukraine_opportunity(),
            "supply_chain": SupplyChainMapper.analyze_ukraine_impact()
        },
        "regulatory_watch": RegulatoryTracker.get_upcoming_catalysts(30)[:3],
        "market_thesis": (
            "Three converging opportunities: "
            "1) Agro-robotics adoption accelerating (45% CAGR), "
            "2) Regulatory catalysts creating predictable gains, "
            "3) Supply chain disruptions favoring prepared companies"
        ),
        "action_items": [
            "Position in DE and AGCO for agro-robotics",
            "Watch EU sustainable agriculture mandate (March)",
            "Monitor Ukraine spring planting season impact"
        ]
    }


# ============= EXTREME SIGNAL DETECTION ENDPOINTS =============

@router.get("/extreme/active")
async def get_active_extreme_signals(
    limit: int = Query(20, le=100),
    min_confidence: float = Query(0.7, ge=0, le=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get active extreme signals with >30% expected returns."""
    from ..models import Signal
    from ..services.signal_processor import SignalProcessor
    
    processor = SignalProcessor(db)
    signals = processor.get_active_signals(limit)
    
    # Filter for high confidence extreme signals
    extreme_signals = [
        s for s in signals 
        if s.get('confidence', 0) >= min_confidence 
        and s.get('expected_return', 0) >= 0.30
    ]
    
    return {
        "signals": extreme_signals,
        "count": len(extreme_signals),
        "avg_expected_return": sum(s['expected_return'] for s in extreme_signals) / len(extreme_signals) if extreme_signals else 0,
        "thesis": "Multi-layer pattern detection targeting >30% returns"
    }


@router.post("/extreme/scan")
async def scan_for_extreme_signals(
    data: Dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Scan data sources for extreme alpha opportunities."""
    from ..services.signal_processor import SignalProcessor
    
    processor = SignalProcessor(db)
    signals = await processor.scan_all_sources(data)
    
    return {
        "signals_detected": len(signals),
        "extreme_count": sum(1 for s in signals if s.signal_type == 'extreme'),
        "meme_count": sum(1 for s in signals if s.signal_type == 'meme'),
        "divergence_count": sum(1 for s in signals if s.signal_type == 'divergence'),
        "top_signals": [s.to_dict() for s in signals[:5]]
    }


@router.get("/extreme/performance")
async def get_extreme_signal_performance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get performance metrics for extreme signals."""
    from ..services.signal_processor import SignalProcessor
    
    processor = SignalProcessor(db)
    performance = processor.get_signal_performance()
    
    return {
        **performance,
        "target_annual_return": "35%",
        "strategy": "Compound small wins + extreme events"
    }


@router.get("/extreme/meme-velocity/{ticker}")
async def get_meme_velocity_data(
    ticker: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Track meme velocity for potential 50-400% returns."""
    from ..models import MemeVelocity
    from datetime import datetime, timedelta
    
    velocities = db.query(MemeVelocity).filter_by(
        ticker=ticker.upper()
    ).order_by(MemeVelocity.timestamp.desc()).limit(24).all()
    
    if not velocities:
        return {
            "ticker": ticker.upper(),
            "status": "not_tracking",
            "message": "No velocity data available"
        }
    
    current = velocities[0]
    
    return {
        "ticker": ticker.upper(),
        "current_velocity": current.velocity,
        "acceleration": current.acceleration,
        "signal": "BUY" if current.acceleration > 5 else "WATCH",
        "expected_return": "50-400%" if current.acceleration > 5 else "Monitor",
        "platforms": {
            "reddit": current.reddit_score,
            "twitter": current.twitter_score,
            "tiktok": current.tiktok_score,
            "discord": current.discord_score,
            "youtube": current.youtube_score
        }
    }


@router.get("/extreme/forty-eight-hour")
async def get_forty_eight_hour_signals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get signals detected 48 hours before mainstream."""
    from ..models import Signal
    from datetime import datetime, timedelta
    
    signals = db.query(Signal).filter(
        Signal.pattern_type == 'forty_eight_hour',
        Signal.executed == False,
        Signal.created_at > datetime.utcnow() - timedelta(hours=48)
    ).order_by(Signal.confidence.desc()).all()
    
    return {
        "signals": [
            {
                "ticker": s.ticker,
                "confidence": s.confidence,
                "expected_return": s.expected_return,
                "hours_until_mainstream": max(0, 48 - (datetime.utcnow() - s.created_at).total_seconds() / 3600),
                "sources": s.sources
            } for s in signals
        ],
        "count": len(signals),
        "strategy": "Early detection from 4chan, Discord, small subreddits"
    }


@router.get("/extreme/divergence")
async def get_smart_money_divergence(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Find divergence between institutional and retail sentiment."""
    from ..models import InformationAsymmetry
    from datetime import datetime, timedelta
    
    asymmetries = db.query(InformationAsymmetry).filter(
        InformationAsymmetry.resolved_at == None,
        InformationAsymmetry.divergence_score > 0.4
    ).order_by(InformationAsymmetry.divergence_score.desc()).limit(10).all()
    
    return {
        "opportunities": [
            {
                "ticker": a.ticker,
                "retail_sentiment": a.retail_sentiment,
                "institutional_sentiment": a.institutional_sentiment,
                "divergence": a.divergence_score,
                "action": "BUY" if a.institutional_sentiment > a.retail_sentiment else "SHORT",
                "entry_window": a.entry_window
            } for a in asymmetries
        ],
        "count": len(asymmetries),
        "thesis": "Follow smart money when retail disagrees"
    }


@router.get("/extreme/strategy-returns")
async def calculate_strategy_returns(
    initial_capital: float = Query(100000, description="Starting capital")
):
    """Calculate expected returns from extreme signal strategy."""
    from ..services.signal_processor import ExtremeReturnsStrategy
    
    strategy = ExtremeReturnsStrategy()
    
    compound = strategy.compound_small_wins(initial_capital)
    extreme = strategy.extreme_event_strategy(initial_capital)
    
    return {
        "compound_strategy": compound,
        "extreme_strategy": extreme,
        "recommendation": "Mix both strategies for optimal risk-adjusted returns",
        "target": "35%+ annual returns"
    }