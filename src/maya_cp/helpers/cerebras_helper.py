"""
Cerebras Helper

Advanced AI integration helper for Cerebras inference API.
Provides text generation, embeddings, and tool execution capabilities.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import structlog

logger = structlog.get_logger("cerebras_helper")


class ModelType(str, Enum):
    """Cerebras model types"""
    LLAMA3_8B = "llama3.1-8b"
    LLAMA3_70B = "llama3.1-70b"
    LLAMA3_8B_INSTRUCT = "llama3.1-8b-instruct"
    LLAMA3_70B_INSTRUCT = "llama3.1-70b-instruct"


@dataclass
class GenerationConfig:
    """Configuration for text generation"""
    model: str = ModelType.LLAMA3_8B_INSTRUCT
    max_tokens: int = 1000
    temperature: float = 0.7
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: Optional[List[str]] = None
    stream: bool = False


@dataclass
class EmbeddingConfig:
    """Configuration for embeddings generation"""
    model: str = "text-embedding-ada-002"
    dimensions: Optional[int] = None


class CerebrasHelper:
    """
    Advanced Cerebras AI integration helper.
    
    Provides comprehensive AI capabilities including text generation,
    embeddings, and tool execution for Maya control plane operations.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Cerebras helper with configuration.
        
        Args:
            config: Cerebras API configuration
        """
        self.config = config or {}  # Handle None config
        self.api_key = self.config.get('api_key')
        self.base_url = self.config.get('base_url', 'https://api.cerebras.ai/v1')
        self.timeout = self.config.get('timeout', 60)
        
        # Tool registry
        self.registered_tools: Dict[str, callable] = {}
        
        # Initialize in stub mode if no API key
        self.stub_mode = not bool(self.api_key)
        
        if self.stub_mode:
            logger.info("Cerebras helper initialized in stub mode - no API key provided")
        else:
            logger.info("Cerebras helper initialized with API key")
        
        # Register default tools
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default AI tools"""
        self.register_tool("content_optimizer", self._optimize_content)
        self.register_tool("sentiment_analyzer", self._analyze_sentiment)
        self.register_tool("hashtag_generator", self._generate_hashtags)
        self.register_tool("engagement_predictor", self._predict_engagement)
    
    def register_tool(self, name: str, func: callable):
        """
        Register a tool for AI-powered execution.
        
        Args:
            name: Tool name
            func: Function to execute
        """
        self.registered_tools[name] = func
        logger.info("Registered Cerebras tool", tool_name=name)
    
    async def generate_text(self, messages: List[Dict[str, str]], config: Optional[GenerationConfig] = None, stream: bool = False) -> Dict[str, Any]:
        """
        Generate text using Cerebras models.
        
        Args:
            messages: List of conversation messages
            config: Generation configuration
            stream: Whether to stream the response
            
        Returns:
            Dict containing generated text and metadata
        """
        if not config:
            config = GenerationConfig()
        
        if self.stub_mode:
            # Return stub response
            user_message = messages[-1].get("content", "") if messages else ""
            stub_response = self._generate_stub_response(user_message)
            
            return {
                "success": True,
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": stub_response
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": len(user_message.split()) * 1.3,  # Rough estimate
                    "completion_tokens": len(stub_response.split()),
                    "total_tokens": len(user_message.split()) * 1.3 + len(stub_response.split())
                },
                "model": config.model,
                "timestamp": datetime.utcnow().isoformat(),
                "note": "Stub response for testing purposes"
            }
        
        # TODO: Implement actual Cerebras API integration
        logger.warning("Cerebras API integration not yet implemented")
        return {
            "success": False,
            "error": "Cerebras API integration not yet implemented",
            "note": "Using stub mode for now"
        }
    
    async def generate_embeddings(self, texts: List[str], config: Optional[EmbeddingConfig] = None) -> Dict[str, Any]:
        """
        Generate embeddings for text inputs.
        
        Args:
            texts: List of texts to embed
            config: Embedding configuration
            
        Returns:
            Dict containing embeddings and metadata
        """
        if not config:
            config = EmbeddingConfig()
        
        if self.stub_mode:
            # Return stub embeddings
            import random
            embeddings = []
            
            for text in texts:
                # Generate deterministic "embeddings" based on text hash
                seed = hash(text) % 1000
                random.seed(seed)
                embedding = [random.uniform(-1, 1) for _ in range(1536)]  # 1536 dimensions like OpenAI
                embeddings.append(embedding)
            
            return {
                "success": True,
                "data": [
                    {"object": "embedding", "embedding": emb, "index": i}
                    for i, emb in enumerate(embeddings)
                ],
                "usage": {
                    "prompt_tokens": sum(len(text.split()) for text in texts),
                    "total_tokens": sum(len(text.split()) for text in texts)
                },
                "model": config.model,
                "timestamp": datetime.utcnow().isoformat(),
                "note": "Stub embeddings for testing purposes"
            }
        
        # TODO: Implement actual embeddings API
        logger.warning("Cerebras embeddings not yet implemented")
        return {
            "success": False,
            "error": "Cerebras embeddings not yet implemented"
        }
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a registered AI tool.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            
        Returns:
            Dict containing tool execution result
        """
        if tool_name not in self.registered_tools:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found",
                "available_tools": list(self.registered_tools.keys())
            }
        
        try:
            tool_func = self.registered_tools[tool_name]
            
            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(parameters)
            else:
                result = tool_func(parameters)
            
            return {
                "success": True,
                "tool": tool_name,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Tool execution failed", tool=tool_name, error=str(e))
            return {
                "success": False,
                "tool": tool_name,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List available Cerebras models.
        
        Returns:
            List of available models
        """
        if self.stub_mode:
            return [
                {
                    "id": ModelType.LLAMA3_8B_INSTRUCT,
                    "object": "model",
                    "created": 1677610602,
                    "owned_by": "cerebras",
                    "description": "Llama 3.1 8B Instruct model"
                },
                {
                    "id": ModelType.LLAMA3_70B_INSTRUCT,
                    "object": "model", 
                    "created": 1677610602,
                    "owned_by": "cerebras",
                    "description": "Llama 3.1 70B Instruct model"
                }
            ]
        
        # TODO: Implement actual models API
        logger.warning("Cerebras models API not yet implemented")
        return []
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check for Cerebras integration.
        
        Returns:
            Dict containing health status
        """
        if self.stub_mode:
            return {
                "healthy": True,
                "mode": "stub",
                "message": "Running in stub mode - no API key provided",
                "tools_registered": len(self.registered_tools),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # TODO: Implement actual health check
        return {
            "healthy": True,
            "mode": "live",
            "message": "API key configured but full integration pending",
            "tools_registered": len(self.registered_tools),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _generate_stub_response(self, prompt: str) -> str:
        """Generate a stub AI response based on the prompt"""
        if "social media" in prompt.lower():
            return "Here's an AI-generated social media strategy that focuses on engagement and authentic connection with your audience."
        elif "content" in prompt.lower():
            return "I've analyzed your content requirements and generated optimized text that should perform well across platforms."
        elif "analyze" in prompt.lower():
            return "Based on my analysis, I can see several key insights and opportunities for improvement in your approach."
        else:
            return f"This is an AI-generated response to your query about: {prompt[:50]}..."
    
    async def _optimize_content(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Tool: Optimize content for social media"""
        content = params.get("content", "")
        platform = params.get("platform", "general")
        
        return {
            "optimized_content": f"Optimized for {platform}: {content[:100]}...",
            "suggestions": [
                "Add more engaging hooks",
                "Include relevant hashtags",
                "Optimize for platform-specific formats"
            ],
            "engagement_score": 0.85
        }
    
    async def _analyze_sentiment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Tool: Analyze sentiment of content"""
        content = params.get("content", "")
        
        # Simple keyword-based sentiment analysis for stub
        positive_words = ["great", "awesome", "love", "amazing", "perfect"]
        negative_words = ["bad", "hate", "terrible", "awful", "worst"]
        
        positive_count = sum(1 for word in positive_words if word in content.lower())
        negative_count = sum(1 for word in negative_words if word in content.lower())
        
        if positive_count > negative_count:
            sentiment = "positive"
            confidence = 0.8
        elif negative_count > positive_count:
            sentiment = "negative"
            confidence = 0.8
        else:
            sentiment = "neutral"
            confidence = 0.6
        
        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "emotions": {
                "joy": positive_count * 0.3,
                "anger": negative_count * 0.3,
                "neutral": 0.4
            }
        }
    
    async def _generate_hashtags(self, params: Dict[str, Any]) -> List[str]:
        """Tool: Generate hashtags for content"""
        content = params.get("content", "")
        platform = params.get("platform", "general")
        count = params.get("count", 5)
        
        # Simple hashtag generation based on keywords
        keywords = content.lower().split()[:10]  # Use first 10 words
        hashtags = []
        
        for word in keywords:
            if len(word) > 3 and word.isalpha():
                hashtags.append(f"#{word}")
        
        # Add platform-specific hashtags
        if platform == "twitter":
            hashtags.extend(["#TwitterChat", "#Engagement"])
        elif platform == "instagram":
            hashtags.extend(["#InstaGood", "#PhotoOfTheDay"])
        elif platform == "tiktok":
            hashtags.extend(["#FYP", "#Viral"])
        
        return hashtags[:count]
    
    async def _predict_engagement(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Tool: Predict engagement for content"""
        content = params.get("content", "")
        platform = params.get("platform", "general")
        
        # Simple engagement prediction based on content length and keywords
        engagement_words = ["question", "tip", "how", "why", "secret", "amazing", "incredible"]
        score = 0.5  # Base score
        
        for word in engagement_words:
            if word in content.lower():
                score += 0.1
        
        # Adjust for content length
        if 50 <= len(content) <= 200:
            score += 0.1
        elif len(content) > 300:
            score -= 0.1
        
        score = min(1.0, max(0.0, score))  # Clamp between 0 and 1
        
        return {
            "engagement_score": score,
            "predicted_likes": int(score * 1000),
            "predicted_shares": int(score * 200),
            "predicted_comments": int(score * 50),
            "confidence": 0.75,
            "factors": {
                "content_quality": score,
                "optimal_length": 50 <= len(content) <= 200,
                "engaging_keywords": sum(1 for word in engagement_words if word in content.lower())
            }
        }


async def create_cerebras_helper(config: Dict[str, Any]) -> CerebrasHelper:
    """
    Factory function to create and initialize Cerebras helper.
    
    Args:
        config: Cerebras configuration
        
    Returns:
        Initialized CerebrasHelper instance
    """
    helper = CerebrasHelper(config)
    await helper.health_check()  # Perform initial health check
    return helper


def get_model_recommendations() -> Dict[str, Any]:
    """
    Get model recommendations for different use cases.
    
    Returns:
        Dict containing model recommendations
    """
    return {
        "content_generation": {
            "model": ModelType.LLAMA3_8B_INSTRUCT,
            "description": "Optimized for generating social media content"
        },
        "analysis": {
            "model": ModelType.LLAMA3_70B_INSTRUCT,
            "description": "Better for complex analysis and reasoning"
        },
        "chat": {
            "model": ModelType.LLAMA3_8B_INSTRUCT,
            "description": "Fast and efficient for conversational tasks"
        },
        "creative_writing": {
            "model": ModelType.LLAMA3_70B_INSTRUCT,
            "description": "Superior creativity and narrative capabilities"
        }
    }