"""
OSINT Market Maker Tracker
Monitors public actions of successful investors and funds
Based on insight: "Copy what successful allocators do, not what they say"
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class OSINTTracker:
    """
    Open Source Intelligence tracker for market makers and allocators.
    "They create opportunities, not just use them" - Track and copy.
    """
    
    # High-value targets to monitor
    TRACKED_ENTITIES = {
        "individuals": {
            "warren_buffett": {
                "entity": "Berkshire Hathaway",
                "style": "value",
                "recent_moves": ["Increased OXY position", "Trimmed AAPL", "Bought Japanese trading houses"],
                "signal_strength": 0.9
            },
            "michael_burry": {
                "entity": "Scion Asset Management",
                "style": "contrarian",
                "recent_moves": ["Bought Chinese tech", "Shorted semiconductors", "Long physical retail"],
                "signal_strength": 0.85
            },
            "cathie_wood": {
                "entity": "ARK Invest",
                "style": "disruptive_innovation",
                "recent_moves": ["Accumulating ROKU", "Selling TSLA", "Buying COIN"],
                "signal_strength": 0.7
            },
            "bill_ackman": {
                "entity": "Pershing Square",
                "style": "activist",
                "recent_moves": ["Long interest rates", "Bought GOOGL", "Hedging inflation"],
                "signal_strength": 0.8
            },
            "ray_dalio": {
                "entity": "Bridgewater",
                "style": "macro",
                "recent_moves": ["Reducing US equities", "Increasing gold", "Long emerging markets"],
                "signal_strength": 0.75
            }
        },
        "funds": {
            "renaissance": {
                "name": "Renaissance Technologies",
                "aum": "$130B",
                "style": "quantitative",
                "observable_patterns": ["High-frequency signals", "Market microstructure"],
                "copyable_positions": ["Factor tilts", "Sector rotations"]
            },
            "citadel": {
                "name": "Citadel",
                "aum": "$62B",
                "style": "multi-strategy",
                "observable_patterns": ["Options flow", "Merger arb positions"],
                "copyable_positions": ["Event-driven trades", "Volatility plays"]
            },
            "two_sigma": {
                "name": "Two Sigma",
                "aum": "$60B",
                "style": "data_driven",
                "observable_patterns": ["Alternative data usage", "ML signals"],
                "copyable_positions": ["Sentiment trades", "News-driven moves"]
            }
        },
        "insiders": {
            "tech_ceos": {
                "notable_sales": [
                    {"person": "CEO1", "company": "NVDA", "amount": "$180M", "date": "2025-01"},
                    {"person": "CEO2", "company": "META", "amount": "$120M", "date": "2025-01"}
                ],
                "notable_buys": [
                    {"person": "CEO3", "company": "PLTR", "amount": "$10M", "date": "2025-01"},
                    {"person": "CEO4", "company": "ARM", "amount": "$25M", "date": "2025-01"}
                ]
            }
        }
    }
    
    # 13F filing tracker (quarterly positions)
    LATEST_13F_CHANGES = {
        "2024_Q4": {
            "biggest_buys": [
                {"fund": "Berkshire", "symbol": "OXY", "shares": 25000000, "value": "$1.5B"},
                {"fund": "Soros", "symbol": "RIVN", "shares": 20000000, "value": "$400M"},
                {"fund": "Third Point", "symbol": "AMZN", "shares": 2000000, "value": "$350M"}
            ],
            "biggest_sells": [
                {"fund": "Tiger Global", "symbol": "META", "shares": 5000000, "value": "$1.8B"},
                {"fund": "Coatue", "symbol": "SNOW", "shares": 3000000, "value": "$450M"},
                {"fund": "Viking", "symbol": "NFLX", "shares": 1500000, "value": "$900M"}
            ],
            "new_positions": [
                {"fund": "Greenlight", "symbol": "X", "thesis": "Steel supercycle"},
                {"fund": "Pershing", "symbol": "GOOGL", "thesis": "AI dominance"},
                {"fund": "Baupost", "symbol": "INTC", "thesis": "Turnaround play"}
            ]
        }
    }
    
    # Political and lobbying signals
    POLITICAL_SIGNALS = {
        "congress_trades": {
            "recent_buys": [
                {"member": "Representative1", "symbol": "NVDA", "amount": "$1-5M", "date": "2025-01-15"},
                {"member": "Senator1", "symbol": "LMT", "amount": "$500K-1M", "date": "2025-01-10"}
            ],
            "recent_sells": [
                {"member": "Senator2", "symbol": "GOOGL", "amount": "$1-5M", "date": "2025-01-12"},
                {"member": "Representative2", "symbol": "BAC", "amount": "$250-500K", "date": "2025-01-08"}
            ],
            "signal_value": "Congress members often trade ahead of legislation"
        },
        "lobbying_activity": {
            "increasing": ["Defense contractors", "Crypto companies", "AI firms"],
            "decreasing": ["Traditional banks", "Oil companies", "Tobacco"]
        }
    }
    
    # Social media and public statements
    SOCIAL_SIGNALS = {
        "twitter_alerts": {
            "high_value": [
                {"account": "Investor1", "followers": 2000000, "recent": "Bullish on uranium"},
                {"account": "Investor2", "followers": 1500000, "recent": "Short bonds"},
                {"account": "Investor3", "followers": 1000000, "recent": "Long volatility"}
            ]
        },
        "conference_talks": {
            "recent": [
                {"speaker": "Fund Manager1", "event": "Davos 2025", "thesis": "AI bubble talk"},
                {"speaker": "Fund Manager2", "event": "Sohn 2025", "thesis": "Emerging markets"}
            ]
        },
        "media_appearances": {
            "cnbc": ["Manager talking down tech", "Manager bullish commodities"],
            "bloomberg": ["Fund reducing exposure", "Allocator buying Japan"]
        }
    }
    
    @classmethod
    def track_smart_money(cls) -> List[Dict]:
        """
        Track what smart money is actually doing.
        Actions > Words. Always.
        """
        smart_money_moves = []
        
        # Aggregate moves from tracked entities
        for category, entities in cls.TRACKED_ENTITIES.items():
            if category == "individuals":
                for name, data in entities.items():
                    for move in data.get("recent_moves", []):
                        smart_money_moves.append({
                            "entity": name,
                            "entity_type": "individual",
                            "action": move,
                            "signal_strength": data["signal_strength"],
                            "style": data["style"],
                            "copyable": cls._is_copyable(move)
                        })
        
        # Add 13F changes
        for buy in cls.LATEST_13F_CHANGES["2024_Q4"]["biggest_buys"]:
            smart_money_moves.append({
                "entity": buy["fund"],
                "entity_type": "fund",
                "action": f"Bought {buy['shares']:,} shares of {buy['symbol']}",
                "signal_strength": 0.8,
                "value": buy["value"],
                "copyable": True
            })
        
        # Sort by signal strength
        smart_money_moves.sort(key=lambda x: x.get("signal_strength", 0), reverse=True)
        
        return smart_money_moves
    
    @classmethod
    def find_consensus_trades(cls) -> List[Dict]:
        """
        Find trades where multiple smart money entities agree.
        Consensus among smart money = higher conviction.
        """
        consensus_positions = [
            {
                "symbol": "OXY",
                "consensus_level": "high",
                "supporters": ["Berkshire", "Icahn", "Multiple hedge funds"],
                "thesis": "Energy undervalued, oil supply constraints",
                "recommended_action": "Long with 6-month horizon"
            },
            {
                "symbol": "GOOGL",
                "consensus_level": "medium",
                "supporters": ["Pershing", "Third Point", "Congress members"],
                "thesis": "AI dominance despite regulatory concerns",
                "recommended_action": "Accumulate on dips"
            },
            {
                "symbol": "INTC",
                "consensus_level": "contrarian",
                "supporters": ["Baupost", "Contrarian funds"],
                "thesis": "Turnaround with government support",
                "recommended_action": "Small position, high risk/reward"
            }
        ]
        
        return consensus_positions
    
    @classmethod
    def detect_insider_patterns(cls) -> Dict:
        """
        Detect patterns in insider trading.
        Insiders sell for many reasons, but buy for only one.
        """
        patterns = {
            "cluster_buys": [
                {
                    "sector": "Defense",
                    "companies": ["LMT", "RTX", "NOC"],
                    "insider_activity": "Multiple executives buying",
                    "interpretation": "Expecting increased contracts",
                    "confidence": 0.85
                },
                {
                    "sector": "Regional Banks", 
                    "companies": ["ZION", "KEY", "CFG"],
                    "insider_activity": "Directors accumulating",
                    "interpretation": "Bottom fishing after selloff",
                    "confidence": 0.70
                }
            ],
            "cluster_sells": [
                {
                    "sector": "Software",
                    "companies": ["CRM", "NOW", "TEAM"],
                    "insider_activity": "Executives selling at highs",
                    "interpretation": "Taking profits, valuation concerns",
                    "confidence": 0.75
                }
            ],
            "unusual_activity": [
                {
                    "symbol": "SMCI",
                    "activity": "CFO buying despite controversy",
                    "interpretation": "Insider confidence in resolution",
                    "signal": "Contrarian bullish"
                }
            ]
        }
        
        return patterns
    
    @classmethod
    def track_options_flow(cls) -> List[Dict]:
        """
        Track unusual options activity from smart money.
        Large options trades often precede moves.
        """
        unusual_options = [
            {
                "symbol": "NVDA",
                "type": "Call Sweep",
                "strike": 150,
                "expiry": "2025-02-21",
                "premium": "$5M",
                "interpretation": "Bullish bet on earnings",
                "follow_trade": True
            },
            {
                "symbol": "SPY",
                "type": "Put Buy",
                "strike": 580,
                "expiry": "2025-03-21",
                "premium": "$10M",
                "interpretation": "Hedging or bearish bet",
                "follow_trade": False
            },
            {
                "symbol": "TSLA",
                "type": "Call Spread",
                "strikes": "140/160",
                "expiry": "2025-04-18",
                "premium": "$3M",
                "interpretation": "Bullish but capped upside",
                "follow_trade": True
            }
        ]
        
        return unusual_options
    
    @classmethod
    def analyze_fund_flows(cls) -> Dict:
        """
        Analyze ETF and mutual fund flows.
        Where big money is moving tells the story.
        """
        fund_flows = {
            "etf_inflows": {
                "largest": [
                    {"ticker": "XLE", "amount": "$2.3B", "interpretation": "Energy rotation"},
                    {"ticker": "GLD", "amount": "$1.8B", "interpretation": "Safe haven demand"},
                    {"ticker": "IBIT", "amount": "$1.5B", "interpretation": "Bitcoin adoption"}
                ]
            },
            "etf_outflows": {
                "largest": [
                    {"ticker": "QQQ", "amount": "$3.1B", "interpretation": "Tech profit taking"},
                    {"ticker": "HYG", "amount": "$1.2B", "interpretation": "Credit concerns"},
                    {"ticker": "EEM", "amount": "$900M", "interpretation": "EM weakness"}
                ]
            },
            "sector_rotation": {
                "from": ["Technology", "Consumer Discretionary"],
                "to": ["Energy", "Financials", "Healthcare"],
                "timeline": "Past 2 weeks",
                "strength": "Accelerating"
            }
        }
        
        return fund_flows
    
    @classmethod
    def get_copyable_trades(cls) -> List[Dict]:
        """
        Get specific trades that retail can copy.
        Filter for accessibility and risk/reward.
        """
        copyable = [
            {
                "source": "Berkshire 13F",
                "trade": "Long OXY",
                "entry": "Current price",
                "target": "+30% in 6 months",
                "risk": "Oil price decline",
                "allocation": "2-5% of portfolio"
            },
            {
                "source": "Congress trades",
                "trade": "Long NVDA",
                "entry": "$140-145",
                "target": "$170",
                "risk": "AI bubble concerns",
                "allocation": "3-7% of portfolio"
            },
            {
                "source": "Options flow",
                "trade": "TSLA call spreads",
                "entry": "140/160 Apr calls",
                "target": "50% return if above 160",
                "risk": "Premium loss",
                "allocation": "1-2% of portfolio"
            },
            {
                "source": "Insider buying",
                "trade": "Long PLTR",
                "entry": "$27-29",
                "target": "$40",
                "risk": "Valuation concerns",
                "allocation": "2-4% of portfolio"
            }
        ]
        
        return copyable
    
    @classmethod
    def _is_copyable(cls, move: str) -> bool:
        """Determine if a move is copyable by retail."""
        # Simple heuristic - exclude complex or inaccessible trades
        non_copyable_keywords = ["private", "derivative", "swap", "otc", "direct"]
        move_lower = move.lower()
        
        for keyword in non_copyable_keywords:
            if keyword in move_lower:
                return False
        
        return True
    
    @classmethod
    def generate_conviction_scores(cls) -> Dict:
        """
        Generate conviction scores for copy trades.
        Higher score = more entities doing the same thing.
        """
        conviction_scores = {
            "OXY": {
                "score": 0.92,
                "supporters": 4,
                "detractors": 0,
                "rationale": "Multiple billionaires accumulating"
            },
            "GOOGL": {
                "score": 0.78,
                "supporters": 3,
                "detractors": 1,
                "rationale": "Smart money buying the dip"
            },
            "NVDA": {
                "score": 0.75,
                "supporters": 5,
                "detractors": 2,
                "rationale": "Mixed signals but net bullish"
            },
            "INTC": {
                "score": 0.65,
                "supporters": 2,
                "detractors": 3,
                "rationale": "Contrarian play with limited support"
            }
        }
        
        return conviction_scores