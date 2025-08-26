"""
Maya API Schema Definitions

Data models and schemas for Maya API operations.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class CampaignStatus(str, Enum):
    """Campaign status enumeration"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PostStatus(str, Enum):
    """Post status enumeration"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


class EventType(str, Enum):
    """Event type enumeration"""
    CAMPAIGN_CREATED = "campaign_created"
    POST_PUBLISHED = "post_published"
    ENGAGEMENT_RECEIVED = "engagement_received"
    ANALYTICS_UPDATED = "analytics_updated"


class Campaign(BaseModel):
    """Campaign data model"""
    id: str = Field(..., description="Unique campaign identifier")
    name: str = Field(..., description="Campaign name")
    description: Optional[str] = Field(None, description="Campaign description")
    status: CampaignStatus = Field(default=CampaignStatus.DRAFT, description="Campaign status")
    platforms: List[str] = Field(default_factory=list, description="Target platforms")
    start_date: Optional[datetime] = Field(None, description="Campaign start date")
    end_date: Optional[datetime] = Field(None, description="Campaign end date")
    budget: Optional[float] = Field(None, description="Campaign budget")
    target_audience: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Target audience criteria")
    content_strategy: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Content strategy settings")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional campaign metadata")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Post(BaseModel):
    """Social media post data model"""
    id: str = Field(..., description="Unique post identifier")
    campaign_id: Optional[str] = Field(None, description="Associated campaign ID")
    platform: str = Field(..., description="Target platform (twitter, youtube, tiktok)")
    content: str = Field(..., description="Post content/text")
    media_urls: List[str] = Field(default_factory=list, description="Associated media URLs")
    hashtags: List[str] = Field(default_factory=list, description="Post hashtags")
    mentions: List[str] = Field(default_factory=list, description="User mentions")
    status: PostStatus = Field(default=PostStatus.DRAFT, description="Post status")
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled publication time")
    published_at: Optional[datetime] = Field(None, description="Actual publication time")
    engagement_metrics: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Engagement metrics")
    ai_generated: bool = Field(default=False, description="Whether content was AI-generated")
    ai_model: Optional[str] = Field(None, description="AI model used for generation")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional post metadata")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Event(BaseModel):
    """System event data model"""
    id: str = Field(..., description="Unique event identifier")
    type: EventType = Field(..., description="Event type")
    source: str = Field(..., description="Event source (system, user, external)")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event data payload")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    user_id: Optional[str] = Field(None, description="Associated user ID")
    session_id: Optional[str] = Field(None, description="Associated session ID")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracking")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional event metadata")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Additional utility models
class PlatformConfig(BaseModel):
    """Platform-specific configuration"""
    platform: str = Field(..., description="Platform name")
    enabled: bool = Field(default=True, description="Whether platform is enabled")
    api_credentials: Optional[Dict[str, str]] = Field(default_factory=dict, description="API credentials")
    rate_limits: Optional[Dict[str, int]] = Field(default_factory=dict, description="Rate limit configuration")
    content_rules: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Content rules and restrictions")


class AnalyticsMetrics(BaseModel):
    """Analytics metrics data model"""
    platform: str = Field(..., description="Platform name")
    metric_type: str = Field(..., description="Type of metric (engagement, reach, etc.)")
    value: float = Field(..., description="Metric value")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Metric timestamp")
    dimensions: Optional[Dict[str, str]] = Field(default_factory=dict, description="Metric dimensions")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }