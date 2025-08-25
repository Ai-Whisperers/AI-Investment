"""
Credibility Scoring System for Human Financial Sources
Evaluates and tracks the trustworthiness of content creators and analysts
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
import json
import re
from collections import defaultdict

logger = logging.getLogger(__name__)


class SourceStatus(Enum):
    """Status of information source based on credibility."""
    WHITELISTED = "whitelisted"  # Trusted, analytic-informative
    TESTLISTED = "testlisted"    # Under evaluation, context needed
    BLACKLISTED = "blacklisted"  # Scammers, non-trustworthy
    UNKNOWN = "unknown"          # New source, not yet evaluated


class ContentType(Enum):
    """Type of content from source."""
    ANALYSIS = "analysis"
    PREDICTION = "prediction"
    NEWS = "news"
    OPINION = "opinion"
    PROMOTION = "promotion"
    EDUCATION = "education"


@dataclass
class SourceProfile:
    """Profile of a content creator or analyst."""
    source_id: str
    name: str
    platform: str  # youtube, reddit, twitter, etc.
    status: SourceStatus = SourceStatus.UNKNOWN
    credibility_score: float = 0.5  # 0-1 scale
    total_predictions: int = 0
    correct_predictions: int = 0
    accuracy_rate: float = 0.0
    follower_count: int = 0
    engagement_rate: float = 0.0
    content_quality_score: float = 0.5
    scam_indicators: int = 0
    verified: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_evaluated: datetime = field(default_factory=datetime.utcnow)
    evaluation_history: List[dict] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "source_id": self.source_id,
            "name": self.name,
            "platform": self.platform,
            "status": self.status.value,
            "credibility_score": self.credibility_score,
            "accuracy_rate": self.accuracy_rate,
            "total_predictions": self.total_predictions,
            "correct_predictions": self.correct_predictions,
            "follower_count": self.follower_count,
            "engagement_rate": self.engagement_rate,
            "content_quality_score": self.content_quality_score,
            "scam_indicators": self.scam_indicators,
            "verified": self.verified,
            "created_at": self.created_at.isoformat(),
            "last_evaluated": self.last_evaluated.isoformat(),
            "tags": self.tags
        }


@dataclass
class ContentEvaluation:
    """Evaluation of a single piece of content."""
    content_id: str
    source_id: str
    content_type: ContentType
    timestamp: datetime
    prediction: Optional[str] = None
    outcome: Optional[str] = None
    accuracy: Optional[bool] = None
    sentiment: float = 0.5
    quality_score: float = 0.5
    engagement_score: float = 0.0
    scam_flags: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)


class CredibilityScorer:
    """
    Evaluates and tracks credibility of financial information sources.
    Helps identify trustworthy analysts vs scammers.
    """
    
    # Scam indicator patterns
    SCAM_PATTERNS = [
        r"guaranteed (\d+)% returns?",
        r"get rich quick",
        r"limited time offer",
        r"secret strategy",
        r"insider information",
        r"pump and dump",
        r"risk-?free",
        r"double your money",
        r"financial freedom in \d+ days",
        r"forex signals",
        r"binary options",
        r"click.*(link|here) below",
        r"DM me for",
        r"telegram group",
        r"whatsapp (\+\d+|group)",
        r"100% accurate",
        r"never lose",
        r"millionaire in months"
    ]
    
    # Quality indicator patterns
    QUALITY_PATTERNS = [
        r"fundamental analysis",
        r"technical analysis",
        r"risk management",
        r"disclaimer",
        r"not financial advice",
        r"due diligence",
        r"balance sheet",
        r"earnings report",
        r"market cap",
        r"P/E ratio",
        r"stop loss",
        r"diversification",
        r"volatility",
        r"correlation",
        r"standard deviation"
    ]
    
    # Credibility thresholds
    WHITELIST_THRESHOLD = 0.75
    BLACKLIST_THRESHOLD = 0.25
    MIN_EVALUATIONS = 10
    
    def __init__(self):
        self.sources: Dict[str, SourceProfile] = {}
        self.evaluations: List[ContentEvaluation] = []
        self.prediction_tracker: Dict[str, List[dict]] = defaultdict(list)
        
    def evaluate_content(
        self,
        content: str,
        source_id: str,
        source_name: str,
        platform: str,
        metadata: Dict = None
    ) -> Tuple[float, List[str], SourceStatus]:
        """
        Evaluate a piece of content for credibility.
        
        Args:
            content: The text content to evaluate
            source_id: Unique identifier for the source
            source_name: Name of the content creator
            platform: Platform (youtube, reddit, etc.)
            metadata: Additional metadata (followers, likes, etc.)
            
        Returns:
            Tuple of (credibility_score, scam_flags, source_status)
        """
        # Get or create source profile
        if source_id not in self.sources:
            self.sources[source_id] = SourceProfile(
                source_id=source_id,
                name=source_name,
                platform=platform
            )
        
        source = self.sources[source_id]
        
        # Check for scam indicators
        scam_flags = self._detect_scam_patterns(content)
        scam_score = len(scam_flags) / max(len(self.SCAM_PATTERNS), 1)
        
        # Check for quality indicators
        quality_indicators = self._detect_quality_patterns(content)
        quality_score = len(quality_indicators) / max(len(self.QUALITY_PATTERNS), 1)
        
        # Calculate engagement metrics if provided
        engagement_score = self._calculate_engagement_score(metadata)
        
        # Update source profile
        source.scam_indicators += len(scam_flags)
        source.content_quality_score = (
            source.content_quality_score * 0.8 + quality_score * 0.2
        )
        source.engagement_rate = (
            source.engagement_rate * 0.9 + engagement_score * 0.1
        )
        
        # Calculate overall credibility
        credibility = self._calculate_credibility(
            quality_score,
            scam_score,
            engagement_score,
            source.accuracy_rate
        )
        
        # Update source credibility (moving average)
        source.credibility_score = (
            source.credibility_score * 0.7 + credibility * 0.3
        )
        
        # Update status based on credibility
        source.status = self._determine_status(source)
        source.last_evaluated = datetime.utcnow()
        
        # Store evaluation
        evaluation = ContentEvaluation(
            content_id=f"{source_id}_{datetime.utcnow().timestamp()}",
            source_id=source_id,
            content_type=self._classify_content_type(content),
            timestamp=datetime.utcnow(),
            quality_score=quality_score,
            engagement_score=engagement_score,
            scam_flags=scam_flags
        )
        self.evaluations.append(evaluation)
        
        return credibility, scam_flags, source.status
    
    def _detect_scam_patterns(self, content: str) -> List[str]:
        """Detect scam indicator patterns in content."""
        content_lower = content.lower()
        detected_patterns = []
        
        for pattern in self.SCAM_PATTERNS:
            if re.search(pattern, content_lower):
                detected_patterns.append(pattern)
        
        return detected_patterns
    
    def _detect_quality_patterns(self, content: str) -> List[str]:
        """Detect quality indicator patterns in content."""
        content_lower = content.lower()
        detected_patterns = []
        
        for pattern in self.QUALITY_PATTERNS:
            if re.search(pattern, content_lower):
                detected_patterns.append(pattern)
        
        return detected_patterns
    
    def _calculate_engagement_score(self, metadata: Dict) -> float:
        """Calculate engagement score from metadata."""
        if not metadata:
            return 0.5
        
        score = 0.5
        
        # Follower count contribution
        followers = metadata.get("followers", 0)
        if followers > 100000:
            score += 0.2
        elif followers > 10000:
            score += 0.1
        elif followers < 100:
            score -= 0.1
        
        # Engagement rate (likes/views ratio)
        views = metadata.get("views", 0)
        likes = metadata.get("likes", 0)
        
        if views > 0:
            engagement_rate = likes / views
            if engagement_rate > 0.1:
                score += 0.2
            elif engagement_rate > 0.05:
                score += 0.1
            elif engagement_rate < 0.01:
                score -= 0.1
        
        # Comment sentiment
        positive_comments = metadata.get("positive_comments", 0)
        negative_comments = metadata.get("negative_comments", 0)
        
        if positive_comments + negative_comments > 0:
            sentiment_ratio = positive_comments / (positive_comments + negative_comments)
            if sentiment_ratio > 0.8:
                score += 0.1
            elif sentiment_ratio < 0.3:
                score -= 0.2
        
        return max(0, min(1, score))
    
    def _calculate_credibility(
        self,
        quality_score: float,
        scam_score: float,
        engagement_score: float,
        accuracy_rate: float
    ) -> float:
        """Calculate overall credibility score."""
        # Weighted average with scam patterns having negative weight
        credibility = (
            quality_score * 0.3 +
            (1 - scam_score) * 0.4 +  # Inverse of scam score
            engagement_score * 0.1 +
            accuracy_rate * 0.2
        )
        
        # Heavy penalty for high scam score
        if scam_score > 0.3:
            credibility *= 0.5
        
        return max(0, min(1, credibility))
    
    def _classify_content_type(self, content: str) -> ContentType:
        """Classify the type of content."""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ["predict", "forecast", "will be", "target"]):
            return ContentType.PREDICTION
        elif any(word in content_lower for word in ["analysis", "analyzed", "examining"]):
            return ContentType.ANALYSIS
        elif any(word in content_lower for word in ["breaking", "announced", "reported"]):
            return ContentType.NEWS
        elif any(word in content_lower for word in ["learn", "how to", "guide", "tutorial"]):
            return ContentType.EDUCATION
        elif any(word in content_lower for word in ["sponsor", "affiliate", "partner"]):
            return ContentType.PROMOTION
        else:
            return ContentType.OPINION
    
    def _determine_status(self, source: SourceProfile) -> SourceStatus:
        """Determine source status based on credibility and history."""
        # Need minimum evaluations before whitelisting/blacklisting
        evaluation_count = len([
            e for e in self.evaluations 
            if e.source_id == source.source_id
        ])
        
        if evaluation_count < self.MIN_EVALUATIONS:
            return SourceStatus.TESTLISTED
        
        # Check credibility thresholds
        if source.credibility_score >= self.WHITELIST_THRESHOLD:
            return SourceStatus.WHITELISTED
        elif source.credibility_score <= self.BLACKLIST_THRESHOLD:
            return SourceStatus.BLACKLISTED
        else:
            return SourceStatus.TESTLISTED
    
    def track_prediction(
        self,
        source_id: str,
        prediction: str,
        target_date: datetime,
        metadata: Dict = None
    ) -> str:
        """
        Track a prediction made by a source.
        
        Args:
            source_id: Source who made the prediction
            prediction: The prediction text
            target_date: When the prediction should be evaluated
            metadata: Additional context
            
        Returns:
            Prediction ID for later evaluation
        """
        prediction_id = f"pred_{source_id}_{datetime.utcnow().timestamp()}"
        
        self.prediction_tracker[source_id].append({
            "id": prediction_id,
            "prediction": prediction,
            "made_at": datetime.utcnow().isoformat(),
            "target_date": target_date.isoformat(),
            "metadata": metadata or {},
            "evaluated": False,
            "outcome": None
        })
        
        if source_id in self.sources:
            self.sources[source_id].total_predictions += 1
        
        logger.info(f"Tracking prediction {prediction_id} from {source_id}")
        return prediction_id
    
    def evaluate_prediction(
        self,
        prediction_id: str,
        outcome: bool,
        details: str = ""
    ) -> None:
        """
        Evaluate a tracked prediction.
        
        Args:
            prediction_id: ID of the prediction
            outcome: Whether prediction was correct
            details: Additional details about outcome
        """
        # Find the prediction
        for source_id, predictions in self.prediction_tracker.items():
            for pred in predictions:
                if pred["id"] == prediction_id and not pred["evaluated"]:
                    pred["evaluated"] = True
                    pred["outcome"] = outcome
                    pred["outcome_details"] = details
                    pred["evaluated_at"] = datetime.utcnow().isoformat()
                    
                    # Update source accuracy
                    if source_id in self.sources:
                        source = self.sources[source_id]
                        if outcome:
                            source.correct_predictions += 1
                        
                        if source.total_predictions > 0:
                            source.accuracy_rate = (
                                source.correct_predictions / source.total_predictions
                            )
                        
                        # Boost/reduce credibility based on prediction outcome
                        if outcome:
                            source.credibility_score = min(
                                1.0, source.credibility_score * 1.1
                            )
                        else:
                            source.credibility_score = max(
                                0.0, source.credibility_score * 0.9
                            )
                    
                    logger.info(
                        f"Evaluated prediction {prediction_id}: "
                        f"{'Correct' if outcome else 'Incorrect'}"
                    )
                    return
    
    def get_source_report(self, source_id: str) -> Optional[Dict]:
        """Get detailed report for a source."""
        if source_id not in self.sources:
            return None
        
        source = self.sources[source_id]
        
        # Get recent evaluations
        recent_evaluations = [
            e for e in self.evaluations[-100:]
            if e.source_id == source_id
        ]
        
        # Get prediction history
        predictions = self.prediction_tracker.get(source_id, [])
        
        return {
            "profile": source.to_dict(),
            "recent_evaluations": len(recent_evaluations),
            "average_quality": sum(e.quality_score for e in recent_evaluations) / max(len(recent_evaluations), 1),
            "total_scam_flags": sum(len(e.scam_flags) for e in recent_evaluations),
            "predictions": {
                "total": len(predictions),
                "evaluated": sum(1 for p in predictions if p["evaluated"]),
                "correct": sum(1 for p in predictions if p.get("outcome") is True),
                "pending": sum(1 for p in predictions if not p["evaluated"])
            },
            "recommendation": self._get_recommendation(source)
        }
    
    def _get_recommendation(self, source: SourceProfile) -> str:
        """Get recommendation for a source."""
        if source.status == SourceStatus.WHITELISTED:
            return "TRUSTED: High quality content with good track record"
        elif source.status == SourceStatus.BLACKLISTED:
            return "AVOID: Multiple scam indicators detected"
        elif source.status == SourceStatus.TESTLISTED:
            if source.credibility_score > 0.6:
                return "PROMISING: Shows potential but needs more evaluation"
            elif source.credibility_score < 0.4:
                return "CAUTION: Low credibility scores, proceed carefully"
            else:
                return "NEUTRAL: Mixed signals, use with context"
        else:
            return "UNKNOWN: Insufficient data for evaluation"
    
    def get_top_sources(
        self,
        platform: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """Get top credible sources."""
        sources = list(self.sources.values())
        
        # Filter by platform if specified
        if platform:
            sources = [s for s in sources if s.platform == platform]
        
        # Filter to whitelisted and high-credibility testlisted
        sources = [
            s for s in sources
            if s.status == SourceStatus.WHITELISTED or
            (s.status == SourceStatus.TESTLISTED and s.credibility_score > 0.6)
        ]
        
        # Sort by credibility
        sources.sort(key=lambda x: x.credibility_score, reverse=True)
        
        return [s.to_dict() for s in sources[:limit]]
    
    def get_blacklisted_sources(self) -> List[Dict]:
        """Get list of blacklisted sources to avoid."""
        blacklisted = [
            s for s in self.sources.values()
            if s.status == SourceStatus.BLACKLISTED
        ]
        
        return [s.to_dict() for s in blacklisted]


# Global credibility scorer instance
credibility_scorer = CredibilityScorer()