"""
Maya Control Plane Audio-First System Demo

Comprehensive demonstration of the complete audio-first social media management system.
Shows integration between Twitter monitoring, Cerebras analysis, AssemblyAI audio processing,
Maya audio bridge, Redis conversation threading, and live streaming coordination.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("maya_audio_demo")

# Import all the helpers we've created
from helpers.assemblyai_helper import create_assemblyai_helper
from helpers.redis_helper import create_redis_helper, ThreadType, MessageRole
from helpers.maya_audio_bridge import create_maya_audio_bridge
from helpers.live_streaming_coordinator import create_live_streaming_coordinator, StreamPlatform
from helpers.integration_orchestrator import create_integration_orchestrator, WorkflowType
from helpers.cerebras_helper import CerebrasHelper
from adapters.twitter_adapter import TwitterAdapter


async def demo_audio_transcription():
    """Demo AssemblyAI audio transcription capabilities"""
    print("\n🎤 Demo: AssemblyAI Audio Transcription")
    print("=" * 50)
    
    # Create AssemblyAI helper in stub mode
    assemblyai_helper = create_assemblyai_helper({
        'use_stub': True,
        'api_key': 'demo_key'
    })
    
    # Demo 1: File transcription
    print("\n1. Audio File Transcription:")
    result = await assemblyai_helper.transcribe_audio_file(
        "sample_audio.wav",
        {
            'sentiment_analysis': True,
            'entity_detection': True,
            'auto_highlights': True
        }
    )
    
    print(f"✅ Transcription: {result['transcription']['text'][:100]}...")
    print(f"📊 Confidence: {result['transcription']['confidence']}")
    print(f"😊 Sentiment: {result['transcription']['sentiment_analysis_results'][0]['sentiment']}")
    print(f"🏷️ Entities: {len(result['transcription']['entities'])} detected")
    
    # Demo 2: Real-time transcription
    print("\n2. Real-time Audio Transcription:")
    
    transcript_count = 0
    
    def on_transcript(transcript_data):
        nonlocal transcript_count
        transcript_count += 1
        status = "Final" if transcript_data['is_final'] else "Partial"
        print(f"📝 {status}: {transcript_data['text']}")
        
        if transcript_count >= 10:  # Stop after 10 transcripts
            asyncio.create_task(assemblyai_helper.stop_realtime_transcription())
    
    started = await assemblyai_helper.start_realtime_transcription(on_transcript)
    print(f"🔄 Real-time transcription started: {started}")
    
    # Wait for simulated transcription
    await asyncio.sleep(15)
    
    print("\n✅ Audio transcription demo completed!")


async def demo_redis_conversation_threading():
    """Demo Redis conversation threading and context management"""
    print("\n🧵 Demo: Redis Conversation Threading")
    print("=" * 50)
    
    # Create Redis helper in stub mode
    redis_helper = create_redis_helper({
        'use_stub': True,
        'default_ttl': 3600
    })
    
    # Demo 1: Create conversation thread
    print("\n1. Creating Twitter conversation thread:")
    thread = await redis_helper.create_thread(
        ThreadType.TWITTER,
        "Discussion about AI in social media",
        {
            'tweet_id': '123456789',
            'user_id': 'tech_enthusiast',
            'platform': 'twitter'
        },
        ['tech_enthusiast', 'maya']
    )
    
    print(f"✅ Thread created: {thread.id}")
    print(f"📝 Title: {thread.title}")
    
    # Demo 2: Add messages to thread
    print("\n2. Adding messages to conversation:")
    
    # User message
    user_message = await redis_helper.add_message(
        thread.id,
        MessageRole.USER,
        "How can AI improve social media engagement?",
        'twitter',
        {'tweet_id': '123456789'}
    )
    print(f"👤 User message added: {user_message.id}")
    
    # Cerebras analysis
    cerebras_message = await redis_helper.add_message(
        thread.id,
        MessageRole.CEREBRAS,
        "Analysis: This is a question about AI applications with positive sentiment. Priority: medium.",
        'cerebras_analysis',
        {'analysis_type': 'intent_and_sentiment'}
    )
    print(f"🧠 Cerebras analysis added: {cerebras_message.id}")
    
    # Maya response
    maya_message = await redis_helper.add_message(
        thread.id,
        MessageRole.MAYA,
        "AI can improve engagement through personalized content, optimal timing, and sentiment-aware responses!",
        'maya_audio',
        {'audio_duration': 5.2, 'confidence': 0.92}
    )
    print(f"🎭 Maya response added: {maya_message.id}")
    
    # Demo 3: Get conversation context
    print("\n3. Retrieving conversation context:")
    context = await redis_helper.get_conversation_context(thread.id)
    print(f"📊 Context retrieved: {context['message_count']} messages")
    print(f"👥 Participants: {', '.join(context['participants'])}")
    
    # Demo 4: Working memory
    print("\n4. Working memory management:")
    await redis_helper.set_working_memory(
        'current_analysis',
        {
            'user_intent': 'learning',
            'sentiment': 'curious',
            'priority': 'medium'
        }
    )
    
    memory_data = await redis_helper.get_working_memory('current_analysis')
    print(f"🧠 Working memory: {memory_data}")
    
    print("\n✅ Redis conversation threading demo completed!")


async def demo_maya_audio_bridge():
    """Demo Maya audio bridge and browser automation"""
    print("\n🌉 Demo: Maya Audio Bridge")
    print("=" * 50)
    
    # Create Maya audio bridge in stub mode
    maya_bridge = create_maya_audio_bridge({
        'use_stub': True,
        'sesame_url': 'https://sesame.com',
        'headless': True
    })
    
    # Demo 1: Connect to Maya
    print("\n1. Connecting to Maya interface:")
    connected = await maya_bridge.connect_to_maya()
    print(f"✅ Connected to Maya: {connected}")
    print(f"🆔 Session ID: {maya_bridge.session_id}")
    
    # Demo 2: Send message to Maya
    print("\n2. Sending message to Maya:")
    message = "Hi Maya! I need you to create a social media post about AI innovation."
    
    response = await maya_bridge.send_message_to_maya(
        message,
        use_tts=True,
        wait_for_response=True
    )
    
    print(f"📤 Message sent: {message[:50]}...")
    print(f"📥 Maya responded: {response['maya_response']['transcription'][:50]}...")
    print(f"⏱️ Response time: {response['maya_response']['duration']} seconds")
    
    # Demo 3: Conversation context injection
    print("\n3. Injecting conversation context:")
    context = {
        'platform': 'twitter',
        'audience': 'tech professionals',
        'tone': 'professional yet engaging',
        'goal': 'increase engagement'
    }
    
    injected = await maya_bridge.inject_conversation_context(context)
    print(f"✅ Context injected: {injected}")
    
    # Demo 4: Start conversation loop
    print("\n4. Starting conversation loop:")
    
    response_count = 0
    
    def on_maya_response(response_data):
        nonlocal response_count
        response_count += 1
        print(f"🎭 Maya response {response_count}: {response_data.get('transcription', '')[:50]}...")
        
        if response_count >= 3:  # Stop after 3 responses
            asyncio.create_task(maya_bridge.stop_conversation_loop())
    
    loop_started = await maya_bridge.start_conversation_loop(on_maya_response)
    print(f"🔄 Conversation loop started: {loop_started}")
    
    # Wait for simulated responses
    await asyncio.sleep(20)
    
    print("\n✅ Maya audio bridge demo completed!")


async def demo_live_streaming_coordination():
    """Demo live streaming coordination with real-time processing"""
    print("\n📺 Demo: Live Streaming Coordination")
    print("=" * 50)
    
    # Create live streaming coordinator in stub mode
    coordinator = create_live_streaming_coordinator({
        'use_stub': True,
        'max_concurrent_streams': 3
    })
    
    # Demo 1: Start Twitter Spaces stream
    print("\n1. Starting Twitter Spaces stream:")
    
    transcript_count = 0
    highlight_count = 0
    
    def on_transcript(data):
        nonlocal transcript_count
        transcript_count += 1
        print(f"📝 Live transcript {transcript_count}: {data.get('transcript', {}).get('text', '')[:50]}...")
    
    def on_highlight(data):
        nonlocal highlight_count
        highlight_count += 1
        print(f"⭐ Highlight {highlight_count}: {data.get('highlight', {}).get('text', '')[:50]}...")
    
    stream_result = await coordinator.start_stream(
        StreamPlatform.TWITTER_SPACES,
        {
            'host_user': 'maya',
            'topic': 'AI and Social Media Innovation',
            'audience_size': 'medium'
        },
        on_transcript=on_transcript,
        on_highlight=on_highlight
    )
    
    print(f"✅ Stream started: {stream_result['stream_id']}")
    print(f"📊 Platform: {stream_result['platform']}")
    
    # Demo 2: Process live audio
    print("\n2. Processing live audio:")
    sample_audio = b"sample_audio_data_for_demo"
    
    for i in range(3):
        audio_result = await coordinator.process_live_audio(
            stream_result['stream_id'],
            sample_audio
        )
        print(f"🎵 Audio chunk {i+1} processed: {audio_result['chunk_size']} bytes")
        await asyncio.sleep(2)
    
    # Demo 3: Identify key moments
    print("\n3. Identifying key moments:")
    await asyncio.sleep(5)  # Wait for simulated transcripts
    
    key_moments = await coordinator.identify_key_moments(stream_result['stream_id'])
    print(f"⭐ Key moments identified: {len(key_moments)}")
    
    for i, moment in enumerate(key_moments[:2]):  # Show first 2
        print(f"   {i+1}. {moment['moment_type']}: {moment['text'][:40]}... (score: {moment['score']:.2f})")
    
    # Demo 4: Suggest clips
    if key_moments:
        print("\n4. Generating clip suggestions:")
        clip_suggestions = await coordinator.suggest_clips(
            stream_result['stream_id'],
            key_moments[0]
        )
        
        print(f"🎬 Clip suggestions generated:")
        short_clips = clip_suggestions['clip_suggestions']['short_clips']
        print(f"   📱 Short clips: {len(short_clips)}")
        print(f"   📹 Medium clips: {len(clip_suggestions['clip_suggestions']['medium_clips'])}")
    
    # Demo 5: Stop stream
    print("\n5. Stopping stream:")
    stop_result = await coordinator.stop_stream(stream_result['stream_id'])
    final_report = stop_result['final_report']
    
    print(f"✅ Stream stopped")
    print(f"⏱️ Duration: {final_report['duration_seconds']:.1f} seconds")
    print(f"📝 Transcript segments: {final_report['transcript_segments']}")
    
    print("\n✅ Live streaming coordination demo completed!")


async def demo_complete_integration_workflow():
    """Demo complete integration workflow"""
    print("\n🎼 Demo: Complete Integration Workflow")
    print("=" * 50)
    
    # Create integration orchestrator
    orchestrator = create_integration_orchestrator({
        'use_stub': True,
        'max_concurrent_workflows': 5
    })
    
    # Set up helpers (in stub mode)
    twitter_adapter = TwitterAdapter({'use_stub': True})
    cerebras_helper = CerebrasHelper({'use_stub': True})
    assemblyai_helper = create_assemblyai_helper({'use_stub': True})
    maya_bridge = create_maya_audio_bridge({'use_stub': True})
    redis_helper = create_redis_helper({'use_stub': True})
    
    orchestrator.set_helpers(
        twitter_adapter=twitter_adapter,
        cerebras_helper=cerebras_helper,
        assemblyai_helper=assemblyai_helper,
        maya_bridge=maya_bridge,
        redis_helper=redis_helper
    )
    
    # Demo 1: Twitter mention response workflow
    print("\n1. Twitter Mention Response Workflow:")
    
    mention_data = {
        'id': '1234567890',
        'text': 'Hey @maya, can you help me create better content for my AI startup?',
        'user': {
            'username': 'startup_founder',
            'verified': False,
            'followers_count': 5000
        },
        'created_at': datetime.utcnow().isoformat(),
        'retweet_count': 2,
        'like_count': 15
    }
    
    workflow_result = await orchestrator.execute_twitter_mention_workflow(mention_data)
    
    print(f"✅ Workflow completed: {workflow_result['workflow_id']}")
    print(f"📝 Mention processed: {workflow_result['mention_id']}")
    print(f"📤 Response posted: {workflow_result['response_result']['success']}")
    print(f"⏱️ Duration: {workflow_result['duration_seconds']:.1f} seconds")
    
    # Demo 2: Audio conversation workflow
    print("\n2. Audio Conversation Workflow:")
    
    sample_audio = b"sample_audio_data_representing_user_speech"
    conversation_context = {
        'user_id': 'audio_user_123',
        'session_type': 'content_creation',
        'previous_topics': ['AI', 'social media']
    }
    
    audio_workflow = await orchestrator.execute_audio_conversation_workflow(
        sample_audio,
        conversation_context
    )
    
    print(f"✅ Audio workflow completed: {audio_workflow['workflow_id']}")
    print(f"🎤 Transcription: {audio_workflow['transcription']['transcription']['text'][:50]}...")
    print(f"🎭 Maya response: {audio_workflow['maya_response']['maya_response']['transcription'][:50]}...")
    print(f"⏱️ Duration: {audio_workflow['duration_seconds']:.1f} seconds")
    
    # Demo 3: Content creation pipeline
    print("\n3. Content Creation Pipeline:")
    
    content_request = {
        'topic': 'AI-powered content optimization',
        'platforms': ['twitter', 'linkedin'],
        'tone': 'professional',
        'target_audience': 'marketing professionals',
        'auto_publish': False
    }
    
    content_workflow = await orchestrator.execute_content_creation_pipeline(content_request)
    
    print(f"✅ Content creation completed: {content_workflow['workflow_id']}")
    print(f"📝 Platforms optimized: {len(content_workflow['content_result']['platform_versions'])}")
    print(f"⏱️ Duration: {content_workflow['duration_seconds']:.1f} seconds")
    
    # Demo 4: Live stream workflow
    print("\n4. Live Stream Workflow:")
    
    stream_config = {
        'platform': StreamPlatform.TWITTER_SPACES,
        'title': 'AI Innovation Discussion',
        'description': 'Live discussion about AI in social media'
    }
    
    stream_workflow = await orchestrator.execute_live_stream_workflow(stream_config)
    
    print(f"✅ Live stream workflow started: {stream_workflow['workflow_id']}")
    print(f"📺 Stream ID: {stream_workflow['stream_id']}")
    print(f"🔴 Real-time processing: {stream_workflow['real_time_active']}")
    
    print("\n✅ Complete integration workflow demo completed!")


async def demo_end_to_end_pipeline():
    """Demo the complete end-to-end pipeline"""
    print("\n🚀 Demo: End-to-End Audio-First Pipeline")
    print("=" * 60)
    
    print("""
    This demo showcases the complete Maya Control Plane audio-first system:
    
    1. Twitter mention detected
    2. Cerebras analyzes sentiment and intent
    3. Context stored in Redis
    4. Maya receives audio cue
    5. Maya responds via audio
    6. Response transcribed and posted
    7. Conversation thread updated
    """)
    
    # Create all components
    components = {
        'twitter_adapter': TwitterAdapter({'use_stub': True}),
        'cerebras_helper': CerebrasHelper({'use_stub': True}),
        'assemblyai_helper': create_assemblyai_helper({'use_stub': True}),
        'maya_bridge': create_maya_audio_bridge({'use_stub': True}),
        'redis_helper': create_redis_helper({'use_stub': True}),
        'orchestrator': create_integration_orchestrator({'use_stub': True})
    }
    
    # Set up orchestrator
    components['orchestrator'].set_helpers(**{k: v for k, v in components.items() if k != 'orchestrator'})
    
    print("\n🎯 Step 1: Twitter mention detected")
    mention = {
        'id': '9876543210',
        'text': 'Hey @maya, I need help creating viral content for my tech company!',
        'user': {
            'username': 'tech_ceo',
            'verified': True,
            'followers_count': 50000
        }
    }
    print(f"📱 Mention: {mention['text']}")
    print(f"👤 From: @{mention['user']['username']} ({mention['user']['followers_count']:,} followers)")
    
    print("\n🧠 Step 2: Cerebras analysis")
    sentiment = await components['cerebras_helper'].analyze_tweet_sentiment(mention['text'])
    priority = await components['cerebras_helper'].classify_engagement_priority(mention)
    
    print(f"😊 Sentiment: {sentiment['analysis']['sentiment']} (confidence: {sentiment['analysis']['confidence']})")
    print(f"⚡ Priority: {priority['priority_classification']['priority_level']} (score: {priority['priority_classification']['priority_score']})")
    
    print("\n🧵 Step 3: Context stored in Redis")
    thread = await components['redis_helper'].create_thread(
        ThreadType.TWITTER,
        f"Viral content help - @{mention['user']['username']}",
        mention
    )
    
    await components['redis_helper'].add_message(
        thread.id,
        MessageRole.USER,
        mention['text'],
        'twitter'
    )
    
    print(f"✅ Thread created: {thread.id}")
    print(f"💾 Context preserved in Redis")
    
    print("\n🎭 Step 4: Maya receives audio cue")
    await components['maya_bridge'].connect_to_maya()
    
    tts_message = f"High priority mention from verified user with 50K followers asking about viral content creation"
    maya_notification = await components['maya_bridge'].send_message_to_maya(
        tts_message,
        use_tts=True,
        wait_for_response=True
    )
    
    print(f"🔊 Audio cue sent to Maya")
    print(f"🎤 Maya responded: {maya_notification['maya_response']['transcription'][:80]}...")
    
    print("\n📝 Step 5: Response generation and posting")
    response_text = "I'd love to help you create viral content! Let's focus on authentic storytelling that resonates with your audience. What's your company's unique innovation story? 🚀 #ContentStrategy #TechInnovation"
    
    tweet_response = await components['twitter_adapter'].create_post({
        'text': response_text,
        'in_reply_to_tweet_id': mention['id']
    })
    
    print(f"📤 Response posted: {tweet_response['tweet_id']}")
    print(f"💬 Response: {response_text[:60]}...")
    
    print("\n🔄 Step 6: Conversation thread updated")
    await components['redis_helper'].add_message(
        thread.id,
        MessageRole.MAYA,
        response_text,
        'twitter'
    )
    
    final_context = await components['redis_helper'].get_conversation_context(thread.id)
    print(f"✅ Thread updated: {final_context['message_count']} messages total")
    
    print("\n🎉 End-to-End Pipeline Complete!")
    print("=" * 60)
    print("""
    ✅ The complete audio-first Maya Control Plane system is now operational!
    
    Key Features Demonstrated:
    • Twitter monitoring and mention detection
    • Cerebras-powered sentiment and priority analysis
    • Redis conversation threading and context preservation
    • Maya audio bridge with real-time communication
    • AssemblyAI audio processing pipeline
    • Complete workflow orchestration
    • End-to-end social media response automation
    
    The system is ready for production deployment with real API keys!
    """)


async def main():
    """Main demo function"""
    print("🎭 Maya Control Plane Audio-First System Demo")
    print("=" * 60)
    print("""
    Welcome to the comprehensive demo of Maya Control Plane's 
    audio-first social media management system!
    
    This demo showcases all major components working together:
    • AssemblyAI integration for audio processing
    • Redis conversation threading
    • Maya audio bridge automation
    • Live streaming coordination
    • Complete workflow orchestration
    • End-to-end pipeline demonstration
    
    All demos run in stub mode for development purposes.
    """)
    
    try:
        # Run all demos
        await demo_audio_transcription()
        await demo_redis_conversation_threading()
        await demo_maya_audio_bridge()
        await demo_live_streaming_coordination()
        await demo_complete_integration_workflow()
        await demo_end_to_end_pipeline()
        
        print("\n🎊 All demos completed successfully!")
        print("\nThe Maya Control Plane audio-first system is ready for deployment!")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())