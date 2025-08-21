"""
TikTok collector for FinTok content analysis.
Implements zero-cost collection with manual/proxy approach.

Priority: 10% weight for swing signals (retail sentiment indicator)
Challenge: No official API, requires creative collection methods
Focus: Viral financial content, youth sentiment trends
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

from .base_collector import SocialCollector
from ..base import RawContent, SourceType, CollectionError, TickerExtractor

logger = logging.getLogger(__name__)


class TikTokCollector(SocialCollector):
    """
    TikTok collector for FinTok content.
    
    Note: TikTok has no official public API for content scraping.
    This collector implements a framework that can be enhanced with:
    1. Manual data entry for high-value content
    2. Third-party scraping services (when budget allows)
    3. RSS feeds or unofficial APIs
    """
    
    def __init__(self, priority_weight: float = 0.10):
        super().__init__(SourceType.TIKTOK, rate_limit_per_hour=60, priority_weight=priority_weight)
        
        # Key FinTok creators to monitor (manual tracking for MVP)
        self.fintok_creators = {
            'humphreytalks': {
                'followers': '3.3M',
                'focus': 'Personal finance education',
                'credibility': 0.8
            },
            'investwithqueenie': {
                'followers': '1M', 
                'focus': 'Stock investing for beginners',
                'credibility': 0.7
            },
            'ceowatchlist': {
                'followers': '500K',
                'focus': 'CEO insights and market analysis',
                'credibility': 0.9
            },
            'taylormitchell': {
                'followers': '800K',
                'focus': 'Trading education',
                'credibility': 0.6
            },
            'austin.hankwitz': {
                'followers': '1.2M',
                'focus': 'Business and investing',
                'credibility': 0.7
            }
        }
        
        # Financial hashtags to track
        self.financial_hashtags = [
            '#stocks', '#investing', '#stockmarket', '#fintok', '#stocktok',
            '#options', '#trading', '#pennystocks', '#crypto', '#bitcoin',
            '#ethereum', '#passiveincome', '#wealthbuilding', '#financialliteracy',
            '#stockanalysis', '#daytrading', '#swingtrading', '#portfoliomanagement'
        ]
        
        # Manual data placeholder for MVP
        self.manual_content_queue = []
        
    def get_collector_name(self) -> str:
        """Return the collector name."""
        return "TikTokCollector"
        
    def validate_config(self) -> bool:
        """Validate configuration."""
        return True  # No API key required for manual collection
        
    async def collect_content(self, **kwargs) -> List[RawContent]:
        """Generic content collection method."""
        signal_type = kwargs.get('signal_type', 'swing')
        
        # TikTok is primarily for swing/momentum signals (youth sentiment)
        return await self.collect_swing_signals(**kwargs)
        
    async def collect_long_term_signals(self, **kwargs) -> List[RawContent]:
        """
        Limited long-term content on TikTok, but we look for:
        - Educational content from trusted creators
        - Long-term investing trends
        - Generational investment shifts
        """
        return await self._collect_educational_content(**kwargs)
        
    async def collect_swing_signals(self, **kwargs) -> List[RawContent]:
        """
        Collect swing trading signals from TikTok.
        Focus on viral trends, FOMO indicators, contrarian signals.
        """
        content_list = []
        
        logger.info("Collecting FinTok signals (manual/placeholder mode)")
        
        try:
            # Method 1: Process manual content queue
            manual_content = await self._process_manual_queue()
            content_list.extend(manual_content)
            
            # Method 2: Simulate trend detection (for MVP)
            trending_content = await self._simulate_trending_content()
            content_list.extend(trending_content)
            
            # Method 3: Process creator updates (manual tracking)
            creator_content = await self._process_creator_updates()
            content_list.extend(creator_content)
            
            logger.info(f"TikTok collection complete: {len(content_list)} items")
            
        except Exception as e:
            self._record_error()
            raise CollectionError(f"TikTok collection failed: {e}", SourceType.TIKTOK)
            
        return content_list
        
    async def _process_manual_queue(self) -> List[RawContent]:
        """Process manually added content."""
        content_list = []
        
        # Process items from manual queue
        while self.manual_content_queue:
            item = self.manual_content_queue.pop(0)
            
            try:
                content = self._create_tiktok_content(item)
                if content:
                    content_list.append(content)
                    self._record_success()
            except Exception as e:
                self._record_error()
                logger.error(f"Error processing manual TikTok item: {e}")
                
        return content_list
        
    async def _simulate_trending_content(self) -> List[RawContent]:
        """
        Simulate trending content detection for MVP.
        In production, this would connect to actual TikTok data sources.
        """
        # This is a placeholder that simulates what real collection would look like
        simulated_trends = [
            {
                'id': f'tiktok_trend_{int(datetime.now().timestamp())}',
                'content': 'Trend: #StockTok creators discussing market volatility',
                'hashtags': ['#stocktok', '#marketvolatility', '#investing'],
                'engagement': {'views': 1500000, 'likes': 75000, 'shares': 12000},
                'creator': 'Multiple creators',
                'trend_velocity': 'High'
            }
        ]
        
        content_list = []
        for trend in simulated_trends:
            content = self._create_simulated_content(trend)
            if content:
                content_list.append(content)
                
        return content_list
        
    async def _process_creator_updates(self) -> List[RawContent]:
        """Process updates from tracked FinTok creators."""
        # This would integrate with creator monitoring in production
        # For MVP, we return placeholder content
        return []
        
    async def _collect_educational_content(self, **kwargs) -> List[RawContent]:
        """Collect educational FinTok content."""
        content_list = []
        
        # Focus on educational creators for long-term insights
        educational_creators = [
            creator for creator, data in self.fintok_creators.items() 
            if data['credibility'] > 0.7
        ]
        
        logger.info(f"Monitoring {len(educational_creators)} educational FinTok creators")
        
        # For MVP, return placeholder educational content
        placeholder_content = {
            'id': f'tiktok_edu_{int(datetime.now().timestamp())}',
            'content': 'Educational content: Long-term investing strategies for Gen Z',
            'creator': 'humphreytalks',
            'focus': 'Investment education',
            'engagement': {'views': 500000, 'likes': 25000, 'saves': 5000}
        }
        
        content = self._create_educational_content(placeholder_content)
        if content:
            content_list.append(content)
            
        return content_list
        
    def _create_tiktok_content(self, item: Dict) -> Optional[RawContent]:
        """Create RawContent from TikTok item."""
        try:
            # Extract tickers from content
            full_text = item.get('caption', '') + ' ' + item.get('description', '')
            tickers = TickerExtractor.extract_tickers(full_text)
            
            # Calculate engagement metrics
            engagement = {
                'views': item.get('views', 0),
                'likes': item.get('likes', 0), 
                'comments': item.get('comments', 0),
                'shares': item.get('shares', 0),
                'engagement_rate': self._calculate_engagement_rate(item)
            }
            
            # Extract metadata
            metadata = {
                'creator': item.get('creator', 'Unknown'),
                'hashtags': item.get('hashtags', []),
                'tickers': tickers,
                'video_length': item.get('duration', 0),
                'is_trending': item.get('is_trending', False),
                'credibility_score': self._get_creator_credibility(item.get('creator', '')),
                'viral_potential': self._calculate_viral_potential(item),
                'sentiment_indicators': self._extract_tiktok_sentiment(full_text)
            }
            
            return RawContent(
                id=item.get('id', f"tiktok_{int(datetime.now().timestamp())}"),
                source=SourceType.TIKTOK,
                platform_id=item.get('video_id', ''),
                title=item.get('caption', '')[:100],  # Limit title length
                text=full_text,
                author=item.get('creator', 'Unknown'),
                created_at=datetime.fromisoformat(item.get('created_at', datetime.now().isoformat())),
                engagement=engagement,
                url=item.get('url', ''),
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error creating TikTok content: {e}")
            return None
            
    def _create_simulated_content(self, trend: Dict) -> Optional[RawContent]:
        """Create content from simulated trend data."""
        try:
            full_text = trend['content']
            tickers = TickerExtractor.extract_tickers(full_text)
            
            metadata = {
                'creator': trend['creator'],
                'hashtags': trend.get('hashtags', []),
                'tickers': tickers,
                'trend_velocity': trend.get('trend_velocity', 'Medium'),
                'is_simulated': True,  # Mark as simulated for MVP
                'sentiment_indicators': self._extract_tiktok_sentiment(full_text)
            }
            
            return RawContent(
                id=trend['id'],
                source=SourceType.TIKTOK,
                platform_id=trend['id'],
                title=f"Trending: {full_text[:50]}...",
                text=full_text,
                author=trend['creator'],
                created_at=datetime.now(),
                engagement=trend['engagement'],
                url=f"https://tiktok.com/trend/{trend['id']}",
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error creating simulated content: {e}")
            return None
            
    def _create_educational_content(self, item: Dict) -> Optional[RawContent]:
        """Create educational content item."""
        try:
            full_text = item['content']
            
            metadata = {
                'creator': item['creator'],
                'content_type': 'educational',
                'focus': item['focus'],
                'credibility_score': self._get_creator_credibility(item['creator']),
                'is_educational': True,
                'sentiment_indicators': self._extract_tiktok_sentiment(full_text)
            }
            
            return RawContent(
                id=item['id'],
                source=SourceType.TIKTOK,
                platform_id=item['id'],
                title=f"Educational: {full_text[:50]}...",
                text=full_text,
                author=item['creator'],
                created_at=datetime.now(),
                engagement=item['engagement'],
                url=f"https://tiktok.com/@{item['creator']}",
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error creating educational content: {e}")
            return None
            
    def _calculate_engagement_rate(self, item: Dict) -> float:
        """Calculate engagement rate for TikTok content."""
        views = item.get('views', 1)
        likes = item.get('likes', 0)
        comments = item.get('comments', 0)
        shares = item.get('shares', 0)
        
        total_engagement = likes + comments + shares
        return (total_engagement / views) * 100 if views > 0 else 0.0
        
    def _get_creator_credibility(self, creator: str) -> float:
        """Get credibility score for creator."""
        if creator in self.fintok_creators:
            return self.fintok_creators[creator]['credibility']
        return 0.5  # Default neutral credibility
        
    def _calculate_viral_potential(self, item: Dict) -> float:
        """Calculate viral potential score."""
        engagement_rate = self._calculate_engagement_rate(item)
        views = item.get('views', 0)
        shares = item.get('shares', 0)
        
        # High engagement rate + good share count = viral potential
        viral_score = 0.0
        
        if engagement_rate > 10:  # Very high engagement
            viral_score += 0.4
        elif engagement_rate > 5:
            viral_score += 0.2
            
        if shares > 1000:
            viral_score += 0.3
        elif shares > 100:
            viral_score += 0.1
            
        if views > 1000000:  # 1M+ views
            viral_score += 0.3
        elif views > 100000:
            viral_score += 0.2
            
        return min(viral_score, 1.0)
        
    def _extract_tiktok_sentiment(self, text: str) -> Dict[str, Any]:
        """Extract TikTok-specific sentiment indicators."""
        text_lower = text.lower()
        
        # TikTok/Gen Z specific bullish terms
        bullish_terms = [
            'to the moon', 'diamond hands', 'hodl', 'buy the dip', 'bullish',
            'stonks', 'tendies', 'gains', 'rocket', 'fire', 'lit', 'slaps',
            'no cap', 'facts', 'based', 'this is the way'
        ]
        
        # TikTok/Gen Z specific bearish terms
        bearish_terms = [
            'dump', 'crash', 'rip', 'dead', 'rekt', 'bearish', 'sus',
            'cap', 'not it', 'mid', 'trash', 'scam', 'rug pull'
        ]
        
        bullish_count = sum(1 for term in bullish_terms if term in text_lower)
        bearish_count = sum(1 for term in bearish_terms if term in text_lower)
        
        total_sentiment = bullish_count + bearish_count
        sentiment_score = 0.0
        if total_sentiment > 0:
            sentiment_score = (bullish_count - bearish_count) / total_sentiment
            
        return {
            'bullish_indicators': bullish_count,
            'bearish_indicators': bearish_count,
            'net_sentiment': sentiment_score,
            'sentiment_strength': min(total_sentiment / 2.0, 1.0),
            'has_gen_z_language': any(term in text_lower for term in ['no cap', 'facts', 'slaps', 'fire']),
            'has_investment_terms': any(term in text_lower for term in ['stonks', 'tendies', 'diamond hands']),
            'viral_indicators': sum(1 for term in ['viral', 'trending', 'blowing up'] if term in text_lower)
        }
        
    def add_manual_content(self, content_data: Dict):
        """Add content manually for processing."""
        self.manual_content_queue.append(content_data)
        logger.info(f"Added manual TikTok content: {content_data.get('id', 'unknown')}")
        
    def get_creator_stats(self) -> Dict[str, Any]:
        """Get statistics about tracked creators."""
        return {
            'tracked_creators': len(self.fintok_creators),
            'creators': self.fintok_creators,
            'total_followers': sum(
                int(data['followers'].replace('M', '000000').replace('K', '000').replace('.', ''))
                for data in self.fintok_creators.values()
                if data['followers'].replace('M', '').replace('K', '').replace('.', '').isdigit()
            ),
            'avg_credibility': sum(data['credibility'] for data in self.fintok_creators.values()) / len(self.fintok_creators)
        }
        
    def simulate_viral_trend(self, ticker: str, trend_type: str = "bullish") -> Dict[str, Any]:
        """
        Simulate a viral trend for testing/demo purposes.
        This would be replaced with real trend detection in production.
        """
        trend_data = {
            'ticker': ticker,
            'trend_type': trend_type,
            'velocity': 'high',
            'estimated_reach': 2500000,  # 2.5M estimated views
            'key_creators': ['humphreytalks', 'investwithqueenie'],
            'hashtags': [f'#{ticker.lower()}', '#stocktok', '#investing'],
            'sentiment_shift': 0.7 if trend_type == "bullish" else -0.7,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Simulated viral trend for {ticker}: {trend_type}")
        return trend_data