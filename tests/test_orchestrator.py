"""
Tests for Maya Orchestrator

Unit tests for the core orchestration functionality.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from hub.orchestrator import MayaOrchestrator, OrchestrationRequest
from stubs.schemas import Campaign, Post, PlatformType, ContentType


class TestMayaOrchestrator:
    """Test suite for Maya Orchestrator"""
    
    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance for testing"""
        return MayaOrchestrator("config/test_config.yaml")
    
    @pytest.fixture
    def sample_request(self):
        """Create sample orchestration request"""
        return OrchestrationRequest(
            intent="Create a post about AI innovation",
            platform="twitter",
            content={"text": "AI is transforming the world!"},
            priority=5
        )
    
    @pytest.fixture
    def sample_campaign(self):
        """Create sample campaign"""
        campaign = Campaign(
            name="Test Campaign",
            description="Test campaign for unit tests",
            platforms=[PlatformType.TWITTER, PlatformType.YOUTUBE],
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(days=7)
        )
        
        # Add test posts
        post1 = Post(
            title="Test Post 1",
            content="This is a test post for Twitter",
            platforms=[PlatformType.TWITTER],
            hashtags=["test", "ai"]
        )
        
        post2 = Post(
            title="Test Post 2",
            content="This is a test post for YouTube",
            platforms=[PlatformType.YOUTUBE],
            content_type=ContentType.VIDEO
        )
        
        campaign.add_post(post1)
        campaign.add_post(post2)
        
        return campaign
    
    def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initialization"""
        assert orchestrator is not None
        assert orchestrator.adapters is not None
        assert orchestrator.helpers is not None
        assert orchestrator.app is not None
        assert "twitter" in orchestrator.adapters
        assert "youtube" in orchestrator.adapters
        assert "tiktok" in orchestrator.adapters
        assert "cerebras" in orchestrator.helpers
        assert "webhook" in orchestrator.helpers
    
    @pytest.mark.asyncio
    async def test_process_request_success(self, orchestrator, sample_request):
        """Test successful request processing"""
        with patch('stubs.maya_stub.call_maya') as mock_maya:
            mock_maya.return_value = {
                "success": True,
                "intent_type": "social_post",
                "suggested_platform": "twitter",
                "confidence": 0.9
            }
            
            # Mock background tasks
            mock_background_tasks = Mock()
            
            response = await orchestrator.process_request(sample_request, mock_background_tasks)
            
            assert response.success is True
            assert response.data is not None
            assert response.request_id is not None
            assert mock_maya.called
    
    @pytest.mark.asyncio
    async def test_process_request_failure(self, orchestrator):
        """Test request processing failure"""
        with patch('stubs.maya_stub.call_maya') as mock_maya:
            mock_maya.side_effect = Exception("Maya API error")
            
            request = OrchestrationRequest(
                intent="Invalid request",
                content={}
            )
            
            mock_background_tasks = Mock()
            
            response = await orchestrator.process_request(request, mock_background_tasks)
            
            assert response.success is False
            assert "Maya API error" in response.message
    
    @pytest.mark.asyncio
    async def test_route_social_post_intent(self, orchestrator):
        """Test routing of social post intent"""
        maya_response = {
            "intent_type": "social_post",
            "suggested_platform": "twitter"
        }
        
        request = OrchestrationRequest(
            intent="Create a tweet",
            platform="twitter",
            content={"text": "Test tweet"}
        )
        
        with patch.object(orchestrator.adapters['twitter'], 'create_post') as mock_create:
            mock_create.return_value = {"success": True, "post_id": "123"}
            
            result = await orchestrator._route_request(request, maya_response)
            
            assert result is not None
            mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_route_ai_generation_intent(self, orchestrator):
        """Test routing of AI generation intent"""
        maya_response = {
            "intent_type": "ai_generation"
        }
        
        request = OrchestrationRequest(
            intent="Generate content about AI",
            content={"prompt": "AI innovation"}
        )
        
        with patch.object(orchestrator.helpers['cerebras'], 'generate_content') as mock_generate:
            mock_generate.return_value = {"success": True, "content": "Generated content"}
            
            result = await orchestrator._route_request(request, maya_response)
            
            assert result is not None
            mock_generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_campaign(self, orchestrator, sample_campaign):
        """Test campaign execution"""
        with patch.object(orchestrator.adapters['twitter'], 'execute_campaign') as mock_twitter:
            with patch.object(orchestrator.adapters['youtube'], 'execute_campaign') as mock_youtube:
                mock_twitter.return_value = {"success": True, "posts_created": 1}
                mock_youtube.return_value = {"success": True, "posts_created": 1}
                
                results = await orchestrator._execute_campaign(sample_campaign)
                
                assert "twitter" in results
                assert "youtube" in results
                assert results["twitter"]["success"] is True
                assert results["youtube"]["success"] is True
                mock_twitter.assert_called_once()
                mock_youtube.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_campaign_partial_failure(self, orchestrator, sample_campaign):
        """Test campaign execution with partial failure"""
        with patch.object(orchestrator.adapters['twitter'], 'execute_campaign') as mock_twitter:
            with patch.object(orchestrator.adapters['youtube'], 'execute_campaign') as mock_youtube:
                mock_twitter.return_value = {"success": True, "posts_created": 1}
                mock_youtube.side_effect = Exception("YouTube API error")
                
                results = await orchestrator._execute_campaign(sample_campaign)
                
                assert "twitter" in results
                assert "youtube" in results
                assert results["twitter"]["success"] is True
                assert results["youtube"]["success"] is False
                assert "YouTube API error" in results["youtube"]["error"]
    
    @pytest.mark.asyncio
    async def test_handle_campaign_create_operation(self, orchestrator):
        """Test campaign creation operation"""
        maya_response = {
            "operation": "create"
        }
        
        request = OrchestrationRequest(
            intent="Create campaign",
            content={
                "name": "Test Campaign",
                "platforms": ["twitter"],
                "posts": []
            }
        )
        
        with patch.object(orchestrator, '_execute_campaign') as mock_execute:
            mock_execute.return_value = {"success": True}
            
            result = await orchestrator._handle_campaign_operation(request, maya_response)
            
            assert result is not None
            mock_execute.assert_called_once()
    
    def test_load_config_success(self, tmp_path):
        """Test successful config loading"""
        config_file = tmp_path / "test_config.yaml"
        config_content = """
        app:
          host: "0.0.0.0"
          port: 8000
        platforms:
          twitter:
            api_key: "test_key"
        """
        config_file.write_text(config_content)
        
        orchestrator = MayaOrchestrator(str(config_file))
        
        assert orchestrator.config is not None
        assert orchestrator.config["app"]["host"] == "0.0.0.0"
        assert orchestrator.config["platforms"]["twitter"]["api_key"] == "test_key"
    
    def test_load_config_file_not_found(self):
        """Test config loading with missing file"""
        orchestrator = MayaOrchestrator("nonexistent_config.yaml")
        
        # Should not raise exception, should use empty config
        assert orchestrator.config == {}
    
    @pytest.mark.asyncio
    async def test_high_priority_request_background_task(self, orchestrator):
        """Test that high priority requests trigger background tasks"""
        request = OrchestrationRequest(
            intent="Urgent post needed",
            priority=8  # High priority
        )
        
        mock_background_tasks = Mock()
        
        with patch('stubs.maya_stub.call_maya') as mock_maya:
            mock_maya.return_value = {
                "success": True,
                "intent_type": "social_post"
            }
            
            with patch.object(orchestrator, '_route_request') as mock_route:
                mock_route.return_value = {"status": "processed"}
                
                response = await orchestrator.process_request(request, mock_background_tasks)
                
                assert response.success is True
                mock_background_tasks.add_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_route_maya_response_social_action(self, orchestrator):
        """Test routing Maya response for social action"""
        maya_response = {
            "type": "social_action",
            "platform": "twitter",
            "action": {
                "type": "create_post",
                "content": "Test content"
            }
        }
        
        with patch.object(orchestrator.adapters['twitter'], 'execute_action') as mock_execute:
            mock_execute.return_value = {"success": True}
            
            result = await orchestrator._route_maya_response(maya_response)
            
            assert result is not None
            mock_execute.assert_called_once_with(maya_response["action"])
    
    @pytest.mark.asyncio
    async def test_route_maya_response_ai_request(self, orchestrator):
        """Test routing Maya response for AI request"""
        maya_response = {
            "type": "ai_request",
            "request": {
                "type": "generate",
                "prompt": "Generate content"
            }
        }
        
        with patch.object(orchestrator.helpers['cerebras'], 'process_request') as mock_process:
            mock_process.return_value = {"success": True}
            
            result = await orchestrator._route_maya_response(maya_response)
            
            assert result is not None
            mock_process.assert_called_once_with(maya_response["request"])
    
    def test_orchestrator_app_routes(self, orchestrator):
        """Test that FastAPI routes are properly set up"""
        routes = [route.path for route in orchestrator.app.routes]
        
        assert "/health" in routes
        assert "/orchestrate" in routes
        assert "/maya/intent" in routes
        assert "/campaign/create" in routes
    
    @pytest.mark.asyncio
    async def test_log_high_priority_request_background_task(self, orchestrator):
        """Test background task for logging high priority requests"""
        request = OrchestrationRequest(
            intent="High priority request",
            priority=9
        )
        
        result = {"status": "processed"}
        
        # This should not raise an exception
        await orchestrator._log_high_priority_request(request, result)
        
        # Test passes if no exception is raised


@pytest.mark.asyncio
async def test_orchestrator_integration():
    """Integration test for orchestrator with all components"""
    orchestrator = MayaOrchestrator()
    
    # Test health check
    assert orchestrator is not None
    
    # Test that all adapters are initialized
    assert len(orchestrator.adapters) == 3  # twitter, youtube, tiktok
    assert len(orchestrator.helpers) == 2   # cerebras, webhook
    
    # Test basic request processing
    request = OrchestrationRequest(
        intent="Test integration",
        platform="twitter"
    )
    
    mock_background_tasks = Mock()
    
    with patch('stubs.maya_stub.call_maya') as mock_maya:
        mock_maya.return_value = {
            "success": True,
            "intent_type": "social_post",
            "suggested_platform": "twitter"
        }
        
        response = await orchestrator.process_request(request, mock_background_tasks)
        
        assert response.success is True
        assert response.data is not None


if __name__ == "__main__":
    pytest.main([__file__])