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
from src.adapters.youtube_adapter_v2 import YouTubeAdapterV2
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
            self.adapters['youtube'] = YouTubeAdapterV2(self.config.get('platforms', {}).get('youtube', {}))
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
            from src.orchestrator.routes.youtube import router as youtube_router
            self.app.include_router(youtube_router)
            logger.info("YouTube routes included successfully")
        except ImportError as e:
            logger.warning(f"Failed to import YouTube routes: {e}")
        
        # Include Twitter routes if they exist
        try:
            from src.orchestrator.routes.twitter import router as twitter_router
            self.app.include_router(twitter_router)
            logger.info("Twitter routes included successfully")
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
        
        @self.app.post("/cerebras/fine-tune")
        async def cerebras_fine_tune(request: Dict[str, Any]):
            """Start Cerebras fine-tuning job"""
            await self.initialize()
            try:
                from src.maya_cp.helpers.cerebras_helper import FineTuningConfig
                
                config_data = request.get("config", {})
                dataset_path = request.get("dataset_path")
                
                # Create fine-tuning config
                config = FineTuningConfig(**config_data)
                
                result = await self.helpers['cerebras'].start_fine_tuning(config, dataset_path)
                return result
                
            except Exception as e:
                logger.error("Cerebras fine-tuning failed", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/cerebras/fine-tune/{job_id}")
        async def cerebras_fine_tune_status(job_id: str):
            """Get Cerebras fine-tuning job status"""
            await self.initialize()
            try:
                result = await self.helpers['cerebras'].get_fine_tuning_status(job_id)
                return result
                
            except Exception as e:
                logger.error("Failed to get fine-tuning status", job_id=job_id, error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/cerebras/tools")
        async def cerebras_tools(request: Dict[str, Any]):
            """Cerebras generation with tool calling"""
            await self.initialize()
            try:
                messages = request.get("messages", [])
                tools = request.get("tools")
                config_data = request.get("config", {})
                
                from src.maya_cp.helpers.cerebras_helper import GenerationConfig
                config = GenerationConfig(**config_data) if config_data else None
                
                result = await self.helpers['cerebras'].call_with_tools(messages, tools, config)
                return result
                
            except Exception as e:
                logger.error("Cerebras tool calling failed", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/cerebras/models/recommend/{task_type}")
        async def cerebras_model_recommend(task_type: str):
            """Get Cerebras model recommendations for task type"""
            try:
                recommendations = get_model_recommendations(task_type)
                return recommendations
                
            except Exception as e:
                logger.error("Model recommendation failed", task_type=task_type, error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/cerebras/metrics")
        async def cerebras_metrics(window_minutes: int = 60):
            """Get Cerebras performance metrics"""
            await self.initialize()
            try:
                metrics = self.helpers['cerebras'].get_performance_metrics(window_minutes)
                return metrics
                
            except Exception as e:
                logger.error("Failed to get metrics", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/maya/intent")
        async def process_maya_intent(intent_data: Dict[str, Any]):
            """Process intent from Maya API"""
            try:
                # Call Maya API stub
                maya_response = await call_maya("process_intent", intent_data)
                
                # Route to appropriate handler
                return await self._route_maya_response(maya_response)
                
            except Exception as e:
                logger.error("Failed to process Maya intent", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/campaign/create")
        async def create_campaign(campaign: Campaign):
            """Create a new campaign"""
            try:
                # Process through Maya API
                maya_response = await call_maya("create_campaign", campaign.dict())
                
                # Execute campaign across platforms
                results = await self._execute_campaign(campaign)
                
                return {
                    "campaign_id": campaign.id,
                    "maya_response": maya_response,
                    "platform_results": results
                }
                
            except Exception as e:
                logger.error("Failed to create campaign", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
    
    async def process_request(self, request: OrchestrationRequest, background_tasks: BackgroundTasks) -> OrchestrationResponse:
        """
        Process an orchestration request by routing to appropriate components
        """
        request_id = f"req_{datetime.utcnow().timestamp()}"
        
        try:
            logger.info("Processing orchestration request", 
                       intent=request.intent, 
                       platform=request.platform,
                       request_id=request_id)
            
            # Analyze intent with Maya API
            maya_response = await call_maya("analyze_intent", {
                "intent": request.intent,
                "context": request.content or {},
                "platform": request.platform
            })
            
            # Route based on intent and platform
            result = await self._route_request(request, maya_response)
            
            # Schedule background tasks if needed
            if request.priority > 5:
                background_tasks.add_task(self._log_high_priority_request, request, result)
            
            return OrchestrationResponse(
                success=True,
                message="Request processed successfully",
                data=result,
                timestamp=datetime.utcnow(),
                request_id=request_id
            )
            
        except Exception as e:
            logger.error("Failed to process request", error=str(e), request_id=request_id)
            return OrchestrationResponse(
                success=False,
                message=f"Processing failed: {str(e)}",
                data=None,
                timestamp=datetime.utcnow(),
                request_id=request_id
            )
    
    async def _route_request(self, request: OrchestrationRequest, maya_response: Dict[str, Any]) -> Dict[str, Any]:
        """Route request to appropriate adapter or helper with advanced Cerebras integration"""
        
        intent_type = maya_response.get("intent_type", "unknown")
        target_platform = request.platform or maya_response.get("suggested_platform")
        
        if intent_type == "social_post" and target_platform in self.adapters:
            # Enhanced social media posting with Cerebras optimization
            adapter = self.adapters[target_platform]
            
            # Use Cerebras to optimize content for the platform
            if request.content and request.content.get("content"):
                from src.maya_cp.helpers.cerebras_helper import GenerationConfig
                
                # Get optimal model for social media content
                optimal_model = self.helpers['cerebras'].select_optimal_model(
                    f"Create {target_platform} content", 
                    constraints={"max_latency_ms": 2000}
                )
                
                # Generate optimized content
                messages = [
                    {"role": "system", "content": f"You are an expert {target_platform} content creator."},
                    {"role": "user", "content": f"Optimize this content for {target_platform}: {request.content['content']}"}
                ]
                
                config = GenerationConfig(
                    model=optimal_model,
                    max_tokens=280 if target_platform == "twitter" else 1000,
                    temperature=0.8
                )
                
                cerebras_result = await self.helpers['cerebras'].generate_text(messages, config)
                
                if cerebras_result.get("success"):
                    request.content["content"] = cerebras_result["content"]
                    request.content["ai_optimized"] = True
                    request.content["model_used"] = optimal_model
            
            return await adapter.create_post(request.content)
            
        elif intent_type == "ai_generation":
            # Advanced AI generation with dynamic model selection
            cerebras_helper = self.helpers['cerebras']
            
            # Determine optimal model based on request complexity
            task_description = str(request.content)
            optimal_model = cerebras_helper.select_optimal_model(task_description)
            
            # Use advanced generation with tools if needed
            if request.content.get("use_tools", False):
                messages = [{"role": "user", "content": request.content.get("prompt", "")}]
                tools = request.content.get("tools")
                
                from src.maya_cp.helpers.cerebras_helper import GenerationConfig
                config = GenerationConfig(model=optimal_model)
                
                return await cerebras_helper.call_with_tools(messages, tools, config)
            else:
                # Standard generation with optimal model
                request.content["model"] = optimal_model
                return await cerebras_helper.process_request(request.content)
            
        elif intent_type == "content_analysis":
            # Use Cerebras embeddings for content analysis
            cerebras_helper = self.helpers['cerebras']
            
            content_texts = request.content.get("texts", [])
            if content_texts:
                from src.maya_cp.helpers.cerebras_helper import EmbeddingConfig
                config = EmbeddingConfig(task_type="retrieval_query")
                
                embeddings_result = await cerebras_helper.generate_embeddings(content_texts, config)
                
                return {
                    "status": "analyzed",
                    "embeddings": embeddings_result,
                    "analysis_type": "semantic_similarity"
                }
            
        elif intent_type == "campaign_management":
            # Handle campaign operations with AI assistance
            return await self._handle_campaign_operation(request, maya_response)
            
        elif intent_type == "fine_tuning":
            # Handle fine-tuning requests
            cerebras_helper = self.helpers['cerebras']
            
            from src.maya_cp.helpers.cerebras_helper import FineTuningConfig
            config_data = request.content.get("fine_tuning_config", {})
            config = FineTuningConfig(**config_data)
            
            dataset_path = request.content.get("dataset_path")
            return await cerebras_helper.start_fine_tuning(config, dataset_path)
            
        else:
            # Default handling with intelligent routing
            return {
                "status": "routed",
                "intent_type": intent_type,
                "maya_response": maya_response,
                "suggested_model": get_model_recommendations(intent_type),
                "message": "Request routed but no specific handler found"
            }
    
    async def _route_maya_response(self, maya_response: Dict[str, Any]) -> Dict[str, Any]:
        """Route Maya API response to appropriate handlers"""
        
        response_type = maya_response.get("type", "unknown")
        
        if response_type == "social_action":
            platform = maya_response.get("platform")
            if platform in self.adapters:
                return await self.adapters[platform].execute_action(maya_response.get("action", {}))
        
        elif response_type == "ai_request":
            return await self.helpers['cerebras'].process_request(maya_response.get("request", {}))
        
        return {"status": "processed", "original_response": maya_response}
    
    async def _execute_campaign(self, campaign: Campaign) -> Dict[str, Any]:
        """Execute campaign across multiple platforms"""
        results = {}
        
        for platform in campaign.platforms:
            if platform in self.adapters:
                try:
                    adapter = self.adapters[platform]
                    result = await adapter.execute_campaign(campaign)
                    results[platform] = {"success": True, "data": result}
                except Exception as e:
                    results[platform] = {"success": False, "error": str(e)}
                    logger.error("Campaign execution failed", platform=platform, error=str(e))
        
        return results
    
    async def _handle_campaign_operation(self, request: OrchestrationRequest, maya_response: Dict[str, Any]) -> Dict[str, Any]:
        """Handle campaign-related operations"""
        operation = maya_response.get("operation", "unknown")
        
        if operation == "create":
            # Create new campaign
            campaign_data = request.content or {}
            campaign = Campaign(**campaign_data)
            return await self._execute_campaign(campaign)
            
        elif operation == "update":
            # Update existing campaign
            return {"status": "campaign_updated", "campaign_id": request.campaign_id}
            
        elif operation == "analyze":
            # Analyze campaign performance
            return {"status": "campaign_analyzed", "campaign_id": request.campaign_id}
        
        return {"status": "unknown_operation", "operation": operation}
    
    async def _log_high_priority_request(self, request: OrchestrationRequest, result: Dict[str, Any]):
        """Background task for logging high-priority requests"""
        logger.info("High priority request processed", 
                   intent=request.intent,
                   result_status=result.get("status"),
                   priority=request.priority)
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the orchestrator server"""
        import uvicorn
        
        app_config = self.config.get('app', {})
        host = app_config.get('host', host)
        port = app_config.get('port', port)
        workers = app_config.get('workers', 1)
        
        logger.info("Starting Maya Orchestrator", host=host, port=port, workers=workers)
        
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            workers=workers,
            log_config=None  # Use our structured logging
        )


# Global orchestrator instance
orchestrator = MayaOrchestrator()


if __name__ == "__main__":
    orchestrator.run()
