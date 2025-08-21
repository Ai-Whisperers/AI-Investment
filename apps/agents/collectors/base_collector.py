"""
Base collector implementation and orchestrator for social media data collection.
Follows zero-budget architecture using free tiers and smart rate limiting.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

from ..base import BaseCollector, RawContent, SourceType, CollectionError

logger = logging.getLogger(__name__)


class SocialCollector(BaseCollector):
    """
    Enhanced base collector with social media specific functionality.
    """
    
    def __init__(
        self, 
        source_type: SourceType,
        rate_limit_per_hour: int = 60,
        priority_weight: float = 1.0
    ):
        super().__init__(source_type, rate_limit_per_hour)
        self.priority_weight = priority_weight  # From mermaid data sources priority
        self.collection_stats = {
            'total_collected': 0,
            'high_value_items': 0,
            'signals_generated': 0,
            'last_collection': None
        }
        
    @abstractmethod
    async def collect_long_term_signals(self, **kwargs) -> List[RawContent]:
        """Collect content for long-term investment analysis."""
        pass
        
    @abstractmethod  
    async def collect_swing_signals(self, **kwargs) -> List[RawContent]:
        """Collect content for swing trade opportunities."""
        pass
        
    def should_collect_now(self, signal_type: str) -> bool:
        """Determine if we should collect based on schedule and priority."""
        current_hour = datetime.now().hour
        
        if signal_type == "long_term":
            # Collect long-term signals once daily at 6 AM
            return current_hour == 6
        elif signal_type == "swing":
            # Collect swing signals every 2 hours during market hours
            return current_hour % 2 == 0 and 6 <= current_hour <= 20
        
        return False
        
    def filter_high_value_content(self, content_list: List[RawContent]) -> List[RawContent]:
        """Filter content to focus on high-value items only."""
        high_value = []
        
        for content in content_list:
            value_score = self._calculate_value_score(content)
            if value_score > 0.6:  # Only keep high-value content
                high_value.append(content)
                
        self.collection_stats['high_value_items'] += len(high_value)
        self.collection_stats['total_collected'] += len(content_list)
        
        return high_value
        
    def _calculate_value_score(self, content: RawContent) -> float:
        """Calculate value score for content prioritization."""
        score = 0.0
        
        # Engagement score (0-0.4)
        engagement = content.engagement
        views = engagement.get('views', 0)
        likes = engagement.get('likes', 0)
        comments = engagement.get('comments', 0)
        
        if views > 10000:
            score += 0.2
        elif views > 1000:
            score += 0.1
            
        if comments > 100:
            score += 0.2
        elif comments > 10:
            score += 0.1
            
        # Content quality score (0-0.3)
        text_length = len(content.text) if content.text else 0
        if text_length > 500:
            score += 0.2
        elif text_length > 100:
            score += 0.1
            
        if content.title and len(content.title) > 20:
            score += 0.1
            
        # Recency score (0-0.3)
        age_hours = (datetime.now() - content.created_at).total_seconds() / 3600
        if age_hours < 6:
            score += 0.3
        elif age_hours < 24:
            score += 0.2
        elif age_hours < 72:
            score += 0.1
            
        return min(score, 1.0)


class CollectorOrchestrator:
    """
    Orchestrates collection from multiple sources based on priority weights.
    Implements zero-budget strategy using GitHub Actions scheduling.
    """
    
    def __init__(self):
        self.collectors: Dict[SourceType, SocialCollector] = {}
        self.collection_schedule = self._create_collection_schedule()
        self.daily_budget_minutes = 60  # 60 min/day for GitHub Actions
        self.used_minutes_today = 0
        
    def register_collector(self, collector: SocialCollector):
        """Register a collector with the orchestrator."""
        self.collectors[collector.source_type] = collector
        logger.info(f"Registered {collector.get_collector_name()} collector")
        
    def _create_collection_schedule(self) -> Dict[str, Dict]:
        """Create collection schedule based on data source priorities."""
        return {
            "06:00": {  # Morning: Long-term research (20 min)
                "type": "long_term",
                "sources": [SourceType.YOUTUBE, SourceType.REDDIT],
                "budget_minutes": 20,
                "priority": "high"
            },
            "09:00": {  # Market open: Momentum signals (15 min)
                "type": "swing", 
                "sources": [SourceType.REDDIT, SourceType.CHAN],
                "budget_minutes": 15,
                "priority": "high"
            },
            "13:00": {  # Midday: Sentiment check (15 min)
                "type": "swing",
                "sources": [SourceType.TIKTOK, SourceType.REDDIT],
                "budget_minutes": 15,
                "priority": "medium"
            },
            "16:00": {  # After close: Daily wrap-up (10 min)
                "type": "long_term",
                "sources": [SourceType.YOUTUBE, SourceType.CHAN],
                "budget_minutes": 10,
                "priority": "medium"
            }
        }
        
    async def execute_scheduled_collection(self) -> Dict[str, Any]:
        """Execute collection based on current time schedule."""
        current_time = datetime.now().strftime("%H:00")
        
        if current_time not in self.collection_schedule:
            logger.info(f"No collection scheduled for {current_time}")
            return {"status": "no_collection_scheduled"}
            
        schedule = self.collection_schedule[current_time]
        
        # Check budget
        if self.used_minutes_today + schedule["budget_minutes"] > self.daily_budget_minutes:
            logger.warning(f"Daily budget exceeded, skipping collection at {current_time}")
            return {"status": "budget_exceeded"}
            
        logger.info(f"Starting {schedule['type']} collection at {current_time}")
        
        start_time = datetime.now()
        all_content = []
        
        # Collect from prioritized sources
        for source_type in schedule["sources"]:
            if source_type not in self.collectors:
                logger.warning(f"No collector registered for {source_type.value}")
                continue
                
            collector = self.collectors[source_type]
            
            try:
                if schedule["type"] == "long_term":
                    content = await collector.collect_long_term_signals()
                else:
                    content = await collector.collect_swing_signals()
                    
                # Filter to high-value only
                high_value_content = collector.filter_high_value_content(content)
                all_content.extend(high_value_content)
                
                logger.info(f"Collected {len(high_value_content)}/{len(content)} high-value items from {source_type.value}")
                
            except CollectionError as e:
                logger.error(f"Collection failed for {source_type.value}: {e}")
                continue
                
        # Update budget usage
        execution_time = (datetime.now() - start_time).total_seconds() / 60
        self.used_minutes_today += execution_time
        
        return {
            "status": "success",
            "collection_type": schedule["type"],
            "items_collected": len(all_content),
            "sources_used": [s.value for s in schedule["sources"]],
            "execution_time_minutes": round(execution_time, 2),
            "budget_remaining": self.daily_budget_minutes - self.used_minutes_today,
            "content": all_content
        }
        
    async def collect_all_sources(self, signal_type: str = "swing") -> List[RawContent]:
        """Collect from all registered sources for a specific signal type."""
        all_content = []
        
        tasks = []
        for source_type, collector in self.collectors.items():
            if signal_type == "long_term":
                task = collector.collect_long_term_signals()
            else:
                task = collector.collect_swing_signals()
            tasks.append(task)
            
        # Execute collections in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                source = list(self.collectors.keys())[i]
                logger.error(f"Collection failed for {source.value}: {result}")
                continue
                
            all_content.extend(result)
            
        return all_content
        
    def get_orchestrator_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics for all collectors."""
        stats = {
            "daily_budget_minutes": self.daily_budget_minutes,
            "used_minutes_today": self.used_minutes_today,
            "budget_remaining": self.daily_budget_minutes - self.used_minutes_today,
            "collectors": {}
        }
        
        for source_type, collector in self.collectors.items():
            stats["collectors"][source_type.value] = {
                **collector.get_stats(),
                **collector.collection_stats
            }
            
        return stats
        
    def reset_daily_budget(self):
        """Reset daily budget counter (called at midnight)."""
        self.used_minutes_today = 0
        logger.info("Daily budget reset")
        
    def get_priority_sources_for_time(self, time_str: str) -> List[SourceType]:
        """Get priority sources for a specific time."""
        if time_str in self.collection_schedule:
            return self.collection_schedule[time_str]["sources"]
        return []