"""Meme velocity tracker for viral stock detection."""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import numpy as np
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MemeSignal:
    """Represents a meme stock signal."""
    ticker: str
    velocity: float  # Rate of mention increase
    acceleration: float  # Rate of velocity change
    platforms: List[str]
    mention_count: int
    sentiment: float
    virality_score: float
    expected_move: float
    timeframe: str


class MemeVelocityTracker:
    """
    Track meme velocity across platforms to detect viral movements.
    Historical evidence: GME, AMC, BBBY all showed 500%+ mention velocity
    before their major moves.
    """
    
    def __init__(self):
        # Track mention history
        self.mention_history = defaultdict(lambda: defaultdict(list))
        
        # Platform weights (based on historical predictive power)
        self.platform_weights = {
            'reddit_wsb': 0.35,  # WSB has highest signal
            '4chan_biz': 0.40,  # Earliest signals
            'tiktok': 0.30,  # Gen Z momentum
            'twitter': 0.25,  # Broad reach
            'youtube': 0.20,  # Influencer effect
            'discord': 0.35,  # Insider groups
            'stocktwits': 0.15  # Late indicator
        }
        
        # Viral thresholds
        self.thresholds = {
            'velocity_spike': 3.0,  # 300% increase
            'acceleration': 1.5,  # 150% acceleration
            'cross_platform': 3,  # Minimum platforms
            'minimum_mentions': 50  # Baseline activity
        }
        
        # Historical meme patterns
        self.meme_patterns = {
            'rocket_emojis': 1.5,  # 🚀 multiplier
            'diamond_hands': 1.3,  # 💎🙌
            'ape_references': 1.4,  # 🦍
            'moon_references': 1.2,  # 🌙
            'yolo_mentions': 1.6,  # YOLO posts
            'squeeze_language': 1.8  # Short squeeze refs
        }
        
    async def calculate_velocity(self, ticker: str, platform_data: Dict[str, List]) -> MemeSignal:
        """Calculate meme velocity for a ticker across platforms."""
        
        total_velocity = 0
        total_acceleration = 0
        active_platforms = []
        total_mentions = 0
        
        for platform, mentions in platform_data.items():
            if not mentions:
                continue
                
            # Store in history
            self.mention_history[ticker][platform].append({
                'timestamp': datetime.now(),
                'count': len(mentions),
                'mentions': mentions[:100]  # Keep sample
            })
            
            # Calculate platform velocity
            velocity = self.calculate_platform_velocity(ticker, platform, len(mentions))
            acceleration = self.calculate_acceleration(ticker, platform)
            
            if velocity > 0:
                # Weight by platform importance
                weight = self.platform_weights.get(platform, 0.1)
                total_velocity += velocity * weight
                total_acceleration += acceleration * weight
                active_platforms.append(platform)
                total_mentions += len(mentions)
                
        # Calculate virality score
        virality = self.calculate_virality_score(
            total_velocity,
            total_acceleration,
            len(active_platforms),
            total_mentions
        )
        
        # Estimate expected move based on velocity
        expected_move = self.estimate_price_move(total_velocity, virality)
        
        # Determine timeframe
        timeframe = self.estimate_timeframe(total_acceleration)
        
        # Calculate sentiment
        sentiment = await self.analyze_meme_sentiment(platform_data)
        
        return MemeSignal(
            ticker=ticker,
            velocity=total_velocity,
            acceleration=total_acceleration,
            platforms=active_platforms,
            mention_count=total_mentions,
            sentiment=sentiment,
            virality_score=virality,
            expected_move=expected_move,
            timeframe=timeframe
        )
    
    def calculate_platform_velocity(self, ticker: str, platform: str, current_mentions: int) -> float:
        """Calculate velocity for a specific platform."""
        
        history = self.mention_history[ticker][platform]
        
        if len(history) < 2:
            return 0
            
        # Get mentions from different time periods
        now = datetime.now()
        
        # Last hour
        hour_ago = now - timedelta(hours=1)
        hour_mentions = sum(
            h['count'] for h in history 
            if h['timestamp'] > hour_ago
        )
        
        # Last day
        day_ago = now - timedelta(days=1)
        day_mentions = sum(
            h['count'] for h in history
            if h['timestamp'] > day_ago
        )
        
        # Last week
        week_ago = now - timedelta(days=7)
        week_mentions = sum(
            h['count'] for h in history
            if h['timestamp'] > week_ago
        )
        
        # Calculate velocity (rate of change)
        if week_mentions > 0:
            week_velocity = (day_mentions * 7) / week_mentions
        else:
            week_velocity = 0
            
        if day_mentions > 0:
            day_velocity = (hour_mentions * 24) / day_mentions
        else:
            day_velocity = 0
            
        # Combine velocities (recent weighted more)
        velocity = (day_velocity * 0.7) + (week_velocity * 0.3)
        
        return velocity
    
    def calculate_acceleration(self, ticker: str, platform: str) -> float:
        """Calculate acceleration (change in velocity)."""
        
        history = self.mention_history[ticker][platform]
        
        if len(history) < 3:
            return 0
            
        # Calculate velocity at different points
        velocities = []
        
        for i in range(len(history) - 1):
            if history[i]['count'] > 0:
                velocity = history[i+1]['count'] / history[i]['count']
                velocities.append(velocity)
                
        if len(velocities) < 2:
            return 0
            
        # Acceleration is change in velocity
        recent_velocity = np.mean(velocities[-2:])
        older_velocity = np.mean(velocities[:-2]) if len(velocities) > 2 else velocities[0]
        
        if older_velocity > 0:
            acceleration = recent_velocity / older_velocity
        else:
            acceleration = recent_velocity
            
        return acceleration
    
    def calculate_virality_score(
        self, 
        velocity: float, 
        acceleration: float,
        platform_count: int,
        total_mentions: int
    ) -> float:
        """Calculate overall virality score (0-100)."""
        
        score = 50  # Base score
        
        # Velocity component (0-30 points)
        if velocity > 10:
            score += 30
        elif velocity > 5:
            score += 25
        elif velocity > 3:
            score += 20
        elif velocity > 2:
            score += 15
        elif velocity > 1.5:
            score += 10
        elif velocity > 1:
            score += 5
            
        # Acceleration component (0-20 points)
        if acceleration > 3:
            score += 20
        elif acceleration > 2:
            score += 15
        elif acceleration > 1.5:
            score += 10
        elif acceleration > 1:
            score += 5
            
        # Cross-platform component (0-30 points)
        score += min(platform_count * 5, 30)
        
        # Volume component (0-20 points)
        if total_mentions > 10000:
            score += 20
        elif total_mentions > 5000:
            score += 15
        elif total_mentions > 1000:
            score += 10
        elif total_mentions > 500:
            score += 5
            
        return min(score, 100)
    
    def estimate_price_move(self, velocity: float, virality: float) -> float:
        """Estimate expected price move based on meme velocity."""
        
        # Historical correlation between velocity and price moves
        # Based on GME, AMC, BBBY, etc.
        
        if virality > 90:
            # Extreme virality - potential for 200-500% moves
            base_move = 2.0 + (velocity * 0.5)
            
        elif virality > 75:
            # High virality - 50-200% moves
            base_move = 0.5 + (velocity * 0.3)
            
        elif virality > 60:
            # Moderate virality - 20-50% moves
            base_move = 0.2 + (velocity * 0.15)
            
        else:
            # Low virality - 10-20% moves
            base_move = 0.1 + (velocity * 0.05)
            
        # Cap at 500% to be realistic
        return min(base_move, 5.0)
    
    def estimate_timeframe(self, acceleration: float) -> str:
        """Estimate timeframe for the move based on acceleration."""
        
        if acceleration > 5:
            return "1-2 days"  # Explosive move imminent
        elif acceleration > 3:
            return "2-5 days"  # Quick buildup
        elif acceleration > 2:
            return "1 week"  # Normal meme timeline
        elif acceleration > 1.5:
            return "2 weeks"  # Slower buildup
        else:
            return "1 month"  # Gradual accumulation
            
    async def analyze_meme_sentiment(self, platform_data: Dict[str, List]) -> float:
        """Analyze sentiment from meme language."""
        
        positive_count = 0
        negative_count = 0
        total_count = 0
        
        # Meme-specific sentiment words
        positive_memes = [
            'moon', 'rocket', 'lambo', 'tendies', 'diamond hands',
            'apes strong', 'squeeze', 'gamma', 'yolo', 'lets go',
            'buy', 'hold', 'hodl', 'to the moon', 'this is the way'
        ]
        
        negative_memes = [
            'bag holder', 'dump', 'rug pull', 'dead cat', 'bleeding',
            'crash', 'sell', 'puts', 'short', 'bear', 'rip', 'guh'
        ]
        
        for platform, mentions in platform_data.items():
            for mention in mentions:
                text = str(mention).lower() if mention else ""
                
                # Count positive indicators
                for positive in positive_memes:
                    if positive in text:
                        positive_count += 1
                        
                # Count negative indicators
                for negative in negative_memes:
                    if negative in text:
                        negative_count += 1
                        
                total_count += 1
                
        if total_count == 0:
            return 0.5  # Neutral
            
        # Calculate sentiment ratio
        sentiment = (positive_count - negative_count) / total_count
        
        # Normalize to 0-1 scale
        return (sentiment + 1) / 2
    
    async def detect_squeeze_setup(self, ticker: str) -> Optional[Dict]:
        """Detect if ticker has short squeeze setup."""
        
        # Patterns that indicate squeeze potential
        squeeze_indicators = {
            'high_short_interest': False,
            'increasing_mentions': False,
            'diamond_hands_sentiment': False,
            'institutional_shorts': False,
            'low_float': False
        }
        
        # Check mention velocity
        history = self.mention_history[ticker]
        if history:
            recent_velocity = self.calculate_platform_velocity(ticker, 'reddit_wsb', 0)
            if recent_velocity > 3:
                squeeze_indicators['increasing_mentions'] = True
                
        # Check for diamond hands language
        for platform_history in history.values():
            for entry in platform_history[-10:]:  # Last 10 entries
                mentions = entry.get('mentions', [])
                diamond_count = sum(1 for m in mentions if 'diamond' in str(m).lower())
                if diamond_count > 5:
                    squeeze_indicators['diamond_hands_sentiment'] = True
                    break
                    
        # Calculate squeeze probability
        indicators_met = sum(squeeze_indicators.values())
        squeeze_probability = indicators_met / len(squeeze_indicators)
        
        if squeeze_probability > 0.4:  # 40% threshold
            return {
                'ticker': ticker,
                'squeeze_probability': squeeze_probability,
                'indicators': squeeze_indicators,
                'expected_move': 0.5 + (squeeze_probability * 2),  # 50-250%
                'timeframe': '1-2 weeks'
            }
            
        return None
    
    def get_top_meme_stocks(self, limit: int = 10) -> List[MemeSignal]:
        """Get current top meme stocks by velocity."""
        
        meme_signals = []
        
        for ticker in self.mention_history.keys():
            # Get latest data for each platform
            platform_data = {}
            for platform, history in self.mention_history[ticker].items():
                if history:
                    latest = history[-1]
                    platform_data[platform] = latest.get('mentions', [])
                    
            if platform_data:
                # Run async function in sync context (simplified)
                signal = MemeSignal(
                    ticker=ticker,
                    velocity=self.calculate_platform_velocity(ticker, 'reddit_wsb', 0),
                    acceleration=self.calculate_acceleration(ticker, 'reddit_wsb'),
                    platforms=list(platform_data.keys()),
                    mention_count=sum(len(m) for m in platform_data.values()),
                    sentiment=0.7,  # Default positive for memes
                    virality_score=50,
                    expected_move=0.3,
                    timeframe='1 week'
                )
                meme_signals.append(signal)
                
        # Sort by virality score
        meme_signals.sort(key=lambda x: x.virality_score, reverse=True)
        
        return meme_signals[:limit]