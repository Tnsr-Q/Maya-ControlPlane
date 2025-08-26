"""
Feedback Loop System

Implements continuous learning and optimization based on performance data.
Collects feedback from campaigns, analyzes results, and improves future content.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
import uuid
import json
import structlog
from collections import defaultdict

from stubs.schemas import Campaign, Post, Event, Analytics, PlatformType
from stubs.maya_stub import call_maya
from hub.logger import get_logger


logger = get_logger("feedback_loop")


class FeedbackType(Enum):
    """Types of feedback"""
    PERFORMANCE_METRICS = "performance_metrics"
    USER_ENGAGEMENT = "user_engagement"
    AUDIENCE_SENTIMENT = "audience_sentiment"
    CONTENT_QUALITY = "content_quality"
    TIMING_EFFECTIVENESS = "timing_effectiveness"
    PLATFORM_OPTIMIZATION = "platform_optimization"


class LearningPriority(Enum):
    """Priority levels for learning insights"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class FeedbackData:
    """Individual feedback data point"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    feedback_type: FeedbackType = FeedbackType.PERFORMANCE_METRICS
    source: str = ""  # e.g., "twitter_adapter", "user_interaction", "analytics"
    
    # Related entities
    campaign_id: Optional[str] = None
    post_id: Optional[str] = None
    platform: Optional[PlatformType] = None
    
    # Feedback content
    data: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    confidence: float = 1.0  # Confidence in the feedback (0.0 to 1.0)
    processed: bool = False


@dataclass
class LearningInsight:
    """Insight derived from feedback analysis"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    insight_type: str = ""
    
    # Priority and impact
    priority: LearningPriority = LearningPriority.MEDIUM
    impact_score: float = 0.0  # Expected impact (0.0 to 1.0)
    confidence: float = 0.0  # Confidence in insight (0.0 to 1.0)
    
    # Supporting data
    supporting_feedback: List[str] = field(default_factory=list)  # Feedback IDs
    evidence: Dict[str, Any] = field(default_factory=dict)
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    action_items: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    applied: bool = False
    applied_at: Optional[datetime] = None


class FeedbackLoopSystem:
    """Continuous learning and optimization system for Maya Control Plane"""
    
    def __init__(self):
        self.feedback_data: Dict[str, FeedbackData] = {}
        self.insights: Dict[str, LearningInsight] = {}
        self.learning_models: Dict[str, Dict[str, Any]] = {}
        
        # Performance tracking
        self.performance_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.optimization_rules: List[Dict[str, Any]] = []
        
        logger.info("Feedback Loop System initialized")
    
    async def collect_feedback(self, feedback: FeedbackData) -> str:
        """Collect feedback data from various sources"""
        
        # Store feedback
        self.feedback_data[feedback.id] = feedback
        
        logger.info("Feedback collected",
                   feedback_id=feedback.id,
                   type=feedback.feedback_type.value,
                   source=feedback.source,
                   platform=feedback.platform.value if feedback.platform else None)
        
        return feedback.id
    
    async def collect_campaign_feedback(self, campaign: Campaign, analytics: Analytics) -> List[str]:
        """Collect comprehensive feedback from a completed campaign"""
        feedback_ids = []
        
        # Performance metrics feedback
        performance_feedback = FeedbackData(
            feedback_type=FeedbackType.PERFORMANCE_METRICS,
            source="campaign_analytics",
            campaign_id=campaign.id,
            data={
                "campaign_name": campaign.name,
                "platforms": [p.value for p in campaign.platforms],
                "duration_days": (campaign.end_time - campaign.start_time).days if campaign.end_time and campaign.start_time else 0,
                "post_count": len(campaign.posts)
            },
            metrics={
                "engagement_rate": analytics.engagement_rate,
                "reach": analytics.reach,
                "impressions": analytics.impressions,
                "clicks": analytics.clicks,
                "conversions": analytics.conversion_rate
            },
            context={
                "target_audience": campaign.target_audience,
                "budget": campaign.budget,
                "goals": campaign.goals
            }
        )
        
        feedback_id = await self.collect_feedback(performance_feedback)
        feedback_ids.append(feedback_id)
        
        return feedback_ids
    
    def get_feedback_summary(self) -> Dict[str, Any]:
        """Get summary of collected feedback"""
        
        total_feedback = len(self.feedback_data)
        processed_feedback = len([f for f in self.feedback_data.values() if f.processed])
        
        # Group by type
        feedback_by_type = defaultdict(int)
        for feedback in self.feedback_data.values():
            feedback_by_type[feedback.feedback_type.value] += 1
        
        # Group by platform
        feedback_by_platform = defaultdict(int)
        for feedback in self.feedback_data.values():
            if feedback.platform:
                feedback_by_platform[feedback.platform.value] += 1
        
        # Recent feedback (last 7 days)
        recent_cutoff = datetime.utcnow() - timedelta(days=7)
        recent_feedback = len([
            f for f in self.feedback_data.values()
            if f.timestamp >= recent_cutoff
        ])
        
        return {
            "total_feedback": total_feedback,
            "processed_feedback": processed_feedback,
            "unprocessed_feedback": total_feedback - processed_feedback,
            "recent_feedback_7d": recent_feedback,
            "feedback_by_type": dict(feedback_by_type),
            "feedback_by_platform": dict(feedback_by_platform),
            "total_insights": len(self.insights),
            "applied_insights": len([i for i in self.insights.values() if i.applied]),
            "optimization_rules": len(self.optimization_rules),
            "last_updated": datetime.utcnow().isoformat()
        }


# Global feedback loop system instance
feedback_loop_system = FeedbackLoopSystem()


# Convenience functions
async def collect_campaign_performance_feedback(campaign: Campaign, analytics: Analytics) -> List[str]:
    """Convenience function to collect campaign feedback"""
    return await feedback_loop_system.collect_campaign_feedback(campaign, analytics)


async def collect_post_performance_feedback(post: Post, metrics: Dict[str, Any]) -> str:
    """Convenience function to collect post feedback"""
    return await feedback_loop_system.collect_post_feedback(post, metrics)