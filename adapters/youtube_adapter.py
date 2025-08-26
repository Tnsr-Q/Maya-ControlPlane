"""
YouTube Platform Adapter

Handles YouTube API integration for Maya control plane operations.
Supports video uploads, community posts, and analytics tracking.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog

from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from stubs.schemas import Campaign, Post, Event
from hub.logger import get_logger


logger = get_logger("youtube_adapter")


class YouTubeAdapter:
    """
    YouTube platform adapter for Maya control plane
    
    Features:
    - Video upload and management
    - Community post creation
    - Analytics and engagement tracking
    - Campaign execution on YouTube
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.refresh_token = config.get('refresh_token')
        
        self.youtube = None
        self.credentials = None
        
        if self._has_credentials():
            self._initialize_client()
        else:
            logger.warning("YouTube credentials not provided, using stub mode")
    
    def _has_credentials(self) -> bool:
        """Check if all required credentials are available"""
        return all([
            self.client_id,
            self.client_secret,
            self.refresh_token
        ])
    
    def _initialize_client(self):
        """Initialize YouTube API client"""
        try:
            # Create credentials object
            self.credentials = Credentials(
                token=None,
                refresh_token=self.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            
            # Refresh the token
            self.credentials.refresh(Request())
            
            # Build YouTube service
            self.youtube = build('youtube', 'v3', credentials=self.credentials)
            
            logger.info("YouTube API client initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize YouTube client", error=str(e))
            self.youtube = None
            self.credentials = None
    
    async def create_post(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Create a community post on YouTube"""
        try:
            text = content.get('text', '')
            media_url = content.get('media_url')
            
            if not self.youtube:
                # Stub mode
                return self._create_stub_response("community_post_created", {
                    "post_id": f"stub_post_{datetime.utcnow().timestamp()}",
                    "text": text,
                    "created_at": datetime.utcnow().isoformat(),
                    "has_media": bool(media_url)
                })
            
            # Create community post
            post_body = {
                'snippet': {
                    'text': text
                }
            }
            
            if media_url:
                # Handle media attachment (simplified)
                post_body['snippet']['media'] = {
                    'url': media_url
                }
            
            response = self.youtube.communityPosts().insert(
                part='snippet',
                body=post_body
            ).execute()
            
            result = {
                "success": True,
                "post_id": response['id'],
                "text": text,
                "created_at": datetime.utcnow().isoformat(),
                "has_media": bool(media_url)
            }
            
            logger.info("YouTube community post created", 
                       post_id=response['id'],
                       text_length=len(text))
            
            return result
            
        except Exception as e:
            logger.error("Failed to create YouTube post", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def upload_video(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """Upload a video to YouTube"""
        try:
            title = video_data.get('title', '')
            description = video_data.get('description', '')
            tags = video_data.get('tags', [])
            video_file = video_data.get('file_path')
            privacy_status = video_data.get('privacy_status', 'private')
            
            if not self.youtube:
                # Stub mode
                return self._create_stub_response("video_uploaded", {
                    "video_id": f"stub_video_{datetime.utcnow().timestamp()}",
                    "title": title,
                    "privacy_status": privacy_status,
                    "uploaded_at": datetime.utcnow().isoformat()
                })
            
            # Video metadata
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': tags,
                    'categoryId': '22'  # People & Blogs
                },
                'status': {
                    'privacyStatus': privacy_status,
                    'selfDeclaredMadeForKids': False
                }
            }
            
            # Upload video (simplified - actual implementation would handle file upload)
            response = self.youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=video_file
            ).execute()
            
            result = {
                "success": True,
                "video_id": response['id'],
                "title": title,
                "privacy_status": privacy_status,
                "uploaded_at": datetime.utcnow().isoformat(),
                "url": f"https://www.youtube.com/watch?v={response['id']}"
            }
            
            logger.info("Video uploaded to YouTube", 
                       video_id=response['id'],
                       title=title)
            
            return result
            
        except Exception as e:
            logger.error("Failed to upload video", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def execute_campaign(self, campaign: Campaign) -> Dict[str, Any]:
        """Execute a campaign on YouTube"""
        try:
            results = []
            
            for post in campaign.posts:
                if post.platform == "youtube" or "youtube" in post.platforms:
                    if post.content_type == "video":
                        result = await self.upload_video({
                            "title": post.title or post.content[:50],
                            "description": post.content,
                            "tags": post.tags,
                            "file_path": post.media_urls[0] if post.media_urls else None,
                            "privacy_status": "public"
                        })
                    else:
                        result = await self.create_post({
                            "text": post.content,
                            "media_url": post.media_urls[0] if post.media_urls else None
                        })
                    
                    results.append(result)
                    
                    # Delay between posts
                    await asyncio.sleep(3)
            
            campaign_result = {
                "success": True,
                "campaign_id": campaign.id,
                "platform": "youtube",
                "posts_created": len([r for r in results if r.get("success")]),
                "posts_failed": len([r for r in results if not r.get("success")]),
                "results": results,
                "executed_at": datetime.utcnow().isoformat()
            }
            
            logger.info("YouTube campaign executed",
                       campaign_id=campaign.id,
                       posts_created=campaign_result["posts_created"],
                       posts_failed=campaign_result["posts_failed"])
            
            return campaign_result
            
        except Exception as e:
            logger.error("Failed to execute YouTube campaign", 
                        campaign_id=campaign.id, 
                        error=str(e))
            return {
                "success": False,
                "campaign_id": campaign.id,
                "platform": "youtube",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific YouTube action"""
        action_type = action.get("type")
        
        if action_type == "community_post":
            return await self.create_post(action.get("data", {}))
        elif action_type == "video_upload":
            return await self.upload_video(action.get("data", {}))
        elif action_type == "like_video":
            return await self.like_video(action.get("video_id"))
        elif action_type == "subscribe":
            return await self.subscribe_to_channel(action.get("channel_id"))
        elif action_type == "comment":
            return await self.add_comment(action.get("video_id"), action.get("text"))
        else:
            return {
                "success": False,
                "error": f"Unknown action type: {action_type}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def like_video(self, video_id: str) -> Dict[str, Any]:
        """Like a video"""
        try:
            if not self.youtube:
                return self._create_stub_response("video_liked", {"video_id": video_id})
            
            self.youtube.videos().rate(
                id=video_id,
                rating='like'
            ).execute()
            
            logger.info("Video liked", video_id=video_id)
            return {
                "success": True,
                "action": "like",
                "video_id": video_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to like video", video_id=video_id, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def subscribe_to_channel(self, channel_id: str) -> Dict[str, Any]:
        """Subscribe to a channel"""
        try:
            if not self.youtube:
                return self._create_stub_response("channel_subscribed", {"channel_id": channel_id})
            
            self.youtube.subscriptions().insert(
                part='snippet',
                body={
                    'snippet': {
                        'resourceId': {
                            'kind': 'youtube#channel',
                            'channelId': channel_id
                        }
                    }
                }
            ).execute()
            
            logger.info("Subscribed to channel", channel_id=channel_id)
            return {
                "success": True,
                "action": "subscribe",
                "channel_id": channel_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to subscribe", channel_id=channel_id, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def add_comment(self, video_id: str, text: str) -> Dict[str, Any]:
        """Add a comment to a video"""
        try:
            if not self.youtube:
                return self._create_stub_response("comment_added", {
                    "video_id": video_id,
                    "text": text
                })
            
            response = self.youtube.commentThreads().insert(
                part='snippet',
                body={
                    'snippet': {
                        'videoId': video_id,
                        'topLevelComment': {
                            'snippet': {
                                'textOriginal': text
                            }
                        }
                    }
                }
            ).execute()
            
            logger.info("Comment added", video_id=video_id, comment_id=response['id'])
            return {
                "success": True,
                "action": "comment",
                "video_id": video_id,
                "comment_id": response['id'],
                "text": text,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to add comment", video_id=video_id, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_analytics(self, video_id: str) -> Dict[str, Any]:
        """Get analytics for a video"""
        try:
            if not self.youtube:
                return self._create_stub_response("analytics_retrieved", {
                    "video_id": video_id,
                    "views": 5420,
                    "likes": 234,
                    "comments": 45,
                    "shares": 12
                })
            
            # Get video statistics
            response = self.youtube.videos().list(
                part='statistics',
                id=video_id
            ).execute()
            
            if not response['items']:
                raise Exception("Video not found")
            
            stats = response['items'][0]['statistics']
            
            result = {
                "success": True,
                "video_id": video_id,
                "views": int(stats.get('viewCount', 0)),
                "likes": int(stats.get('likeCount', 0)),
                "comments": int(stats.get('commentCount', 0)),
                "favorites": int(stats.get('favoriteCount', 0)),
                "retrieved_at": datetime.utcnow().isoformat()
            }
            
            logger.info("Video analytics retrieved", video_id=video_id)
            return result
            
        except Exception as e:
            logger.error("Failed to get analytics", video_id=video_id, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _create_stub_response(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a stub response for testing/demo purposes"""
        return {
            "success": True,
            "stub_mode": True,
            "action": action,
            "platform": "youtube",
            "timestamp": datetime.utcnow().isoformat(),
            **data
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check YouTube API connection health"""
        try:
            if not self.youtube:
                return {
                    "healthy": True,
                    "mode": "stub",
                    "message": "Running in stub mode - no credentials provided"
                }
            
            # Simple API call to check connectivity
            response = self.youtube.channels().list(
                part='snippet',
                mine=True
            ).execute()
            
            if response['items']:
                channel = response['items'][0]
                return {
                    "healthy": True,
                    "mode": "live",
                    "channel_id": channel['id'],
                    "channel_title": channel['snippet']['title'],
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "healthy": False,
                    "error": "No channel found for authenticated user",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
        except Exception as e:
            logger.error("YouTube health check failed", error=str(e))
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
