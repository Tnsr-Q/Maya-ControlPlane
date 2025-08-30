"""
Twitter/X Platform Adapter

Handles Twitter/X API integration for Maya control plane operations.
Supports posting, engagement tracking, and audience analysis.
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable
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
    
    # Enhanced Twitter Monitoring Methods
    
    async def monitor_mentions(self, 
                             keywords: List[str] = None,
                             callback: Callable[[Dict[str, Any]], None] = None) -> Dict[str, Any]:
        """
        Monitor Twitter for mentions and relevant tweets
        
        Args:
            keywords: Keywords to monitor
            callback: Callback function for new mentions
            
        Returns:
            Monitoring status
        """
        if not self.client:
            return self._create_stub_monitoring_response(keywords)
        
        try:
            # In production, this would use Twitter's streaming API
            # For now, return stub response
            return self._create_stub_monitoring_response(keywords)
            
        except Exception as e:
            logger.error("Failed to start mention monitoring", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def detect_replies_needed(self, 
                                  mentions: List[Dict[str, Any]],
                                  priority_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Detect mentions that need replies with priority classification
        
        Args:
            mentions: List of mention data
            priority_threshold: Minimum priority score for reply
            
        Returns:
            List of mentions needing replies with priority scores
        """
        replies_needed = []
        
        for mention in mentions:
            # Analyze mention for reply necessity
            priority_score = await self._calculate_mention_priority(mention)
            
            if priority_score >= priority_threshold:
                mention_with_priority = {
                    **mention,
                    'priority_score': priority_score,
                    'reply_suggested': True,
                    'analysis_timestamp': datetime.utcnow().isoformat()
                }
                replies_needed.append(mention_with_priority)
        
        return replies_needed
    
    async def batch_process_mentions(self, 
                                   mentions: List[Dict[str, Any]],
                                   batch_size: int = 10) -> Dict[str, Any]:
        """
        Process mentions in batches with priority classification
        
        Args:
            mentions: List of mentions to process
            batch_size: Size of processing batches
            
        Returns:
            Batch processing results
        """
        processed_batches = []
        total_mentions = len(mentions)
        
        for i in range(0, total_mentions, batch_size):
            batch = mentions[i:i + batch_size]
            
            # Process each batch
            batch_result = {
                'batch_number': i // batch_size + 1,
                'batch_size': len(batch),
                'processed_mentions': [],
                'errors': []
            }
            
            for mention in batch:
                try:
                    # Analyze mention
                    priority_score = await self._calculate_mention_priority(mention)
                    reply_needed = priority_score >= 0.5
                    
                    processed_mention = {
                        **mention,
                        'priority_score': priority_score,
                        'reply_needed': reply_needed,
                        'processed_at': datetime.utcnow().isoformat()
                    }
                    
                    batch_result['processed_mentions'].append(processed_mention)
                    
                except Exception as e:
                    batch_result['errors'].append({
                        'mention_id': mention.get('id', 'unknown'),
                        'error': str(e)
                    })
            
            processed_batches.append(batch_result)
            
            # Small delay between batches
            await asyncio.sleep(0.5)
        
        return {
            'success': True,
            'total_mentions': total_mentions,
            'total_batches': len(processed_batches),
            'processed_batches': processed_batches,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def track_conversation_thread(self, 
                                      tweet_id: str,
                                      depth: int = 3) -> Dict[str, Any]:
        """
        Track conversation thread for a tweet
        
        Args:
            tweet_id: Root tweet ID
            depth: Maximum depth to track
            
        Returns:
            Conversation thread data
        """
        if not self.client:
            return self._create_stub_conversation_thread(tweet_id, depth)
        
        try:
            # In production, this would fetch actual conversation thread
            return self._create_stub_conversation_thread(tweet_id, depth)
            
        except Exception as e:
            logger.error("Failed to track conversation thread", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_trending_topics(self, location_id: int = 1) -> Dict[str, Any]:
        """
        Get trending topics for engagement opportunities
        
        Args:
            location_id: Location ID for trends (1 = worldwide)
            
        Returns:
            Trending topics data
        """
        if not self.client:
            return self._create_stub_trending_topics()
        
        try:
            # In production, this would fetch actual trending topics
            return self._create_stub_trending_topics()
            
        except Exception as e:
            logger.error("Failed to get trending topics", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    # Private helper methods for new functionality
    
    async def _calculate_mention_priority(self, mention: Dict[str, Any]) -> float:
        """Calculate priority score for a mention"""
        score = 0.5  # Base score
        
        # Increase score based on various factors
        if mention.get('user', {}).get('verified', False):
            score += 0.2  # Verified user
        
        if mention.get('user', {}).get('followers_count', 0) > 10000:
            score += 0.1  # High follower count
        
        if mention.get('retweet_count', 0) > 5:
            score += 0.1  # High engagement
        
        if mention.get('like_count', 0) > 10:
            score += 0.1  # High likes
        
        # Check for urgent keywords
        urgent_keywords = ['urgent', 'important', 'help', 'issue', 'problem']
        text = mention.get('text', '').lower()
        if any(keyword in text for keyword in urgent_keywords):
            score += 0.2
        
        # Check for negative sentiment indicators
        negative_keywords = ['complaint', 'disappointed', 'bad', 'terrible']
        if any(keyword in text for keyword in negative_keywords):
            score += 0.3  # High priority for negative sentiment
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _create_stub_monitoring_response(self, keywords: List[str]) -> Dict[str, Any]:
        """Create stub response for mention monitoring"""
        return {
            "success": True,
            "monitoring_active": True,
            "keywords": keywords or ["default", "maya", "ai"],
            "mentions_found": 15,
            "monitoring_started": datetime.utcnow().isoformat(),
            "stub_mode": True,
            "sample_mentions": [
                {
                    "id": "1234567890",
                    "text": "Hey @maya, can you help me with content creation?",
                    "user": {
                        "username": "user123",
                        "verified": False,
                        "followers_count": 500
                    },
                    "created_at": datetime.utcnow().isoformat(),
                    "priority_score": 0.6
                },
                {
                    "id": "1234567891",
                    "text": "Love what @maya is doing with AI-powered social media!",
                    "user": {
                        "username": "influencer456",
                        "verified": True,
                        "followers_count": 50000
                    },
                    "created_at": datetime.utcnow().isoformat(),
                    "priority_score": 0.8
                }
            ]
        }
    
    def _create_stub_conversation_thread(self, tweet_id: str, depth: int) -> Dict[str, Any]:
        """Create stub conversation thread"""
        return {
            "success": True,
            "root_tweet_id": tweet_id,
            "thread_depth": depth,
            "conversation_tree": {
                "root": {
                    "id": tweet_id,
                    "text": "Original tweet about AI in social media",
                    "author": "original_user",
                    "replies": [
                        {
                            "id": "reply_1",
                            "text": "This is really interesting! Tell me more.",
                            "author": "interested_user",
                            "replies": [
                                {
                                    "id": "reply_1_1",
                                    "text": "I'd love to know more about the implementation",
                                    "author": "developer_user",
                                    "replies": []
                                }
                            ]
                        },
                        {
                            "id": "reply_2",
                            "text": "Great insights on AI technology!",
                            "author": "tech_enthusiast",
                            "replies": []
                        }
                    ]
                }
            },
            "total_replies": 3,
            "engagement_level": "medium",
            "stub_mode": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _create_stub_trending_topics(self) -> Dict[str, Any]:
        """Create stub trending topics"""
        return {
            "success": True,
            "location": "Worldwide",
            "trends": [
                {
                    "name": "#AI",
                    "volume": "500K tweets",
                    "engagement_opportunity": "high",
                    "relevance_score": 0.9
                },
                {
                    "name": "#SocialMedia",
                    "volume": "250K tweets",
                    "engagement_opportunity": "medium",
                    "relevance_score": 0.8
                },
                {
                    "name": "#Technology",
                    "volume": "800K tweets",
                    "engagement_opportunity": "high",
                    "relevance_score": 0.7
                },
                {
                    "name": "#Innovation",
                    "volume": "150K tweets",
                    "engagement_opportunity": "medium",
                    "relevance_score": 0.6
                }
            ],
            "generated_at": datetime.utcnow().isoformat(),
            "stub_mode": True
        }