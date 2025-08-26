"""
Twitter/X Platform Adapter

Handles Twitter/X API integration for Maya control plane operations.
Supports posting, engagement tracking, and audience analysis.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import tweepy
import structlog

from stubs.schemas import Campaign, Post, Event
from hub.logger import get_logger


logger = get_logger("twitter_adapter")


class TwitterAdapter:
    """
    Twitter/X platform adapter for Maya control plane
    
    Features:
    - Tweet posting and thread management
    - Engagement tracking and analytics
    - Audience interaction monitoring
    - Campaign execution on Twitter/X
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get('api_key')
        self.api_secret = config.get('api_secret')
        self.access_token = config.get('access_token')
        self.access_token_secret = config.get('access_token_secret')
        self.bearer_token = config.get('bearer_token')
        
        self.client = None
        self.api = None
        
        if self._has_credentials():
            self._initialize_client()
        else:
            logger.warning("Twitter credentials not provided, using stub mode")
    
    def _has_credentials(self) -> bool:
        """Check if all required credentials are available"""
        return all([
            self.api_key,
            self.api_secret,
            self.access_token,
            self.access_token_secret,
            self.bearer_token
        ])
    
    def _initialize_client(self):
        """Initialize Twitter API clients"""
        try:
            # Initialize v2 client
            self.client = tweepy.Client(
                bearer_token=self.bearer_token,
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret,
                wait_on_rate_limit=True
            )
            
            # Initialize v1.1 API for additional features
            auth = tweepy.OAuth1UserHandler(
                self.api_key,
                self.api_secret,
                self.access_token,
                self.access_token_secret
            )
            self.api = tweepy.API(auth, wait_on_rate_limit=True)
            
            logger.info("Twitter API clients initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize Twitter clients", error=str(e))
            self.client = None
            self.api = None
    
    async def create_post(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new post on Twitter/X"""
        try:
            text = content.get('text', '')
            media_urls = content.get('media_urls', [])
            reply_to = content.get('reply_to')
            
            if not self.client:
                # Stub mode
                return self._create_stub_response("post_created", {
                    "tweet_id": f"stub_tweet_{datetime.utcnow().timestamp()}",
                    "text": text,
                    "created_at": datetime.utcnow().isoformat(),
                    "media_count": len(media_urls)
                })
            
            # Handle media upload if present
            media_ids = []
            if media_urls and self.api:
                for media_url in media_urls[:4]:  # Twitter allows max 4 media
                    try:
                        # Download and upload media (simplified)
                        media = self.api.media_upload(media_url)
                        media_ids.append(media.media_id)
                    except Exception as e:
                        logger.warning("Failed to upload media", url=media_url, error=str(e))
            
            # Create tweet
            response = self.client.create_tweet(
                text=text,
                media_ids=media_ids if media_ids else None,
                in_reply_to_tweet_id=reply_to
            )
            
            tweet_data = response.data
            result = {
                "success": True,
                "tweet_id": tweet_data['id'],
                "text": tweet_data['text'],
                "created_at": datetime.utcnow().isoformat(),
                "media_count": len(media_ids)
            }
            
            logger.info("Tweet created successfully", 
                       tweet_id=tweet_data['id'],
                       text_length=len(text),
                       media_count=len(media_ids))
            
            return result
            
        except Exception as e:
            logger.error("Failed to create tweet", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def create_thread(self, posts: List[str]) -> Dict[str, Any]:
        """Create a Twitter thread"""
        try:
            if not self.client:
                # Stub mode
                return self._create_stub_response("thread_created", {
                    "thread_id": f"stub_thread_{datetime.utcnow().timestamp()}",
                    "tweet_count": len(posts),
                    "created_at": datetime.utcnow().isoformat()
                })
            
            tweet_ids = []
            reply_to = None
            
            for i, text in enumerate(posts):
                response = self.client.create_tweet(
                    text=text,
                    in_reply_to_tweet_id=reply_to
                )
                
                tweet_id = response.data['id']
                tweet_ids.append(tweet_id)
                reply_to = tweet_id
                
                # Small delay between tweets
                await asyncio.sleep(1)
            
            result = {
                "success": True,
                "thread_id": tweet_ids[0],  # First tweet ID as thread ID
                "tweet_ids": tweet_ids,
                "tweet_count": len(tweet_ids),
                "created_at": datetime.utcnow().isoformat()
            }
            
            logger.info("Twitter thread created", 
                       thread_id=tweet_ids[0],
                       tweet_count=len(tweet_ids))
            
            return result
            
        except Exception as e:
            logger.error("Failed to create thread", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def execute_campaign(self, campaign: Campaign) -> Dict[str, Any]:
        """Execute a campaign on Twitter/X"""
        try:
            results = []
            
            for post in campaign.posts:
                if post.platform == "twitter" or "twitter" in post.platforms:
                    result = await self.create_post({
                        "text": post.content,
                        "media_urls": post.media_urls,
                        "scheduled_time": post.scheduled_time
                    })
                    results.append(result)
                    
                    # Delay between posts to avoid rate limiting
                    await asyncio.sleep(2)
            
            campaign_result = {
                "success": True,
                "campaign_id": campaign.id,
                "platform": "twitter",
                "posts_created": len([r for r in results if r.get("success")]),
                "posts_failed": len([r for r in results if not r.get("success")]),
                "results": results,
                "executed_at": datetime.utcnow().isoformat()
            }
            
            logger.info("Twitter campaign executed",
                       campaign_id=campaign.id,
                       posts_created=campaign_result["posts_created"],
                       posts_failed=campaign_result["posts_failed"])
            
            return campaign_result
            
        except Exception as e:
            logger.error("Failed to execute Twitter campaign", 
                        campaign_id=campaign.id, 
                        error=str(e))
            return {
                "success": False,
                "campaign_id": campaign.id,
                "platform": "twitter",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _create_stub_response(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a stub response for testing/demo purposes"""
        return {
            "success": True,
            "stub_mode": True,
            "action": action,
            "platform": "twitter",
            "timestamp": datetime.utcnow().isoformat(),
            **data
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Twitter API connection health"""
        try:
            if not self.client:
                return {
                    "healthy": True,
                    "mode": "stub",
                    "message": "Running in stub mode - no credentials provided"
                }
            
            # Simple API call to check connectivity
            me = self.client.get_me()
            
            return {
                "healthy": True,
                "mode": "live",
                "user_id": me.data.id,
                "username": me.data.username,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Twitter health check failed", error=str(e))
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }