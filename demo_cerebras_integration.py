#!/usr/bin/env python3
"""
Demo script showcasing comprehensive Cerebras integration for Maya-ControlPlane

This script demonstrates all the advanced features implemented:
- Text generation with streaming and optimization
- Embeddings generation and management
- Fine-tuning capabilities
- Tool calling and function integration
- Dynamic API selection
- Performance optimization
"""

import asyncio
import json
from pathlib import Path
import sys

# Add the src directory to Python path
sys.path.append(str(Path(__file__).parent / "src"))

from maya_cp.helpers.cerebras_helper import (
    CerebrasHelper,
    GenerationConfig,
    EmbeddingConfig,
    FineTuningConfig,
    CerebrasModel,
    create_cerebras_helper,
    get_model_recommendations
)


async def demo_text_generation():
    """Demo advanced text generation capabilities"""
    print("🚀 Demo: Advanced Text Generation")
    print("=" * 50)
    
    # Initialize helper (stub mode for demo)
    helper = CerebrasHelper({})
    
    # Basic text generation
    print("\n1. Basic Text Generation:")
    messages = [
        {"role": "system", "content": "You are a social media expert."},
        {"role": "user", "content": "Create a Twitter post about AI innovation"}
    ]
    
    task = helper.generate_text(messages)
    result = await task
    
    print(f"✅ Generated content: {result['content']}")
    print(f"📊 Model used: {result['model']}")
    print(f"🔧 Stub mode: {result.get('stub_mode', False)}")
    
    # Advanced configuration
    print("\n2. Advanced Configuration:")
    config = GenerationConfig(
        model=CerebrasModel.LLAMA_3_1_405B.value,
        max_tokens=500,
        temperature=0.8,
        top_p=0.9,
        reasoning_effort="high"
    )
    
    complex_messages = [
        {"role": "user", "content": "Analyze the future impact of AI on social media marketing"}
    ]
    
    task = helper.generate_text(complex_messages, config)
    result = await task
    
    print(f"✅ Complex analysis: {result['content'][:100]}...")
    print(f"📊 Model: {result['model']}")
    
    # Streaming generation
    print("\n3. Streaming Generation:")
    stream_messages = [
        {"role": "user", "content": "Tell me about the benefits of AI in content creation"}
    ]
    
    print("🔄 Streaming response:")
    async for chunk in helper.generate_text(stream_messages, stream=True):
        if not chunk.get("is_final", False):
            print(chunk["content"], end="", flush=True)
        else:
            print(f"\n✅ Stream completed with {chunk.get('chunk_index', 0)} chunks")
    
    print("\n" + "=" * 50)


async def demo_embeddings():
    """Demo embeddings generation and management"""
    print("\n🧠 Demo: Embeddings Generation")
    print("=" * 50)
    
    helper = CerebrasHelper({})
    
    # Generate embeddings for content analysis
    texts = [
        "AI is revolutionizing social media marketing",
        "Machine learning enables personalized content creation",
        "Deep learning models understand user preferences",
        "Today's weather is sunny and warm"
    ]
    
    config = EmbeddingConfig(
        model="text-embedding-3-large",
        dimensions=1024,
        normalize=True,
        task_type="retrieval_document"
    )
    
    result = await helper.generate_embeddings(texts, config)
    
    print(f"✅ Generated embeddings for {result['count']} texts")
    print(f"📐 Dimensions: {result['dimensions']}")
    print(f"⚡ Processing time: {result.get('processing_time_ms', 0):.1f}ms")
    print(f"🔧 Stub mode: {result.get('stub_mode', False)}")
    
    # Demonstrate similarity (mock calculation for demo)
    print(f"\n📊 Sample embedding vector (first 5 values): {result['embeddings'][0][:5]}")
    
    print("=" * 50)


async def demo_fine_tuning():
    """Demo fine-tuning capabilities"""
    print("\n🎯 Demo: Fine-tuning Workflows")
    print("=" * 50)
    
    helper = CerebrasHelper({})
    
    # Instruction tuning
    print("\n1. Instruction Tuning:")
    config = FineTuningConfig(
        base_model=CerebrasModel.LLAMA_3_1_8B.value,
        dataset_path="/path/to/instruction_data.jsonl",
        method="instruction_tuning",
        learning_rate=1e-5,
        batch_size=8,
        epochs=3
    )
    
    result = await helper.start_fine_tuning(config)
    print(f"✅ Fine-tuning job started: {result['job_id']}")
    print(f"📊 Base model: {result['base_model']}")
    print(f"🔧 Method: {result['method']}")
    
    # DPO fine-tuning
    print("\n2. Direct Preference Optimization (DPO):")
    dpo_config = FineTuningConfig(
        base_model=CerebrasModel.LLAMA_3_1_8B.value,
        dataset_path="/path/to/preference_data.jsonl",
        method="dpo",
        learning_rate=5e-6,
        batch_size=4,
        epochs=2,
        beta=0.1
    )
    
    dpo_result = await helper.start_fine_tuning(dpo_config)
    print(f"✅ DPO job started: {dpo_result['job_id']}")
    print(f"🎛️ Beta parameter: {dpo_config.beta}")
    
    # Check status
    print("\n3. Job Status Monitoring:")
    status = await helper.get_fine_tuning_status(result['job_id'])
    print(f"📈 Status: {status['status']}")
    print(f"📊 Progress: {status.get('progress', 0):.1%}")
    
    print("=" * 50)


async def demo_tool_calling():
    """Demo tool calling and function integration"""
    print("\n🛠️ Demo: Tool Calling & Function Integration")
    print("=" * 50)
    
    helper = CerebrasHelper({})
    
    # Register custom tools
    def analyze_sentiment(text: str) -> dict:
        """Analyze sentiment of text"""
        return {
            "sentiment": "positive",
            "confidence": 0.85,
            "text_length": len(text)
        }
    
    def generate_hashtags(content: str, platform: str) -> dict:
        """Generate hashtags for content"""
        hashtags = ["#AI", "#Innovation", "#SocialMedia", "#Technology"]
        return {
            "hashtags": hashtags[:3],  # Limit for demo
            "platform": platform,
            "content_preview": content[:50] + "..."
        }
    
    # Register tools
    helper.register_tool(
        "analyze_sentiment",
        analyze_sentiment,
        "Analyze the sentiment of given text",
        {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to analyze"}
            },
            "required": ["text"]
        }
    )
    
    helper.register_tool(
        "generate_hashtags",
        generate_hashtags,
        "Generate relevant hashtags for content",
        {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Content to generate hashtags for"},
                "platform": {"type": "string", "description": "Target social media platform"}
            },
            "required": ["content", "platform"]
        }
    )
    
    print(f"✅ Registered {len(helper.registered_tools)} tools")
    
    # Use tools in generation
    messages = [
        {"role": "user", "content": "Create a positive social media post about AI and analyze its sentiment"}
    ]
    
    result = await helper.call_with_tools(messages, tools=["analyze_sentiment", "generate_hashtags"])
    
    print(f"✅ Generated with tools: {result['content'][:100]}...")
    print(f"🔧 Available tools: {len(result.get('tool_calls', []))}")
    
    print("=" * 50)


async def demo_dynamic_selection():
    """Demo dynamic API selection and optimization"""
    print("\n⚡ Demo: Dynamic Model Selection & Optimization")
    print("=" * 50)
    
    helper = CerebrasHelper({})
    
    # Test different task complexities
    tasks = [
        ("Simple greeting", "Say hello to the user"),
        ("Content creation", "Create a comprehensive blog post about AI trends"),
        ("Complex analysis", "Analyze and compare quantum computing vs classical computing"),
        ("Reasoning task", "Solve this logic puzzle step by step")
    ]
    
    print("🎯 Optimal model selection for different tasks:")
    for task_type, description in tasks:
        optimal_model = helper.select_optimal_model(description)
        print(f"  • {task_type}: {optimal_model}")
    
    # Model recommendations by category
    print("\n📋 Model recommendations by category:")
    categories = ["social_media", "reasoning", "creative_writing", "code_generation"]
    
    for category in categories:
        rec = get_model_recommendations(category)
        print(f"  • {category}: {rec['recommended']}")
    
    # Performance metrics
    print("\n📊 Performance metrics:")
    metrics = helper.get_performance_metrics(window_minutes=60)
    print(f"  • Sample count: {metrics['sample_count']}")
    if metrics['sample_count'] > 0:
        print(f"  • Average latency: {metrics['metrics']['average_latency_ms']:.1f}ms")
        print(f"  • Average throughput: {metrics['metrics']['average_throughput_tps']:.1f} tokens/sec")
    
    print("=" * 50)


async def demo_health_check():
    """Demo system health monitoring"""
    print("\n🏥 Demo: System Health & Monitoring")
    print("=" * 50)
    
    helper = CerebrasHelper({})
    
    health = await helper.health_check()
    
    print(f"✅ System healthy: {health['healthy']}")
    print(f"🔧 Mode: {health.get('mode', 'unknown')}")
    print(f"📊 Registered tools: {health.get('registered_tools', 0)}")
    print(f"📈 Metrics samples: {health.get('metrics_samples', 0)}")
    
    if health.get('response_time_ms'):
        print(f"⚡ Response time: {health['response_time_ms']:.1f}ms")
    
    print("=" * 50)


async def main():
    """Run all demos"""
    print("🎉 Maya-ControlPlane: Comprehensive Cerebras Integration Demo")
    print("🚀 Showcasing advanced AI capabilities for sesame.ai pitch")
    print("=" * 70)
    
    try:
        await demo_text_generation()
        await demo_embeddings()
        await demo_fine_tuning()
        await demo_tool_calling()
        await demo_dynamic_selection()
        await demo_health_check()
        
        print("\n🎊 Demo completed successfully!")
        print("✨ All Cerebras integration features demonstrated")
        print("🚀 Ready for production deployment and sesame.ai pitch!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())