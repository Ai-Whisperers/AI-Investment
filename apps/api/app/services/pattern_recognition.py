"""Multi-layer pattern recognition for extreme alpha detection."""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy.orm import Session
from app.models import Signal, MemeVelocity, PatternDetection, InformationAsymmetry


class MultiLayerAlphaDetection:
    """Find patterns that others miss by looking at correlations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.pattern_layers = {
            'surface': 'Direct mentions and sentiment',
            'network': 'Who is talking to whom',
            'velocity': 'Rate of change in discussions',
            'divergence': 'When sources disagree',
            'confluence': 'When unlikely sources agree'
        }
        
    async def detect_alpha_event(self, ticker: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect events that lead to >30% moves."""
        patterns = []
        
        # Layer 1: Surface signals
        volume_spike = self._detect_mention_spike(data)
        if volume_spike > 10:  # 10x normal volume
            patterns.append({
                'type': 'volume_spike',
                'strength': 0.8,
                'value': volume_spike
            })
            
        # Layer 2: Network effects
        if self._detect_influencer_pivot(data):
            patterns.append({
                'type': 'influencer_shift',
                'strength': 0.9,
                'details': data.get('influencer_details')
            })
            
        # Layer 3: Velocity
        momentum = self._calculate_momentum_acceleration(data)
        if momentum > 2:  # Accelerating interest
            patterns.append({
                'type': 'momentum_surge',
                'strength': 0.85,
                'acceleration': momentum
            })
            
        # Layer 4: Divergence
        divergence = self._detect_institutional_retail_divergence(data)
        if divergence:
            patterns.append({
                'type': 'smart_dumb_divergence',
                'strength': 0.95,
                'divergence_score': divergence
            })
            
        # Layer 5: Confluence
        confluence = self._detect_cross_platform_agreement(data)
        if confluence > 0.8:
            patterns.append({
                'type': 'universal_signal',
                'strength': 1.0,
                'agreement_score': confluence
            })
            
        # Stack patterns for mega-signals
        if len(patterns) >= 3:
            confidence = sum(p['strength'] for p in patterns) / len(patterns)
            
            # Store pattern detection
            detection = PatternDetection(
                pattern_name='multi_layer_alpha',
                ticker=ticker,
                confidence=confidence,
                indicators_met=[p['type'] for p in patterns],
                strength=confidence,
                market_context=data.get('market_context'),
                cross_validation={'patterns': patterns}
            )
            self.db.add(detection)
            
            # Create signal
            signal = Signal(
                ticker=ticker,
                signal_type='extreme',
                pattern_type='multi_layer',
                confidence=confidence,
                expected_return=0.35 if confidence > 0.9 else 0.30,
                timeframe='2_weeks' if confidence > 0.9 else '1_month',
                sources=data.get('sources', []),
                pattern_stack=patterns,
                detection_metadata={'detection_id': detection.id},
                action='BUY',
                stop_loss=-0.10,
                take_profit=0.30,
                allocation_percent=0.10 if confidence > 0.9 else 0.05,
                volume_spike=volume_spike,
                momentum_score=momentum,
                sentiment_divergence=divergence
            )
            self.db.add(signal)
            self.db.commit()
            
            return {
                'action': 'STRONG_BUY',
                'confidence': confidence,
                'expected_return': '30-50%',
                'timeframe': '2-4 weeks',
                'signal_id': signal.id,
                'patterns': patterns
            }
            
        return None
    
    def _detect_mention_spike(self, data: Dict) -> float:
        """Calculate mention spike ratio."""
        current_mentions = data.get('current_mentions', 0)
        baseline_mentions = data.get('baseline_mentions', 1)
        return current_mentions / max(baseline_mentions, 1)
    
    def _detect_influencer_pivot(self, data: Dict) -> bool:
        """Detect if key influencers changed stance."""
        influencer_changes = data.get('influencer_changes', [])
        for change in influencer_changes:
            if change.get('follower_count', 0) > 100000 and change.get('stance_change'):
                return True
        return False
    
    def _calculate_momentum_acceleration(self, data: Dict) -> float:
        """Calculate momentum acceleration."""
        velocity_history = data.get('velocity_history', [])
        if len(velocity_history) < 3:
            return 0
        
        recent = velocity_history[-3:]
        acceleration = (recent[-1] - recent[0]) / len(recent)
        return acceleration
    
    def _detect_institutional_retail_divergence(self, data: Dict) -> float:
        """Detect divergence between institutional and retail sentiment."""
        institutional = data.get('institutional_sentiment', 0.5)
        retail = data.get('retail_sentiment', 0.5)
        divergence = abs(institutional - retail)
        
        if divergence > 0.4:  # Significant divergence
            # Store asymmetry
            asymmetry = InformationAsymmetry(
                ticker=data.get('ticker'),
                retail_sentiment=retail,
                institutional_sentiment=institutional,
                divergence_score=divergence,
                early_source=data.get('early_source'),
                mainstream_lag=data.get('mainstream_lag', 24),
                information_path=data.get('information_path'),
                propagation_speed=data.get('propagation_speed', 1.0),
                entry_window='48_hours',
                expected_convergence='1_week'
            )
            self.db.add(asymmetry)
            
        return divergence if divergence > 0.4 else 0
    
    def _detect_cross_platform_agreement(self, data: Dict) -> float:
        """Detect agreement across multiple platforms."""
        platform_sentiments = data.get('platform_sentiments', {})
        if len(platform_sentiments) < 3:
            return 0
        
        sentiments = list(platform_sentiments.values())
        mean_sentiment = np.mean(sentiments)
        std_sentiment = np.std(sentiments)
        
        # High agreement = low standard deviation
        if std_sentiment < 0.1 and mean_sentiment > 0.7:
            return 0.9
        elif std_sentiment < 0.2 and mean_sentiment > 0.6:
            return 0.7
        else:
            return std_sentiment


class AsymmetryExploiter:
    """Find information before it becomes mainstream."""
    
    def __init__(self, db: Session):
        self.db = db
        self.early_sources = {
            '4chan_biz': {'lead_time': 48, 'reliability': 0.3, 'alpha': 'extreme'},
            'small_discord': {'lead_time': 36, 'reliability': 0.5, 'alpha': 'high'},
            'tiktok_early': {'lead_time': 24, 'reliability': 0.6, 'alpha': 'medium'},
            'reddit_new': {'lead_time': 12, 'reliability': 0.7, 'alpha': 'medium'}
        }
        
    async def find_early_signals(self, data: Dict[str, List[Dict]]) -> List[Dict]:
        """Monitor sources in order of lead time."""
        signals = []
        
        # Start with earliest (least reliable)
        for source, config in sorted(self.early_sources.items(), 
                                    key=lambda x: -x[1]['lead_time']):
            source_data = data.get(source, [])
            
            for item in source_data:
                if await self._validate_with_other_sources(item, data, threshold=2):
                    confidence = config['reliability'] * 3  # Triple if validated
                    
                    signal = {
                        'ticker': item.get('ticker'),
                        'confidence': min(confidence, 0.95),
                        'source': source,
                        'lead_time': config['lead_time'],
                        'alpha_potential': config['alpha'],
                        'validation_sources': self._get_validation_sources(item, data)
                    }
                    signals.append(signal)
                    
        # Boost confidence for multi-source confirmation
        ticker_counts = {}
        for signal in signals:
            ticker = signal['ticker']
            ticker_counts[ticker] = ticker_counts.get(ticker, 0) + 1
            
        for signal in signals:
            if ticker_counts[signal['ticker']] > 1:
                signal['confidence'] = min(signal['confidence'] * 1.2, 0.95)
                signal['multi_source'] = True
                
        return signals
    
    async def _validate_with_other_sources(self, item: Dict, all_data: Dict, 
                                          threshold: int) -> bool:
        """Validate signal with other sources."""
        ticker = item.get('ticker')
        validations = 0
        
        for source, source_data in all_data.items():
            if source == item.get('source'):
                continue
                
            for other_item in source_data:
                if other_item.get('ticker') == ticker:
                    validations += 1
                    if validations >= threshold:
                        return True
        
        return False
    
    def _get_validation_sources(self, item: Dict, all_data: Dict) -> List[str]:
        """Get list of sources that validate this signal."""
        ticker = item.get('ticker')
        sources = []
        
        for source, source_data in all_data.items():
            for other_item in source_data:
                if other_item.get('ticker') == ticker and source not in sources:
                    sources.append(source)
                    
        return sources


class MemeVelocityTracker:
    """Track and analyze meme stock velocity."""
    
    def __init__(self, db: Session):
        self.db = db
        
    async def calculate_meme_velocity(self, ticker: str, platform_data: Dict) -> Dict:
        """Calculate meme velocity across platforms."""
        
        # Get previous velocity
        prev_velocity = self.db.query(MemeVelocity)\
            .filter_by(ticker=ticker)\
            .order_by(MemeVelocity.timestamp.desc())\
            .first()
        
        # Calculate current scores
        reddit_score = self._calculate_platform_score(platform_data.get('reddit', {}))
        twitter_score = self._calculate_platform_score(platform_data.get('twitter', {}))
        tiktok_score = self._calculate_platform_score(platform_data.get('tiktok', {}))
        discord_score = self._calculate_platform_score(platform_data.get('discord', {}))
        youtube_score = self._calculate_platform_score(platform_data.get('youtube', {}))
        
        total_score = reddit_score + twitter_score + tiktok_score + discord_score + youtube_score
        
        # Calculate velocity and acceleration
        velocity = 0
        acceleration = 0
        
        if prev_velocity:
            velocity = total_score - prev_velocity.total_score
            if prev_velocity.velocity:
                acceleration = velocity - prev_velocity.velocity
        
        # Store new velocity
        meme_velocity = MemeVelocity(
            ticker=ticker,
            timestamp=datetime.utcnow(),
            reddit_score=reddit_score,
            twitter_score=twitter_score,
            tiktok_score=tiktok_score,
            discord_score=discord_score,
            youtube_score=youtube_score,
            total_score=total_score,
            velocity=velocity,
            acceleration=acceleration,
            average_sentiment=platform_data.get('average_sentiment', 0.5),
            sentiment_divergence=platform_data.get('sentiment_divergence', 0),
            top_influencers=platform_data.get('top_influencers', []),
            influencer_reach=platform_data.get('influencer_reach', 0)
        )
        self.db.add(meme_velocity)
        
        # Generate signal if velocity is extreme
        if acceleration > 5:  # 500% acceleration
            signal = Signal(
                ticker=ticker,
                signal_type='meme',
                pattern_type='velocity_surge',
                confidence=0.90,
                expected_return=0.50,
                timeframe='1_week',
                sources=list(platform_data.keys()),
                pattern_stack=[{
                    'type': 'meme_velocity',
                    'velocity': velocity,
                    'acceleration': acceleration
                }],
                action='BUY',
                stop_loss=-0.15,
                take_profit=0.50,
                allocation_percent=0.05,
                meme_velocity=acceleration
            )
            self.db.add(signal)
            
        self.db.commit()
        
        return {
            'ticker': ticker,
            'total_score': total_score,
            'velocity': velocity,
            'acceleration': acceleration,
            'signal_generated': acceleration > 5
        }
    
    def _calculate_platform_score(self, platform_data: Dict) -> float:
        """Calculate normalized score for a platform."""
        mentions = platform_data.get('mentions', 0)
        sentiment = platform_data.get('sentiment', 0.5)
        engagement = platform_data.get('engagement', 0)
        
        # Weighted score
        score = (mentions * 0.4 + engagement * 0.4) * sentiment
        return min(score / 1000, 100)  # Normalize to 0-100