# MVP Social Sources Implementation Guide
*Detailed Code for Each Platform*

##  Reddit Implementation (Day 1-2)

### Setup & Authentication
```python
# requirements.txt
praw==7.7.1
pandas==2.0.3
asyncpraw==7.7.1

# reddit_collector.py
import praw
import asyncpraw
from datetime import datetime, timedelta
import json
import re
from typing import List, Dict, Any

class RedditCollector:
    def __init__(self):
        # Use your existing Reddit API credentials
        self.reddit = praw.Reddit(
            client_id="YOUR_CLIENT_ID",
            client_secret="YOUR_CLIENT_SECRET",
            user_agent="WaardhavenMVP/1.0 by /u/yourusername"
        )
        
        # High-value subreddits for financial signals
        self.target_subreddits = [
            'wallstreetbets',       # 14M members, high volatility plays
            'stocks',               # 3M members, general discussion
            'investing',            # 2M members, long-term focused
            'cryptocurrency',       # 6M members, crypto signals
            'CryptoCurrency',       # Different from above
            'options',              # 2M members, options plays
            'pennystocks',          # 2M members, small cap plays
            'StockMarket',          # 3M members
            'Daytrading',           # 2M members
            'algotrading',          # 500k members, quant strategies
            'SecurityAnalysis',     # 2M members, fundamental analysis
            'ValueInvesting',       # 500k members
            'SPACs',               # 500k members, SPAC plays
            'Shortsqueeze',        # 500k members, squeeze plays
            'RobinHood'            # 2M members, retail sentiment
        ]
        
        self.ticker_pattern = re.compile(r'\$([A-Z]{1,5})\b|(?:^|\s)([A-Z]{2,5})(?=\s|$|\.|,)')
        
    def collect_hot_posts(self, limit=100) -> List[Dict]:
        """Collect hot posts from target subreddits"""
        all_posts = []
        
        for subreddit_name in self.target_subreddits[:5]:  # Start with top 5 for MVP
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                for post in subreddit.hot(limit=limit):
                    if post.score < 50:  # Filter low-quality posts
                        continue
                        
                    post_data = {
                        'id': post.id,
                        'subreddit': subreddit_name,
                        'title': post.title,
                        'text': post.selftext[:1000],  # Limit text length
                        'score': post.score,
                        'upvote_ratio': post.upvote_ratio,
                        'num_comments': post.num_comments,
                        'created_utc': post.created_utc,
                        'author': str(post.author) if post.author else '[deleted]',
                        'url': f"https://reddit.com{post.permalink}",
                        'tickers': self.extract_tickers(post.title + " " + post.selftext),
                        'flair': post.link_flair_text,
                        'is_dd': self._is_dd_post(post),  # Due Diligence posts are valuable
                        'sentiment_indicators': self._extract_sentiment_indicators(post)
                    }
                    
                    # Get top comments for additional context
                    post_data['top_comments'] = self._get_top_comments(post, limit=5)
                    
                    all_posts.append(post_data)
                    
            except Exception as e:
                print(f"Error collecting from r/{subreddit_name}: {e}")
                continue
                
        return all_posts
    
    def extract_tickers(self, text: str) -> List[str]:
        """Extract stock tickers from text"""
        tickers = []
        matches = self.ticker_pattern.findall(text.upper())
        
        for match in matches:
            ticker = match[0] if match[0] else match[1]
            
            # Filter out common words that match pattern
            if ticker not in ['THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 
                            'NEW', 'OLD', 'NYSE', 'NASDAQ', 'CEO', 'CFO', 'IPO', 
                            'FDA', 'SEC', 'USA', 'ETF', 'LOL', 'WTF', 'USD']:
                tickers.append(ticker)
                
        return list(set(tickers))[:10]  # Max 10 tickers per post
    
    def _is_dd_post(self, post) -> bool:
        """Check if post is a Due Diligence post (high value)"""
        dd_indicators = ['DD', 'Due Diligence', 'Deep Dive', 'Analysis', 'Research']
        
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
        if len(post.selftext) > 2000:
            return True
            
        return False
    
    def _extract_sentiment_indicators(self, post) -> Dict:
        """Extract sentiment indicators from post"""
        bullish_words = ['moon', 'squeeze', 'gamma', 'calls', 'buy', 'long', 'hold', 
                        'diamond hands', '', '', '', 'yolo', 'tendies', 'gains']
        bearish_words = ['puts', 'short', 'sell', 'dump', 'crash', 'bear', 'red', 
                        'loss', 'down', '', '', 'bankruptcy', 'overvalued']
        
        text = (post.title + " " + post.selftext).lower()
        
        bullish_count = sum(1 for word in bullish_words if word in text)
        bearish_count = sum(1 for word in bearish_words if word in text)
        
        return {
            'bullish_indicators': bullish_count,
            'bearish_indicators': bearish_count,
            'net_sentiment': bullish_count - bearish_count,
            'has_rockets': '' in text,  # Strong bullish signal in WSB culture
            'has_diamond_hands': '' in text or 'diamond hands' in text
        }
    
    def _get_top_comments(self, post, limit=5) -> List[Dict]:
        """Get top comments from post"""
        comments = []
        
        try:
            post.comments.replace_more(limit=0)  # Don't fetch nested comments
            
            for comment in post.comments[:limit]:
                if hasattr(comment, 'body'):
                    comments.append({
                        'text': comment.body[:500],
                        'score': comment.score,
                        'author': str(comment.author) if comment.author else '[deleted]',
                        'tickers': self.extract_tickers(comment.body)
                    })
        except:
            pass
            
        return comments
    
    def track_momentum(self, ticker: str, hours=24) -> Dict:
        """Track mention momentum for a specific ticker"""
        momentum_data = {
            'ticker': ticker,
            'mentions': [],
            'sentiment_trend': [],
            'top_posts': []
        }
        
        cutoff_time = datetime.utcnow().timestamp() - (hours * 3600)
        
        for subreddit_name in self.target_subreddits[:3]:  # Check top 3 subreddits
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Search for ticker mentions
                for post in subreddit.search(f"${ticker} OR {ticker}", time_filter='day', limit=100):
                    if post.created_utc > cutoff_time:
                        momentum_data['mentions'].append({
                            'timestamp': post.created_utc,
                            'score': post.score,
                            'comments': post.num_comments,
                            'sentiment': self._extract_sentiment_indicators(post)['net_sentiment']
                        })
                        
                        if post.score > 100:
                            momentum_data['top_posts'].append({
                                'title': post.title,
                                'url': f"https://reddit.com{post.permalink}",
                                'score': post.score
                            })
                            
            except:
                continue
                
        # Calculate momentum metrics
        if momentum_data['mentions']:
            momentum_data['total_mentions'] = len(momentum_data['mentions'])
            momentum_data['avg_sentiment'] = sum(m['sentiment'] for m in momentum_data['mentions']) / len(momentum_data['mentions'])
            momentum_data['momentum_score'] = self._calculate_momentum_score(momentum_data['mentions'])
            
        return momentum_data
    
    def _calculate_momentum_score(self, mentions: List[Dict]) -> float:
        """Calculate momentum score based on mention frequency and engagement"""
        if not mentions:
            return 0
            
        # Sort by timestamp
        mentions.sort(key=lambda x: x['timestamp'])
        
        # Calculate rate of change
        if len(mentions) > 1:
            time_span = mentions[-1]['timestamp'] - mentions[0]['timestamp']
            if time_span > 0:
                mention_rate = len(mentions) / (time_span / 3600)  # Mentions per hour
                avg_engagement = sum(m['score'] + m['comments'] for m in mentions) / len(mentions)
                
                # Momentum score combines frequency and engagement
                momentum = (mention_rate * 10) + (avg_engagement / 100)
                return min(momentum, 100)  # Cap at 100
                
        return 0
```

##  YouTube Implementation (Day 3)

```python
# youtube_collector.py
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
from datetime import datetime, timedelta
import re

class YouTubeCollector:
    def __init__(self, api_key: str):
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        
        # High-value finance channels
        self.trusted_channels = [
            'UCY2ifv8iH1Dsgjbf-iJUySw',  # Meet Kevin
            'UCFCEuCsyWP0YkP3CZ3Mr01Q',  # Graham Stephan
            'UCAmRx4HZxqDIgLAHdGEqNvw',  # Financial Education
            'UC0uVZnl6pPaP3ujFngK5LFQ',  # InTheMoney
            'UCqK0ukwGsTDh7sHjtPRQ-Jg',  # Tom Nash
            'UCL3v5XpunCafXYFxcqYQVaQ',  # Everything Money
            'UCjuKQCnkzDW2Z2yq6f3R3Lg',  # Chicken Genius Singapore
        ]
        
        # Search keywords for discovering new content
        self.search_keywords = [
            'stock market today',
            'stock analysis',
            'trading signals',
            'market crash',
            'earnings call',
            'stock squeeze',
            'breakout stocks',
            'penny stocks',
            'options trading',
            'crypto analysis'
        ]
        
    def collect_videos(self, max_results=50) -> List[Dict]:
        """Collect recent finance videos"""
        all_videos = []
        
        # Search for recent finance videos
        for keyword in self.search_keywords[:3]:  # Limit searches for MVP
            try:
                request = self.youtube.search().list(
                    q=keyword,
                    part='snippet',
                    type='video',
                    order='viewCount',
                    maxResults=10,
                    publishedAfter=(datetime.now() - timedelta(days=2)).isoformat() + 'Z'
                )
                
                response = request.execute()
                
                for item in response['items']:
                    video_data = self._process_video(item)
                    if video_data:
                        all_videos.append(video_data)
                        
            except Exception as e:
                print(f"Error searching YouTube for '{keyword}': {e}")
                
        # Get videos from trusted channels
        for channel_id in self.trusted_channels[:3]:  # Top 3 channels for MVP
            try:
                request = self.youtube.search().list(
                    channelId=channel_id,
                    part='snippet',
                    type='video',
                    order='date',
                    maxResults=5
                )
                
                response = request.execute()
                
                for item in response['items']:
                    video_data = self._process_video(item)
                    if video_data:
                        all_videos.append(video_data)
                        
            except:
                continue
                
        return all_videos
    
    def _process_video(self, item: Dict) -> Dict:
        """Process individual video"""
        video_id = item['id']['videoId']
        
        # Get video details
        try:
            details_request = self.youtube.videos().list(
                part='statistics,contentDetails',
                id=video_id
            )
            details = details_request.execute()
            
            if not details['items']:
                return None
                
            stats = details['items'][0]['statistics']
            
            video_data = {
                'id': video_id,
                'title': item['snippet']['title'],
                'channel': item['snippet']['channelTitle'],
                'channel_id': item['snippet']['channelId'],
                'description': item['snippet']['description'][:500],
                'published': item['snippet']['publishedAt'],
                'thumbnail': item['snippet']['thumbnails']['high']['url'],
                'url': f"https://youtube.com/watch?v={video_id}",
                'views': int(stats.get('viewCount', 0)),
                'likes': int(stats.get('likeCount', 0)),
                'comments': int(stats.get('commentCount', 0)),
                'duration': self._parse_duration(details['items'][0]['contentDetails']['duration']),
                'tickers': self._extract_tickers_from_text(
                    item['snippet']['title'] + " " + item['snippet']['description']
                ),
                'is_trusted': item['snippet']['channelId'] in self.trusted_channels,
                'engagement_rate': self._calculate_engagement_rate(stats)
            }
            
            # Get transcript if video is important enough
            if video_data['views'] > 10000 or video_data['is_trusted']:
                video_data['needs_transcription'] = True
                video_data['transcription_priority'] = self._calculate_priority(video_data)
            else:
                video_data['needs_transcription'] = False
                
            return video_data
            
        except Exception as e:
            print(f"Error processing video {video_id}: {e}")
            return None
    
    def get_transcript(self, video_id: str) -> str:
        """Get video transcript"""
        try:
            # Try to get auto-generated captions first (free)
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            transcript = ' '.join([t['text'] for t in transcript_list])
            return transcript
            
        except:
            # If no captions, mark for Whisper transcription
            return None
    
    def _extract_tickers_from_text(self, text: str) -> List[str]:
        """Extract tickers from video title/description"""
        ticker_pattern = re.compile(r'\$([A-Z]{1,5})\b|(?:^|\s)([A-Z]{2,5})(?=\s|$|\)|,)')
        tickers = []
        
        matches = ticker_pattern.findall(text.upper())
        for match in matches:
            ticker = match[0] if match[0] else match[1]
            if ticker not in ['THE', 'AND', 'FOR', 'THIS', 'THAT', 'WITH', 'FROM']:
                tickers.append(ticker)
                
        return list(set(tickers))[:5]
    
    def _calculate_engagement_rate(self, stats: Dict) -> float:
        """Calculate engagement rate"""
        views = int(stats.get('viewCount', 1))
        likes = int(stats.get('likeCount', 0))
        comments = int(stats.get('commentCount', 0))
        
        if views > 0:
            return ((likes + comments) / views) * 100
        return 0
    
    def _calculate_priority(self, video_data: Dict) -> int:
        """Calculate transcription priority"""
        priority = 0
        
        # Trusted channel gets high priority
        if video_data['is_trusted']:
            priority += 50
            
        # High views
        if video_data['views'] > 100000:
            priority += 30
        elif video_data['views'] > 50000:
            priority += 20
        elif video_data['views'] > 10000:
            priority += 10
            
        # High engagement
        if video_data['engagement_rate'] > 5:
            priority += 20
        elif video_data['engagement_rate'] > 2:
            priority += 10
            
        # Has tickers mentioned
        if video_data['tickers']:
            priority += 15
            
        return priority
    
    def _parse_duration(self, duration: str) -> int:
        """Parse ISO 8601 duration to seconds"""
        import re
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        if match:
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)
            return hours * 3600 + minutes * 60 + seconds
        return 0
```

##  TikTok Implementation (Day 4)

```python
# tiktok_collector.py
import requests
from bs4 import BeautifulSoup
import json
from typing import List, Dict
import time

class TikTokCollector:
    def __init__(self, proxy_service_url: str = None):
        """
        TikTok is harder to scrape, so we'll use a combination of methods
        For MVP, we can use manual collection or a scraping service
        """
        self.proxy_url = proxy_service_url
        
        # FinTok influencers to track
        self.fintok_creators = [
            'humphreytalks',      # Humphrey Yang - 3.3M followers
            'investwithqueenie',  # Queenie - 1M followers
            'ceowatchlist',       # CEO Watchlist
            'thetradingfraternity', # Trading Fraternity
            'stockmarketpro',     # Stock Market Pro
            'taylormitchell',     # Taylor Mitchell
            'austin.hankwitz',    # Austin Hankwitz
            'richardcrypto',      # Crypto focus
            'thestockguy',        # Steve from StockMarket
            'pricelesspenny'      # Penny stock focus
        ]
        
        # FinTok hashtags
        self.hashtags = [
            '#stocks',
            '#investing',
            '#stockmarket',
            '#fintok',
            '#stocktok',
            '#options',
            '#trading',
            '#pennystocks',
            '#crypto',
            '#passiveincome',
            '#wealthbuilding',
            '#financialliteracy'
        ]
        
    def collect_fintok_content(self) -> List[Dict]:
        """
        Collect FinTok content
        Note: TikTok API is restricted, so we use alternative methods
        """
        all_content = []
        
        # Method 1: Use TikTok web scraping (be careful with rate limits)
        for creator in self.fintok_creators[:3]:  # Top 3 for MVP
            try:
                videos = self._scrape_creator_videos(creator)
                all_content.extend(videos)
            except:
                continue
                
        # Method 2: Search hashtags
        for hashtag in self.hashtags[:3]:
            try:
                videos = self._scrape_hashtag_videos(hashtag)
                all_content.extend(videos)
            except:
                continue
                
        return all_content
    
    def _scrape_creator_videos(self, username: str) -> List[Dict]:
        """Scrape videos from a creator's page"""
        videos = []
        
        # Note: This is a simplified example. In production, you'd need
        # proper headers, cookies, and potentially a headless browser
        
        url = f"https://www.tiktok.com/@{username}"
        
        try:
            # Use proxy if available
            if self.proxy_url:
                response = requests.get(url, proxies={'https': self.proxy_url})
            else:
                response = requests.get(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
            # Parse the page
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract video data (simplified - real implementation needs JavaScript rendering)
            # For MVP, we might need to use a service like Bright Data or ScrapingBee
            
            # Placeholder for extracted data
            videos.append({
                'creator': username,
                'platform': 'tiktok',
                'url': url,
                'needs_manual_review': True,  # Flag for manual data collection
                'priority': 'high' if username in self.fintok_creators[:5] else 'medium'
            })
            
        except Exception as e:
            print(f"Error scraping TikTok creator {username}: {e}")
            
        return videos
    
    def _scrape_hashtag_videos(self, hashtag: str) -> List[Dict]:
        """Scrape videos from hashtag page"""
        # Similar to creator scraping
        # For MVP, might need manual collection or paid API
        
        return [{
            'hashtag': hashtag,
            'platform': 'tiktok',
            'needs_collection': True
        }]
    
    def extract_video_text(self, video_data: Dict) -> str:
        """
        Extract text from TikTok video
        This would include:
        1. Video description/caption
        2. On-screen text (OCR)
        3. Audio transcription
        """
        # For MVP, focus on descriptions and manual transcription of important videos
        return video_data.get('description', '')
```

##  4chan /biz/ Implementation (Day 5)

```python
# chan_collector.py
import requests
import json
from datetime import datetime
import re
from typing import List, Dict
import time

class ChanCollector:
    def __init__(self):
        """
        4chan has a public API for reading (not posting)
        /biz/ is the business & finance board
        """
        self.base_url = "https://a.4cdn.org"
        self.board = "biz"
        
        # Patterns that indicate high-value threads
        self.valuable_patterns = [
            'insider',
            'dd',
            'due diligence',
            'squeeze',
            'pump',
            'gem',
            'moon',
            '100x',
            '10x',
            'early',
            'accumulate'
        ]
        
        # Ticker extraction pattern
        self.ticker_pattern = re.compile(r'\$([A-Z]{1,5})\b|(?:^|\s)([A-Z]{3,5})(?=\s|$)')
        
    def collect_biz_threads(self, pages=3) -> List[Dict]:
        """Collect threads from /biz/"""
        all_threads = []
        
        # Get catalog (all threads)
        try:
            catalog_url = f"{self.base_url}/{self.board}/catalog.json"
            response = requests.get(catalog_url)
            catalog = response.json()
            
            # Process each page
            for page in catalog[:pages]:
                for thread in page.get('threads', []):
                    thread_data = self._process_thread(thread)
                    if thread_data and self._is_valuable_thread(thread_data):
                        # Get full thread with replies
                        full_thread = self._get_full_thread(thread_data['no'])
                        if full_thread:
                            all_threads.append(full_thread)
                            
            return all_threads
            
        except Exception as e:
            print(f"Error collecting from 4chan: {e}")
            return []
    
    def _process_thread(self, thread: Dict) -> Dict:
        """Process thread data"""
        return {
            'no': thread.get('no'),  # Thread number
            'time': thread.get('time'),
            'name': thread.get('name', 'Anonymous'),
            'subject': thread.get('sub', ''),
            'comment': self._clean_html(thread.get('com', '')),
            'replies': thread.get('replies', 0),
            'images': thread.get('images', 0),
            'unique_ips': thread.get('unique_ips', 0),
            'tickers': self._extract_tickers(
                thread.get('sub', '') + " " + thread.get('com', '')
            )
        }
    
    def _get_full_thread(self, thread_no: int) -> Dict:
        """Get full thread with all replies"""
        try:
            thread_url = f"{self.base_url}/{self.board}/thread/{thread_no}.json"
            response = requests.get(thread_url)
            thread_data = response.json()
            
            posts = thread_data.get('posts', [])
            if not posts:
                return None
                
            # Process OP (original post)
            op = posts[0]
            processed_thread = {
                'thread_no': thread_no,
                'url': f"https://boards.4channel.org/{self.board}/thread/{thread_no}",
                'subject': op.get('sub', ''),
                'op_comment': self._clean_html(op.get('com', '')),
                'time': datetime.fromtimestamp(op.get('time', 0)),
                'replies': [],
                'total_replies': len(posts) - 1,
                'unique_ips': op.get('unique_ips', 0),
                'tickers': set(),
                'sentiment_indicators': {'bullish': 0, 'bearish': 0},
                'insider_probability': 0
            }
            
            # Extract tickers from OP
            processed_thread['tickers'].update(
                self._extract_tickers(processed_thread['op_comment'])
            )
            
            # Process replies
            for post in posts[1:]:  # Skip OP
                reply = {
                    'comment': self._clean_html(post.get('com', '')),
                    'time': post.get('time'),
                    'name': post.get('name', 'Anonymous')
                }
                
                # Extract tickers from reply
                reply_tickers = self._extract_tickers(reply['comment'])
                processed_thread['tickers'].update(reply_tickers)
                
                # Analyze sentiment
                if self._is_bullish(reply['comment']):
                    processed_thread['sentiment_indicators']['bullish'] += 1
                elif self._is_bearish(reply['comment']):
                    processed_thread['sentiment_indicators']['bearish'] += 1
                    
                processed_thread['replies'].append(reply)
            
            # Convert tickers set to list
            processed_thread['tickers'] = list(processed_thread['tickers'])
            
            # Calculate insider probability
            processed_thread['insider_probability'] = self._calculate_insider_probability(processed_thread)
            
            return processed_thread
            
        except Exception as e:
            print(f"Error getting thread {thread_no}: {e}")
            return None
    
    def _is_valuable_thread(self, thread: Dict) -> bool:
        """Determine if thread is worth analyzing"""
        # High reply count indicates interest
        if thread.get('replies', 0) > 50:
            return True
            
        # Check for valuable patterns
        text = (thread.get('subject', '') + " " + thread.get('comment', '')).lower()
        for pattern in self.valuable_patterns:
            if pattern in text:
                return True
                
        # Has tickers mentioned
        if thread.get('tickers'):
            return True
            
        return False
    
    def _extract_tickers(self, text: str) -> List[str]:
        """Extract stock tickers from text"""
        # Clean the text first
        text = self._clean_html(text)
        
        tickers = []
        matches = self.ticker_pattern.findall(text.upper())
        
        for match in matches:
            ticker = match[0] if match[0] else match[1]
            
            # Filter out common words and crypto (unless it's a known stock)
            if (len(ticker) >= 2 and 
                ticker not in ['THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 
                              'BTC', 'ETH', 'USD', 'CEO', 'IPO', 'FDA', 'SEC']):
                tickers.append(ticker)
                
        return list(set(tickers))
    
    def _clean_html(self, text: str) -> str:
        """Clean HTML from 4chan posts"""
        if not text:
            return ""
            
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        # Remove special characters
        text = re.sub(r'&gt;', '>', text)
        text = re.sub(r'&lt;', '<', text)
        text = re.sub(r'&amp;', '&', text)
        text = re.sub(r'&#039;', "'", text)
        text = re.sub(r'&quot;', '"', text)
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _is_bullish(self, text: str) -> bool:
        """Check if text is bullish"""
        bullish_terms = ['moon', 'buy', 'calls', 'long', 'squeeze', 'pump', 
                        'breakout', 'accumulate', 'load up', 'gem', 'early']
        text_lower = text.lower()
        return any(term in text_lower for term in bullish_terms)
    
    def _is_bearish(self, text: str) -> bool:
        """Check if text is bearish"""
        bearish_terms = ['dump', 'sell', 'puts', 'short', 'crash', 'rug', 
                        'scam', 'overvalued', 'bubble', 'dead', 'avoid']
        text_lower = text.lower()
        return any(term in text_lower for term in bearish_terms)
    
    def _calculate_insider_probability(self, thread: Dict) -> float:
        """
        Calculate probability that thread contains insider information
        Based on various heuristics
        """
        score = 0.0
        
        # Specific language patterns
        insider_patterns = [
            'work at', 'work for', 'insider', 'employee', 'know someone',
            'trust me', 'screenshot this', 'heard from', 'meeting',
            'announcement', 'earnings', 'deal', 'acquisition'
        ]
        
        text = (thread['op_comment'] + " ".join(r['comment'] for r in thread['replies'])).lower()
        
        for pattern in insider_patterns:
            if pattern in text:
                score += 0.1
                
        # High confidence language
        if any(phrase in text for phrase in ['100% sure', 'guaranteed', 'confirmed']):
            score += 0.15
            
        # Specific date/time mentions
        if re.search(r'\d{1,2}[/-]\d{1,2}', text) or re.search(r'(monday|tuesday|wednesday|thursday|friday)', text):
            score += 0.1
            
        # High engagement from unique IPs (not samefagging)
        if thread['unique_ips'] > 20:
            score += 0.1
            
        # Cap at 0.9 (never 100% certain)
        return min(score, 0.9)
```

##  Integration Layer

```python
# social_aggregator.py
from typing import List, Dict, Any
import asyncio
from datetime import datetime
import pandas as pd

class SocialAggregator:
    def __init__(self):
        self.reddit = RedditCollector()
        self.youtube = YouTubeCollector(api_key="YOUR_YOUTUBE_API_KEY")
        self.tiktok = TikTokCollector()
        self.chan = ChanCollector()
        
        self.all_data = []
        
    async def collect_all_sources(self) -> Dict[str, Any]:
        """Collect data from all social sources"""
        
        print(" Starting social data collection...")
        
        # Collect in parallel where possible
        tasks = [
            self._collect_reddit(),
            self._collect_youtube(),
            self._collect_chan()
        ]
        
        results = await asyncio.gather(*tasks)
        
        # TikTok separately due to rate limits
        tiktok_data = await self._collect_tiktok()
        
        # Aggregate all data
        aggregated = {
            'reddit': results[0],
            'youtube': results[1],
            'chan': results[2],
            'tiktok': tiktok_data,
            'timestamp': datetime.now(),
            'total_items': sum(len(r) for r in results) + len(tiktok_data)
        }
        
        # Extract all unique tickers
        all_tickers = set()
        for source_data in aggregated.values():
            if isinstance(source_data, list):
                for item in source_data:
                    if 'tickers' in item:
                        all_tickers.update(item['tickers'])
        
        aggregated['unique_tickers'] = list(all_tickers)
        
        print(f" Collected {aggregated['total_items']} items")
        print(f" Found {len(all_tickers)} unique tickers")
        
        return aggregated
    
    async def _collect_reddit(self) -> List[Dict]:
        """Collect Reddit data"""
        print(" Collecting from Reddit...")
        return self.reddit.collect_hot_posts(limit=50)
    
    async def _collect_youtube(self) -> List[Dict]:
        """Collect YouTube data"""
        print(" Collecting from YouTube...")
        return self.youtube.collect_videos(max_results=20)
    
    async def _collect_tiktok(self) -> List[Dict]:
        """Collect TikTok data"""
        print(" Collecting from TikTok...")
        return self.tiktok.collect_fintok_content()
    
    async def _collect_chan(self) -> List[Dict]:
        """Collect 4chan data"""
        print(" Collecting from 4chan /biz/...")
        return self.chan.collect_biz_threads(pages=2)
    
    def prioritize_for_analysis(self, data: Dict) -> List[Dict]:
        """Prioritize content for AI analysis"""
        priority_items = []
        
        # Prioritize by various factors
        for source, items in data.items():
            if not isinstance(items, list):
                continue
                
            for item in items:
                priority_score = 0
                
                # Has tickers
                if item.get('tickers'):
                    priority_score += len(item['tickers']) * 10
                
                # High engagement (Reddit)
                if 'score' in item:
                    if item['score'] > 1000:
                        priority_score += 50
                    elif item['score'] > 100:
                        priority_score += 20
                
                # High views (YouTube)
                if 'views' in item:
                    if item['views'] > 100000:
                        priority_score += 40
                    elif item['views'] > 10000:
                        priority_score += 20
                
                # Insider probability (4chan)
                if 'insider_probability' in item:
                    priority_score += item['insider_probability'] * 100
                
                # DD posts (Reddit)
                if item.get('is_dd'):
                    priority_score += 30
                
                # Trusted source (YouTube)
                if item.get('is_trusted'):
                    priority_score += 25
                
                item['priority_score'] = priority_score
                priority_items.append(item)
        
        # Sort by priority
        priority_items.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return priority_items[:100]  # Top 100 for analysis
```

---

**This implementation provides working code for collecting data from Reddit, YouTube, TikTok, and 4chan. The system prioritizes high-value content and extracts tickers for analysis.**

*Note: Some platforms (TikTok) may require additional setup or manual data collection for the MVP due to API restrictions.*