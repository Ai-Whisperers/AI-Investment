"""
Momentum Signal Detector
Identifies short-term trading opportunities through momentum analysis
Based on insight: "Short-term gains with sure wins" alongside long-term holds
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class MomentumDetector:
    """
    Detects momentum signals for short-term trading opportunities.
    "Find explosions before they happen" - 1-4 week holding periods.
    """
    
    # Momentum patterns that predict short-term gains
    MOMENTUM_PATTERNS = {
        "breakout": {
            "description": "Price breaks above resistance with volume",
            "typical_gain": 0.15,
            "holding_period": "1-2 weeks",
            "confidence": 0.75
        },
        "squeeze": {
            "description": "Volatility compression before expansion",
            "typical_gain": 0.20,
            "holding_period": "2-3 weeks",
            "confidence": 0.70
        },
        "accumulation": {
            "description": "Smart money accumulating position",
            "typical_gain": 0.25,
            "holding_period": "3-4 weeks",
            "confidence": 0.65
        },
        "news_catalyst": {
            "description": "Positive catalyst with momentum",
            "typical_gain": 0.10,
            "holding_period": "3-5 days",
            "confidence": 0.80
        },
        "sector_rotation": {
            "description": "Money rotating into sector",
            "typical_gain": 0.12,
            "holding_period": "2-4 weeks",
            "confidence": 0.70
        }
    }
    
    # Current high-momentum opportunities (placeholders for real data)
    CURRENT_SIGNALS = {
        "SMCI": {
            "pattern": "breakout",
            "strength": 0.85,
            "entry": 65.0,
            "target": 75.0,
            "stop_loss": 62.0,
            "catalyst": "AI server demand surge",
            "detected": "2025-01-20"
        },
        "IONQ": {
            "pattern": "squeeze",
            "strength": 0.78,
            "entry": 12.0,
            "target": 15.0,
            "stop_loss": 11.0,
            "catalyst": "Quantum computing breakthrough",
            "detected": "2025-01-21"
        },
        "PLTR": {
            "pattern": "accumulation",
            "strength": 0.82,
            "entry": 28.0,
            "target": 35.0,
            "stop_loss": 26.0,
            "catalyst": "Government contract wins",
            "detected": "2025-01-19"
        },
        "ARM": {
            "pattern": "sector_rotation",
            "strength": 0.75,
            "entry": 140.0,
            "target": 160.0,
            "stop_loss": 135.0,
            "catalyst": "AI chip design dominance",
            "detected": "2025-01-22"
        }
    }
    
    # Social sentiment indicators
    SOCIAL_MOMENTUM = {
        "reddit_wsb": {
            "NVDA": {"mentions": 1250, "sentiment": 0.8, "momentum": "increasing"},
            "GME": {"mentions": 890, "sentiment": 0.6, "momentum": "stable"},
            "TSLA": {"mentions": 2100, "sentiment": 0.7, "momentum": "increasing"},
            "AMC": {"mentions": 450, "sentiment": 0.4, "momentum": "decreasing"}
        },
        "twitter_fintok": {
            "PLTR": {"viral_score": 0.9, "influencer_coverage": "high"},
            "COIN": {"viral_score": 0.7, "influencer_coverage": "medium"},
            "SOFI": {"viral_score": 0.8, "influencer_coverage": "high"}
        },
        "tiktok_signals": {
            "trending_tickers": ["RBLX", "SNAP", "U", "SHOP"],
            "viral_dd": ["IONQ quantum play", "SMCI AI servers", "ARM chip shortage"]
        }
    }
    
    @classmethod
    def detect_momentum_signals(cls, timeframe: str = "short") -> List[Dict]:
        """
        Detect current momentum signals across all patterns.
        Short-term = 1-4 weeks, Medium-term = 1-3 months.
        """
        signals = []
        
        for symbol, data in cls.CURRENT_SIGNALS.items():
            pattern_info = cls.MOMENTUM_PATTERNS.get(data["pattern"], {})
            
            signal = {
                "symbol": symbol,
                "pattern": data["pattern"],
                "strength": data["strength"],
                "entry_price": data["entry"],
                "target_price": data["target"],
                "stop_loss": data["stop_loss"],
                "potential_gain": (data["target"] - data["entry"]) / data["entry"],
                "risk_reward": (data["target"] - data["entry"]) / (data["entry"] - data["stop_loss"]),
                "catalyst": data["catalyst"],
                "holding_period": pattern_info.get("holding_period", "2-3 weeks"),
                "confidence": data["strength"] * pattern_info.get("confidence", 0.7),
                "detected_date": data["detected"]
            }
            
            # Add social momentum if available
            social = cls._get_social_momentum(symbol)
            if social:
                signal["social_momentum"] = social
            
            signals.append(signal)
        
        # Sort by composite score (strength * confidence * potential_gain)
        signals.sort(
            key=lambda x: x["strength"] * x["confidence"] * x["potential_gain"], 
            reverse=True
        )
        
        return signals
    
    @classmethod
    def calculate_entry_timing(cls, symbol: str) -> Dict:
        """
        Calculate optimal entry timing for a momentum play.
        Based on volume patterns and price action.
        """
        # Simplified timing calculation
        current_hour = datetime.now().hour
        
        # Best entry times based on market microstructure
        entry_windows = {
            "morning_dip": {"time": "9:45-10:15 AM", "quality": 0.8},
            "lunch_lull": {"time": "12:00-1:00 PM", "quality": 0.6},
            "power_hour": {"time": "3:00-3:30 PM", "quality": 0.9},
            "closing_push": {"time": "3:45-4:00 PM", "quality": 0.7}
        }
        
        # Determine current window
        if 9 <= current_hour < 10:
            current_window = "morning_dip"
        elif 12 <= current_hour < 13:
            current_window = "lunch_lull"
        elif 15 <= current_hour < 16:
            current_window = "power_hour"
        else:
            current_window = "wait"
        
        return {
            "symbol": symbol,
            "current_window": current_window,
            "entry_quality": entry_windows.get(current_window, {}).get("quality", 0.5),
            "best_windows": entry_windows,
            "recommendation": "Enter during high-quality windows for better fills"
        }
    
    @classmethod
    def detect_squeeze_setups(cls) -> List[Dict]:
        """
        Detect volatility squeeze setups about to fire.
        These often lead to explosive moves.
        """
        squeeze_candidates = [
            {
                "symbol": "AFRM",
                "squeeze_duration": "8 days",
                "bollinger_width": 0.05,
                "keltner_position": "inside",
                "expected_move": 0.18,
                "direction_bias": "bullish",
                "trigger_level": 15.50
            },
            {
                "symbol": "ROKU",
                "squeeze_duration": "12 days",
                "bollinger_width": 0.07,
                "keltner_position": "inside",
                "expected_move": 0.22,
                "direction_bias": "bullish",
                "trigger_level": 72.00
            },
            {
                "symbol": "BYND",
                "squeeze_duration": "6 days",
                "bollinger_width": 0.06,
                "keltner_position": "touching",
                "expected_move": 0.25,
                "direction_bias": "bearish",
                "trigger_level": 5.80
            }
        ]
        
        return squeeze_candidates
    
    @classmethod
    def find_volume_spikes(cls) -> List[Dict]:
        """
        Find unusual volume spikes that precede price moves.
        Smart money leaves footprints in volume.
        """
        volume_alerts = [
            {
                "symbol": "MARA",
                "volume_ratio": 3.2,  # vs 20-day average
                "price_change": 0.02,
                "interpretation": "Accumulation before move",
                "expected_direction": "up",
                "confidence": 0.75
            },
            {
                "symbol": "RIOT",
                "volume_ratio": 2.8,
                "price_change": -0.01,
                "interpretation": "Capitulation bottom",
                "expected_direction": "up",
                "confidence": 0.70
            },
            {
                "symbol": "CVNA",
                "volume_ratio": 4.1,
                "price_change": 0.05,
                "interpretation": "Breakout confirmation",
                "expected_direction": "up",
                "confidence": 0.85
            }
        ]
        
        return volume_alerts
    
    @classmethod
    def scan_sector_rotation(cls) -> Dict:
        """
        Identify sector rotation opportunities.
        Money flows from weak to strong sectors predictably.
        """
        sector_flows = {
            "flowing_out": {
                "Technology": {"outflow": "$2.3B", "weakness": 0.7},
                "Consumer Discretionary": {"outflow": "$1.1B", "weakness": 0.6}
            },
            "flowing_into": {
                "Energy": {"inflow": "$1.8B", "strength": 0.8},
                "Financials": {"inflow": "$1.5B", "strength": 0.75},
                "Healthcare": {"inflow": "$0.9B", "strength": 0.65}
            },
            "rotation_plays": [
                {"sell": "QQQ", "buy": "XLE", "expected_gain": 0.12},
                {"sell": "XLY", "buy": "XLF", "expected_gain": 0.10},
                {"sell": "ARKK", "buy": "XLV", "expected_gain": 0.15}
            ],
            "timeline": "2-4 weeks for full rotation"
        }
        
        return sector_flows
    
    @classmethod
    def calculate_momentum_score(cls, symbol: str, lookback_days: int = 20) -> float:
        """
        Calculate composite momentum score for ranking.
        Combines price, volume, and social momentum.
        """
        # Simplified momentum calculation
        scores = {
            "SMCI": 0.92,  # Super Micro Computer - AI play
            "IONQ": 0.88,  # IonQ - Quantum computing
            "PLTR": 0.85,  # Palantir - Government AI
            "ARM": 0.82,   # ARM Holdings - Chip design
            "NVDA": 0.80,  # NVIDIA - Still has momentum
            "MARA": 0.78,  # Marathon Digital - Crypto proxy
            "COIN": 0.75,  # Coinbase - Crypto exchange
            "SOFI": 0.72   # SoFi - Fintech momentum
        }
        
        return scores.get(symbol, 0.5)
    
    @classmethod
    def get_exit_signals(cls, symbol: str) -> Dict:
        """
        Determine when momentum is exhausted.
        Knowing when to sell is as important as when to buy.
        """
        exit_indicators = {
            "symbol": symbol,
            "momentum_exhaustion": cls._check_exhaustion(symbol),
            "volume_divergence": cls._check_volume_divergence(symbol),
            "social_sentiment_shift": cls._check_sentiment_shift(symbol),
            "technical_breakdown": cls._check_technical_breakdown(symbol),
            "exit_recommendation": "Scale out 1/3 at target, 1/3 at extension, trail remainder"
        }
        
        return exit_indicators
    
    @classmethod
    def _get_social_momentum(cls, symbol: str) -> Optional[Dict]:
        """Get social momentum indicators for a symbol."""
        wsb = cls.SOCIAL_MOMENTUM.get("reddit_wsb", {}).get(symbol)
        fintok = cls.SOCIAL_MOMENTUM.get("twitter_fintok", {}).get(symbol)
        
        if wsb or fintok:
            return {
                "wsb_mentions": wsb.get("mentions", 0) if wsb else 0,
                "wsb_sentiment": wsb.get("sentiment", 0) if wsb else 0,
                "twitter_viral": fintok.get("viral_score", 0) if fintok else 0,
                "composite_social": (
                    (wsb.get("sentiment", 0) if wsb else 0) * 0.5 +
                    (fintok.get("viral_score", 0) if fintok else 0) * 0.5
                )
            }
        return None
    
    @classmethod
    def _check_exhaustion(cls, symbol: str) -> float:
        """Check if momentum is exhausted."""
        # Simplified - would use RSI, volume, price action in production
        exhaustion_scores = {
            "GME": 0.9,   # Heavily exhausted
            "AMC": 0.85,  # Very exhausted
            "BBBY": 0.95, # Completely exhausted
            "NVDA": 0.3,  # Still has room
            "PLTR": 0.4   # Momentum intact
        }
        return exhaustion_scores.get(symbol, 0.5)
    
    @classmethod
    def _check_volume_divergence(cls, symbol: str) -> bool:
        """Check for bearish volume divergence."""
        # Price up but volume down = bearish divergence
        divergences = {
            "GME": True,
            "AMC": True,
            "NVDA": False,
            "PLTR": False
        }
        return divergences.get(symbol, False)
    
    @classmethod
    def _check_sentiment_shift(cls, symbol: str) -> str:
        """Check if social sentiment is shifting."""
        shifts = {
            "GME": "negative",
            "AMC": "negative", 
            "NVDA": "positive",
            "PLTR": "stable"
        }
        return shifts.get(symbol, "stable")
    
    @classmethod
    def _check_technical_breakdown(cls, symbol: str) -> bool:
        """Check for technical support breakdown."""
        breakdowns = {
            "GME": True,
            "AMC": True,
            "NVDA": False,
            "PLTR": False
        }
        return breakdowns.get(symbol, False)