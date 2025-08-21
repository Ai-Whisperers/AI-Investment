"""
News and sentiment API endpoints.
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..schemas.news import (
    EntitySentimentResponse,
    NewsArticleResponse,
    TrendingEntityResponse,
)
from ..services.news import NewsService
from ..utils.token_dep import get_current_user

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/search", response_model=list[NewsArticleResponse])
async def search_news(
    symbols: str | None = Query(None, description="Comma-separated stock symbols"),
    keywords: str | None = Query(None, description="Search keywords"),
    sentiment_min: float | None = Query(None, ge=-1, le=1),
    sentiment_max: float | None = Query(None, ge=-1, le=1),
    published_after: datetime | None = None,
    published_before: datetime | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Search for news articles with various filters.
    """
    service = NewsService(db)

    # Parse symbols
    symbol_list = symbols.split(",") if symbols else None

    articles = service.search_news(
        symbols=symbol_list,
        keywords=keywords,
        sentiment_min=sentiment_min,
        sentiment_max=sentiment_max,
        published_after=published_after,
        published_before=published_before,
        limit=limit,
        offset=offset,
    )

    return articles


@router.get("/article/{article_id}", response_model=NewsArticleResponse)
async def get_article(
    article_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get a specific news article by ID.
    """
    service = NewsService(db)
    article = service.get_article(article_id)

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    return article


@router.get("/similar/{article_id}", response_model=list[NewsArticleResponse])
async def get_similar_articles(
    article_id: str,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get articles similar to a given article.
    """
    service = NewsService(db)
    articles = service.get_similar_articles(article_id, limit)

    return articles


@router.get("/sentiment/{symbol}", response_model=EntitySentimentResponse)
async def get_entity_sentiment(
    symbol: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get sentiment analysis for a specific stock symbol over time.
    """
    service = NewsService(db)

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    sentiment_data = service.get_entity_sentiment(
        symbol=symbol, start_date=start_date, end_date=end_date
    )

    return sentiment_data


@router.get("/trending", response_model=list[TrendingEntityResponse])
async def get_trending_entities(
    entity_type: str | None = Query(None, description="Filter by entity type"),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get trending entities in recent news.
    """
    service = NewsService(db)
    trending = service.get_trending_entities(entity_type, limit)

    return trending


@router.post("/refresh")
async def refresh_news(
    symbols: list[str] | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Refresh news data for specified symbols or all assets.
    Requires authentication.
    """
    service = NewsService(db)

    try:
        result = service.refresh_news(symbols)
        return {
            "status": "success",
            "articles_fetched": result["articles_fetched"],
            "symbols_processed": result["symbols_processed"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_news_stats(
    db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    """
    Get statistics about news data in the database.
    """
    service = NewsService(db)
    stats = service.get_stats()

    return stats
