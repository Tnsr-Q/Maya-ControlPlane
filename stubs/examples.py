"""
Maya API Examples and Usage Demonstrations

Example API calls and usage patterns for the Maya Control Plane system.
Demonstrates how to use the Maya API stubs and integrate with the orchestrator.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json

from stubs.maya_stub import (
    call_maya, analyze_intent, create_campaign, generate_content,
    get_recommendations
)
from stubs.schemas import Campaign, Post, Event, PlatformType, ContentType, create_example_campaign


async def example_intent_analysis():
    """Example: Analyze user intent"""
    print("🔍 Example: Intent Analysis")
    print("-" * 40)
    
    # Analyze different types of intents
    intents = [
        "I want to create a post about our new product launch",
        "Schedule a campaign for next week across all platforms",
        "How is our Twitter performance this month?",
        "Generate content for TikTok about AI trends"
    ]
    
    for intent in intents:
        result = await analyze_intent(intent, platform="twitter")
        print(f"Intent: {intent[:50]}...")
        print(f"Type: {result['intent_type']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Suggested Platform: {result['suggested_platform']}")
        print(f"Actions: {', '.join(result['suggested_actions'])}")
        print()


async def example_content_generation():
    """Example: Generate content for different platforms"""
    print("✨ Example: Content Generation")
    print("-" * 40)
    
    prompts = [
        {
            "prompt": "Announce our new AI-powered social media tool",
            "content_type": "social_post",
            "platform": "twitter",
            "tone": "exciting"
        },
        {
            "prompt": "Explain the benefits of AI in social media marketing",
            "content_type": "thread",
            "platform": "twitter",
            "tone": "educational"
        },
        {
            "prompt": "Behind the scenes of building Maya Control Plane",
            "content_type": "video_script",
            "platform": "youtube",
            "tone": "casual"
        }
    ]
    
    for prompt_data in prompts:
        result = await generate_content(**prompt_data)
        print(f"Platform: {prompt_data['platform'].title()}")
        print(f"Type: {prompt_data['content_type']}")
        print(f"Generated Content:")
        if isinstance(result['content'], list):
            for i, content in enumerate(result['content'], 1):
                print(f"  {i}. {content}")
        else:
            print(f"  {result['content']}")
        print(f"Word Count: {result['metadata']['word_count']}")
        print()


async def example_campaign_creation():
    """Example: Create and manage a campaign"""
    print("📊 Example: Campaign Creation")
    print("-" * 40)
    
    # Create campaign data
    campaign_data = {
        "name": "AI Innovation Showcase",
        "description": "Multi-platform campaign showcasing Maya's AI capabilities",
        "platforms": ["twitter", "youtube", "tiktok"],
        "target_audience": {
            "age_range": "25-45",
            "interests": ["technology", "AI", "social media"],
            "locations": ["US", "UK", "Canada"]
        },
        "budget": 5000,
        "duration_days": 14,
        "posts": [
            {
                "content": "🚀 Introducing Maya Control Plane - the future of AI-powered social media management!",
                "platform": "twitter",
                "scheduled_time": (datetime.utcnow() + timedelta(hours=2)).isoformat()
            },
            {
                "content": "Deep dive into how Maya revolutionizes content creation and audience engagement",
                "platform": "youtube",
                "scheduled_time": (datetime.utcnow() + timedelta(days=1)).isoformat()
            }
        ]
    }
    
    result = await create_campaign(campaign_data)
    
    print(f"Campaign Created: {result['campaign_id']}")
    print(f"Status: {result['status']}")
    print(f"Platforms: {', '.join(result['platforms'])}")
    print(f"Posts Scheduled: {result['scheduling']['posts_scheduled']}")
    print(f"Estimated Reach: {result['estimated_metrics']['total_reach']:,}")
    print(f"Estimated Engagement: {result['estimated_metrics']['estimated_engagement']:,}")
    print()
    print("Budget Allocation:")
    for platform, allocation in result['budget_allocation'].items():
        print(f"  {platform.title()}: {allocation*100:.0f}%")
    print()


async def example_recommendations():
    """Example: Get AI recommendations"""
    print("💡 Example: AI Recommendations")
    print("-" * 40)
    
    recommendation_types = ["content", "scheduling", "engagement"]
    
    for rec_type in recommendation_types:
        result = await get_recommendations(
            context={"platform": "twitter", "audience_size": 15000},
            recommendation_type=rec_type
        )
        
        print(f"Recommendation Type: {rec_type.title()}")
        print("Suggestions:")
        for i, recommendation in enumerate(result['recommendations'], 1):
            print(f"  {i}. {recommendation}")
        print(f"Expected Impact: {result['expected_impact']['engagement_increase']} engagement increase")
        print(f"Confidence: {result['confidence_score']:.0%}")
        print()


async def example_schema_usage():
    """Example: Using Pydantic schemas"""
    print("📋 Example: Schema Usage")
    print("-" * 40)
    
    # Create example campaign using schemas
    campaign = create_example_campaign()
    
    print(f"Campaign: {campaign.name}")
    print(f"Platforms: {', '.join([p.value for p in campaign.platforms])}")
    print(f"Posts: {len(campaign.posts)}")
    print(f"Budget: ${campaign.budget}")
    print(f"Duration: {(campaign.end_time - campaign.start_time).days} days")
    print()
    
    # Show posts
    print("Posts in Campaign:")
    for i, post in enumerate(campaign.posts, 1):
        print(f"  {i}. {post.title}")
        print(f"     Content: {post.content[:50]}...")
        print(f"     Platforms: {', '.join([p.value for p in post.platforms])}")
        print(f"     Scheduled: {post.scheduled_time.strftime('%Y-%m-%d %H:%M')}")
        print()


async def run_all_examples():
    """Run all examples"""
    print("🚀 Maya Control Plane API Examples")
    print("=" * 50)
    print()
    
    examples = [
        example_intent_analysis,
        example_content_generation,
        example_campaign_creation,
        example_recommendations,
        example_schema_usage
    ]
    
    for example_func in examples:
        try:
            await example_func()
            print("✅ Example completed successfully")
        except Exception as e:
            print(f"❌ Example failed: {e}")
        
        print("\n" + "="*50 + "\n")
        await asyncio.sleep(0.5)  # Small delay between examples


if __name__ == "__main__":
    # Run examples
    asyncio.run(run_all_examples())