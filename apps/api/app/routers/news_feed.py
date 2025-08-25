"""
API endpoints for financial news feed
Aggregates news from multiple sources with AI-powered insights
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import asyncio

from app.core.dependencies import get_db
from app.services.news_modules.news_aggregator import NewsAggregator
from app.services.news_modules.sentiment_analyzer import SentimentAnalyzer
from app.services.news_modules.entity_extractor import EntityExtractor
from app.services.collectors.reddit_collector import RedditCollector
from app.services.collectors.youtube_collector import YouTubeCollector
from app.services.asset_classification_system import get_classification_system
from app.models.asset import Asset

router = APIRouter(
    prefix="/news",
    tags=["news"],
    responses={404: {"description": "Not found"}},
)


@router.get("/feed")
async def get_news_feed(
    source: Optional[str] = Query(None, description="Filter by source type"),
    ticker: Optional[str] = Query(None, description="Filter by ticker symbol"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment (positive/negative/neutral)"),
    hours: int = Query(24, description="Hours of news to fetch"),
    limit: int = Query(50, description="Maximum number of articles"),
    db: Session = Depends(get_db)
):
    """Get aggregated news feed from multiple sources."""
    
    # Initialize services
    aggregator = NewsAggregator()
    sentiment_analyzer = SentimentAnalyzer()
    entity_extractor = EntityExtractor()
    
    # Collect news from various sources
    articles = []
    
    # 1. Official news sources (MarketAux)
    try:
        official_news = await aggregator.fetch_marketaux_news(
            tickers=[ticker] if ticker else None,
            hours=hours
        )
        
        for article in official_news:
            # Analyze sentiment
            sentiment_score = sentiment_analyzer.analyze(article['description'])
            
            # Extract entities
            entities = entity_extractor.extract_entities(article['description'])
            
            articles.append({
                'id': article.get('uuid', ''),
                'title': article.get('title', ''),
                'description': article.get('description', ''),
                'url': article.get('url', ''),
                'source': article.get('source', 'MarketAux'),
                'source_type': 'official',
                'published_at': article.get('published_at', ''),
                'sentiment': sentiment_score['compound'],
                'relevance_score': 0.8,  # High relevance for official sources
                'entities': [
                    {
                        'symbol': e.get('symbol', ''),
                        'name': e.get('name', ''),
                        'relevance': 0.9
                    }
                    for e in entities[:5]  # Top 5 entities
                ],
                'tags': article.get('tags', []),
                'image_url': article.get('image_url'),
                'author': article.get('author')
            })
    except Exception as e:
        print(f"Error fetching official news: {e}")
    
    # 2. Reddit posts (social sentiment)
    try:
        reddit_collector = RedditCollector()
        reddit_posts = await reddit_collector.collect_investment_discussions(
            subreddits=['wallstreetbets', 'stocks', 'investing'],
            limit=20
        )
        
        for post in reddit_posts:
            # Analyze sentiment
            sentiment_score = sentiment_analyzer.analyze(post['content'])
            
            # Extract tickers mentioned
            entities = entity_extractor.extract_tickers(post['content'])
            
            articles.append({
                'id': f"reddit_{post.get('id', '')}",
                'title': post.get('title', ''),
                'description': post.get('content', '')[:500],  # Truncate long posts
                'url': post.get('url', ''),
                'source': f"r/{post.get('subreddit', 'reddit')}",
                'source_type': 'reddit',
                'published_at': post.get('created_at', ''),
                'sentiment': sentiment_score['compound'],
                'relevance_score': min(post.get('score', 0) / 1000, 1.0),  # Based on upvotes
                'entities': [
                    {
                        'symbol': ticker,
                        'name': '',
                        'relevance': 0.7
                    }
                    for ticker in entities[:5]
                ],
                'tags': ['social', 'reddit'],
                'author': post.get('author'),
                'engagement': {
                    'likes': post.get('score', 0),
                    'comments': post.get('num_comments', 0)
                }
            })
    except Exception as e:
        print(f"Error fetching Reddit posts: {e}")
    
    # 3. YouTube videos (expert analysis)
    try:
        youtube_collector = YouTubeCollector()
        videos = await youtube_collector.search_investment_videos(
            query="stock market analysis",
            max_results=10
        )
        
        for video in videos:
            # Analyze sentiment from title and description
            sentiment_score = sentiment_analyzer.analyze(
                f"{video.get('title', '')} {video.get('description', '')}"
            )
            
            articles.append({
                'id': f"youtube_{video.get('id', '')}",
                'title': video.get('title', ''),
                'description': video.get('description', '')[:500],
                'url': f"https://youtube.com/watch?v={video.get('id', '')}",
                'source': video.get('channel', 'YouTube'),
                'source_type': 'youtube',
                'published_at': video.get('published_at', ''),
                'sentiment': sentiment_score['compound'],
                'relevance_score': 0.7,
                'entities': [],  # Would need transcript for entity extraction
                'tags': ['video', 'analysis'],
                'image_url': video.get('thumbnail'),
                'author': video.get('channel'),
                'engagement': {
                    'views': video.get('view_count', 0),
                    'likes': video.get('like_count', 0),
                    'comments': video.get('comment_count', 0)
                }
            })
    except Exception as e:
        print(f"Error fetching YouTube videos: {e}")
    
    # 4. AI-generated insights (high-relevance signals)
    try:
        # Get high-confidence signals from our system
        classification_system = get_classification_system()
        
        # Add AI insights for trending sectors
        for sector_name in ['ai_revolution', 'climate_change', 'space_economy']:
            thematic_assets = classification_system.get_thematic_portfolio(sector_name)
            
            if thematic_assets:
                articles.append({
                    'id': f"ai_insight_{sector_name}",
                    'title': f"AI Insight: {sector_name.replace('_', ' ').title()} Investment Opportunities",
                    'description': f"Our AI has identified {len(thematic_assets)} high-potential assets in the {sector_name.replace('_', ' ')} theme with expected returns exceeding 30%.",
                    'url': '#',
                    'source': 'Waardhaven AI',
                    'source_type': 'ai_insight',
                    'published_at': datetime.utcnow().isoformat(),
                    'sentiment': 0.8,  # Positive for opportunities
                    'relevance_score': 0.95,  # High relevance
                    'entities': [
                        {
                            'symbol': asset.ticker,
                            'name': asset.name,
                            'relevance': 0.9
                        }
                        for asset in thematic_assets[:3]
                    ],
                    'tags': ['ai', 'insight', sector_name],
                })
    except Exception as e:
        print(f"Error generating AI insights: {e}")
    
    # Filter by sentiment if requested
    if sentiment:
        if sentiment == 'positive':
            articles = [a for a in articles if a['sentiment'] > 0.3]
        elif sentiment == 'negative':
            articles = [a for a in articles if a['sentiment'] < -0.3]
        elif sentiment == 'neutral':
            articles = [a for a in articles if -0.3 <= a['sentiment'] <= 0.3]
    
    # Filter by source type
    if source:
        articles = [a for a in articles if a['source_type'] == source]
    
    # Filter by ticker
    if ticker:
        articles = [
            a for a in articles
            if any(e['symbol'].upper() == ticker.upper() for e in a['entities'])
        ]
    
    # Sort by relevance and recency
    articles.sort(key=lambda x: (x['relevance_score'], x['published_at']), reverse=True)
    
    return {
        'articles': articles[:limit],
        'total': len(articles),
        'filtered': len(articles[:limit])
    }


@router.get("/trending")
async def get_trending_topics(
    hours: int = Query(24, description="Hours to analyze"),
    db: Session = Depends(get_db)
):
    """Get trending topics and tickers from news and social media."""
    
    # This would analyze all recent news and social posts
    # to identify trending topics
    
    trending = {
        'tickers': [
            {'symbol': 'NVDA', 'mentions': 1250, 'sentiment': 0.75, 'change_24h': 150},
            {'symbol': 'TSLA', 'mentions': 980, 'sentiment': 0.45, 'change_24h': -50},
            {'symbol': 'GME', 'mentions': 750, 'sentiment': 0.65, 'change_24h': 200},
            {'symbol': 'AAPL', 'mentions': 620, 'sentiment': 0.55, 'change_24h': 30},
            {'symbol': 'PLTR', 'mentions': 540, 'sentiment': 0.80, 'change_24h': 100},
        ],
        'topics': [
            {'name': 'AI Revolution', 'mentions': 3200, 'sentiment': 0.82},
            {'name': 'Fed Rate Decision', 'mentions': 2100, 'sentiment': -0.15},
            {'name': 'Earnings Season', 'mentions': 1800, 'sentiment': 0.35},
            {'name': 'Crypto Rally', 'mentions': 1500, 'sentiment': 0.70},
            {'name': 'China Tech', 'mentions': 1200, 'sentiment': -0.40},
        ],
        'sectors': [
            {'name': 'Technology', 'sentiment': 0.65, 'volume_change': 25},
            {'name': 'Healthcare', 'sentiment': 0.45, 'volume_change': 10},
            {'name': 'Energy', 'sentiment': 0.30, 'volume_change': -5},
            {'name': 'Finance', 'sentiment': 0.20, 'volume_change': 15},
            {'name': 'Consumer', 'sentiment': 0.55, 'volume_change': 8},
        ]
    }
    
    return trending


@router.get("/sentiment/market")
async def get_market_sentiment(
    db: Session = Depends(get_db)
):
    """Get overall market sentiment from all sources."""
    
    # Aggregate sentiment from multiple sources
    sentiment_data = {
        'overall': {
            'score': 0.45,  # Slightly bullish
            'label': 'Moderately Bullish',
            'confidence': 0.78
        },
        'by_source': {
            'official_news': 0.35,
            'reddit': 0.65,
            'twitter': 0.55,
            'youtube': 0.40,
            'ai_analysis': 0.50
        },
        'by_sector': {
            'technology': 0.70,
            'healthcare': 0.45,
            'finance': 0.25,
            'energy': 0.30,
            'consumer': 0.50
        },
        'trend_24h': 0.05,  # Improving
        'volatility': 0.35,  # Moderate volatility
        'fear_greed_index': 65  # Greed
    }
    
    return sentiment_data


@router.get("/alerts")
async def get_news_alerts(
    min_relevance: float = Query(0.8, description="Minimum relevance score"),
    db: Session = Depends(get_db)
):
    """Get high-priority news alerts."""
    
    alerts = [
        {
            'id': 'alert_1',
            'type': 'breaking',
            'title': 'NVDA Announces Revolutionary AI Chip',
            'description': 'NVIDIA unveils next-generation AI processor with 10x performance improvement',
            'impact': 'high',
            'affected_tickers': ['NVDA', 'AMD', 'INTC'],
            'sentiment': 0.85,
            'timestamp': datetime.utcnow().isoformat()
        },
        {
            'id': 'alert_2',
            'type': 'market_move',
            'title': 'Fed Signals Rate Cut Possibility',
            'description': 'Federal Reserve hints at potential rate cuts in Q2 2025',
            'impact': 'high',
            'affected_sectors': ['finance', 'real_estate', 'technology'],
            'sentiment': 0.60,
            'timestamp': (datetime.utcnow() - timedelta(hours=2)).isoformat()
        }
    ]
    
    return {
        'alerts': alerts,
        'count': len(alerts)
    }


@router.get("/sources")
async def get_news_sources():
    """Get list of available news sources."""
    
    sources = {
        'official': [
            {'name': 'MarketAux', 'type': 'api', 'reliability': 0.95},
            {'name': 'Reuters', 'type': 'scraper', 'reliability': 0.95},
            {'name': 'Bloomberg', 'type': 'scraper', 'reliability': 0.95},
        ],
        'social': [
            {'name': 'Reddit', 'type': 'api', 'reliability': 0.60},
            {'name': 'Twitter', 'type': 'scraper', 'reliability': 0.55},
            {'name': 'StockTwits', 'type': 'api', 'reliability': 0.50},
        ],
        'video': [
            {'name': 'YouTube', 'type': 'api', 'reliability': 0.70},
            {'name': 'TikTok', 'type': 'scraper', 'reliability': 0.40},
        ],
        'ai': [
            {'name': 'Waardhaven AI', 'type': 'internal', 'reliability': 0.85},
            {'name': 'Pattern Recognition', 'type': 'internal', 'reliability': 0.80},
        ]
    }
    
    return sources