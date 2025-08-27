"""Twitter Route Handlers

FastAPI route handlers specifically for Twitter operations
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.config.twitter_settings import TwitterSettings, default_twitter_settings
from adapters.twitter_adapter import TwitterAdapter
from stubs.schemas import Post, Campaign
from hub.logger import get_logger

logger = get_logger("twitter_routes")
router = APIRouter(prefix="/twitter", tags=["twitter"])

# Dependency to get Twitter settings
def get_twitter_settings() -> TwitterSettings:
    return default_twitter_settings

# Dependency to get Twitter adapter (would be injected in real implementation)
async def get_twitter_adapter() -> TwitterAdapter:
    # In real implementation, this would be injected
    config = {}
    return TwitterAdapter(config)

@router.post("/post")
async def create_twitter_post(
    post_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    settings: TwitterSettings = Depends(get_twitter_settings),
    adapter: TwitterAdapter = Depends(get_twitter_adapter)
):
    """Create a single Twitter post"""
    try:
        # Validate content length
        content = post_data.get('content', '')
        if len(content) > settings.content.max_tweet_length:
            raise HTTPException(
                status_code=400, 
                detail=f"Tweet exceeds {settings.content.max_tweet_length} characters"
            )
        
        # Create the post
        result = await adapter.create_post(post_data)
        
        # Log success
        logger.info("Twitter post created", 
                   post_id=result.get('post_id'),
                   content_length=len(content))
        
        # Schedule background analytics tracking
        if result.get('success'):
            background_tasks.add_task(
                track_post_performance,
                result.get('post_id'),
                post_data
            )
        
        return {
            "success": True,
            "data": result,
            "platform": "twitter",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to create Twitter post", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/thread")
async def create_twitter_thread(
    thread_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    settings: TwitterSettings = Depends(get_twitter_settings),
    adapter: TwitterAdapter = Depends(get_twitter_adapter)
):
    """Create a Twitter thread"""
    try:
        tweets = thread_data.get('tweets', [])
        
        # Validate thread length
        if len(tweets) > settings.content.max_thread_length:
            raise HTTPException(
                status_code=400,
                detail=f"Thread exceeds {settings.content.max_thread_length} tweets"
            )
        
        # Validate each tweet length
        for i, tweet in enumerate(tweets):
            if len(tweet) > settings.content.max_tweet_length:
                raise HTTPException(
                    status_code=400,
                    detail=f"Tweet {i+1} exceeds {settings.content.max_tweet_length} characters"
                )
        
        # Create the thread
        result = await adapter.create_thread(thread_data)
        
        logger.info("Twitter thread created",
                   thread_length=len(tweets),
                   thread_id=result.get('thread_id'))
        
        return {
            "success": True,
            "data": result,
            "platform": "twitter",
            "thread_length": len(tweets),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to create Twitter thread", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/campaign")
async def execute_twitter_campaign(
    campaign_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    settings: TwitterSettings = Depends(get_twitter_settings),
    adapter: TwitterAdapter = Depends(get_twitter_adapter)
):
    """Execute a Twitter campaign"""
    try:
        # Create campaign object
        campaign = Campaign(**campaign_data)
        
        # Filter for Twitter posts only
        twitter_posts = [
            post for post in campaign.posts 
            if 'twitter' in post.platforms or post.platform == 'twitter'
        ]
        
        if not twitter_posts:
            raise HTTPException(
                status_code=400,
                detail="No Twitter posts found in campaign"
            )
        
        # Execute campaign
        result = await adapter.execute_campaign(campaign)
        
        logger.info("Twitter campaign executed",
                   campaign_id=campaign.id,
                   posts_count=len(twitter_posts))
        
        return {
            "success": True,
            "data": result,
            "platform": "twitter",
            "campaign_id": campaign.id,
            "posts_processed": len(twitter_posts),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to execute Twitter campaign", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/{post_id}")
async def get_twitter_analytics(
    post_id: str,
    adapter: TwitterAdapter = Depends(get_twitter_adapter)
):
    """Get analytics for a specific Twitter post"""
    try:
        result = await adapter.get_analytics(post_id)
        
        return {
            "success": True,
            "data": result,
            "platform": "twitter",
            "post_id": post_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get Twitter analytics", 
                    post_id=post_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/settings")
async def get_twitter_settings(
    settings: TwitterSettings = Depends(get_twitter_settings)
):
    """Get current Twitter settings and limits"""
    return {
        "success": True,
        "data": {
            "platform_limits": settings.get_platform_limits(),
            "rate_limits": settings.get_rate_limits(),
            "optimal_posting_times": settings.optimization.optimal_posting_times,
            "content_recommendations": {
                "post": settings.get_content_recommendations("post"),
                "thread": settings.get_content_recommendations("thread")
            }
        },
        "platform": "twitter",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/optimize")
async def optimize_twitter_content(
    content_data: Dict[str, Any],
    settings: TwitterSettings = Depends(get_twitter_settings)
):
    """Optimize content for Twitter"""
    try:
        content = content_data.get('content', '')
        content_type = content_data.get('type', 'post')
        
        # Get recommendations
        recommendations = settings.get_content_recommendations(content_type)
        
        # Basic optimization logic
        optimized_content = content
        optimizations_applied = []
        
        # Truncate if too long
        if len(content) > recommendations['max_length']:
            optimized_content = content[:recommendations['max_length']-3] + "..."
            optimizations_applied.append("Content truncated to fit character limit")
        
        # Add hashtag recommendations
        if content_type == 'post' and '#' not in content:
            suggested_hashtags = ["#AI", "#Innovation", "#Technology"]
            optimizations_applied.append("Suggested hashtags added")
        
        return {
            "success": True,
            "data": {
                "original_content": content,
                "optimized_content": optimized_content,
                "optimizations_applied": optimizations_applied,
                "recommendations": recommendations,
                "character_count": len(optimized_content)
            },
            "platform": "twitter",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to optimize Twitter content", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Background task functions
async def track_post_performance(post_id: str, post_data: Dict[str, Any]):
    """Background task to track post performance"""
    try:
        # This would integrate with analytics systems
        logger.info("Tracking post performance", post_id=post_id)
        # Implementation would go here
    except Exception as e:
        logger.error("Failed to track post performance", 
                    post_id=post_id, error=str(e))
