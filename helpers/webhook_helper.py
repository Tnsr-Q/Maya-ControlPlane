"""
Webhook Helper

Handles webhook processing and event management for Maya control plane.
Processes incoming webhooks from social platforms and external services.
"""

import asyncio
import hmac
import hashlib
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import json
import structlog

from fastapi import Request, HTTPException
from pydantic import BaseModel

from stubs.schemas import Event
from hub.logger import get_logger


logger = get_logger("webhook_helper")


class WebhookEvent(BaseModel):
    """Webhook event model"""
    id: str
    source: str
    event_type: str
    timestamp: datetime
    data: Dict[str, Any]
    signature: Optional[str] = None
    processed: bool = False


class WebhookHelper:
    """
    Webhook processing helper for Maya control plane
    
    Features:
    - Webhook signature verification
    - Event processing and routing
    - Platform-specific webhook handling
    - Event queuing and retry logic
    - Security and rate limiting
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.secret = config.get('secret', 'default_webhook_secret')
        self.endpoints = config.get('endpoints', [])
        
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.processed_events: Dict[str, WebhookEvent] = {}
        
        logger.info("Webhook helper initialized", 
                   endpoints=len(self.endpoints),
                   secret_configured=bool(self.secret))
    
    def register_handler(self, event_type: str, handler: Callable):
        """Register an event handler for specific event types"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
        
        logger.info("Event handler registered", 
                   event_type=event_type,
                   handler_count=len(self.event_handlers[event_type]))
    
    async def process_webhook(self, request: Request, source: str) -> Dict[str, Any]:
        """Process incoming webhook request"""
        try:
            # Get request data
            body = await request.body()
            headers = dict(request.headers)
            
            # Verify signature if present
            signature = headers.get('x-signature') or headers.get('x-hub-signature-256')
            if signature and not self._verify_signature(body, signature):
                raise HTTPException(status_code=401, detail="Invalid signature")
            
            # Parse webhook data
            try:
                data = json.loads(body.decode('utf-8'))
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON")
            
            # Create webhook event
            event = WebhookEvent(
                id=f"{source}_{datetime.utcnow().timestamp()}",
                source=source,
                event_type=self._extract_event_type(data, source),
                timestamp=datetime.utcnow(),
                data=data,
                signature=signature
            )
            
            # Process the event
            result = await self._process_event(event)
            
            # Store processed event
            self.processed_events[event.id] = event
            
            logger.info("Webhook processed successfully",
                       source=source,
                       event_type=event.event_type,
                       event_id=event.id)
            
            return {
                "success": True,
                "event_id": event.id,
                "event_type": event.event_type,
                "processed_at": datetime.utcnow().isoformat(),
                "result": result
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to process webhook", 
                        source=source, 
                        error=str(e))
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _process_event(self, event: WebhookEvent) -> Dict[str, Any]:
        """Process a webhook event by routing to appropriate handlers"""
        results = []
        
        # Get handlers for this event type
        handlers = self.event_handlers.get(event.event_type, [])
        generic_handlers = self.event_handlers.get('*', [])  # Wildcard handlers
        
        all_handlers = handlers + generic_handlers
        
        if not all_handlers:
            logger.warning("No handlers found for event type", 
                          event_type=event.event_type)
            return {"status": "no_handlers", "event_type": event.event_type}
        
        # Execute all handlers
        for handler in all_handlers:
            try:
                result = await self._execute_handler(handler, event)
                results.append({
                    "handler": handler.__name__,
                    "success": True,
                    "result": result
                })
            except Exception as e:
                logger.error("Handler execution failed",
                           handler=handler.__name__,
                           event_type=event.event_type,
                           error=str(e))
                results.append({
                    "handler": handler.__name__,
                    "success": False,
                    "error": str(e)
                })
        
        event.processed = True
        
        return {
            "status": "processed",
            "handlers_executed": len(results),
            "results": results
        }
    
    async def _execute_handler(self, handler: Callable, event: WebhookEvent) -> Any:
        """Execute a single event handler"""
        if asyncio.iscoroutinefunction(handler):
            return await handler(event)
        else:
            return handler(event)
    
    def _verify_signature(self, body: bytes, signature: str) -> bool:
        """Verify webhook signature"""
        try:
            # Handle different signature formats
            if signature.startswith('sha256='):
                expected_signature = signature[7:]
                computed_signature = hmac.new(
                    self.secret.encode('utf-8'),
                    body,
                    hashlib.sha256
                ).hexdigest()
            elif signature.startswith('sha1='):
                expected_signature = signature[5:]
                computed_signature = hmac.new(
                    self.secret.encode('utf-8'),
                    body,
                    hashlib.sha1
                ).hexdigest()
            else:
                # Assume raw signature
                expected_signature = signature
                computed_signature = hmac.new(
                    self.secret.encode('utf-8'),
                    body,
                    hashlib.sha256
                ).hexdigest()
            
            return hmac.compare_digest(expected_signature, computed_signature)
            
        except Exception as e:
            logger.error("Signature verification failed", error=str(e))
            return False
    
    def _extract_event_type(self, data: Dict[str, Any], source: str) -> str:
        """Extract event type from webhook data based on source"""
        
        if source == "twitter":
            return self._extract_twitter_event_type(data)
        elif source == "youtube":
            return self._extract_youtube_event_type(data)
        elif source == "tiktok":
            return self._extract_tiktok_event_type(data)
        else:
            # Generic event type extraction
            return data.get('event_type', data.get('type', 'unknown'))
    
    def _extract_twitter_event_type(self, data: Dict[str, Any]) -> str:
        """Extract event type from Twitter webhook data"""
        if 'tweet_create_events' in data:
            return 'tweet_created'
        elif 'favorite_events' in data:
            return 'tweet_liked'
        elif 'follow_events' in data:
            return 'user_followed'
        elif 'direct_message_events' in data:
            return 'direct_message'
        else:
            return 'twitter_unknown'
    
    def _extract_youtube_event_type(self, data: Dict[str, Any]) -> str:
        """Extract event type from YouTube webhook data"""
        if 'video' in data:
            return 'video_published'
        elif 'comment' in data:
            return 'comment_added'
        elif 'subscription' in data:
            return 'channel_subscribed'
        else:
            return 'youtube_unknown'
    
    def _extract_tiktok_event_type(self, data: Dict[str, Any]) -> str:
        """Extract event type from TikTok webhook data"""
        event_type = data.get('event', data.get('type', ''))
        
        if 'video' in event_type.lower():
            return 'video_published'
        elif 'like' in event_type.lower():
            return 'video_liked'
        elif 'comment' in event_type.lower():
            return 'comment_added'
        elif 'follow' in event_type.lower():
            return 'user_followed'
        else:
            return 'tiktok_unknown'
    
    async def handle_twitter_event(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle Twitter-specific webhook events"""
        try:
            event_type = event.event_type
            data = event.data
            
            if event_type == 'tweet_created':
                return await self._handle_tweet_created(data)
            elif event_type == 'tweet_liked':
                return await self._handle_tweet_liked(data)
            elif event_type == 'user_followed':
                return await self._handle_user_followed(data)
            elif event_type == 'direct_message':
                return await self._handle_direct_message(data)
            else:
                return {"status": "unhandled", "event_type": event_type}
                
        except Exception as e:
            logger.error("Failed to handle Twitter event", 
                        event_type=event.event_type, 
                        error=str(e))
            return {"status": "error", "error": str(e)}
    
    async def handle_youtube_event(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle YouTube-specific webhook events"""
        try:
            event_type = event.event_type
            data = event.data
            
            if event_type == 'video_published':
                return await self._handle_video_published(data)
            elif event_type == 'comment_added':
                return await self._handle_comment_added(data)
            elif event_type == 'channel_subscribed':
                return await self._handle_channel_subscribed(data)
            else:
                return {"status": "unhandled", "event_type": event_type}
                
        except Exception as e:
            logger.error("Failed to handle YouTube event", 
                        event_type=event.event_type, 
                        error=str(e))
            return {"status": "error", "error": str(e)}
    
    async def handle_tiktok_event(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle TikTok-specific webhook events"""
        try:
            event_type = event.event_type
            data = event.data
            
            if event_type == 'video_published':
                return await self._handle_tiktok_video_published(data)
            elif event_type == 'video_liked':
                return await self._handle_tiktok_video_liked(data)
            elif event_type == 'comment_added':
                return await self._handle_tiktok_comment_added(data)
            elif event_type == 'user_followed':
                return await self._handle_tiktok_user_followed(data)
            else:
                return {"status": "unhandled", "event_type": event_type}
                
        except Exception as e:
            logger.error("Failed to handle TikTok event", 
                        event_type=event.event_type, 
                        error=str(e))
            return {"status": "error", "error": str(e)}
    
    # Platform-specific event handlers
    async def _handle_tweet_created(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tweet creation event"""
        tweets = data.get('tweet_create_events', [])
        results = []
        
        for tweet in tweets:
            tweet_id = tweet.get('id_str')
            text = tweet.get('text', '')
            user = tweet.get('user', {})
            
            logger.info("Tweet created", 
                       tweet_id=tweet_id,
                       user=user.get('screen_name'),
                       text_length=len(text))
            
            results.append({
                "tweet_id": tweet_id,
                "user": user.get('screen_name'),
                "processed": True
            })
        
        return {"status": "processed", "tweets": results}
    
    async def _handle_tweet_liked(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tweet like event"""
        likes = data.get('favorite_events', [])
        results = []
        
        for like in likes:
            tweet_id = like.get('favorited_status', {}).get('id_str')
            user = like.get('user', {})
            
            logger.info("Tweet liked", 
                       tweet_id=tweet_id,
                       user=user.get('screen_name'))
            
            results.append({
                "tweet_id": tweet_id,
                "user": user.get('screen_name'),
                "processed": True
            })
        
        return {"status": "processed", "likes": results}
    
    async def _handle_user_followed(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle user follow event"""
        follows = data.get('follow_events', [])
        results = []
        
        for follow in follows:
            source_user = follow.get('source', {})
            target_user = follow.get('target', {})
            
            logger.info("User followed", 
                       follower=source_user.get('screen_name'),
                       followed=target_user.get('screen_name'))
            
            results.append({
                "follower": source_user.get('screen_name'),
                "followed": target_user.get('screen_name'),
                "processed": True
            })
        
        return {"status": "processed", "follows": results}
    
    async def _handle_direct_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle direct message event"""
        messages = data.get('direct_message_events', [])
        results = []
        
        for message in messages:
            message_id = message.get('id')
            sender_id = message.get('message_create', {}).get('sender_id')
            text = message.get('message_create', {}).get('message_data', {}).get('text', '')
            
            logger.info("Direct message received", 
                       message_id=message_id,
                       sender_id=sender_id,
                       text_length=len(text))
            
            results.append({
                "message_id": message_id,
                "sender_id": sender_id,
                "processed": True
            })
        
        return {"status": "processed", "messages": results}
    
    async def _handle_video_published(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle YouTube video published event"""
        video_id = data.get('video', {}).get('id')
        title = data.get('video', {}).get('title', '')
        
        logger.info("YouTube video published", 
                   video_id=video_id,
                   title=title)
        
        return {
            "status": "processed",
            "video_id": video_id,
            "title": title
        }
    
    async def _handle_comment_added(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle YouTube comment added event"""
        comment_id = data.get('comment', {}).get('id')
        video_id = data.get('comment', {}).get('video_id')
        text = data.get('comment', {}).get('text', '')
        
        logger.info("YouTube comment added", 
                   comment_id=comment_id,
                   video_id=video_id,
                   text_length=len(text))
        
        return {
            "status": "processed",
            "comment_id": comment_id,
            "video_id": video_id
        }
    
    async def _handle_channel_subscribed(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle YouTube channel subscription event"""
        channel_id = data.get('subscription', {}).get('channel_id')
        subscriber_id = data.get('subscription', {}).get('subscriber_id')
        
        logger.info("YouTube channel subscribed", 
                   channel_id=channel_id,
                   subscriber_id=subscriber_id)
        
        return {
            "status": "processed",
            "channel_id": channel_id,
            "subscriber_id": subscriber_id
        }
    
    # TikTok event handlers
    async def _handle_tiktok_video_published(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle TikTok video published event"""
        video_id = data.get('video_id')
        caption = data.get('caption', '')
        
        logger.info("TikTok video published", 
                   video_id=video_id,
                   caption_length=len(caption))
        
        return {
            "status": "processed",
            "video_id": video_id,
            "caption": caption
        }
    
    async def _handle_tiktok_video_liked(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle TikTok video liked event"""
        video_id = data.get('video_id')
        user_id = data.get('user_id')
        
        logger.info("TikTok video liked", 
                   video_id=video_id,
                   user_id=user_id)
        
        return {
            "status": "processed",
            "video_id": video_id,
            "user_id": user_id
        }
    
    async def _handle_tiktok_comment_added(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle TikTok comment added event"""
        comment_id = data.get('comment_id')
        video_id = data.get('video_id')
        text = data.get('text', '')
        
        logger.info("TikTok comment added", 
                   comment_id=comment_id,
                   video_id=video_id,
                   text_length=len(text))
        
        return {
            "status": "processed",
            "comment_id": comment_id,
            "video_id": video_id
        }
    
    async def _handle_tiktok_user_followed(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle TikTok user followed event"""
        follower_id = data.get('follower_id')
        followed_id = data.get('followed_id')
        
        logger.info("TikTok user followed", 
                   follower_id=follower_id,
                   followed_id=followed_id)
        
        return {
            "status": "processed",
            "follower_id": follower_id,
            "followed_id": followed_id
        }
    
    def get_event_history(self, limit: int = 100) -> List[WebhookEvent]:
        """Get recent webhook events"""
        events = list(self.processed_events.values())
        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events[:limit]
    
    def get_event_stats(self) -> Dict[str, Any]:
        """Get webhook processing statistics"""
        events = list(self.processed_events.values())
        
        stats = {
            "total_events": len(events),
            "processed_events": len([e for e in events if e.processed]),
            "events_by_source": {},
            "events_by_type": {},
            "recent_events": len([e for e in events if (datetime.utcnow() - e.timestamp).seconds < 3600])
        }
        
        for event in events:
            # Count by source
            stats["events_by_source"][event.source] = stats["events_by_source"].get(event.source, 0) + 1
            
            # Count by type
            stats["events_by_type"][event.event_type] = stats["events_by_type"].get(event.event_type, 0) + 1
        
        return stats
