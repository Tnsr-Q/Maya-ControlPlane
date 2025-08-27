"""YouTube Route Handlers

FastAPI route handlers specifically for YouTube operations
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Dict, Any, List, Optional
from datetime import datetime

from adapters.youtube_adapter import YouTubeAdapter
from stubs.schemas import Campaign
from hub.logger import get_logger

logger = get_logger("youtube_routes")
router = APIRouter(prefix="/youtube", tags=["youtube"])

# Dependency to get YouTube adapter
async def get_youtube_adapter() -> YouTubeAdapter:
    # In real implementation, this would be injected
    config = {}
    return YouTubeAdapter(config)

@router.post("/upload")
async def upload_youtube_video(
    video_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    adapter: YouTubeAdapter = Depends(get_youtube_adapter)
):
    """Upload a video to YouTube"""
    try:
        # Validate required fields
        required_fields = ['title', 'description']
        for field in required_fields:
            if field not in video_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required field: {field}"
                )
        
        # Upload video
        result = await adapter.upload_video(video_data)
        
        logger.info("YouTube video uploaded",
                   video_id=result.get('video_id'),
                   title=video_data.get('title'))
        
        # Schedule background tasks
        if result.get('success'):
            background_tasks.add_task(
                track_video_performance,
                result.get('video_id'),
                video_data
            )
        
        return {
            "success": True,
            "data": result,
            "platform": "youtube",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to upload YouTube video", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/community-post")
async def create_youtube_community_post(
    post_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    adapter: YouTubeAdapter = Depends(get_youtube_adapter)
):
    """Create a YouTube community post"""
    try:
        result = await adapter.create_post(post_data)
        
        logger.info("YouTube community post created",
                   post_id=result.get('post_id'))
        
        return {
            "success": True,
            "data": result,
            "platform": "youtube",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to create YouTube community post", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/campaign")
async def execute_youtube_campaign(
    campaign_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    adapter: YouTubeAdapter = Depends(get_youtube_adapter)
):
    """Execute a YouTube campaign"""
    try:
        campaign = Campaign(**campaign_data)
        
        # Filter for YouTube content
        youtube_posts = [
            post for post in campaign.posts
            if 'youtube' in post.platforms or post.platform == 'youtube'
        ]
        
        if not youtube_posts:
            raise HTTPException(
                status_code=400,
                detail="No YouTube content found in campaign"
            )
        
        result = await adapter.execute_campaign(campaign)
        
        logger.info("YouTube campaign executed",
                   campaign_id=campaign.id,
                   content_count=len(youtube_posts))
        
        return {
            "success": True,
            "data": result,
            "platform": "youtube",
            "campaign_id": campaign.id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to execute YouTube campaign", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/{video_id}")
async def get_youtube_analytics(
    video_id: str,
    adapter: YouTubeAdapter = Depends(get_youtube_adapter)
):
    """Get analytics for a YouTube video"""
    try:
        result = await adapter.get_analytics(video_id)
        
        return {
            "success": True,
            "data": result,
            "platform": "youtube",
            "video_id": video_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get YouTube analytics",
                    video_id=video_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def youtube_health_check(
    adapter: YouTubeAdapter = Depends(get_youtube_adapter)
):
    """Check YouTube API health"""
    try:
        result = await adapter.health_check()
        
        return {
            "success": True,
            "data": result,
            "platform": "youtube",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("YouTube health check failed", error=str(e))
        return {
            "success": False,
            "error": str(e),
            "platform": "youtube",
            "timestamp": datetime.utcnow().isoformat()
        }

# Background task functions
async def track_video_performance(video_id: str, video_data: Dict[str, Any]):
    """Background task to track video performance"""
    try:
        logger.info("Tracking video performance", video_id=video_id)
        # Implementation would go here
    except Exception as e:
        logger.error("Failed to track video performance",
                    video_id=video_id, error=str(e))
