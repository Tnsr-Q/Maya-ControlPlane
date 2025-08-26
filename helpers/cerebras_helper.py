"""
Cerebras AI Helper

Integration with Cerebras inference API for advanced AI capabilities.
Handles content generation, analysis, and humanization for Maya control plane.
"""

import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import httpx
import structlog

from hub.logger import get_logger


logger = get_logger("cerebras_helper")


class CerebrasHelper:
    """
    Cerebras AI integration helper for Maya control plane
    
    Features:
    - Content generation and enhancement
    - Text humanization and style adaptation
    - Intent analysis and classification
    - Audio-first content optimization
    - Multi-platform content adaptation
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url', 'https://api.cerebras.ai')
        self.model = config.get('model', 'llama3.1-70b')
        self.timeout = config.get('timeout', 30)
        
        self.client = None
        
        if self.api_key:
            self._initialize_client()
        else:
            logger.warning("Cerebras API key not provided, using stub mode")
    
    def _initialize_client(self):
        """Initialize Cerebras API client"""
        try:
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=self.timeout
            )
            
            logger.info("Cerebras API client initialized successfully", model=self.model)
            
        except Exception as e:
            logger.error("Failed to initialize Cerebras client", error=str(e))
            self.client = None
    
    async def generate_content(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate content using Cerebras AI"""
        try:
            prompt = request.get('prompt', '')
            content_type = request.get('content_type', 'social_post')
            platform = request.get('platform', 'general')
            tone = request.get('tone', 'conversational')
            max_tokens = request.get('max_tokens', 500)
            
            if not self.client:
                # Stub mode
                return self._create_stub_response("content_generated", {
                    "content": f"[STUB] Generated {content_type} for {platform}: {prompt[:50]}...",
                    "content_type": content_type,
                    "platform": platform,
                    "tone": tone,
                    "word_count": 45
                })
            
            # Enhanced prompt with platform-specific instructions
            enhanced_prompt = self._enhance_prompt(prompt, content_type, platform, tone)
            
            response = await self.client.post(
                "/v1/chat/completions",
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": self._get_system_prompt(content_type, platform, tone)
                        },
                        {
                            "role": "user",
                            "content": enhanced_prompt
                        }
                    ],
                    "max_tokens": max_tokens,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "stream": False
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Cerebras API error: {response.text}")
            
            data = response.json()
            generated_content = data['choices'][0]['message']['content']
            
            result = {
                "success": True,
                "content": generated_content,
                "content_type": content_type,
                "platform": platform,
                "tone": tone,
                "word_count": len(generated_content.split()),
                "model": self.model,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            logger.info("Content generated successfully",
                       content_type=content_type,
                       platform=platform,
                       word_count=result["word_count"])
            
            return result
            
        except Exception as e:
            logger.error("Failed to generate content", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _enhance_prompt(self, prompt: str, content_type: str, platform: str, tone: str) -> str:
        """Enhance prompt with context and instructions"""
        enhancements = {
            "social_post": f"Create an engaging {platform} post",
            "thread": f"Create a {platform} thread",
            "video_script": f"Write a video script for {platform}",
            "caption": f"Write a compelling caption for {platform}",
            "bio": f"Create a {platform} bio"
        }
        
        base_instruction = enhancements.get(content_type, f"Create {content_type} content")
        
        return f"{base_instruction} with a {tone} tone. {prompt}"
    
    def _get_system_prompt(self, content_type: str, platform: str, tone: str) -> str:
        """Get system prompt based on content type and platform"""
        return f"""You are Maya, an advanced AI content creator specializing in {platform} content.
        
        Your expertise:
        - Creating {content_type} that resonates with {platform} audiences
        - Using a {tone} tone that feels authentic and human
        - Understanding platform-specific best practices
        - Optimizing for engagement and reach
        - Maintaining brand voice consistency
        
        Always create content that:
        - Sounds natural and conversational
        - Fits the platform's culture and norms
        - Encourages engagement and interaction
        - Is optimized for the target audience
        - Maintains authenticity while being compelling"""
    
    def _create_stub_response(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a stub response for testing/demo purposes"""
        return {
            "success": True,
            "stub_mode": True,
            "action": action,
            "service": "cerebras",
            "timestamp": datetime.utcnow().isoformat(),
            **data
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Cerebras API connection health"""
        try:
            if not self.client:
                return {
                    "healthy": True,
                    "mode": "stub",
                    "message": "Running in stub mode - no API key provided"
                }
            
            # Simple API call to check connectivity
            response = await self.client.post(
                "/v1/chat/completions",
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": "Hello"
                        }
                    ],
                    "max_tokens": 5
                }
            )
            
            if response.status_code == 200:
                return {
                    "healthy": True,
                    "mode": "live",
                    "model": self.model,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "healthy": False,
                    "error": f"API returned status {response.status_code}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
        except Exception as e:
            logger.error("Cerebras health check failed", error=str(e))
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.client:
            await self.client.aclose()