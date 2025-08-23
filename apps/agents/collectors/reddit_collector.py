"""
Reddit collector for social sentiment analysis.
Implements zero-cost collection using PRAW with smart rate limiting.

Priority sources from mermaid:
- Long-term: r/stocks, r/investing (20% weight)  
- Swing: r/wallstreetbets, r/options, r/cryptocurrency (25% weight)
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import praw
import asyncpraw
from praw.exceptions import RedditAPIException

from .base_collector import SocialCollector
from ..base import RawContent, SourceType, CollectionError, TickerExtractor

logger = logging.getLogger(__name__)


class RedditCollector(SocialCollector):
    """
    Reddit data collector using PRAW for free API access.
    Rate limit: 60 requests/minute in free tier.
    """
    
    def __init__(
        self, 
        client_id: str,
        client_secret: str, 
        user_agent: str,
        priority_weight: float = 0.225  # Average of 20% + 25% from mermaid
    ):
        super().__init__(SourceType.REDDIT, rate_limit_per_hour=3600, priority_weight=priority_weight)
        
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent
        
        # Initialize Reddit clients
        self.reddit = None
        self.async_reddit = None
        
        # Subreddit categorization based on mermaid priorities
        self.long_term_subreddits = [
            'stocks',          # General stock discussion
            'investing',       # Long-term investment strategies  
            'SecurityAnalysis', # Fundamental analysis
            'ValueInvesting',  # Value investing focus
            'StockMarket',     # Market discussion
            'financialindependence',  # FIRE movement
            'portfolios'       # Portfolio discussion
        ]
        
        self.swing_subreddits = [
            'wallstreetbets',  # High-momentum plays
            'options',         # Options trading
            'cryptocurrency',  # Crypto swings
            'CryptoCurrency', 
            'pennystocks',     # Small cap momentum
            'Daytrading',      # Short-term trading
            'shortsqueeze',    # Squeeze plays
            'SPACs'           # SPAC opportunities
        ]
        
        # Sentiment indicators specific to Reddit culture
        self.bullish_indicators = [
            'moon', 'rocket', '', 'diamond hands', '', '',
            'hold', 'buy the dip', 'squeeze', 'gamma', 'calls',
            'yolo', 'to the moon', 'tendies', 'bullish', 'long'
        ]
        
        self.bearish_indicators = [
            'puts', 'short', 'sell', 'dump', 'crash', 'bear',
            'red', 'loss', 'down', 'overvalued', 'bubble',
            'dead cat bounce', 'rug pull', 'bagholding'
        ]
        
    def get_collector_name(self) -> str:
        """Return the collector name."""
        return "RedditCollector"
        
    def validate_config(self) -> bool:
        """Validate Reddit API configuration."""
        return all([self.client_id, self.client_secret, self.user_agent])
        
    def _initialize_reddit_clients(self):
        """Initialize Reddit API clients."""
        if not self.reddit:
            self.reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent
            )
            
        if not self.async_reddit:
            self.async_reddit = asyncpraw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent
            )
            
    async def collect_content(self, **kwargs) -> List[RawContent]:
        """Generic content collection method."""
        signal_type = kwargs.get('signal_type', 'swing')
        
        if signal_type == 'long_term':
            return await self.collect_long_term_signals(**kwargs)
        else:
            return await self.collect_swing_signals(**kwargs)
            
    async def collect_long_term_signals(self, **kwargs) -> List[RawContent]:
        """
        Collect content from long-term investment subreddits.
        Focus on DD posts, fundamental analysis, and long-term thesis.
        """
        self._initialize_reddit_clients()
        
        content_list = []
        limit = kwargs.get('limit', 50)  # Limit per subreddit
        
        logger.info(f"Collecting long-term signals from {len(self.long_term_subreddits)} subreddits")
        
        for subreddit_name in self.long_term_subreddits[:3]:  # Top 3 for budget
            try:
                self._check_rate_limit()
                self._record_request()
                
                subreddit = await self.async_reddit.subreddit(subreddit_name)
                
                # Focus on hot posts with good engagement
                async for post in subreddit.hot(limit=limit):
                    if post.score < 20:  # Filter low-quality posts
                        continue
                        
                    content = await self._process_reddit_post(post, subreddit_name)
                    if content and self._is_investment_relevant(content):
                        content_list.append(content)
                        
                self._record_success()
                logger.debug(f"Collected {len([c for c in content_list if c.metadata.get('subreddit') == subreddit_name])} posts from r/{subreddit_name}")
                
            except RedditAPIException as e:
                self._record_error()
                logger.error(f"Reddit API error for r/{subreddit_name}: {e}")
                continue
            except Exception as e:
                self._record_error()
                logger.error(f"Unexpected error collecting from r/{subreddit_name}: {e}")
                continue
                
        logger.info(f"Long-term collection complete: {len(content_list)} high-quality posts")
        return content_list
        
    async def collect_swing_signals(self, **kwargs) -> List[RawContent]:
        """
        Collect content from momentum/swing trading subreddits.
        Focus on breaking news, momentum plays, and short-term catalysts.
        """
        self._initialize_reddit_clients()
        
        content_list = []
        limit = kwargs.get('limit', 30)  # Smaller limit for swing (more frequent)
        
        logger.info(f"Collecting swing signals from {len(self.swing_subreddits)} subreddits")
        
        for subreddit_name in self.swing_subreddits[:4]:  # Top 4 for budget
            try:
                self._check_rate_limit()
                self._record_request()
                
                subreddit = await self.async_reddit.subreddit(subreddit_name)
                
                # For swing trades, prioritize new and rising posts
                tasks = [
                    self._collect_from_listing(subreddit.hot(limit=limit//2), subreddit_name),
                    self._collect_from_listing(subreddit.new(limit=limit//2), subreddit_name)
                ]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"Error collecting from r/{subreddit_name}: {result}")
                        continue
                    content_list.extend(result)
                    
                self._record_success()
                
            except Exception as e:
                self._record_error()
                logger.error(f"Error collecting swing signals from r/{subreddit_name}: {e}")
                continue
                
        logger.info(f"Swing collection complete: {len(content_list)} posts")
        return content_list
        
    async def _collect_from_listing(self, listing, subreddit_name: str) -> List[RawContent]:
        """Collect content from a Reddit listing."""
        content_list = []
        
        async for post in listing:
            if post.score < 10:  # Lower threshold for swing trades
                continue
                
            content = await self._process_reddit_post(post, subreddit_name)
            if content and self._has_momentum_signals(content):
                content_list.append(content)
                
        return content_list
        
    async def _process_reddit_post(self, post, subreddit_name: str) -> Optional[RawContent]:
        """Process a Reddit post into RawContent format."""
        try:
            # Get top comments for additional context
            await post.comments.replace_more(limit=0)
            top_comments = []
            
            for comment in post.comments[:5]:  # Top 5 comments only
                if hasattr(comment, 'body') and comment.score > 5:
                    top_comments.append({
                        'body': comment.body[:300],  # Limit comment length
                        'score': comment.score,
                        'author': str(comment.author) if comment.author else '[deleted]'
                    })
                    
            # Extract engagement metrics
            engagement = {
                'score': post.score,
                'upvote_ratio': post.upvote_ratio,
                'num_comments': post.num_comments,
                'awards': getattr(post, 'total_awards_received', 0)
            }
            
            # Combine post text and top comments
            full_text = post.title + "\n\n" + (post.selftext or "")
            if top_comments:
                comments_text = "\n".join([c['body'] for c in top_comments])
                full_text += "\n\nTop Comments:\n" + comments_text
                
            # Extract metadata
            metadata = {
                'subreddit': subreddit_name,
                'flair': post.link_flair_text,
                'is_dd': self._is_due_diligence(post),
                'is_discussion': 'discussion' in (post.link_flair_text or '').lower(),
                'tickers': TickerExtractor.extract_tickers(full_text),
                'sentiment_indicators': self._extract_sentiment_indicators(full_text),
                'top_comments': top_comments
            }
            
            return RawContent(
                id=f"reddit_{post.id}",
                source=SourceType.REDDIT,
                platform_id=post.id,
                title=post.title,
                text=full_text,
                author=str(post.author) if post.author else '[deleted]',
                created_at=datetime.fromtimestamp(post.created_utc),
                engagement=engagement,
                url=f"https://reddit.com{post.permalink}",
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error processing Reddit post {post.id}: {e}")
            return None
            
    def _is_due_diligence(self, post) -> bool:
        """Check if post is a Due Diligence post (high value for long-term)."""
        dd_indicators = ['DD', 'Due Diligence', 'Deep Dive', 'Analysis', 'Research', 'Thesis']
        
        # Check flair
        if post.link_flair_text:
            for indicator in dd_indicators:
                if indicator.lower() in post.link_flair_text.lower():
                    return True
                    
        # Check title
        for indicator in dd_indicators:
            if indicator.lower() in post.title.lower():
                return True
                
        # Check post length (DD posts are usually long)
        if len(post.selftext) > 1500:
            return True
            
        return False
        
    def _extract_sentiment_indicators(self, text: str) -> Dict[str, Any]:
        """Extract Reddit-specific sentiment indicators."""
        text_lower = text.lower()
        
        bullish_count = sum(1 for indicator in self.bullish_indicators if indicator in text_lower)
        bearish_count = sum(1 for indicator in self.bearish_indicators if indicator in text_lower)
        
        # Calculate sentiment score
        total_indicators = bullish_count + bearish_count
        sentiment_score = 0.0
        if total_indicators > 0:
            sentiment_score = (bullish_count - bearish_count) / total_indicators
            
        return {
            'bullish_indicators': bullish_count,
            'bearish_indicators': bearish_count,
            'net_sentiment': sentiment_score,
            'has_rockets': '' in text or 'rocket' in text_lower,
            'has_diamond_hands': '' in text or 'diamond hands' in text_lower,
            'has_yolo': 'yolo' in text_lower,
            'sentiment_strength': min(total_indicators / 3.0, 1.0)  # Normalize to 0-1
        }
        
    def _is_investment_relevant(self, content: RawContent) -> bool:
        """Check if content is relevant for investment analysis."""
        # Must have tickers or be DD
        if not content.metadata.get('tickers') and not content.metadata.get('is_dd'):
            return False
            
        # Must have minimum engagement
        if content.engagement['score'] < 20:
            return False
            
        # Must have some sentiment indicators or decent length
        sentiment = content.metadata.get('sentiment_indicators', {})
        if sentiment.get('sentiment_strength', 0) < 0.1 and len(content.text) < 200:
            return False
            
        return True
        
    def _has_momentum_signals(self, content: RawContent) -> bool:
        """Check if content has momentum/swing trading signals."""
        # Check for momentum indicators
        sentiment = content.metadata.get('sentiment_indicators', {})
        
        # Strong sentiment signals
        if sentiment.get('sentiment_strength', 0) > 0.3:
            return True
            
        # Recent post with good engagement
        age_hours = (datetime.now() - content.created_at).total_seconds() / 3600
        if age_hours < 6 and content.engagement['score'] > 50:
            return True
            
        # Has momentum keywords
        momentum_keywords = ['squeeze', 'moon', 'rocket', 'breakout', 'momentum', 'surge']
        text_lower = content.text.lower()
        if any(keyword in text_lower for keyword in momentum_keywords):
            return True
            
        return False
        
    async def track_ticker_momentum(self, ticker: str, hours: int = 24) -> Dict[str, Any]:
        """Track mention momentum for a specific ticker across Reddit."""
        self._initialize_reddit_clients()
        
        momentum_data = {
            'ticker': ticker,
            'mentions': [],
            'subreddit_breakdown': {},
            'sentiment_trend': [],
            'total_mentions': 0
        }
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Search across key subreddits
        search_subreddits = self.long_term_subreddits + self.swing_subreddits
        
        for subreddit_name in search_subreddits[:5]:  # Limit for API budget
            try:
                self._check_rate_limit()
                subreddit = await self.async_reddit.subreddit(subreddit_name)
                
                # Search for ticker mentions
                async for post in subreddit.search(f"${ticker} OR {ticker}", time_filter='day', limit=20):
                    post_time = datetime.fromtimestamp(post.created_utc)
                    
                    if post_time > cutoff_time:
                        mention_data = {
                            'timestamp': post.created_utc,
                            'score': post.score,
                            'comments': post.num_comments,
                            'subreddit': subreddit_name,
                            'sentiment': self._extract_sentiment_indicators(post.title + " " + (post.selftext or {}))['net_sentiment']
                        }
                        
                        momentum_data['mentions'].append(mention_data)
                        
                        # Update subreddit breakdown
                        if subreddit_name not in momentum_data['subreddit_breakdown']:
                            momentum_data['subreddit_breakdown'][subreddit_name] = 0
                        momentum_data['subreddit_breakdown'][subreddit_name] += 1
                        
            except Exception as e:
                logger.error(f"Error tracking {ticker} in r/{subreddit_name}: {e}")
                continue
                
        # Calculate momentum metrics
        momentum_data['total_mentions'] = len(momentum_data['mentions'])
        
        if momentum_data['mentions']:
            # Average sentiment
            avg_sentiment = sum(m['sentiment'] for m in momentum_data['mentions']) / len(momentum_data['mentions'])
            momentum_data['average_sentiment'] = avg_sentiment
            
            # Momentum score (mentions per hour * engagement)
            time_span_hours = max(hours, 1)
            mention_rate = len(momentum_data['mentions']) / time_span_hours
            avg_engagement = sum(m['score'] + m['comments'] for m in momentum_data['mentions']) / len(momentum_data['mentions'])
            momentum_data['momentum_score'] = mention_rate * (avg_engagement / 100)  # Normalize engagement
            
        return momentum_data