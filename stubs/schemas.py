"""
Maya Control Plane Data Schemas

Pydantic models for data validation and serialization across the Maya control plane system.
Defines the structure for campaigns, posts, events, and other core entities.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid


class PlatformType(str, Enum):
    """Supported social media platforms"""
    TWITTER = "twitter"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"


class ContentType(str, Enum):
    """Types of content"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    THREAD = "thread"
    STORY = "story"
    LIVE = "live"


class CampaignStatus(str, Enum):
    """Campaign status options"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PostStatus(str, Enum):
    """Post status options"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"
    DELETED = "deleted"


class EventType(str, Enum):
    """Event types for tracking"""
    POST_CREATED = "post_created"
    POST_PUBLISHED = "post_published"
    POST_ENGAGEMENT = "post_engagement"
    CAMPAIGN_STARTED = "campaign_started"
    CAMPAIGN_COMPLETED = "campaign_completed"
    USER_INTERACTION = "user_interaction"
    SYSTEM_EVENT = "system_event"
    ERROR_EVENT = "error_event"


class Post(BaseModel):
    """Individual post model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: Optional[str] = None
    content: str = Field(..., min_length=1, max_length=10000)
    content_type: ContentType = ContentType.TEXT
    platform: Optional[PlatformType] = None
    platforms: List[PlatformType] = Field(default_factory=list)
    
    # Media and attachments
    media_urls: List[str] = Field(default_factory=list)
    thumbnail_url: Optional[str] = None
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    hashtags: List[str] = Field(default_factory=list)
    mentions: List[str] = Field(default_factory=list)
    
    # Scheduling
    scheduled_time: Optional[datetime] = None
    published_time: Optional[datetime] = None
    
    # Status and tracking
    status: PostStatus = PostStatus.DRAFT
    external_ids: Dict[str, str] = Field(default_factory=dict)
    
    # Analytics
    metrics: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('platforms', pre=True, always=True)
    def set_platforms(cls, v, values):
        """Ensure platforms list includes the single platform if specified"""
        if not v and 'platform' in values and values['platform']:
            return [values['platform']]
        return v or []
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Campaign(BaseModel):
    """Campaign model for multi-platform content campaigns"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    
    # Campaign configuration
    platforms: List[PlatformType] = Field(..., min_items=1)
    content_type: ContentType = ContentType.TEXT
    
    # Content
    posts: List[Post] = Field(default_factory=list)
    template_content: Optional[str] = None
    
    # Targeting and audience
    target_audience: Dict[str, Any] = Field(default_factory=dict)
    demographics: Dict[str, Any] = Field(default_factory=dict)
    
    # Scheduling
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    timezone: str = "UTC"
    
    # Budget and resources
    budget: Optional[float] = None
    currency: str = "USD"
    
    # Status and tracking
    status: CampaignStatus = CampaignStatus.DRAFT
    
    # Analytics and performance
    goals: Dict[str, Any] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def add_post(self, post: Post) -> None:
        """Add a post to the campaign"""
        if not post.platforms:
            post.platforms = self.platforms
        self.posts.append(post)
        self.updated_at = datetime.utcnow()
    
    def get_posts_by_platform(self, platform: PlatformType) -> List[Post]:
        """Get all posts for a specific platform"""
        return [post for post in self.posts if platform in post.platforms]
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Event(BaseModel):
    """Event model for tracking system events and analytics"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    
    # Event source and context
    source: str
    platform: Optional[PlatformType] = None
    
    # Related entities
    campaign_id: Optional[str] = None
    post_id: Optional[str] = None
    user_id: Optional[str] = None
    
    # Event data
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Event properties
    severity: str = "info"
    message: Optional[str] = None
    
    # Timestamps
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    
    # Processing status
    processed: bool = False
    retry_count: int = 0
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Analytics(BaseModel):
    """Analytics model for performance tracking"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # What is being analyzed
    entity_type: str
    entity_id: str
    platform: Optional[PlatformType] = None
    
    # Time period
    start_date: datetime
    end_date: datetime
    
    # Core metrics
    impressions: int = 0
    reach: int = 0
    engagement: int = 0
    clicks: int = 0
    shares: int = 0
    comments: int = 0
    likes: int = 0
    
    # Calculated metrics
    engagement_rate: float = 0.0
    click_through_rate: float = 0.0
    conversion_rate: float = 0.0
    
    # Platform-specific metrics
    platform_metrics: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Example data for testing
def create_example_post() -> Post:
    """Create an example post for testing"""
    return Post(
        title="Example Social Media Post",
        content="This is an example post created by Maya Control Plane! 🚀 #Innovation #AI #SocialMedia",
        content_type=ContentType.TEXT,
        platforms=[PlatformType.TWITTER, PlatformType.LINKEDIN],
        hashtags=["Innovation", "AI", "SocialMedia"],
        scheduled_time=datetime.utcnow() + timedelta(hours=1),
        tags=["example", "test", "demo"]
    )


def create_example_campaign() -> Campaign:
    """Create an example campaign for testing"""
    campaign = Campaign(
        name="Maya Control Plane Demo Campaign",
        description="Demonstration campaign showcasing Maya's capabilities across multiple platforms",
        platforms=[PlatformType.TWITTER, PlatformType.YOUTUBE, PlatformType.TIKTOK],
        content_type=ContentType.TEXT,
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(days=7),
        budget=1000.0,
        goals={
            "reach": 10000,
            "engagement": 1000,
            "conversions": 50
        },
        tags=["demo", "maya", "ai", "social-media"]
    )
    
    # Add example posts
    for i in range(3):
        post = Post(
            title=f"Demo Post {i+1}",
            content=f"This is demo post #{i+1} for the Maya Control Plane campaign! 🎯",
            platforms=campaign.platforms,
            hashtags=["Maya", "AI", "Demo"],
            scheduled_time=datetime.utcnow() + timedelta(hours=i*8)
        )
        campaign.add_post(post)
    
    return campaign