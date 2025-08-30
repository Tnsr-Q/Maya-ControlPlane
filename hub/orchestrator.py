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

# Import new audio-first components
from helpers.config_loader import create_component_configs, validate_audio_system_config
from helpers.assemblyai_helper import create_assemblyai_helper
from helpers.redis_helper import create_redis_helper
from helpers.maya_audio_bridge import create_maya_audio_bridge
from helpers.live_streaming_coordinator import create_live_streaming_coordinator
from helpers.integration_orchestrator import create_integration_orchestrator as create_audio_orchestrator


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
        
        # Audio-first system components
        self.audio_components = {}
        self.audio_orchestrator = None
        
        self.app = FastAPI(
            title="Maya Control Plane",
            description="AI-powered social media orchestration system with audio-first interactions",
            version="0.2.0"
        )
        
        # Initialize components asynchronously
        self._components_initialized = False
        self._audio_system_initialized = False
        self._setup_routes()
        
        logger.info("Maya Orchestrator initialized", config_loaded=bool(self.config))
    
    async def initialize(self):
        """Initialize components asynchronously"""
        if not self._components_initialized:
            await self._initialize_components()
            self._components_initialized = True
        
        if not self._audio_system_initialized:
            await self._initialize_audio_system()
            self._audio_system_initialized = True
    
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
    
    async def _initialize_audio_system(self):
        """Initialize audio-first system components"""
        try:
            logger.info("Initializing audio-first system components...")
            
            # Validate audio system configuration
            if not validate_audio_system_config():
                logger.warning("Audio system configuration validation failed, using default settings")
            
            # Get component configurations
            configs = create_component_configs()
            
            # Initialize audio components
            self.audio_components['assemblyai'] = create_assemblyai_helper(configs['assemblyai'])
            self.audio_components['redis'] = create_redis_helper(configs['redis'])
            self.audio_components['maya_bridge'] = create_maya_audio_bridge(configs['maya_bridge'])
            self.audio_components['live_streaming'] = create_live_streaming_coordinator(configs['live_streaming'])
            
            # Initialize audio orchestrator
            self.audio_orchestrator = create_audio_orchestrator(configs['orchestrator'])
            
            # Set up audio orchestrator with all helpers
            self.audio_orchestrator.set_helpers(
                twitter_adapter=self.adapters.get('twitter'),
                cerebras_helper=self.helpers.get('cerebras'),
                assemblyai_helper=self.audio_components['assemblyai'],
                maya_bridge=self.audio_components['maya_bridge'],
                redis_helper=self.audio_components['redis'],
                live_streaming_coordinator=self.audio_components['live_streaming']
            )
            
            # Set up live streaming coordinator dependencies
            self.audio_components['live_streaming'].set_dependencies(
                assemblyai_helper=self.audio_components['assemblyai'],
                maya_bridge=self.audio_components['maya_bridge'],
                redis_helper=self.audio_components['redis']
            )
            
            logger.info("Audio-first system initialized successfully", 
                       components=len(self.audio_components),
                       orchestrator_ready=bool(self.audio_orchestrator))
            
        except Exception as e:
            logger.error("Failed to initialize audio system", error=str(e))
            # Don't raise - allow orchestrator to work without audio system
            logger.warning("Continuing without audio-first features")
    
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
        
        # Audio-First System Endpoints
        
        @self.app.post("/audio/transcribe")
        async def transcribe_audio(file_path: str, options: Dict[str, Any] = None):
            """Transcribe audio file with AssemblyAI"""
            await self.initialize()
            try:
                if not self.audio_components.get('assemblyai'):
                    raise HTTPException(status_code=503, detail="AssemblyAI not available")
                
                result = await self.audio_components['assemblyai'].transcribe_audio_file(
                    file_path, options or {}
                )
                return result
                
            except Exception as e:
                logger.error("Audio transcription failed", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/audio/realtime/start")
        async def start_realtime_transcription():
            """Start real-time audio transcription"""
            await self.initialize()
            try:
                if not self.audio_components.get('assemblyai'):
                    raise HTTPException(status_code=503, detail="AssemblyAI not available")
                
                def on_transcript(data):
                    logger.info("Real-time transcript", text=data.get('text', '')[:50])
                
                started = await self.audio_components['assemblyai'].start_realtime_transcription(on_transcript)
                return {"started": started, "status": "real-time transcription active"}
                
            except Exception as e:
                logger.error("Failed to start real-time transcription", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/maya/connect")
        async def connect_to_maya(credentials: Dict[str, Any] = None):
            """Connect to Maya via audio bridge"""
            await self.initialize()
            try:
                if not self.audio_components.get('maya_bridge'):
                    raise HTTPException(status_code=503, detail="Maya Audio Bridge not available")
                
                connected = await self.audio_components['maya_bridge'].connect_to_maya(credentials)
                
                if connected:
                    state = await self.audio_components['maya_bridge'].get_maya_interface_state()
                    return {"connected": True, "session_id": state.get('session_id'), "state": state}
                else:
                    return {"connected": False, "error": "Failed to connect to Maya"}
                
            except Exception as e:
                logger.error("Maya connection failed", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/maya/send_message")
        async def send_message_to_maya(message: str, use_tts: bool = True, wait_for_response: bool = True):
            """Send message to Maya with optional TTS"""
            await self.initialize()
            try:
                if not self.audio_components.get('maya_bridge'):
                    raise HTTPException(status_code=503, detail="Maya Audio Bridge not available")
                
                response = await self.audio_components['maya_bridge'].send_message_to_maya(
                    message, use_tts, wait_for_response
                )
                return response
                
            except Exception as e:
                logger.error("Failed to send message to Maya", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/conversation/create")
        async def create_conversation_thread(thread_type: str, title: str, platform_data: Dict[str, Any]):
            """Create conversation thread in Redis"""
            await self.initialize()
            try:
                if not self.audio_components.get('redis'):
                    raise HTTPException(status_code=503, detail="Redis not available")
                
                from helpers.redis_helper import ThreadType
                thread_type_enum = ThreadType(thread_type)
                
                thread = await self.audio_components['redis'].create_thread(
                    thread_type_enum, title, platform_data
                )
                
                return {
                    "thread_id": thread.id,
                    "type": thread.type.value,
                    "title": thread.title,
                    "created_at": thread.created_at.isoformat()
                }
                
            except Exception as e:
                logger.error("Failed to create conversation thread", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/conversation/{thread_id}/message")
        async def add_conversation_message(thread_id: str, role: str, content: str, platform: str, metadata: Dict[str, Any] = None):
            """Add message to conversation thread"""
            await self.initialize()
            try:
                if not self.audio_components.get('redis'):
                    raise HTTPException(status_code=503, detail="Redis not available")
                
                from helpers.redis_helper import MessageRole
                role_enum = MessageRole(role)
                
                message = await self.audio_components['redis'].add_message(
                    thread_id, role_enum, content, platform, metadata or {}
                )
                
                if message:
                    return {
                        "message_id": message.id,
                        "thread_id": message.thread_id,
                        "role": message.role.value,
                        "timestamp": message.timestamp.isoformat()
                    }
                else:
                    raise HTTPException(status_code=404, detail="Thread not found")
                
            except Exception as e:
                logger.error("Failed to add conversation message", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/conversation/{thread_id}/context")
        async def get_conversation_context(thread_id: str, max_messages: int = 10):
            """Get conversation context"""
            await self.initialize()
            try:
                if not self.audio_components.get('redis'):
                    raise HTTPException(status_code=503, detail="Redis not available")
                
                context = await self.audio_components['redis'].get_conversation_context(
                    thread_id, max_messages
                )
                return context
                
            except Exception as e:
                logger.error("Failed to get conversation context", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/stream/start")
        async def start_live_stream(platform: str, config: Dict[str, Any]):
            """Start live stream"""
            await self.initialize()
            try:
                if not self.audio_components.get('live_streaming'):
                    raise HTTPException(status_code=503, detail="Live Streaming not available")
                
                from helpers.live_streaming_coordinator import StreamPlatform
                platform_enum = StreamPlatform(platform)
                
                result = await self.audio_components['live_streaming'].start_stream(
                    platform_enum, config
                )
                return result
                
            except Exception as e:
                logger.error("Failed to start live stream", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/stream/{stream_id}/status")
        async def get_stream_status(stream_id: str):
            """Get live stream status"""
            await self.initialize()
            try:
                if not self.audio_components.get('live_streaming'):
                    raise HTTPException(status_code=503, detail="Live Streaming not available")
                
                status = await self.audio_components['live_streaming'].get_stream_status(stream_id)
                return status
                
            except Exception as e:
                logger.error("Failed to get stream status", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/stream/{stream_id}/highlights")
        async def get_stream_highlights(stream_id: str, time_window: int = 300):
            """Get key moments from live stream"""
            await self.initialize()
            try:
                if not self.audio_components.get('live_streaming'):
                    raise HTTPException(status_code=503, detail="Live Streaming not available")
                
                highlights = await self.audio_components['live_streaming'].identify_key_moments(
                    stream_id, time_window
                )
                return {"highlights": highlights, "count": len(highlights)}
                
            except Exception as e:
                logger.error("Failed to get stream highlights", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/workflow/twitter_mention")
        async def execute_twitter_mention_workflow(mention_data: Dict[str, Any], config: Dict[str, Any] = None):
            """Execute Twitter mention response workflow"""
            await self.initialize()
            try:
                if not self.audio_orchestrator:
                    raise HTTPException(status_code=503, detail="Audio Orchestrator not available")
                
                result = await self.audio_orchestrator.execute_twitter_mention_workflow(
                    mention_data, config or {}
                )
                return result
                
            except Exception as e:
                logger.error("Twitter mention workflow failed", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/workflow/audio_conversation")
        async def execute_audio_conversation_workflow(audio_data: bytes, context: Dict[str, Any] = None):
            """Execute audio conversation workflow"""
            await self.initialize()
            try:
                if not self.audio_orchestrator:
                    raise HTTPException(status_code=503, detail="Audio Orchestrator not available")
                
                result = await self.audio_orchestrator.execute_audio_conversation_workflow(
                    audio_data, context or {}
                )
                return result
                
            except Exception as e:
                logger.error("Audio conversation workflow failed", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/workflow/{workflow_id}/status")
        async def get_workflow_status(workflow_id: str):
            """Get workflow status"""
            await self.initialize()
            try:
                if not self.audio_orchestrator:
                    raise HTTPException(status_code=503, detail="Audio Orchestrator not available")
                
                status = await self.audio_orchestrator.get_workflow_status(workflow_id)
                return status
                
            except Exception as e:
                logger.error("Failed to get workflow status", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/audio/system/health")
        async def audio_system_health():
            """Check audio system health"""
            await self.initialize()
            
            health_status = {
                "audio_system_initialized": self._audio_system_initialized,
                "components": {},
                "orchestrator": bool(self.audio_orchestrator)
            }
            
            # Check each audio component
            for component_name, component in self.audio_components.items():
                try:
                    if hasattr(component, 'health_check'):
                        health = await component.health_check()
                        health_status["components"][component_name] = health
                    else:
                        health_status["components"][component_name] = {"status": "available"}
                except Exception as e:
                    health_status["components"][component_name] = {"status": "error", "error": str(e)}
            
            return health_status
        
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
