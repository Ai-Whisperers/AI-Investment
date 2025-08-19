"""
Data parsing utilities for MarketAux responses.
Handles transformation of API responses into domain objects.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from ..interface import NewsArticle, NewsSentiment, NewsEntity

logger = logging.getLogger(__name__)


class MarketAuxDataParser:
    """
    Parses MarketAux API responses into domain objects.
    """

    @staticmethod
    def parse_article(data: Dict) -> NewsArticle:
        """
        Parse API response into NewsArticle.
        
        Args:
            data: Raw article data from API
            
        Returns:
            Parsed NewsArticle object
        """
        try:
            # Parse entities
            entities = MarketAuxDataParser._parse_entities(data.get("entities", []))

            # Parse sentiment
            sentiment = MarketAuxDataParser._parse_sentiment(data.get("sentiment"))

            # Parse datetime
            published_at = MarketAuxDataParser._parse_datetime(
                data.get("published_at")
            )

            return NewsArticle(
                uuid=data.get("uuid", ""),
                title=data.get("title", ""),
                description=data.get("description", ""),
                url=data.get("url", ""),
                source=data.get("source", ""),
                published_at=published_at,
                content=data.get("snippet"),  # MarketAux uses 'snippet' for content
                image_url=data.get("image_url"),
                language=data.get("language", "en"),
                country=data.get("country"),
                entities=entities,
                sentiment=sentiment,
                keywords=data.get("keywords", []),
                categories=data.get("categories", []),
            )

        except Exception as e:
            logger.error(f"Failed to parse article: {e}")
            # Return minimal article with available data
            return NewsArticle(
                uuid=data.get("uuid", ""),
                title=data.get("title", "Unknown"),
                description=data.get("description", ""),
                url=data.get("url", ""),
                source=data.get("source", ""),
                published_at=datetime.now(),
                entities=[],
                keywords=[],
                categories=[]
            )

    @staticmethod
    def _parse_entities(entities_data: List[Dict]) -> List[NewsEntity]:
        """
        Parse entity data from API response.
        
        Args:
            entities_data: Raw entities data
            
        Returns:
            List of parsed NewsEntity objects
        """
        entities = []
        
        for entity_data in entities_data:
            try:
                entity = NewsEntity(
                    symbol=entity_data.get("symbol", ""),
                    name=entity_data.get("name", ""),
                    type=entity_data.get("type", "unknown"),
                    exchange=entity_data.get("exchange"),
                    country=entity_data.get("country"),
                    industry=entity_data.get("industry"),
                    match_score=entity_data.get("match_score"),
                    sentiment_score=entity_data.get("sentiment_score"),
                )
                entities.append(entity)
            except Exception as e:
                logger.warning(f"Failed to parse entity: {e}")
                continue
        
        return entities

    @staticmethod
    def _parse_sentiment(sentiment_data: Optional[Dict]) -> Optional[NewsSentiment]:
        """
        Parse sentiment data from API response.
        
        Args:
            sentiment_data: Raw sentiment data
            
        Returns:
            Parsed NewsSentiment object or None
        """
        if not sentiment_data:
            return None
        
        try:
            return NewsSentiment.from_score(
                score=sentiment_data.get("score", 0),
                confidence=sentiment_data.get("confidence", 0.5),
            )
        except Exception as e:
            logger.warning(f"Failed to parse sentiment: {e}")
            return None

    @staticmethod
    def _parse_datetime(datetime_str: Optional[str]) -> datetime:
        """
        Parse datetime string from API response.
        
        Args:
            datetime_str: ISO datetime string
            
        Returns:
            Parsed datetime object
        """
        if not datetime_str:
            return datetime.now()
        
        try:
            # Handle different datetime formats
            if datetime_str.endswith("Z"):
                datetime_str = datetime_str.replace("Z", "+00:00")
            
            return datetime.fromisoformat(datetime_str)
        except Exception as e:
            logger.warning(f"Failed to parse datetime '{datetime_str}': {e}")
            return datetime.now()

    @staticmethod
    def parse_search_params(search_params) -> Dict:
        """
        Convert NewsSearchParams to API parameters.
        
        Args:
            search_params: NewsSearchParams object
            
        Returns:
            Dictionary of API parameters
        """
        api_params = {
            "limit": search_params.limit,
            "page": search_params.offset // search_params.limit + 1 if search_params.offset else 1,
        }

        # Add optional filters
        if search_params.symbols:
            api_params["symbols"] = ",".join(search_params.symbols)

        if search_params.keywords:
            api_params["search"] = " ".join(search_params.keywords)

        if search_params.sources:
            api_params["domains"] = ",".join(search_params.sources)

        if search_params.countries:
            api_params["countries"] = ",".join(search_params.countries)

        if search_params.languages:
            api_params["languages"] = ",".join(search_params.languages)

        if search_params.industries:
            api_params["industries"] = ",".join(search_params.industries)

        if search_params.sentiment_min is not None:
            api_params["sentiment_gte"] = search_params.sentiment_min

        if search_params.sentiment_max is not None:
            api_params["sentiment_lte"] = search_params.sentiment_max

        if search_params.published_after:
            api_params["published_after"] = search_params.published_after.isoformat()

        if search_params.published_before:
            api_params["published_before"] = search_params.published_before.isoformat()

        return api_params