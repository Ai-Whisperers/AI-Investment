"""
Sentiment analysis module for news articles.
"""

import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """Analyzes sentiment in news articles and entities."""

    # Sentiment keywords for basic analysis
    POSITIVE_WORDS = {
        'bullish', 'surge', 'gain', 'rise', 'profit', 'growth', 'positive',
        'upgrade', 'breakthrough', 'success', 'strong', 'outperform', 'boom',
        'rally', 'record', 'high', 'beat', 'exceed', 'expand', 'improve'
    }

    NEGATIVE_WORDS = {
        'bearish', 'fall', 'loss', 'decline', 'crash', 'negative', 'downgrade',
        'fail', 'weak', 'underperform', 'bust', 'plunge', 'low', 'miss',
        'cut', 'reduce', 'concern', 'warning', 'risk', 'threat'
    }

    NEUTRAL_WORDS = {
        'unchanged', 'stable', 'maintain', 'hold', 'steady', 'flat',
        'sideways', 'range', 'consolidate'
    }

    @staticmethod
    def calculate_sentiment_score(
        text: str,
        title_weight: float = 1.5
    ) -> tuple[float, str]:
        """
        Calculate sentiment score for text.

        Args:
            text: Text to analyze
            title_weight: Weight multiplier for title sentiment

        Returns:
            Tuple of (score, sentiment_label)
        """
        if not text:
            return 0.0, 'neutral'

        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)

        if not words:
            return 0.0, 'neutral'

        # Count sentiment words
        positive_count = sum(1 for word in words if word in SentimentAnalyzer.POSITIVE_WORDS)
        negative_count = sum(1 for word in words if word in SentimentAnalyzer.NEGATIVE_WORDS)
        neutral_count = sum(1 for word in words if word in SentimentAnalyzer.NEUTRAL_WORDS)

        # Calculate raw score
        total_sentiment_words = positive_count + negative_count + neutral_count
        if total_sentiment_words == 0:
            return 0.0, 'neutral'

        # Normalize score between -1 and 1
        score = (positive_count - negative_count) / max(total_sentiment_words, 1)
        score = max(-1.0, min(1.0, score))  # Clamp to [-1, 1]

        # Determine sentiment label
        if score > 0.2:
            label = 'positive'
        elif score < -0.2:
            label = 'negative'
        else:
            label = 'neutral'

        return score, label

    @staticmethod
    def analyze_article_sentiment(
        title: str,
        description: str | None = None,
        content: str | None = None
    ) -> dict[str, any]:
        """
        Analyze sentiment for a complete article.

        Args:
            title: Article title
            description: Article description/summary
            content: Full article content

        Returns:
            Dict with sentiment analysis results
        """
        # Analyze title (weighted more heavily)
        title_score, title_label = SentimentAnalyzer.calculate_sentiment_score(title)
        title_score *= 1.5  # Title has more weight

        # Analyze description
        desc_score = 0.0
        if description:
            desc_score, _ = SentimentAnalyzer.calculate_sentiment_score(description)

        # Analyze content
        content_score = 0.0
        if content:
            content_score, _ = SentimentAnalyzer.calculate_sentiment_score(content)

        # Combine scores (weighted average)
        weights = []
        scores = []

        if title:
            weights.append(2.0)  # Title weight
            scores.append(title_score)

        if description:
            weights.append(1.5)  # Description weight
            scores.append(desc_score)

        if content:
            weights.append(1.0)  # Content weight
            scores.append(content_score)

        if not weights:
            return {
                'sentiment_score': 0.0,
                'sentiment_label': 'neutral',
                'confidence': 0.0
            }

        # Calculate weighted average
        total_weight = sum(weights)
        weighted_score = sum(s * w for s, w in zip(scores, weights, strict=False)) / total_weight

        # Normalize final score
        final_score = max(-1.0, min(1.0, weighted_score))

        # Determine final label
        if final_score > 0.2:
            final_label = 'positive'
        elif final_score < -0.2:
            final_label = 'negative'
        else:
            final_label = 'neutral'

        # Calculate confidence (based on consistency of signals)
        score_variance = sum((s - final_score) ** 2 for s in scores) / len(scores)
        confidence = max(0.0, 1.0 - score_variance)

        return {
            'sentiment_score': final_score,
            'sentiment_label': final_label,
            'confidence': confidence,
            'components': {
                'title_score': title_score / 1.5,  # Unnormalize for display
                'description_score': desc_score,
                'content_score': content_score
            }
        }

    @staticmethod
    def calculate_aggregate_sentiment(
        sentiments: list[float],
        weights: list[float] | None = None
    ) -> float:
        """
        Calculate aggregate sentiment from multiple scores.

        Args:
            sentiments: List of sentiment scores
            weights: Optional weights for each score

        Returns:
            Aggregated sentiment score
        """
        if not sentiments:
            return 0.0

        if weights:
            if len(weights) != len(sentiments):
                logger.warning("Weights length doesn't match sentiments length")
                weights = None

        if weights:
            total_weight = sum(weights)
            if total_weight == 0:
                return 0.0
            return sum(s * w for s, w in zip(sentiments, weights, strict=False)) / total_weight
        else:
            return sum(sentiments) / len(sentiments)

    @staticmethod
    def classify_sentiment_trend(
        sentiment_history: list[tuple[datetime, float]]
    ) -> str:
        """
        Classify sentiment trend over time.

        Args:
            sentiment_history: List of (date, sentiment_score) tuples

        Returns:
            Trend classification: 'improving', 'declining', 'stable', 'volatile'
        """
        if len(sentiment_history) < 2:
            return 'stable'

        # Sort by date
        sorted_history = sorted(sentiment_history, key=lambda x: x[0])
        scores = [score for _, score in sorted_history]

        # Calculate trend
        first_half = scores[:len(scores)//2]
        second_half = scores[len(scores)//2:]

        first_avg = sum(first_half) / len(first_half) if first_half else 0
        second_avg = sum(second_half) / len(second_half) if second_half else 0

        # Calculate volatility
        if len(scores) > 1:
            mean_score = sum(scores) / len(scores)
            variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
            volatility = variance ** 0.5
        else:
            volatility = 0

        # Classify trend
        if volatility > 0.5:
            return 'volatile'
        elif second_avg > first_avg + 0.1:
            return 'improving'
        elif second_avg < first_avg - 0.1:
            return 'declining'
        else:
            return 'stable'
