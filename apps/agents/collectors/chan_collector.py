"""
4chan /biz/ collector for early financial signals.
Implements careful collection from 4chan's business & finance board.

Priority: 10% weight for swing signals (unique alpha source)
Key advantage: 48-72 hour early detection of major moves
Risk: High noise, requires intelligent filtering
"""

import asyncio
import logging
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from html import unescape

import aiohttp
from bs4 import BeautifulSoup

from .base_collector import SocialCollector
from ..base import RawContent, SourceType, CollectionError, TickerExtractor, ExtremePatternsDetector

logger = logging.getLogger(__name__)


class ChanCollector(SocialCollector):
    """
    4chan /biz/ collector for early financial signals.
    Uses 4chan's public JSON API with respectful rate limiting.
    
    IMPORTANT: This collector follows 4chan's ToS and robots.txt
    """
    
    def __init__(self, priority_weight: float = 0.10):
        super().__init__(SourceType.CHAN, rate_limit_per_hour=120, priority_weight=priority_weight)
        
        self.base_url = "https://a.4cdn.org"
        self.board = "biz"
        self.min_request_delay = 1.0  # 1 second between requests (respectful)
        
        # Pattern recognition for valuable content
        self.insider_patterns = [
            'screenshot this',
            'trust me bros',  
            'I work at',
            'my source',
            'insider info',
            'leaked',
            'announcement tomorrow',
            'earnings leak',
            'merger talks',
            'buyout rumor'
        ]
        
        self.high_conviction_patterns = [
            'all in',
            'mortgage the house',
            'life savings',
            'guaranteed',
            '100% sure',
            'cant lose',
            'free money',
            'ez money'
        ]
        
        self.momentum_patterns = [
            'moon mission',
            'to the moon',
            'pump incoming',
            'breakout',
            'squeeze setup',
            'short interest',
            'gamma squeeze',
            'accumulation phase'
        ]
        
    def get_collector_name(self) -> str:
        """Return the collector name."""
        return "ChanCollector"
        
    def validate_config(self) -> bool:
        """Validate configuration."""
        return True  # No API key needed for 4chan
        
    async def collect_content(self, **kwargs) -> List[RawContent]:
        """Generic content collection method."""
        signal_type = kwargs.get('signal_type', 'swing')
        
        # 4chan is primarily for swing/momentum signals
        return await self.collect_swing_signals(**kwargs)
        
    async def collect_long_term_signals(self, **kwargs) -> List[RawContent]:
        """
        4chan has limited long-term content, but we look for:
        - Deep fundamental analysis threads
        - Sector rotation discussions
        - Economic trend discussions
        """
        return await self.collect_swing_signals(**kwargs)  # Same collection, different filtering
        
    async def collect_swing_signals(self, **kwargs) -> List[RawContent]:
        """
        Collect swing trading signals from /biz/.
        Focus on threads with high potential for early detection.
        """
        content_list = []
        max_threads = kwargs.get('max_threads', 50)
        
        logger.info("Collecting signals from 4chan /biz/")
        
        try:
            # Get catalog of all threads
            catalog = await self._get_catalog()
            
            # Find high-value threads
            valuable_threads = self._identify_valuable_threads(catalog, max_threads)
            
            logger.info(f"Identified {len(valuable_threads)} valuable threads from {len(catalog)} total")
            
            # Process threads with rate limiting
            for thread_data in valuable_threads:
                try:
                    await asyncio.sleep(self.min_request_delay)  # Respectful rate limiting
                    
                    thread_content = await self._process_thread(thread_data)
                    if thread_content:
                        content_list.append(thread_content)
                        
                    self._record_success()
                    
                except Exception as e:
                    self._record_error()
                    logger.error(f"Error processing thread {thread_data.get('no', 'unknown')}: {e}")
                    continue
                    
        except Exception as e:
            self._record_error()
            raise CollectionError(f"Failed to collect from 4chan /biz/: {e}", SourceType.CHAN)
            
        logger.info(f"4chan collection complete: {len(content_list)} threads processed")
        return content_list
        
    async def _get_catalog(self) -> List[Dict]:
        """Get catalog of all threads on /biz/."""
        self._record_request()
        
        async with aiohttp.ClientSession() as session:
            try:
                url = f"{self.base_url}/{self.board}/catalog.json"
                
                async with session.get(url, timeout=10) as response:
                    if response.status != 200:
                        raise CollectionError(
                            f"4chan API returned status {response.status}",
                            SourceType.CHAN
                        )
                        
                    data = await response.json()
                    
                    # Flatten catalog pages into thread list
                    all_threads = []
                    for page in data:
                        threads = page.get('threads', [])
                        all_threads.extend(threads)
                        
                    return all_threads
                    
            except aiohttp.ClientError as e:
                raise CollectionError(f"Network error accessing 4chan: {e}", SourceType.CHAN)
                
    def _identify_valuable_threads(self, catalog: List[Dict], max_threads: int) -> List[Dict]:
        """Identify threads with potential for valuable signals."""
        valuable = []
        
        for thread in catalog:
            value_score = self._calculate_thread_value(thread)
            
            if value_score > 0.3:  # Threshold for consideration
                thread['value_score'] = value_score
                valuable.append(thread)
                
        # Sort by value score and return top threads
        valuable.sort(key=lambda x: x['value_score'], reverse=True)
        return valuable[:max_threads]
        
    def _calculate_thread_value(self, thread: Dict) -> float:
        """Calculate value score for a thread."""
        score = 0.0
        
        # Get thread text content
        subject = thread.get('sub', '')
        comment = thread.get('com', '')
        combined_text = self._clean_html(subject + ' ' + comment).lower()
        
        # Check for valuable patterns
        
        # Insider information patterns (high value but risky)
        insider_matches = sum(1 for pattern in self.insider_patterns if pattern in combined_text)
        if insider_matches > 0:
            score += 0.4 * (insider_matches / len(self.insider_patterns))
            
        # High conviction patterns
        conviction_matches = sum(1 for pattern in self.high_conviction_patterns if pattern in combined_text)
        if conviction_matches > 0:
            score += 0.3 * (conviction_matches / len(self.high_conviction_patterns))
            
        # Momentum patterns
        momentum_matches = sum(1 for pattern in self.momentum_patterns if pattern in combined_text)
        if momentum_matches > 0:
            score += 0.2 * (momentum_matches / len(self.momentum_patterns))
            
        # Thread engagement score
        replies = thread.get('replies', 0)
        unique_ips = thread.get('unique_ips', 1)
        
        if replies > 100:
            score += 0.3
        elif replies > 50:
            score += 0.2
        elif replies > 20:
            score += 0.1
            
        # High unique IP count indicates genuine interest
        if unique_ips > 50:
            score += 0.2
        elif unique_ips > 20:
            score += 0.1
            
        # Recent activity
        thread_time = thread.get('time', 0)
        if thread_time > 0:
            hours_ago = (time.time() - thread_time) / 3600
            if hours_ago < 6:
                score += 0.2
            elif hours_ago < 24:
                score += 0.1
                
        # Has ticker mentions
        tickers = TickerExtractor.extract_tickers(combined_text)
        if tickers:
            score += 0.1 * min(len(tickers), 3)  # Bonus for ticker mentions
            
        return min(score, 1.0)
        
    async def _process_thread(self, thread_data: Dict) -> Optional[RawContent]:
        """Process a full thread with all replies."""
        thread_no = thread_data['no']
        
        async with aiohttp.ClientSession() as session:
            try:
                url = f"{self.base_url}/{self.board}/thread/{thread_no}.json"
                
                async with session.get(url, timeout=15) as response:
                    if response.status != 200:
                        logger.warning(f"Failed to fetch thread {thread_no}: status {response.status}")
                        return None
                        
                    data = await response.json()
                    posts = data.get('posts', [])
                    
                    if not posts:
                        return None
                        
                    return self._create_thread_content(posts, thread_data)
                    
            except Exception as e:
                logger.error(f"Error fetching thread {thread_no}: {e}")
                return None
                
    def _create_thread_content(self, posts: List[Dict], thread_data: Dict) -> RawContent:
        """Create RawContent from thread posts."""
        op = posts[0]  # Original post
        replies = posts[1:] if len(posts) > 1 else []
        
        # Process OP
        op_text = self._clean_html(op.get('com', ''))
        subject = op.get('sub', '')
        
        # Process replies (limit to avoid huge text blocks)
        reply_texts = []
        for reply in replies[:20]:  # Limit to 20 replies
            reply_text = self._clean_html(reply.get('com', ''))
            if len(reply_text) > 20:  # Skip very short replies
                reply_texts.append(reply_text)
                
        # Combine all text
        full_text = f"Subject: {subject}\n\nOP: {op_text}"
        if reply_texts:
            full_text += "\n\nReplies:\n" + "\n---\n".join(reply_texts[:10])  # Top 10 replies
            
        # Extract tickers from full text
        tickers = TickerExtractor.extract_tickers(full_text)
        
        # Calculate engagement metrics
        engagement = {
            'replies': len(replies),
            'unique_ips': op.get('unique_ips', 1),
            'images': op.get('images', 0),
            'bump_limit': len(replies) >= 300,  # 4chan bump limit
            'thread_age_hours': (time.time() - op.get('time', time.time())) / 3600
        }
        
        # Analyze content for extreme patterns
        pattern_detected = ExtremePatternsDetector.detect_pattern(
            type('temp', (), {
                'text': full_text,
                'metadata': {}
            })()
        )
        
        # Calculate credibility indicators
        credibility_score = self._calculate_credibility_score(full_text, engagement)
        
        # Extract metadata
        metadata = {
            'thread_no': op['no'],
            'board': self.board,
            'tickers': tickers,
            'pattern_detected': pattern_detected,
            'credibility_score': credibility_score,
            'insider_probability': self._calculate_insider_probability(full_text),
            'sentiment_indicators': self._extract_sentiment_indicators(full_text),
            'value_score': thread_data.get('value_score', 0),
            'is_archived': False,
            'reply_count': len(replies)
        }
        
        return RawContent(
            id=f"chan_{op['no']}",
            source=SourceType.CHAN,
            platform_id=str(op['no']),
            title=subject or f"Thread #{op['no']}",
            text=full_text,
            author="Anonymous",  # 4chan is anonymous
            created_at=datetime.fromtimestamp(op.get('time', time.time())),
            engagement=engagement,
            url=f"https://boards.4channel.org/{self.board}/thread/{op['no']}",
            metadata=metadata
        )
        
    def _clean_html(self, text: str) -> str:
        """Clean HTML tags from 4chan post content."""
        if not text:
            return ""
            
        # Unescape HTML entities
        text = unescape(text)
        
        # Remove HTML tags but preserve line breaks
        text = re.sub(r'<br\s*/?>', '\n', text)
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()
        
    def _calculate_credibility_score(self, text: str, engagement: Dict) -> float:
        """Calculate credibility score for thread content."""
        score = 0.5  # Start neutral
        
        # Engagement quality
        replies = engagement.get('replies', 0)
        unique_ips = engagement.get('unique_ips', 1)
        
        if unique_ips > 20 and replies > 50:
            score += 0.2  # Good engagement from multiple users
        elif unique_ips > 10 and replies > 20:
            score += 0.1
            
        # Content quality indicators
        text_length = len(text)
        if text_length > 1000:
            score += 0.1  # Detailed posts are often more credible
            
        # Specific language patterns that indicate credibility
        credible_patterns = [
            'sources say',
            'according to',
            'confirmed by',
            'official announcement',
            'SEC filing',
            'earnings report'
        ]
        
        credible_matches = sum(1 for pattern in credible_patterns if pattern in text.lower())
        if credible_matches > 0:
            score += 0.2
            
        # Red flags that reduce credibility
        red_flags = [
            'trust me bro',
            'source: dude trust me',
            'my dad works at',
            'guaranteed money',
            'cant lose'
        ]
        
        red_flag_matches = sum(1 for flag in red_flags if flag in text.lower())
        if red_flag_matches > 0:
            score -= 0.3
            
        return max(0.0, min(1.0, score))
        
    def _calculate_insider_probability(self, text: str) -> float:
        """Calculate probability that content contains insider information."""
        score = 0.0
        text_lower = text.lower()
        
        # Direct insider claims
        insider_claims = [
            'i work at',
            'insider info',
            'my source',
            'confirmed leak',
            'announcement tomorrow',
            'merger talks',
            'buyout coming'
        ]
        
        for claim in insider_claims:
            if claim in text_lower:
                score += 0.2
                
        # Specific timing mentions
        timing_patterns = [
            'monday',
            'tuesday', 
            'wednesday',
            'thursday',
            'friday',
            'next week',
            'this week',
            'earnings',
            'announcement'
        ]
        
        timing_matches = sum(1 for pattern in timing_patterns if pattern in text_lower)
        if timing_matches >= 2:
            score += 0.3
            
        # Confidence language
        if any(phrase in text_lower for phrase in ['100% sure', 'guaranteed', 'confirmed']):
            score += 0.2
            
        # Screenshot/proof mentions
        if any(phrase in text_lower for phrase in ['screenshot this', 'cap this', 'save this post']):
            score += 0.3
            
        return min(score, 0.9)  # Cap at 90% to never be 100% certain
        
    def _extract_sentiment_indicators(self, text: str) -> Dict[str, Any]:
        """Extract sentiment indicators specific to 4chan culture."""
        text_lower = text.lower()
        
        # 4chan specific bullish terms
        bullish_4chan = [
            'moon mission', 'to the moon', 'pump it', 'bullish', 'long',
            'calls', 'buy the dip', 'accumulate', 'load up', 'based',
            'chad move', 'diamond hands', 'wagmi', 'gmi'
        ]
        
        # 4chan specific bearish terms  
        bearish_4chan = [
            'dump it', 'bearish', 'short', 'puts', 'ngmi', 'bagholding',
            'rekt', 'cope', 'seethe', 'dilate', 'rug pull', 'exit scam'
        ]
        
        bullish_count = sum(1 for term in bullish_4chan if term in text_lower)
        bearish_count = sum(1 for term in bearish_4chan if term in text_lower)
        
        total_sentiment = bullish_count + bearish_count
        sentiment_score = 0.0
        if total_sentiment > 0:
            sentiment_score = (bullish_count - bearish_count) / total_sentiment
            
        return {
            'bullish_indicators': bullish_count,
            'bearish_indicators': bearish_count,
            'net_sentiment': sentiment_score,
            'sentiment_strength': min(total_sentiment / 2.0, 1.0),
            'has_moon_mission': 'moon mission' in text_lower,
            'has_pump_language': any(term in text_lower for term in ['pump', 'moon', 'rocket']),
            'has_dump_language': any(term in text_lower for term in ['dump', 'rekt', 'rug'])
        }