# Maya Control Plane Audio-First System

## Overview

The Maya Control Plane Audio-First System is a comprehensive social media management platform that orchestrates AI-powered content creation and interaction through audio-first interfaces. The system bridges technical analysis (Cerebras) with creative decision-making (Maya) using real-time audio processing.

## 🎯 Key Features

### 1. **Audio-First Architecture**
- Real-time speech-to-text transcription via AssemblyAI
- Text-to-speech for Maya interactions
- Audio-based conversation loops
- Live streaming transcription and analysis

### 2. **Twitter Monitoring & Analysis**
- Advanced mention detection and tracking
- Sentiment analysis and priority classification
- Conversation thread management
- Batch processing with intelligent routing

### 3. **Cerebras AI Integration** 
- Twitter-specific sentiment and intent analysis
- Trending topic identification
- Technical data to natural language translation
- Dynamic model selection and optimization

### 4. **Maya Audio Bridge**
- Browser automation for sesame.com interface
- Real-time conversation management
- Context injection and preservation
- Session state management

### 5. **Redis Conversation Threading**
- Multi-level conversation context storage
- Cross-platform thread linking
- TTL-based memory cleanup
- Working memory for AI processing

### 6. **Live Streaming Coordination**
- Multi-platform streaming (Twitter Spaces, YouTube Live)
- Real-time highlight identification
- Clip suggestion generation
- Live transcript delivery to Maya

### 7. **Complete Workflow Orchestration**
- End-to-end Twitter → Cerebras → Maya → Response pipeline
- Audio conversation workflows
- Content creation pipelines
- Cross-platform campaign management

## 🏗️ Architecture

```
Maya Control Plane Audio-First System
├── Core Orchestrator (hub/orchestrator.py)
│   ├── FastAPI web interface
│   ├── Component initialization
│   └── Audio system integration
├── Audio Components (helpers/)
│   ├── AssemblyAI Helper (assemblyai_helper.py)
│   ├── Redis Helper (redis_helper.py)
│   ├── Maya Audio Bridge (maya_audio_bridge.py)
│   ├── Live Streaming Coordinator (live_streaming_coordinator.py)
│   └── Integration Orchestrator (integration_orchestrator.py)
├── Enhanced Adapters (adapters/)
│   ├── Enhanced Twitter Adapter (twitter_adapter.py)
│   └── Enhanced Cerebras Helper (cerebras_helper.py)
├── Configuration System (helpers/config_loader.py)
└── Audio System Config (config/audio_system.yaml)
```

## 🚀 Quick Start

### Development Mode (Stub Mode)

```bash
# Clone the repository
git clone https://github.com/Tnsr-Q/Maya-ControlPlane.git
cd Maya-ControlPlane

# Install dependencies
pip install -r requirements.txt

# Run basic demo
python demo_basic_system.py

# Run comprehensive demo (requires dependencies)
python demo_maya_audio_system.py

# Start the orchestrator
python -m hub.orchestrator
```

### Production Deployment

1. **Set Environment Variables:**
```bash
export ASSEMBLYAI_API_KEY="your_assemblyai_key"
export CEREBRAS_API_KEY="your_cerebras_key" 
export TWITTER_API_KEY="your_twitter_key"
export TWITTER_BEARER_TOKEN="your_twitter_bearer"
export REDIS_URL="redis://localhost:6379"
export USE_STUBS="false"
```

2. **Start the System:**
```bash
python -m hub.orchestrator
```

3. **Access API endpoints at http://localhost:8000**

## 📡 API Endpoints

### Core Audio-First Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/audio/transcribe` | POST | Transcribe audio file |
| `/audio/realtime/start` | POST | Start real-time transcription |
| `/maya/connect` | POST | Connect to Maya via audio bridge |
| `/maya/send_message` | POST | Send message to Maya with TTS |
| `/conversation/create` | POST | Create conversation thread |
| `/conversation/{id}/message` | POST | Add message to thread |
| `/stream/start` | POST | Start live stream |
| `/workflow/twitter_mention` | POST | Execute Twitter mention workflow |
| `/workflow/audio_conversation` | POST | Execute audio conversation workflow |
| `/audio/system/health` | GET | Check audio system health |

### Integration Workflows

#### Twitter Mention Response
```python
POST /workflow/twitter_mention
{
    "mention_data": {
        "id": "123456789",
        "text": "Hey @maya, help me with content!",
        "user": {"username": "user", "followers_count": 5000}
    }
}
```

#### Audio Conversation
```python
POST /workflow/audio_conversation  
{
    "audio_data": "<base64_audio>",
    "context": {"session_id": "abc123", "platform": "maya"}
}
```

## 🔧 Component Configuration

### AssemblyAI Configuration
```yaml
assemblyai:
  api_key: ${ASSEMBLYAI_API_KEY}
  default_options:
    sentiment_analysis: true
    entity_detection: true
    auto_highlights: true
```

### Redis Configuration
```yaml
redis:
  url: ${REDIS_URL:-redis://localhost:6379}
  ttl:
    default: 604800  # 7 days
    working_memory: 3600  # 1 hour
```

### Maya Bridge Configuration
```yaml
maya_bridge:
  sesame_url: ${SESAME_URL:-https://sesame.com}
  browser:
    headless: ${MAYA_HEADLESS:-false}
  conversation:
    timeout: 30  # seconds
```

## 🔄 Workflow Examples

### 1. Twitter Mention Detection & Response

```python
# 1. Twitter mention detected
mention = {
    "id": "123456789",
    "text": "Hey @maya, help me create viral content!",
    "user": {"username": "creator", "verified": True}
}

# 2. Cerebras analyzes sentiment and priority
analysis = await cerebras.analyze_tweet_sentiment(mention["text"])
priority = await cerebras.classify_engagement_priority(mention)

# 3. Context stored in Redis
thread = await redis.create_thread(ThreadType.TWITTER, mention)

# 4. Maya receives audio cue and responds
maya_response = await maya_bridge.send_message_to_maya(
    "High priority mention about viral content", use_tts=True
)

# 5. Response posted to Twitter
twitter_response = await twitter.create_post({
    "text": maya_response["transcription"],
    "in_reply_to_tweet_id": mention["id"]
})
```

### 2. Audio Conversation Loop

```python
# 1. User speaks to Maya
audio_input = capture_audio()

# 2. AssemblyAI transcribes
transcription = await assemblyai.transcribe_audio_file(audio_input)

# 3. Cerebras analyzes intent
intent = await cerebras.analyze_intent(transcription["text"])

# 4. Maya processes and responds via audio
maya_response = await maya_bridge.send_message_to_maya(
    transcription["text"], use_tts=True, wait_for_response=True
)

# 5. Response converted to audio and played
audio_response = await generate_audio_response(maya_response)
```

### 3. Live Streaming Coordination

```python
# 1. Start live stream
stream = await coordinator.start_stream(
    StreamPlatform.TWITTER_SPACES,
    {"topic": "AI Innovation"}
)

# 2. Process real-time audio
def on_transcript(data):
    # Send key insights to Maya
    if data["confidence"] > 0.9:
        maya_bridge.send_message_to_maya(data["text"])

# 3. Identify highlights
highlights = await coordinator.identify_key_moments(stream_id)

# 4. Generate clip suggestions
clips = await coordinator.suggest_clips(stream_id, highlights[0])
```

## 🧪 Development & Testing

### Stub Mode
All components support stub mode for development without API keys:

```python
# Enable stub mode
config = {
    'use_stub': True,
    'api_key': 'demo_key'
}

# Components work with realistic mock data
assemblyai = create_assemblyai_helper(config)
result = await assemblyai.transcribe_audio_file("test.wav")
# Returns mock transcription with realistic structure
```

### Testing
```bash
# Run all tests
pytest tests/

# Run specific component tests
pytest tests/test_assemblyai_helper.py
pytest tests/test_integration_orchestrator.py

# Run with coverage
pytest --cov=helpers --cov=adapters
```

## 📊 Monitoring & Logging

### Health Checks
```bash
# System health
GET /health

# Audio system health  
GET /audio/system/health

# Component-specific health
GET /cerebras/health
```

### Logging
Structured logging with JSON output:
```python
logger.info("Workflow completed", 
           workflow_id="abc123",
           duration_seconds=5.2,
           success=True)
```

### Metrics
- Workflow execution times
- API response latencies  
- Error rates by component
- Audio processing metrics

## 🔐 Security & Privacy

### API Key Management
- Environment variable configuration
- No hardcoded credentials
- Secure Redis connections
- Browser automation sandboxing

### Data Privacy
- Temporary audio file cleanup
- TTL-based conversation expiry
- No permanent audio storage
- Configurable data retention

## 🚀 Production Deployment

### Infrastructure Requirements
- Redis server for conversation storage
- Audio processing capabilities
- WebSocket support for real-time features
- Browser automation environment

### Scalability
- Horizontal scaling via load balancers
- Redis clustering for high availability
- Component-level scaling
- Async processing throughout

### Monitoring
- Health check endpoints
- Structured logging
- Performance metrics
- Error tracking and alerting

## 🔮 Future Enhancements

### Planned Features
- Multi-language support
- Advanced voice cloning
- Video processing integration
- Enhanced analytics dashboard
- Mobile app companion

### Integration Roadmap
- Discord and Slack support
- Instagram and TikTok audio features
- Advanced AI model fine-tuning
- Custom voice synthesis
- Real-time collaboration tools

## 📚 Documentation

- [API Reference](docs/api_reference.md)
- [Configuration Guide](docs/configuration.md)  
- [Development Setup](docs/development.md)
- [Deployment Guide](docs/deployment.md)
- [Troubleshooting](docs/troubleshooting.md)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/audio-enhancement`)
3. Commit changes (`git commit -am 'Add audio enhancement'`)
4. Push to branch (`git push origin feature/audio-enhancement`)
5. Create Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [AssemblyAI](https://www.assemblyai.com/) for speech processing
- [Cerebras](https://cerebras.ai/) for AI infrastructure
- [Maya](https://sesame.com/) for creative AI platform
- Contributors and beta testers

---

**Maya Control Plane Audio-First System** - Bridging technical AI analysis with creative human decision-making through seamless audio interactions. 🎭🤖🎵