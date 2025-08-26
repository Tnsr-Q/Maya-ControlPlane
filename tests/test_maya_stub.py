"""
Tests for Maya API Stub

Unit tests for the Maya API stub implementation.
"""

import pytest
import asyncio
from datetime import datetime

from stubs.maya_stub import (
    call_maya, analyze_intent, create_campaign, generate_content,
    humanize_response, optimize_for_platform, get_recommendations,
    maya_api_stub
)


class TestMayaAPIStub:
    """Test suite for Maya API Stub"""
    
    @pytest.mark.asyncio
    async def test_analyze_intent_social_post(self):
        """Test intent analysis for social post"""
        result = await analyze_intent(
            "I want to create a tweet about AI innovation",
            platform="twitter"
        )
        
        assert result["success"] is True
        assert result["intent_type"] == "social_post"
        assert result["suggested_platform"] == "twitter"
        assert result["confidence"] > 0.8
        assert "suggested_actions" in result
        assert "context_analysis" in result
    
    @pytest.mark.asyncio
    async def test_analyze_intent_campaign_management(self):
        """Test intent analysis for campaign management"""
        result = await analyze_intent(
            "Create a marketing campaign for our new product",
            platform="multi_platform"
        )
        
        assert result["success"] is True
        assert result["intent_type"] == "campaign_management"
        assert "campaign" in result["suggested_actions"][0]
    
    @pytest.mark.asyncio
    async def test_analyze_intent_performance_analysis(self):
        """Test intent analysis for performance analysis"""
        result = await analyze_intent(
            "How are our posts performing this month?",
            platform="analytics"
        )
        
        assert result["success"] is True
        assert result["intent_type"] == "performance_analysis"
        assert result["suggested_platform"] == "analytics"
    
    @pytest.mark.asyncio
    async def test_generate_content_social_post(self):
        """Test content generation for social post"""
        result = await generate_content(
            prompt="Announce our new AI tool",
            content_type="social_post",
            platform="twitter",
            tone="exciting"
        )
        
        assert result["success"] is True
        assert result["content_type"] == "social_post"
        assert result["platform"] == "twitter"
        assert result["tone"] == "exciting"
        assert "metadata" in result
        assert result["metadata"]["word_count"] > 0
        assert len(result["optimization_suggestions"]) > 0
    
    @pytest.mark.asyncio
    async def test_generate_content_thread(self):
        """Test content generation for thread"""
        result = await generate_content(
            prompt="Explain AI benefits",
            content_type="thread",
            platform="twitter",
            tone="educational"
        )
        
        assert result["success"] is True
        assert result["content_type"] == "thread"
        assert isinstance(result["content"], list)
        assert len(result["content"]) == 3  # Thread with 3 parts
    
    @pytest.mark.asyncio
    async def test_generate_content_video_script(self):
        """Test content generation for video script"""
        result = await generate_content(
            prompt="Behind the scenes content",
            content_type="video_script",
            platform="youtube",
            tone="casual"
        )
        
        assert result["success"] is True
        assert result["content_type"] == "video_script"
        assert result["platform"] == "youtube"
        assert "Video script content" in result["content"]
    
    @pytest.mark.asyncio
    async def test_humanize_response(self):
        """Test response humanization"""
        ai_content = "Our artificial intelligence system delivers superior performance metrics."
        
        result = await humanize_response(ai_content, style="conversational")
        
        assert result["success"] is True
        assert result["original_content"] == ai_content
        assert result["humanized_content"] != ai_content
        assert result["style"] == "conversational"
        assert result["humanization_score"] > 8.0
        assert len(result["improvements"]) > 0
        assert result["authenticity_rating"] == "high"
    
    @pytest.mark.asyncio
    async def test_optimize_for_platform_twitter(self):
        """Test platform optimization for Twitter"""
        content = "This is a long piece of content that needs to be optimized for Twitter's character limit and engagement patterns."
        
        result = await optimize_for_platform(content, "twitter")
        
        assert result["success"] is True
        assert result["platform"] == "twitter"
        assert result["original_content"] == content
        assert len(result["optimized_content"]) <= 280  # Twitter character limit
        assert "#Twitter" in result["optimized_content"]
        assert len(result["optimizations_applied"]) > 0
    
    @pytest.mark.asyncio
    async def test_optimize_for_platform_youtube(self):
        """Test platform optimization for YouTube"""
        content = "Check out this amazing content!"
        
        result = await optimize_for_platform(content, "youtube")
        
        assert result["success"] is True
        assert result["platform"] == "youtube"
        assert "LIKE and SUBSCRIBE" in result["optimized_content"]
        assert result["estimated_performance"]["engagement_boost"] == "25%"
    
    @pytest.mark.asyncio
    async def test_create_campaign(self):
        """Test campaign creation"""
        campaign_data = {
            "name": "AI Innovation Campaign",
            "platforms": ["twitter", "youtube", "tiktok"],
            "posts": [
                {"content": "Post 1", "platform": "twitter"},
                {"content": "Post 2", "platform": "youtube"}
            ]
        }
        
        result = await create_campaign(campaign_data)
        
        assert result["success"] is True
        assert result["status"] == "created"
        assert "campaign_id" in result
        assert result["platforms"] == campaign_data["platforms"]
        assert "scheduling" in result
        assert "estimated_metrics" in result
        assert len(result["next_steps"]) > 0
    
    @pytest.mark.asyncio
    async def test_get_recommendations_content(self):
        """Test content recommendations"""
        result = await get_recommendations(
            context={"platform": "twitter", "audience": "tech_enthusiasts"},
            recommendation_type="content"
        )
        
        assert result["success"] is True
        assert result["recommendation_type"] == "content"
        assert len(result["recommendations"]) > 0
        assert result["confidence_score"] > 0.8
        assert "expected_impact" in result
        assert result["priority_level"] == "high"
    
    @pytest.mark.asyncio
    async def test_get_recommendations_scheduling(self):
        """Test scheduling recommendations"""
        result = await get_recommendations(
            context={"timezone": "UTC", "audience_activity": "high"},
            recommendation_type="scheduling"
        )
        
        assert result["success"] is True
        assert result["recommendation_type"] == "scheduling"
        assert any("time" in rec.lower() for rec in result["recommendations"])
        assert result["implementation_timeline"] == "1-2 weeks"
    
    @pytest.mark.asyncio
    async def test_get_recommendations_engagement(self):
        """Test engagement recommendations"""
        result = await get_recommendations(
            context={"current_engagement": 5.2, "target_engagement": 8.0},
            recommendation_type="engagement"
        )
        
        assert result["success"] is True
        assert result["recommendation_type"] == "engagement"
        assert any("respond" in rec.lower() for rec in result["recommendations"])
        assert "engagement_increase" in result["expected_impact"]
    
    @pytest.mark.asyncio
    async def test_call_maya_analyze_performance(self):
        """Test direct Maya API call for performance analysis"""
        result = await call_maya("analyze_performance", {
            "content_id": "test_post_123",
            "platform": "twitter",
            "time_range": "7d"
        })
        
        assert result["success"] is True
        assert result["content_id"] == "test_post_123"
        assert result["platform"] == "twitter"
        assert result["time_range"] == "7d"
        assert "metrics" in result
        assert result["performance_score"] > 0
        assert len(result["insights"]) > 0
    
    @pytest.mark.asyncio
    async def test_call_maya_schedule_content(self):
        """Test direct Maya API call for content scheduling"""
        result = await call_maya("schedule_content", {
            "content": {"text": "Test post", "media": []},
            "platforms": ["twitter", "linkedin"],
            "schedule_time": "2024-01-01T12:00:00Z"
        })
        
        assert result["success"] is True
        assert "scheduled_id" in result
        assert result["platforms"] == ["twitter", "linkedin"]
        assert result["status"] == "scheduled"
        assert "estimated_reach" in result
    
    @pytest.mark.asyncio
    async def test_call_maya_manage_audience(self):
        """Test direct Maya API call for audience management"""
        result = await call_maya("manage_audience", {
            "action": "analyze",
            "platform": "twitter"
        })
        
        assert result["success"] is True
        assert result["action"] == "analyze"
        assert result["platform"] == "twitter"
        assert "audience_data" in result
        assert result["audience_data"]["total_followers"] > 0
        assert len(result["insights"]) > 0
    
    @pytest.mark.asyncio
    async def test_call_maya_unknown_endpoint(self):
        """Test Maya API call with unknown endpoint"""
        result = await call_maya("unknown_endpoint", {"test": "data"})
        
        assert result["success"] is True
        assert result["endpoint"] == "unknown_endpoint"
        assert result["stub_mode"] is True
        assert result["data"]["test"] == "data"
    
    def test_api_stats(self):
        """Test API usage statistics"""
        # Make a few calls to generate stats
        asyncio.run(call_maya("test_endpoint"))
        
        stats = maya_api_stub.get_api_stats()
        
        assert stats["api_version"] == "v1"
        assert stats["base_url"] == "https://api.maya.beta.com"
        assert stats["stub_mode"] is True
        assert stats["total_requests"] > 0
        assert stats["uptime"] == "100%"
    
    @pytest.mark.asyncio
    async def test_processing_time_tracking(self):
        """Test that processing times are tracked"""
        result = await analyze_intent("Test intent")
        
        assert "processing_time_ms" in result
        assert result["processing_time_ms"] > 0
        assert "timestamp" in result
        
        # Verify timestamp format
        timestamp = datetime.fromisoformat(result["timestamp"].replace('Z', '+00:00'))
        assert isinstance(timestamp, datetime)
    
    @pytest.mark.asyncio
    async def test_error_handling_empty_data(self):
        """Test error handling with empty data"""
        result = await generate_content("", content_type="social_post")
        
        assert result["success"] is True  # Stub should handle gracefully
        assert "content" in result
    
    @pytest.mark.asyncio
    async def test_context_awareness(self):
        """Test context awareness in responses"""
        context = {
            "current_trends": ["AI", "innovation"],
            "audience_interests": ["technology", "startups"],
            "brand_voice": "friendly"
        }
        
        result = await analyze_intent(
            "Create content about our tech startup",
            context=context
        )
        
        assert result["success"] is True
        assert result["context_analysis"]["sentiment"] == "positive"
        assert result["context_analysis"]["target_audience"] == "general"