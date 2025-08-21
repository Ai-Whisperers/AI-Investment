"""
News aggregation and processing module.
"""

import logging
from collections import defaultdict
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class NewsAggregator:
    """Aggregates and processes news data from multiple sources."""

    def __init__(self):
        self.aggregation_cache = {}

    def aggregate_by_symbol(
        self,
        articles: list[dict[str, Any]],
        symbols: list[str]
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Aggregate articles by symbol.

        Args:
            articles: List of article dictionaries
            symbols: List of symbols to aggregate by

        Returns:
            Dict mapping symbols to their related articles
        """
        symbol_articles = defaultdict(list)

        for article in articles:
            # Check entities in article
            article_entities = article.get('entities', [])

            for symbol in symbols:
                # Check if symbol is mentioned in entities
                if any(e.get('symbol') == symbol for e in article_entities):
                    symbol_articles[symbol].append(article)
                # Also check title and description
                elif symbol in article.get('title', '').upper() or \
                     symbol in article.get('description', '').upper():
                    symbol_articles[symbol].append(article)

        return dict(symbol_articles)

    def aggregate_by_date(
        self,
        articles: list[dict[str, Any]],
        date_format: str = '%Y-%m-%d'
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Aggregate articles by date.

        Args:
            articles: List of article dictionaries
            date_format: Format for date keys

        Returns:
            Dict mapping dates to articles
        """
        date_articles = defaultdict(list)

        for article in articles:
            published_at = article.get('published_at')
            if published_at:
                if isinstance(published_at, str):
                    try:
                        published_at = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    except:
                        continue

                date_key = published_at.strftime(date_format)
                date_articles[date_key].append(article)

        return dict(date_articles)

    def aggregate_by_source(
        self,
        articles: list[dict[str, Any]]
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Aggregate articles by source.

        Args:
            articles: List of article dictionaries

        Returns:
            Dict mapping sources to articles
        """
        source_articles = defaultdict(list)

        for article in articles:
            source = article.get('source', {}).get('name', 'Unknown')
            source_articles[source].append(article)

        return dict(source_articles)

    def aggregate_sentiment_by_period(
        self,
        articles: list[dict[str, Any]],
        period: str = 'daily'
    ) -> list[dict[str, Any]]:
        """
        Aggregate sentiment scores by time period.

        Args:
            articles: List of article dictionaries
            period: 'hourly', 'daily', 'weekly', or 'monthly'

        Returns:
            List of aggregated sentiment data by period
        """
        # Determine period format
        period_formats = {
            'hourly': '%Y-%m-%d %H:00',
            'daily': '%Y-%m-%d',
            'weekly': '%Y-W%W',
            'monthly': '%Y-%m'
        }

        date_format = period_formats.get(period, '%Y-%m-%d')

        # Group articles by period
        period_data = defaultdict(lambda: {
            'articles': [],
            'sentiment_scores': [],
            'positive_count': 0,
            'negative_count': 0,
            'neutral_count': 0
        })

        for article in articles:
            published_at = article.get('published_at')
            if not published_at:
                continue

            if isinstance(published_at, str):
                try:
                    published_at = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                except:
                    continue

            period_key = published_at.strftime(date_format)
            period_group = period_data[period_key]

            period_group['articles'].append(article)

            # Add sentiment data
            sentiment = article.get('sentiment', {})
            if sentiment:
                score = sentiment.get('sentiment_score', 0)
                label = sentiment.get('sentiment_label', 'neutral')

                period_group['sentiment_scores'].append(score)

                if label == 'positive':
                    period_group['positive_count'] += 1
                elif label == 'negative':
                    period_group['negative_count'] += 1
                else:
                    period_group['neutral_count'] += 1

        # Calculate aggregates for each period
        results = []
        for period_key, data in sorted(period_data.items()):
            sentiment_scores = data['sentiment_scores']

            aggregate = {
                'period': period_key,
                'article_count': len(data['articles']),
                'average_sentiment': sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0,
                'positive_count': data['positive_count'],
                'negative_count': data['negative_count'],
                'neutral_count': data['neutral_count'],
                'sentiment_distribution': {
                    'positive': data['positive_count'] / len(data['articles']) if data['articles'] else 0,
                    'negative': data['negative_count'] / len(data['articles']) if data['articles'] else 0,
                    'neutral': data['neutral_count'] / len(data['articles']) if data['articles'] else 0
                }
            }

            results.append(aggregate)

        return results

    def calculate_trending_score(
        self,
        article_count: int,
        sentiment_score: float,
        recency_hours: int
    ) -> float:
        """
        Calculate trending score for an entity or topic.

        Args:
            article_count: Number of articles mentioning the entity
            sentiment_score: Average sentiment score
            recency_hours: Hours since most recent mention

        Returns:
            Trending score
        """
        # Base score from article count
        base_score = article_count

        # Boost for positive sentiment
        sentiment_boost = 1 + max(0, sentiment_score)

        # Decay factor for older news
        recency_factor = max(0.1, 1 - (recency_hours / 168))  # Decay over a week

        return base_score * sentiment_boost * recency_factor

    def find_related_articles(
        self,
        article: dict[str, Any],
        all_articles: list[dict[str, Any]],
        max_results: int = 10
    ) -> list[dict[str, Any]]:
        """
        Find articles related to a given article.

        Args:
            article: Reference article
            all_articles: Pool of articles to search
            max_results: Maximum number of related articles to return

        Returns:
            List of related articles
        """
        related = []

        # Get entities from reference article
        ref_entities = set()
        for entity in article.get('entities', []):
            ref_entities.add(entity.get('symbol'))

        # Get keywords from title and description
        ref_text = f"{article.get('title', '')} {article.get('description', '')}".lower()
        ref_words = set(ref_text.split())

        # Score each article
        scored_articles = []
        for other in all_articles:
            # Skip the same article
            if other.get('id') == article.get('id'):
                continue

            score = 0

            # Check entity overlap
            other_entities = set()
            for entity in other.get('entities', []):
                other_entities.add(entity.get('symbol'))

            entity_overlap = len(ref_entities & other_entities)
            score += entity_overlap * 10

            # Check keyword overlap
            other_text = f"{other.get('title', '')} {other.get('description', '')}".lower()
            other_words = set(other_text.split())

            word_overlap = len(ref_words & other_words)
            score += word_overlap

            # Boost for same source
            if article.get('source') == other.get('source'):
                score += 5

            # Boost for temporal proximity
            if article.get('published_at') and other.get('published_at'):
                ref_date = article['published_at']
                other_date = other['published_at']

                if isinstance(ref_date, str):
                    ref_date = datetime.fromisoformat(ref_date.replace('Z', '+00:00'))
                if isinstance(other_date, str):
                    other_date = datetime.fromisoformat(other_date.replace('Z', '+00:00'))

                hours_diff = abs((ref_date - other_date).total_seconds() / 3600)
                if hours_diff < 24:
                    score += 10
                elif hours_diff < 72:
                    score += 5

            if score > 0:
                scored_articles.append((score, other))

        # Sort by score and return top results
        scored_articles.sort(key=lambda x: x[0], reverse=True)

        for score, article in scored_articles[:max_results]:
            related.append(article)

        return related

    def summarize_coverage(
        self,
        articles: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Generate summary statistics for a collection of articles.

        Args:
            articles: List of article dictionaries

        Returns:
            Summary statistics
        """
        if not articles:
            return {
                'total_articles': 0,
                'sources': [],
                'entities': [],
                'date_range': None,
                'sentiment_summary': None
            }

        # Collect statistics
        sources = defaultdict(int)
        entities = defaultdict(int)
        sentiment_scores = []
        dates = []

        for article in articles:
            # Count sources
            source = article.get('source', {}).get('name', 'Unknown')
            sources[source] += 1

            # Count entities
            for entity in article.get('entities', []):
                symbol = entity.get('symbol')
                if symbol:
                    entities[symbol] += 1

            # Collect sentiment
            sentiment = article.get('sentiment', {})
            if sentiment:
                score = sentiment.get('sentiment_score')
                if score is not None:
                    sentiment_scores.append(score)

            # Collect dates
            published_at = article.get('published_at')
            if published_at:
                if isinstance(published_at, str):
                    try:
                        published_at = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    except:
                        continue
                dates.append(published_at)

        # Calculate summary
        summary = {
            'total_articles': len(articles),
            'sources': [
                {'name': name, 'count': count}
                for name, count in sorted(sources.items(), key=lambda x: x[1], reverse=True)[:10]
            ],
            'entities': [
                {'symbol': symbol, 'count': count}
                for symbol, count in sorted(entities.items(), key=lambda x: x[1], reverse=True)[:20]
            ],
            'date_range': {
                'start': min(dates).isoformat() if dates else None,
                'end': max(dates).isoformat() if dates else None
            },
            'sentiment_summary': {
                'average': sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0,
                'positive_ratio': len([s for s in sentiment_scores if s > 0.2]) / len(sentiment_scores) if sentiment_scores else 0,
                'negative_ratio': len([s for s in sentiment_scores if s < -0.2]) / len(sentiment_scores) if sentiment_scores else 0,
                'neutral_ratio': len([s for s in sentiment_scores if -0.2 <= s <= 0.2]) / len(sentiment_scores) if sentiment_scores else 0
            }
        }

        return summary
