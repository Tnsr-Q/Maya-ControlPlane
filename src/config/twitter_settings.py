"""Twitter Configuration Settings

Advanced configuration for Twitter integration
"""

from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class TwitterRateLimits:
    """Twitter API rate limits"""
    posts_per_15min: int = 300
    follows_per_15min: int = 400
    likes_per_15min: int = 1000
    retweets_per_15min: int = 300
    dm_per_15min: int = 1000

@dataclass 
class TwitterContentSettings:
    """Content-specific settings for Twitter"""
    max_tweet_length: int = 280
    max_thread_length: int = 25
    recommended_hashtags: int = 3
    max_hashtags: int = 10
    max_mentions: int = 10
    image_formats: List[str] = None
    video_formats: List[str] = None
    
    def __post_init__(self):
        if self.image_formats is None:
            self.image_formats = ['jpg', 'jpeg', 'png', 'gif', 'webp']
        if self.video_formats is None:
            self.video_formats = ['mp4', 'mov']

@dataclass
class TwitterOptimizationSettings:
    """Optimization settings for Twitter content"""
    optimal_posting_times: List[str] = None
    trending_hashtag_limit: int = 5
    engagement_window_hours: int = 2
    auto_reply_enabled: bool = True
    sentiment_filtering: bool = True
    
    def __post_init__(self):
        if self.optimal_posting_times is None:
            self.optimal_posting_times = ['09:00', '13:00', '15:00', '17:00', '19:00']

class TwitterSettings:
    """Comprehensive Twitter settings manager"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.rate_limits = TwitterRateLimits()
        self.content = TwitterContentSettings()
        self.optimization = TwitterOptimizationSettings()
        
        # Load custom settings if provided
        if config:
            self._load_custom_settings(config)
    
    def _load_custom_settings(self, config: Dict[str, Any]):
        """Load custom settings from configuration"""
        if 'rate_limits' in config:
            for key, value in config['rate_limits'].items():
                if hasattr(self.rate_limits, key):
                    setattr(self.rate_limits, key, value)
        
        if 'content' in config:
            for key, value in config['content'].items():
                if hasattr(self.content, key):
                    setattr(self.content, key, value)
        
        if 'optimization' in config:
            for key, value in config['optimization'].items():
                if hasattr(self.optimization, key):
                    setattr(self.optimization, key, value)
    
    def get_platform_limits(self) -> Dict[str, int]:
        """Get platform-specific limits"""
        return {
            'max_length': self.content.max_tweet_length,
            'max_hashtags': self.content.max_hashtags,
            'max_mentions': self.content.max_mentions,
            'max_thread_length': self.content.max_thread_length
        }
    
    def get_rate_limits(self) -> Dict[str, int]:
        """Get current rate limits"""
        return {
            'posts': self.rate_limits.posts_per_15min,
            'follows': self.rate_limits.follows_per_15min,
            'likes': self.rate_limits.likes_per_15min,
            'retweets': self.rate_limits.retweets_per_15min,
            'dms': self.rate_limits.dm_per_15min
        }
    
    def is_optimal_posting_time(self, hour: int) -> bool:
        """Check if current hour is optimal for posting"""
        current_time = f"{hour:02d}:00"
        return current_time in self.optimization.optimal_posting_times
    
    def get_content_recommendations(self, content_type: str = 'post') -> Dict[str, Any]:
        """Get content recommendations based on type"""
        if content_type == 'thread':
            return {
                'max_tweets': self.content.max_thread_length,
                'recommended_length': self.content.max_tweet_length - 50,
                'use_numbering': True,
                'end_with_cta': True
            }
        else:
            return {
                'max_length': self.content.max_tweet_length,
                'recommended_hashtags': self.content.recommended_hashtags,
                'include_media': True,
                'optimal_engagement': True
            }

# Default Twitter settings instance
default_twitter_settings = TwitterSettings()
