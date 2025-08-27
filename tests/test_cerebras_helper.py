"""
Comprehensive test suite for CerebrasHelper

Tests all major functionality including:
- Text generation (streaming and non-streaming)
- Embeddings generation
- Fine-tuning workflows
- Tool calling integration
- Dynamic API selection
- Performance optimization
- Error handling and retry logic
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

# Import the CerebrasHelper and related classes
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from maya_cp.helpers.cerebras_helper import (
    CerebrasHelper,
    CerebrasModel,
    TaskComplexity,
    GenerationConfig,
    EmbeddingConfig,
    FineTuningConfig,
    create_cerebras_helper,
    get_model_recommendations
)


class TestCerebrasHelper:
    """Test suite for CerebrasHelper class"""
    
    @pytest.fixture
    def config(self):
        """Test configuration"""
        return {
            "api_key": "test_api_key",
            "base_url": "https://api.cerebras.ai",
            "model": "llama3.1-70b",
            "timeout": 30,
            "max_retries": 2,
            "precision_mode": "fp16",
            "enable_streaming": True,
            "enable_caching": True
        }
    
    @pytest.fixture
    def helper(self, config):
        """Create CerebrasHelper instance for testing"""
        return CerebrasHelper(config)
    
    @pytest.fixture
    def stub_helper(self):
        """Create CerebrasHelper instance without API key (stub mode)"""
        return CerebrasHelper({})
    
    def test_initialization_with_api_key(self, helper):
        """Test proper initialization with API key"""
        assert helper.api_key == "test_api_key"
        assert helper.base_url == "https://api.cerebras.ai"
        assert helper.default_model == "llama3.1-70b"
        assert helper.enable_streaming is True
        assert helper.enable_caching is True
    
    def test_initialization_stub_mode(self, stub_helper):
        """Test initialization in stub mode"""
        assert stub_helper.api_key is None
        assert stub_helper.client is None
        assert stub_helper.async_client is None
    
    @pytest.mark.asyncio
    async def test_generate_text_stub_mode(self, stub_helper):
        """Test text generation in stub mode"""
        messages = [{"role": "user", "content": "Hello, world!"}]
        task = stub_helper.generate_text(messages)
        result = await task
        
        assert result["success"] is True
        assert result["stub_mode"] is True
        assert "content" in result
        assert result["model"] == "llama3.1-70b"
    
    @pytest.mark.asyncio
    async def test_generate_text_with_config(self, stub_helper):
        """Test text generation with custom configuration"""
        messages = [{"role": "user", "content": "Test message"}]
        config = GenerationConfig(
            model="llama3.1-8b",
            max_tokens=100,
            temperature=0.5,
            stream=False
        )
        
        task = stub_helper.generate_text(messages, config)
        result = await task
        
        assert result["success"] is True
        assert result["model"] == "llama3.1-8b"
    
    @pytest.mark.asyncio
    async def test_streaming_generation_stub_mode(self, stub_helper):
        """Test streaming text generation in stub mode"""
        messages = [{"role": "user", "content": "Stream this"}]
        
        chunks = []
        stream_generator = stub_helper.generate_text(messages, stream=True)
        async for chunk in stream_generator:
            chunks.append(chunk)
        
        assert len(chunks) == 5  # Stub mode generates 5 chunks
        assert all(chunk["success"] for chunk in chunks)
        assert chunks[-1]["is_final"] is True
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_stub_mode(self, stub_helper):
        """Test embeddings generation in stub mode"""
        texts = ["Hello world", "Test embedding"]
        result = await stub_helper.generate_embeddings(texts)
        
        assert result["success"] is True
        assert result["stub_mode"] is True
        assert len(result["embeddings"]) == 2
        assert result["count"] == 2
        assert result["dimensions"] == 1024
    
    @pytest.mark.asyncio
    async def test_start_fine_tuning_stub_mode(self, stub_helper):
        """Test fine-tuning job creation in stub mode"""
        config = FineTuningConfig(
            base_model="llama3.1-8b",
            dataset_path="/path/to/dataset.jsonl",
            method="instruction_tuning",
            epochs=3
        )
        
        result = await stub_helper.start_fine_tuning(config)
        
        assert result["success"] is True
        assert result["stub_mode"] is True
        assert "job_id" in result
        assert result["base_model"] == "llama3.1-8b"
        assert result["method"] == "instruction_tuning"
    
    def test_tool_registration(self, helper):
        """Test tool registration functionality"""
        def test_function(param1: str, param2: int) -> dict:
            return {"result": f"{param1}_{param2}"}
        
        helper.register_tool(
            "test_tool",
            test_function,
            "A test tool",
            {
                "type": "object",
                "properties": {
                    "param1": {"type": "string"},
                    "param2": {"type": "integer"}
                }
            }
        )
        
        assert "test_tool" in helper.registered_tools
        assert helper.registered_tools["test_tool"]["function"] == test_function
    
    @pytest.mark.asyncio
    async def test_call_with_tools_stub_mode(self, stub_helper):
        """Test tool calling in stub mode"""
        # Register a test tool
        stub_helper.register_tool(
            "test_tool",
            lambda x: {"result": x},
            "Test tool",
            {"type": "object", "properties": {"x": {"type": "string"}}}
        )
        
        messages = [{"role": "user", "content": "Use the test tool"}]
        result = await stub_helper.call_with_tools(messages, tools=["test_tool"])
        
        assert result["success"] is True
        assert "content" in result
        assert "tool_calls" in result
    
    @pytest.mark.asyncio
    async def test_health_check_stub_mode(self, stub_helper):
        """Test health check in stub mode"""
        result = await stub_helper.health_check()
        
        assert result["healthy"] is True
        assert result["mode"] == "stub"
        assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_social_media_content_generation(self, stub_helper):
        """Test social media content generation workflow"""
        messages = [
            {"role": "system", "content": "You are a social media content creator"},
            {"role": "user", "content": "Create a Twitter post about AI innovation"}
        ]
        
        config = GenerationConfig(
            model="llama3.1-70b",
            max_tokens=280,  # Twitter limit
            temperature=0.8
        )
        
        task = stub_helper.generate_text(messages, config)
        result = await task
        
        assert result["success"] is True
        assert "content" in result


class TestUtilityFunctions:
    """Test utility functions"""
    
    @pytest.mark.asyncio
    async def test_create_cerebras_helper(self):
        """Test factory function for creating CerebrasHelper"""
        config = {"api_key": "test_key"}
        helper = await create_cerebras_helper(config)
        
        assert isinstance(helper, CerebrasHelper)
        assert helper.api_key == "test_key"
    
    def test_get_model_recommendations(self):
        """Test model recommendation function"""
        # Test social media recommendation
        rec = get_model_recommendations("social_media")
        assert rec["task_type"] == "social_media"
        assert len(rec["alternatives"]) > 0
        
        # Test reasoning recommendation
        rec = get_model_recommendations("reasoning")
        assert rec["task_type"] == "reasoning"
        
        # Test unknown task type
        rec = get_model_recommendations("unknown_task")
        assert "recommended" in rec  # Default recommendation


class TestErrorHandling:
    """Test error handling scenarios"""
    
    @pytest.fixture
    def config(self):
        """Test configuration for error handling"""
        return {
            "api_key": "test_api_key",
            "base_url": "https://api.cerebras.ai",
            "model": "llama3.1-70b",
            "timeout": 30,
            "max_retries": 2
        }
    
    @pytest.fixture
    def helper_with_mock_client(self, config):
        """Create helper with mocked client for error testing"""
        helper = CerebrasHelper(config)
        helper.async_client = AsyncMock()
        return helper
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, helper_with_mock_client):
        """Test handling of API errors"""
        # Mock API error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        helper_with_mock_client.async_client.request.return_value = mock_response
        
        messages = [{"role": "user", "content": "Test"}]
        task = helper_with_mock_client.generate_text(messages)
        result = await task
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_network_error_handling(self, helper_with_mock_client):
        """Test handling of network errors"""
        # Mock network error
        helper_with_mock_client.async_client.request.side_effect = Exception("Network error")
        
        messages = [{"role": "user", "content": "Test"}]
        task = helper_with_mock_client.generate_text(messages)
        result = await task
        
        assert result["success"] is False
        assert "Network error" in result["error"]


class TestIntegrationScenarios:
    """Test integration scenarios for Maya-ControlPlane"""
    
    @pytest.fixture
    def stub_helper(self):
        """Create CerebrasHelper instance without API key (stub mode)"""
        return CerebrasHelper({})
    
    @pytest.mark.asyncio
    async def test_content_analysis_workflow(self, stub_helper):
        """Test content analysis workflow"""
        # Generate embeddings for content similarity
        contents = [
            "AI is transforming social media",
            "Machine learning revolutionizes content creation",
            "Today's weather is sunny"
        ]
        
        result = await stub_helper.generate_embeddings(contents)
        
        assert result["success"] is True
        assert len(result["embeddings"]) == 3
    
    @pytest.mark.asyncio
    async def test_multi_platform_adaptation(self, stub_helper):
        """Test multi-platform content adaptation"""
        # Generate content for Twitter
        twitter_messages = [
            {"role": "user", "content": "Create a Twitter post about new AI features"}
        ]
        twitter_config = GenerationConfig(max_tokens=280, temperature=0.7)
        twitter_task = stub_helper.generate_text(twitter_messages, twitter_config)
        twitter_result = await twitter_task
        
        # Generate content for LinkedIn
        linkedin_messages = [
            {"role": "user", "content": "Create a LinkedIn post about new AI features"}
        ]
        linkedin_config = GenerationConfig(max_tokens=1000, temperature=0.6)
        linkedin_task = stub_helper.generate_text(linkedin_messages, linkedin_config)
        linkedin_result = await linkedin_task
        
        assert twitter_result["success"] is True
        assert linkedin_result["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])