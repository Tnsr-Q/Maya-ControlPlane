"""
Maya Control Plane Orchestrator

Central orchestration system that routes Maya intents to appropriate adapters and helpers.
Manages the flow of requests between Maya API, social platforms, and AI services.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import yaml
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import structlog

from stubs.maya_stub import call_maya
from stubs.schemas import Campaign, Post, Event
from adapters.twitter_adapter import TwitterAdapter
from adapters.youtube_adapter import YouTubeAdapter
from adapters.tiktok_adapter import TikTokAdapter
# from src.adapters.youtube_adapter_v2 import YouTubeAdapterV2  # Temporarily disabled due to file corruption
from src.maya_cp.helpers.cerebras_helper import CerebrasHelper, create_cerebras_helper, get_model_recommendations
from helpers.webhook_helper import WebhookHelper


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class OrchestrationRequest(BaseModel):
    """Request model for orchestration operations"""
    intent: str
    platform: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    campaign_id: Optional[str] = None
    priority: int = 1
    metadata: Optional[Dict[str, Any]] = None


class OrchestrationResponse(BaseModel):
    """Response model for orchestration operations"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime
    request_id: str


class MayaOrchestrator:
    """
    Central orchestrator for Maya control plane operations.
    
    Routes requests between Maya API, social platforms, and AI services
    based on intent analysis and platform requirements.
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = self._load_config(config_path)
        self.adapters = {}
        self.helpers = {}
        self.app = FastAPI(
            title="Maya Control Plane",
            description="AI-powered social media orchestration system",
            version="0.1.0"
        )
        
        # Initialize components asynchronously
        self._components_initialized = False
        self._setup_routes()
        
        logger.info("Maya Orchestrator initialized", config_loaded=bool(self.config))
    
    async def initialize(self):
        """Initialize components asynchronously"""
        if not self._components_initialized:
            await self._initialize_components()
            self._components_initialized = True
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning("Config file not found, using defaults", path=config_path)
            return {}
        except Exception as e:
            logger.error("Failed to load config", error=str(e))
            return {}
    
    async def _initialize_components(self):
        """Initialize adapters and helpers"""
        try:
            # Initialize platform adapters
            self.adapters['twitter'] = TwitterAdapter(self.config.get('platforms', {}).get('twitter', {}))
            # self.adapters['youtube'] = YouTubeAdapterV2(self.config.get('platforms', {}).get('youtube', {}))  # Temporarily use basic adapter
            self.adapters['youtube'] = YouTubeAdapter(self.config.get('platforms', {}).get('youtube', {}))
            self.adapters['tiktok'] = TikTokAdapter(self.config.get('platforms', {}).get('tiktok', {}))
            
            # Initialize helpers with advanced Cerebras integration
            cerebras_config = self.config.get('ai_services', {}).get('cerebras', {})
            self.helpers['cerebras'] = await create_cerebras_helper(cerebras_config)
            self.helpers['webhook'] = WebhookHelper(self.config.get('webhooks', {}))
            
            # Load Cerebras configuration from dedicated config file
            cerebras_yaml_path = Path("config/cerebras.yaml")
            if cerebras_yaml_path.exists():
                with open(cerebras_yaml_path, 'r') as f:
                    cerebras_full_config = yaml.safe_load(f)
                    # Update helper with full configuration
                    self.helpers['cerebras'].config.update(cerebras_full_config)
                    logger.info("Loaded Cerebras configuration", config_file=str(cerebras_yaml_path))
            
            logger.info("Components initialized successfully", 
                       adapters=len(self.adapters), 
                       helpers=len(self.helpers),
                       cerebras_tools=len(self.helpers['cerebras'].registered_tools))
            
        except Exception as e:
            logger.error("Failed to initialize components", error=str(e))
            raise
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        # Include YouTube routes
        try:
            # from src.orchestrator.routes.youtube import router as youtube_router  # Temporarily disabled due to file corruption
            # self.app.include_router(youtube_router)
            logger.info("YouTube routes temporarily disabled due to file corruption")
        except ImportError as e:
            logger.warning(f"Failed to import YouTube routes: {e}")
        
        # Include Twitter routes if they exist
        try:
            # from src.orchestrator.routes.twitter import router as twitter_router  # Not implemented yet
            # self.app.include_router(twitter_router)
            logger.info("Twitter routes not yet implemented")
        except ImportError:
            logger.info("Twitter routes not found, skipping")
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            await self.initialize()  # Ensure components are initialized
            
            # Check Cerebras health
            cerebras_health = await self.helpers['cerebras'].health_check()
            
            return {
                "status": "healthy", 
                "timestamp": datetime.utcnow(),
                "components": {
                    "cerebras": cerebras_health,
                    "adapters": list(self.adapters.keys()),
                    "helpers": list(self.helpers.keys())
                }
            }
        
        @self.app.post("/orchestrate", response_model=OrchestrationResponse)
        async def orchestrate_request(request: OrchestrationRequest, background_tasks: BackgroundTasks):
            """Main orchestration endpoint"""
            await self.initialize()  # Ensure components are initialized
            return await self.process_request(request, background_tasks)
        
        @self.app.post("/cerebras/generate")
        async def cerebras_generate(request: Dict[str, Any]):
            """Advanced Cerebras text generation endpoint"""
            await self.initialize()
            try:
                from src.maya_cp.helpers.cerebras_helper import GenerationConfig
                
                messages = request.get("messages", [])
                config_data = request.get("config", {})
                stream = request.get("stream", False)
                
                # Create generation config
                config = GenerationConfig(**config_data) if config_data else None
                
                result = await self.helpers['cerebras'].generate_text(messages, config, stream)
                return result
                
            except Exception as e:
                logger.error("Cerebras generation failed", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/cerebras/embeddings")
        async def cerebras_embeddings(request: Dict[str, Any]):
            """Cerebras embeddings generation endpoint"""
            await self.initialize()
            try:
                from src.maya_cp.helpers.cerebras_helper import EmbeddingConfig
                
                texts = request.get("texts", [])
                config_data = request.get("config", {})
                
                # Create embedding config
                config = EmbeddingConfig(**config_data) if config_data else None
                
                result = await self.helpers['cerebras'].generate_embeddings(texts, config)
                return result
                
            except Exception as e:
                logger.error("Cerebras embeddings failed", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/cerebras/tools/execute")
        async def cerebras_execute_tool(request: Dict[str, Any]):
            """Execute Cerebras tool"""
            await self.initialize()
            try:
                tool_name = request.get("tool_name")
                parameters = request.get("parameters", {})
                
                result = await self.helpers['cerebras'].execute_tool(tool_name, parameters)
                return result
                
            except Exception as e:
                logger.error("Cerebras tool execution failed", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/cerebras/models")
        async def get_cerebras_models():
            """Get available Cerebras models with recommendations"""
            await self.initialize()
            try:
                models = await self.helpers['cerebras'].list_models()
                recommendations = get_model_recommendations()
                
                return {
                    "models": models,
                    "recommendations": recommendations
                }
                
            except Exception as e:
                logger.error("Failed to get Cerebras models", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
    
    async def process_request(self, request: OrchestrationRequest, background_tasks: BackgroundTasks) -> OrchestrationResponse:
        """Process orchestration request"""
        request_id = f"req_{datetime.utcnow().timestamp()}"
        
        try:
            logger.info("Processing orchestration request", 
                       intent=request.intent, 
                       platform=request.platform,
                       request_id=request_id)
            
            # Route based on intent and platform
            if request.platform == "twitter":
                result = await self._handle_twitter_request(request)
            elif request.platform == "youtube":
                result = await self._handle_youtube_request(request)
            elif request.platform == "tiktok":
                result = await self._handle_tiktok_request(request)
            else:
                # Multi-platform or general request
                result = await self._handle_general_request(request)
            
            return OrchestrationResponse(
                success=True,
                message="Request processed successfully",
                data=result,
                timestamp=datetime.utcnow(),
                request_id=request_id
            )
            
        except Exception as e:
            logger.error("Request processing failed", 
                        error=str(e), 
                        request_id=request_id)
            
            return OrchestrationResponse(
                success=False,
                message=f"Request failed: {str(e)}",
                data=None,
                timestamp=datetime.utcnow(),
                request_id=request_id
            )
    
    async def _handle_twitter_request(self, request: OrchestrationRequest) -> Dict[str, Any]:
        """Handle Twitter-specific requests"""
        adapter = self.adapters['twitter']
        
        if request.intent == "post":
            return await adapter.create_post(request.content)
        elif request.intent == "analyze":
            return await adapter.analyze_engagement(request.content)
        else:
            raise ValueError(f"Unknown Twitter intent: {request.intent}")
    
    async def _handle_youtube_request(self, request: OrchestrationRequest) -> Dict[str, Any]:
        """Handle YouTube-specific requests"""
        adapter = self.adapters['youtube']
        
        if request.intent == "upload":
            return await adapter.upload_video(request.content)
        elif request.intent == "analyze":
            return await adapter.get_channel_analytics(request.content)
        else:
            raise ValueError(f"Unknown YouTube intent: {request.intent}")
    
    async def _handle_tiktok_request(self, request: OrchestrationRequest) -> Dict[str, Any]:
        """Handle TikTok-specific requests"""
        adapter = self.adapters['tiktok']
        
        if request.intent == "post":
            return await adapter.create_post(request.content)
        elif request.intent == "analyze":
            return await adapter.analyze_performance(request.content)
        else:
            raise ValueError(f"Unknown TikTok intent: {request.intent}")
    
    async def _handle_general_request(self, request: OrchestrationRequest) -> Dict[str, Any]:
        """Handle general or multi-platform requests"""
        if request.intent == "campaign":
            return await self._create_campaign(request.content)
        elif request.intent == "analyze_all":
            return await self._analyze_all_platforms(request.content)
        else:
            raise ValueError(f"Unknown general intent: {request.intent}")
    
    async def _create_campaign(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Create multi-platform campaign"""
        # Implementation for campaign creation
        return {"campaign_id": "camp_123", "status": "created"}
    
    async def _analyze_all_platforms(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance across all platforms"""
        results = {}
        
        for platform, adapter in self.adapters.items():
            try:
                if hasattr(adapter, 'get_analytics'):
                    results[platform] = await adapter.get_analytics()
            except Exception as e:
                logger.error(f"Failed to get {platform} analytics", error=str(e))
                results[platform] = {"error": str(e)}
        
        return results


# Global orchestrator instance
orchestrator = None

def get_orchestrator() -> MayaOrchestrator:
    """Get global orchestrator instance"""
    global orchestrator
    if orchestrator is None:
        orchestrator = MayaOrchestrator()
    return orchestrator


if __name__ == "__main__":
    import uvicorn
    
    app = get_orchestrator().app
    uvicorn.run(app, host="0.0.0.0", port=8000)