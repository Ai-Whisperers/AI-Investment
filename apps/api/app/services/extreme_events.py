"""Extreme event detection for >30% market moves."""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import Signal, ExtremeEvent, PatternDetection
import numpy as np


class ExtremeEventDetector:
    """Detect events that cause >30% moves."""
    
    def __init__(self, db: Session):
        self.db = db
        self.extreme_patterns = {
            'short_squeeze_setup': {
                'indicators': [
                    'high_short_interest',
                    'retail_accumulation', 
                    'catalyst_pending',
                    'options_gamma_squeeze'
                ],
                'historical_returns': (0.50, 4.00),  # 50-400%
                'timeframe': '1-2 weeks',
                'confidence_threshold': 0.7
            },
            'sector_rotation': {
                'indicators': [
                    'macro_shift',
                    'fund_rebalancing',
                    'narrative_change',
                    'regulatory_catalyst'
                ],
                'historical_returns': (0.30, 0.60),  # 30-60%
                'timeframe': '1-3 months',
                'confidence_threshold': 0.6
            },
            'earnings_leak': {
                'indicators': [
                    'insider_language',
                    'unusual_options',
                    'executive_behavior',
                    'supply_chain_signals'
                ],
                'historical_returns': (0.20, 0.40),  # 20-40%
                'timeframe': '1-5 days',
                'confidence_threshold': 0.8
            },
            'viral_adoption': {
                'indicators': [
                    'tiktok_trend',
                    'meme_velocity',
                    'youth_adoption',
                    'influencer_endorsement'
                ],
                'historical_returns': (0.40, 1.00),  # 40-100%
                'timeframe': '2-4 weeks',
                'confidence_threshold': 0.65
            },
            'regulatory_boom': {
                'indicators': [
                    'policy_announcement',
                    'government_contract',
                    'compliance_requirement',
                    'subsidy_program'
                ],
                'historical_returns': (0.25, 0.45),  # 25-45%
                'timeframe': '1-6 months',
                'confidence_threshold': 0.7
            }
        }
        
    async def scan_for_extremes(self, ticker: str, data: Dict[str, Any]) -> List[Dict]:
        """Look for patterns that precede extreme moves."""
        opportunities = []
        
        for pattern_name, pattern_config in self.extreme_patterns.items():
            score = 0
            indicators_met = []
            
            for indicator in pattern_config['indicators']:
                if self._check_indicator(data, indicator):
                    score += 1
                    indicators_met.append(indicator)
                    
            confidence = score / len(pattern_config['indicators'])
            
            if confidence >= pattern_config['confidence_threshold']:
                min_return, max_return = pattern_config['historical_returns']
                expected_return = min_return + (max_return - min_return) * confidence
                
                # Store pattern detection
                detection = PatternDetection(
                    pattern_name=pattern_name,
                    ticker=ticker,
                    confidence=confidence,
                    indicators_met=indicators_met,
                    strength=confidence,
                    market_context=data.get('market_context'),
                    cross_validation=data.get('validation_data')
                )
                self.db.add(detection)
                
                # Create signal for extreme event
                signal = Signal(
                    ticker=ticker,
                    signal_type='extreme',
                    pattern_type=pattern_name,
                    confidence=confidence,
                    expected_return=expected_return,
                    timeframe=self._convert_timeframe(pattern_config['timeframe']),
                    sources=data.get('sources', []),
                    pattern_stack=[{
                        'pattern': pattern_name,
                        'indicators': indicators_met,
                        'confidence': confidence
                    }],
                    detection_metadata={'pattern_detection_id': detection.id},
                    action='BUY' if pattern_name != 'earnings_leak' else 'ACCUMULATE',
                    stop_loss=-0.15 if 'squeeze' in pattern_name else -0.10,
                    take_profit=expected_return * 0.8,  # Take 80% of expected
                    allocation_percent=self._calculate_allocation(confidence, expected_return)
                )
                
                detection.signal_generated = True
                detection.signal_id = signal.id
                self.db.add(signal)
                
                opportunities.append({
                    'type': pattern_name,
                    'confidence': confidence,
                    'expected_return': f"{expected_return:.0%}",
                    'timeframe': pattern_config['timeframe'],
                    'action': signal.action,
                    'signal_id': signal.id,
                    'indicators_met': indicators_met
                })
                
        self.db.commit()
        return opportunities
    
    def _check_indicator(self, data: Dict, indicator: str) -> bool:
        """Check if a specific indicator is present."""
        indicator_checks = {
            'high_short_interest': lambda d: d.get('short_interest', 0) > 0.20,
            'retail_accumulation': lambda d: d.get('retail_flow', 0) > 1000000,
            'catalyst_pending': lambda d: bool(d.get('upcoming_catalyst')),
            'options_gamma_squeeze': lambda d: d.get('gamma_exposure', 0) > 1000000,
            
            'macro_shift': lambda d: d.get('macro_change', False),
            'fund_rebalancing': lambda d: d.get('rebalancing_period', False),
            'narrative_change': lambda d: d.get('narrative_shift_score', 0) > 0.7,
            'regulatory_catalyst': lambda d: bool(d.get('regulatory_event')),
            
            'insider_language': lambda d: d.get('insider_confidence', 0) > 0.8,
            'unusual_options': lambda d: d.get('options_volume_ratio', 0) > 5,
            'executive_behavior': lambda d: bool(d.get('executive_signals')),
            'supply_chain_signals': lambda d: bool(d.get('supply_chain_intel')),
            
            'tiktok_trend': lambda d: d.get('tiktok_views', 0) > 1000000,
            'meme_velocity': lambda d: d.get('meme_acceleration', 0) > 3,
            'youth_adoption': lambda d: d.get('gen_z_interest', 0) > 0.5,
            'influencer_endorsement': lambda d: len(d.get('influencers', [])) > 3,
            
            'policy_announcement': lambda d: bool(d.get('policy_news')),
            'government_contract': lambda d: bool(d.get('gov_contract')),
            'compliance_requirement': lambda d: bool(d.get('new_compliance')),
            'subsidy_program': lambda d: bool(d.get('subsidy_eligible'))
        }
        
        check_func = indicator_checks.get(indicator)
        return check_func(data) if check_func else False
    
    def _convert_timeframe(self, timeframe: str) -> str:
        """Convert human-readable timeframe to system format."""
        if 'day' in timeframe:
            return '48_hours'
        elif 'week' in timeframe:
            return '1_week'
        elif 'month' in timeframe:
            return '1_month'
        else:
            return '1_month'
    
    def _calculate_allocation(self, confidence: float, expected_return: float) -> float:
        """Calculate position size based on confidence and expected return."""
        base_allocation = 0.02  # 2% base
        
        # Adjust for confidence
        if confidence > 0.9:
            base_allocation *= 2.5
        elif confidence > 0.8:
            base_allocation *= 2.0
        elif confidence > 0.7:
            base_allocation *= 1.5
            
        # Adjust for expected return
        if expected_return > 1.0:  # >100%
            base_allocation *= 1.5
        elif expected_return > 0.5:  # >50%
            base_allocation *= 1.2
            
        # Cap at 10%
        return min(base_allocation, 0.10)
    
    async def track_extreme_event(self, ticker: str, event_type: str, 
                                 start_price: float, catalyst: str) -> ExtremeEvent:
        """Track an extreme event for learning."""
        event = ExtremeEvent(
            ticker=ticker,
            event_type=event_type,
            start_date=datetime.utcnow(),
            start_price=start_price,
            catalyst=catalyst,
            precursor_patterns=[]  # Will be filled by analysis
        )
        self.db.add(event)
        self.db.commit()
        return event
    
    async def update_extreme_event(self, event_id: int, end_price: float) -> None:
        """Update extreme event with results."""
        event = self.db.query(ExtremeEvent).filter_by(id=event_id).first()
        if event:
            event.end_date = datetime.utcnow()
            event.peak_price = end_price
            event.total_return = (end_price - event.start_price) / event.start_price
            self.db.commit()


class FortyEightHourStrategy:
    """Find signals 48 hours before mainstream."""
    
    def __init__(self, db: Session):
        self.db = db
        self.early_patterns = {
            'insider_language': [
                'screenshot this',
                'trust me',
                'I work at',
                'heard from',
                'my friend at'
            ],
            'specific_dates': [
                'monday',
                'tuesday', 
                'earnings',
                'announcement',
                'launch'
            ],
            'high_conviction': [
                'all in',
                'mortgage',
                'life savings',
                'yolo',
                'guaranteed'
            ]
        }
        
    async def detect_early_signal(self, posts: List[Dict]) -> Optional[Dict]:
        """Detect signals from early sources."""
        for post in posts:
            content = post.get('content', '').lower()
            ticker = self._extract_ticker(content)
            
            if not ticker:
                continue
                
            pattern_matches = self._check_patterns(content)
            
            if len(pattern_matches) >= 2:  # At least 2 pattern types
                if await self._validate_signal(ticker, post):
                    signal = Signal(
                        ticker=ticker,
                        signal_type='extreme',
                        pattern_type='forty_eight_hour',
                        confidence=0.85,
                        expected_return=0.45,
                        timeframe='48_hours',
                        sources=[post.get('source', 'unknown')],
                        pattern_stack=pattern_matches,
                        detection_metadata={
                            'post_id': post.get('id'),
                            'timestamp': post.get('timestamp')
                        },
                        action='ACCUMULATE',
                        stop_loss=-0.10,
                        take_profit=0.40,
                        allocation_percent=0.05
                    )
                    self.db.add(signal)
                    self.db.commit()
                    
                    return {
                        'ticker': ticker,
                        'confidence': 0.85,
                        'expected_return': 0.45,
                        'timeframe': '48 hours',
                        'signal_id': signal.id
                    }
        
        return None
    
    def _extract_ticker(self, content: str) -> Optional[str]:
        """Extract stock ticker from content."""
        import re
        # Look for $TICKER or common ticker patterns
        pattern = r'\$([A-Z]{1,5})\b|(?:^|\s)([A-Z]{1,5})(?:\s|$)'
        matches = re.findall(pattern, content.upper())
        
        for match in matches:
            ticker = match[0] or match[1]
            if 2 <= len(ticker) <= 5:
                return ticker
        
        return None
    
    def _check_patterns(self, content: str) -> List[Dict]:
        """Check for early signal patterns."""
        matches = []
        
        for pattern_type, keywords in self.early_patterns.items():
            for keyword in keywords:
                if keyword in content:
                    matches.append({
                        'type': pattern_type,
                        'keyword': keyword
                    })
                    break
                    
        return matches
    
    async def _validate_signal(self, ticker: str, post: Dict) -> bool:
        """Validate signal with additional checks."""
        # Check if ticker is valid (would need actual validation)
        if len(ticker) < 2 or len(ticker) > 5:
            return False
            
        # Check post engagement if available
        if post.get('upvotes', 0) < 10:
            return False
            
        # Check if not already signaled recently
        recent_signal = self.db.query(Signal)\
            .filter_by(ticker=ticker)\
            .filter(Signal.created_at > datetime.utcnow() - timedelta(days=7))\
            .first()
            
        return recent_signal is None


class SmartMoneyDivergence:
    """Detect when retail and institutions disagree."""
    
    def __init__(self, db: Session):
        self.db = db
        
    async def analyze_divergence(self, tickers: List[str]) -> List[Dict]:
        """Find smart money divergence opportunities."""
        divergences = []
        
        for ticker in tickers:
            # Get sentiments (would need actual data sources)
            institutional = await self._get_institutional_sentiment(ticker)
            retail = await self._get_retail_sentiment(ticker)
            
            # Look for significant divergence
            if institutional > 0.7 and retail < 0.3:
                signal = Signal(
                    ticker=ticker,
                    signal_type='divergence',
                    pattern_type='smart_buying_retail_selling',
                    confidence=0.80,
                    expected_return=0.35,
                    timeframe='1_month',
                    sources=['institutional_news', 'social_media'],
                    pattern_stack=[{
                        'institutional_sentiment': institutional,
                        'retail_sentiment': retail,
                        'divergence': institutional - retail
                    }],
                    action='BUY',
                    stop_loss=-0.08,
                    take_profit=0.30,
                    allocation_percent=0.07,
                    sentiment_divergence=institutional - retail
                )
                self.db.add(signal)
                
                divergences.append({
                    'ticker': ticker,
                    'type': 'smart_buying_retail_selling',
                    'expected_return': 0.35,
                    'confidence': 0.80,
                    'signal_id': signal.id
                })
                
            elif institutional < 0.3 and retail > 0.7:
                signal = Signal(
                    ticker=ticker,
                    signal_type='divergence',
                    pattern_type='retail_euphoria_smart_selling',
                    confidence=0.75,
                    expected_return=0.30,
                    timeframe='1_month',
                    sources=['institutional_news', 'social_media'],
                    pattern_stack=[{
                        'institutional_sentiment': institutional,
                        'retail_sentiment': retail,
                        'divergence': retail - institutional
                    }],
                    action='SELL',
                    stop_loss=-0.08,
                    take_profit=0.25,
                    allocation_percent=0.05,
                    sentiment_divergence=retail - institutional
                )
                self.db.add(signal)
                
                divergences.append({
                    'ticker': ticker,
                    'type': 'retail_euphoria_smart_selling',
                    'action': 'SHORT',
                    'expected_return': 0.30,
                    'confidence': 0.75,
                    'signal_id': signal.id
                })
        
        self.db.commit()
        return divergences
    
    async def _get_institutional_sentiment(self, ticker: str) -> float:
        """Get institutional sentiment (placeholder)."""
        # This would connect to news APIs, analyst reports, etc.
        return np.random.uniform(0, 1)
    
    async def _get_retail_sentiment(self, ticker: str) -> float:
        """Get retail sentiment (placeholder)."""
        # This would analyze Reddit, Twitter, etc.
        return np.random.uniform(0, 1)