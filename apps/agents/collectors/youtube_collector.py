"""
YouTube collector for financial video analysis.
Implements zero-cost collection using YouTube Data API v3 free tier.

Priority: 30% weight for long-term signals
Free quota: 10,000 units/day (100 searches of 100 units each)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from googleapiclient.errors import HttpError

from .base_collector import SocialCollector
from ..base import RawContent, SourceType, CollectionError, TickerExtractor

logger = logging.getLogger(__name__)


class YouTubeCollector(SocialCollector):
    """
    YouTube data collector using YouTube Data API v3.
    Free tier: 10,000 units/day
    Rate limit: Conservative to stay within quota
    """
    
    def __init__(
        self, 
        api_key: str,
        priority_weight: float = 0.30  # 30% from mermaid priority
    ):
        super().__init__(SourceType.YOUTUBE, rate_limit_per_hour=300, priority_weight=priority_weight)
        
        self.api_key = api_key
        self.youtube = None
        self.daily_quota_used = 0
        self.daily_quota_limit = 8000  # Conservative limit (80% of 10k)
        
        # Trusted finance channels (verified for quality)
        self.trusted_channels = {
            'UCY2ifv8iH1Dsgjbf-iJUySw': 'Meet Kevin',
            'UCFCEuCsyWP0YkP3CZ3Mr01Q': 'Graham Stephan', 
            'UCAmRx4HZxqDIgLAHdGEqNvw': 'Financial Education',
            'UC0uVZnl6pPaP3ujFngK5LFQ': 'InTheMoney',
            'UCqK0ukwGsTDh7sHjtPRQ-Jg': 'Tom Nash',
            'UCL3v5XpunCafXYFxcqYQVaQ': 'Everything Money',
            'UCjuKQCnkzDW2Z2yq6f3R3Lg': 'Chicken Genius Singapore',
            'UCnMn36GT_H0X-w5_ckLtlgQ': 'Ben Felix',
            'UCDXTQ8nWmx_EhZ2v-kp7QxA': 'Plain Bagel'
        }
        
        # Search keywords optimized for different signal types
        self.long_term_keywords = [
            'stock analysis fundamental',
            'long term investing strategy', 
            'value investing 2025',
            'portfolio allocation strategy',
            'dividend growth investing',
            'sector analysis outlook',
            'economic trends 2025'
        ]
        
        self.swing_keywords = [
            'stock market today analysis',
            'breaking market news',
            'earnings reaction analysis',
            'technical analysis breakout',
            'market momentum stocks',
            'trading opportunities today'
        ]
        
    def get_collector_name(self) -> str:
        """Return the collector name."""
        return "YouTubeCollector"
        
    def validate_config(self) -> bool:
        """Validate YouTube API configuration."""
        return bool(self.api_key)
        
    def _initialize_youtube_client(self):
        """Initialize YouTube API client."""
        if not self.youtube:
            self.youtube = build('youtube', 'v3', developerKey=self.api_key)
            
    def _check_quota_limit(self, units_needed: int):
        """Check if we have enough quota remaining."""
        if self.daily_quota_used + units_needed > self.daily_quota_limit:
            raise CollectionError(
                f"Daily quota exceeded: {self.daily_quota_used + units_needed}/{self.daily_quota_limit}",
                SourceType.YOUTUBE
            )
            
    def _record_quota_usage(self, units: int):
        """Record quota usage."""
        self.daily_quota_used += units
        logger.debug(f"YouTube quota used: {units} units (total: {self.daily_quota_used}/{self.daily_quota_limit})")
        
    async def collect_content(self, **kwargs) -> List[RawContent]:
        """Generic content collection method."""
        signal_type = kwargs.get('signal_type', 'long_term')
        
        if signal_type == 'long_term':
            return await self.collect_long_term_signals(**kwargs)
        else:
            return await self.collect_swing_signals(**kwargs)
            
    async def collect_long_term_signals(self, **kwargs) -> List[RawContent]:
        """
        Collect long-term investment analysis videos.
        Focus on trusted channels and educational content.
        """
        self._initialize_youtube_client()
        
        content_list = []
        max_results = kwargs.get('max_results', 20)
        
        logger.info("Collecting long-term investment signals from YouTube")
        
        # Strategy 1: Get videos from trusted channels (higher priority)
        content_list.extend(await self._collect_from_trusted_channels(max_results // 2))
        
        # Strategy 2: Search for high-quality analysis videos
        content_list.extend(await self._search_long_term_content(max_results // 2))
        
        # Filter and prioritize content
        filtered_content = self._filter_long_term_content(content_list)
        
        logger.info(f"Long-term collection complete: {len(filtered_content)} high-quality videos")
        return filtered_content
        
    async def collect_swing_signals(self, **kwargs) -> List[RawContent]:
        """
        Collect short-term trading and momentum videos.
        Focus on recent, high-engagement content.
        """
        self._initialize_youtube_client()
        
        content_list = []
        max_results = kwargs.get('max_results', 15)
        
        logger.info("Collecting swing trading signals from YouTube")
        
        # Focus on recent, high-engagement videos
        for keyword in self.swing_keywords[:3]:  # Limit to 3 keywords for quota
            try:
                videos = await self._search_videos(
                    keyword, 
                    max_results=5,
                    order='viewCount',
                    published_after=(datetime.now() - timedelta(days=2)).isoformat() + 'Z'
                )
                content_list.extend(videos)
                
            except Exception as e:
                logger.error(f"Error searching for '{keyword}': {e}")
                continue
                
        # Filter for swing trading relevance
        filtered_content = self._filter_swing_content(content_list)
        
        logger.info(f"Swing collection complete: {len(filtered_content)} videos")
        return filtered_content
        
    async def _collect_from_trusted_channels(self, max_videos: int) -> List[RawContent]:
        """Collect recent videos from trusted finance channels."""
        content_list = []
        videos_per_channel = max(1, max_videos // len(self.trusted_channels))
        
        for channel_id, channel_name in list(self.trusted_channels.items())[:5]:  # Top 5 channels
            try:
                self._check_quota_limit(100)  # Search costs 100 units
                self._record_request()
                
                # Search for recent videos from this channel
                request = self.youtube.search().list(
                    channelId=channel_id,
                    part='snippet',
                    type='video',
                    order='date',
                    maxResults=videos_per_channel
                )
                
                response = request.execute()
                self._record_quota_usage(100)
                
                for item in response['items']:
                    video = await self._process_youtube_video(item, channel_name, is_trusted=True)
                    if video:
                        content_list.append(video)
                        
                self._record_success()
                logger.debug(f"Collected {len(response['items'])} videos from {channel_name}")
                
            except HttpError as e:
                self._record_error()
                logger.error(f"YouTube API error for channel {channel_name}: {e}")
                continue
            except Exception as e:
                self._record_error()
                logger.error(f"Error collecting from {channel_name}: {e}")
                continue
                
        return content_list
        
    async def _search_long_term_content(self, max_videos: int) -> List[RawContent]:
        """Search for long-term investment content."""
        content_list = []
        videos_per_search = max(1, max_videos // len(self.long_term_keywords))
        
        for keyword in self.long_term_keywords[:3]:  # Limit for quota management
            try:
                videos = await self._search_videos(
                    keyword,
                    max_results=videos_per_search,
                    order='relevance'
                )
                content_list.extend(videos)
                
            except Exception as e:
                logger.error(f"Error searching for '{keyword}': {e}")
                continue
                
        return content_list
        
    async def _search_videos(
        self, 
        query: str, 
        max_results: int = 10,
        order: str = 'relevance',
        published_after: Optional[str] = None
    ) -> List[RawContent]:
        """Search for videos with specified criteria."""
        self._check_quota_limit(100)  # Search costs 100 units
        self._record_request()
        
        search_params = {
            'q': query,
            'part': 'snippet',
            'type': 'video',
            'order': order,
            'maxResults': max_results,
            'relevanceLanguage': 'en',
            'regionCode': 'US'
        }
        
        if published_after:
            search_params['publishedAfter'] = published_after
            
        try:
            request = self.youtube.search().list(**search_params)
            response = request.execute()
            self._record_quota_usage(100)
            
            videos = []
            for item in response['items']:
                video = await self._process_youtube_video(item, None, is_trusted=False)
                if video:
                    videos.append(video)
                    
            self._record_success()
            return videos
            
        except HttpError as e:
            self._record_error()
            raise CollectionError(f"YouTube search failed for '{query}': {e}", SourceType.YOUTUBE)
            
    async def _process_youtube_video(self, item: Dict, channel_name: Optional[str], is_trusted: bool) -> Optional[RawContent]:
        """Process a YouTube video item into RawContent format."""
        try:
            video_id = item['id']['videoId'] if 'videoId' in item['id'] else item['id']
            snippet = item['snippet']
            
            # Get detailed video statistics
            video_details = await self._get_video_details(video_id)
            if not video_details:
                return None
                
            # Get transcript if available
            transcript = await self._get_transcript(video_id)
            
            # Combine title, description, and transcript
            full_text = snippet['title']
            if snippet.get('description'):
                full_text += "\n\n" + snippet['description'][:1000]  # Limit description length
            if transcript:
                full_text += "\n\nTranscript:\n" + transcript[:3000]  # Limit transcript length
                
            # Extract engagement metrics
            stats = video_details.get('statistics', {})
            engagement = {
                'views': int(stats.get('viewCount', 0)),
                'likes': int(stats.get('likeCount', 0)),
                'comments': int(stats.get('commentCount', 0)),
                'duration': video_details.get('contentDetails', {}).get('duration', ''),
                'view_rate': self._calculate_view_rate(stats, snippet['publishedAt'])
            }
            
            # Extract metadata
            metadata = {
                'channel_id': snippet['channelId'],
                'channel_title': channel_name or snippet['channelTitle'],
                'is_trusted_channel': is_trusted,
                'category_id': video_details.get('snippet', {}).get('categoryId'),
                'tags': video_details.get('snippet', {}).get('tags', []),
                'tickers': TickerExtractor.extract_tickers(full_text),
                'has_transcript': bool(transcript),
                'video_quality_score': self._calculate_video_quality_score(engagement, is_trusted, len(full_text)),
                'financial_relevance_score': self._calculate_financial_relevance(full_text)
            }
            
            return RawContent(
                id=f"youtube_{video_id}",
                source=SourceType.YOUTUBE,
                platform_id=video_id,
                title=snippet['title'],
                text=full_text,
                author=channel_name or snippet['channelTitle'],
                created_at=datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00')),
                engagement=engagement,
                url=f"https://youtube.com/watch?v={video_id}",
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error processing YouTube video {video_id}: {e}")
            return None
            
    async def _get_video_details(self, video_id: str) -> Optional[Dict]:
        """Get detailed video information."""
        try:
            self._check_quota_limit(1)  # Videos.list costs 1 unit
            
            request = self.youtube.videos().list(
                part='statistics,contentDetails,snippet',
                id=video_id
            )
            
            response = request.execute()
            self._record_quota_usage(1)
            
            if response['items']:
                return response['items'][0]
                
        except Exception as e:
            logger.error(f"Error getting video details for {video_id}: {e}")
            
        return None
        
    async def _get_transcript(self, video_id: str) -> Optional[str]:
        """Get video transcript if available."""
        try:
            # Try to get auto-generated transcript
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
            transcript = ' '.join([t['text'] for t in transcript_list])
            return transcript
            
        except Exception as e:
            logger.debug(f"No transcript available for video {video_id}: {e}")
            return None
            
    def _calculate_view_rate(self, stats: Dict, published_at: str) -> float:
        """Calculate views per day since publication."""
        try:
            views = int(stats.get('viewCount', 0))
            published = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            days_since = (datetime.now() - published.replace(tzinfo=None)).days
            
            if days_since > 0:
                return views / days_since
            return views
            
        except Exception:
            return 0.0
            
    def _calculate_video_quality_score(self, engagement: Dict, is_trusted: bool, text_length: int) -> float:
        """Calculate overall video quality score."""
        score = 0.0
        
        # View count score (0-0.3)
        views = engagement.get('views', 0)
        if views > 100000:
            score += 0.3
        elif views > 10000:
            score += 0.2
        elif views > 1000:
            score += 0.1
            
        # Engagement score (0-0.3)
        likes = engagement.get('likes', 0)
        comments = engagement.get('comments', 0)
        if views > 0:
            engagement_rate = (likes + comments) / views
            if engagement_rate > 0.05:
                score += 0.3
            elif engagement_rate > 0.02:
                score += 0.2
            elif engagement_rate > 0.01:
                score += 0.1
                
        # Trusted channel bonus (0-0.2)
        if is_trusted:
            score += 0.2
            
        # Content depth score (0-0.2)
        if text_length > 2000:
            score += 0.2
        elif text_length > 1000:
            score += 0.1
            
        return min(score, 1.0)
        
    def _calculate_financial_relevance(self, text: str) -> float:
        """Calculate how relevant the content is to financial analysis."""
        financial_keywords = [
            'stock', 'investment', 'portfolio', 'trading', 'market', 'analysis',
            'earnings', 'dividend', 'valuation', 'fundamental', 'technical',
            'economic', 'financial', 'equity', 'bond', 'etf', 'fund'
        ]
        
        text_lower = text.lower()
        matches = sum(1 for keyword in financial_keywords if keyword in text_lower)
        
        # Normalize to 0-1 scale
        return min(matches / 5.0, 1.0)
        
    def _filter_long_term_content(self, content_list: List[RawContent]) -> List[RawContent]:
        """Filter content for long-term investment relevance."""
        filtered = []
        
        for content in content_list:
            metadata = content.metadata
            
            # Quality thresholds for long-term content
            if (metadata.get('video_quality_score', 0) > 0.4 and
                metadata.get('financial_relevance_score', 0) > 0.3 and
                content.engagement.get('views', 0) > 1000):
                
                filtered.append(content)
                
        # Sort by quality score
        filtered.sort(key=lambda x: x.metadata.get('video_quality_score', 0), reverse=True)
        return filtered[:20]  # Top 20 for processing
        
    def _filter_swing_content(self, content_list: List[RawContent]) -> List[RawContent]:
        """Filter content for swing trading relevance."""
        filtered = []
        
        for content in content_list:
            # Recent content only for swing trades
            age_hours = (datetime.now() - content.created_at).total_seconds() / 3600
            if age_hours > 48:  # Skip content older than 48 hours
                continue
                
            metadata = content.metadata
            
            # Lower quality threshold but require recency and engagement
            if (metadata.get('financial_relevance_score', 0) > 0.2 and
                content.engagement.get('views', 0) > 500 and
                content.engagement.get('view_rate', 0) > 100):  # Good view rate
                
                filtered.append(content)
                
        # Sort by recency and engagement
        filtered.sort(key=lambda x: (x.created_at, x.engagement.get('view_rate', 0)), reverse=True)
        return filtered[:15]  # Top 15 for processing
        
    def get_quota_status(self) -> Dict[str, Any]:
        """Get current quota usage status."""
        return {
            'quota_used': self.daily_quota_used,
            'quota_limit': self.daily_quota_limit,
            'quota_remaining': self.daily_quota_limit - self.daily_quota_used,
            'usage_percentage': (self.daily_quota_used / self.daily_quota_limit) * 100
        }
        
    def reset_daily_quota(self):
        """Reset daily quota counter."""
        self.daily_quota_used = 0
        logger.info("YouTube daily quota reset")