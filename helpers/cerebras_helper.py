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
import json

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
    
    # Twitter-Specific Analysis Tools
    
    async def analyze_tweet_sentiment(self, tweet_text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of a tweet
        
        Args:
            tweet_text: Tweet content to analyze
            
        Returns:
            Sentiment analysis result
        """
        if not self.client:
            return self._create_stub_sentiment_analysis(tweet_text)
        
        try:
            request = {
                'messages': [
                    {
                        'role': 'system',
                        'content': '''You are an expert sentiment analyst for social media content.
                        Analyze the sentiment of tweets and provide detailed insights.
                        
                        Respond with a JSON object containing:
                        - sentiment: "positive", "negative", or "neutral"
                        - confidence: float between 0 and 1
                        - emotional_indicators: list of detected emotions
                        - context_clues: specific phrases that indicate sentiment
                        - urgency_level: "low", "medium", or "high"
                        '''
                    },
                    {
                        'role': 'user',
                        'content': f'Analyze the sentiment of this tweet: "{tweet_text}"'
                    }
                ],
                'model': self.model,
                'temperature': 0.1,
                'max_tokens': 300
            }
            
            result = await self.generate_content(request)
            
            if result.get('success'):
                return {
                    'success': True,
                    'tweet_text': tweet_text,
                    'analysis': result['content'],
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return self._create_stub_sentiment_analysis(tweet_text)
                
        except Exception as e:
            logger.error(f"Tweet sentiment analysis failed: {e}")
            return self._create_stub_sentiment_analysis(tweet_text)
    
    async def extract_conversation_context(self, conversation_thread: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract context from conversation thread
        
        Args:
            conversation_thread: List of messages in conversation
            
        Returns:
            Conversation context analysis
        """
        if not self.client:
            return self._create_stub_conversation_context(conversation_thread)
        
        try:
            # Build conversation text
            conversation_text = "\n".join([
                f"{msg.get('author', 'User')}: {msg.get('text', '')}"
                for msg in conversation_thread
            ])
            
            request = {
                'messages': [
                    {
                        'role': 'system',
                        'content': '''You are an expert conversation analyst for social media.
                        Analyze conversation threads to extract key context and insights.
                        
                        Provide analysis including:
                        - main_topics: key topics being discussed
                        - sentiment_flow: how sentiment changes through conversation
                        - key_participants: important contributors
                        - engagement_level: overall engagement quality
                        - suggested_responses: recommended response strategies
                        '''
                    },
                    {
                        'role': 'user',
                        'content': f'Analyze this conversation thread:\n\n{conversation_text}'
                    }
                ],
                'model': self.model,
                'temperature': 0.2,
                'max_tokens': 500
            }
            
            result = await self.generate_content(request)
            
            if result.get('success'):
                return {
                    'success': True,
                    'conversation_length': len(conversation_thread),
                    'context_analysis': result['content'],
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return self._create_stub_conversation_context(conversation_thread)
                
        except Exception as e:
            logger.error(f"Conversation context extraction failed: {e}")
            return self._create_stub_conversation_context(conversation_thread)
    
    async def identify_trending_topics(self, tweets: List[str]) -> Dict[str, Any]:
        """
        Identify trending topics from a collection of tweets
        
        Args:
            tweets: List of tweet texts
            
        Returns:
            Trending topics analysis
        """
        if not self.client:
            return self._create_stub_trending_analysis(tweets)
        
        try:
            # Combine tweets for analysis
            combined_tweets = "\n".join(tweets[:50])  # Limit for analysis
            
            request = {
                'messages': [
                    {
                        'role': 'system',
                        'content': '''You are a social media trend analyst.
                        Analyze collections of tweets to identify trending topics and themes.
                        
                        Provide analysis including:
                        - trending_topics: list of identified trending topics
                        - engagement_potential: potential for high engagement
                        - relevance_scores: how relevant each topic is
                        - hashtag_suggestions: recommended hashtags
                        - timing_recommendations: best times to engage
                        '''
                    },
                    {
                        'role': 'user',
                        'content': f'Analyze these tweets for trending topics:\n\n{combined_tweets}'
                    }
                ],
                'model': self.model,
                'temperature': 0.3,
                'max_tokens': 400
            }
            
            result = await self.generate_content(request)
            
            if result.get('success'):
                return {
                    'success': True,
                    'tweets_analyzed': len(tweets),
                    'trending_analysis': result['content'],
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return self._create_stub_trending_analysis(tweets)
                
        except Exception as e:
            logger.error(f"Trending topics analysis failed: {e}")
            return self._create_stub_trending_analysis(tweets)
    
    async def classify_engagement_priority(self, mention_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify engagement priority for a mention
        
        Args:
            mention_data: Mention data to analyze
            
        Returns:
            Priority classification result
        """
        if not self.client:
            return self._create_stub_priority_classification(mention_data)
        
        try:
            mention_context = f"""
            Tweet: {mention_data.get('text', '')}
            Author: {mention_data.get('user', {}).get('username', 'unknown')}
            Followers: {mention_data.get('user', {}).get('followers_count', 0)}
            Verified: {mention_data.get('user', {}).get('verified', False)}
            Retweets: {mention_data.get('retweet_count', 0)}
            Likes: {mention_data.get('like_count', 0)}
            """
            
            request = {
                'messages': [
                    {
                        'role': 'system',
                        'content': '''You are a social media engagement strategist.
                        Analyze mentions and classify their engagement priority.
                        
                        Consider factors like:
                        - User influence and verification status
                        - Engagement metrics (likes, retweets)
                        - Sentiment and urgency
                        - Potential for viral reach
                        - Brand relevance
                        
                        Provide priority classification:
                        - priority_level: "urgent", "high", "medium", "low"
                        - priority_score: float between 0 and 1
                        - reasoning: explanation of classification
                        - suggested_response_time: recommended response timeframe
                        '''
                    },
                    {
                        'role': 'user',
                        'content': f'Classify engagement priority for this mention:\n\n{mention_context}'
                    }
                ],
                'model': self.model,
                'temperature': 0.1,
                'max_tokens': 250
            }
            
            result = await self.generate_content(request)
            
            if result.get('success'):
                return {
                    'success': True,
                    'mention_id': mention_data.get('id', 'unknown'),
                    'priority_classification': result['content'],
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return self._create_stub_priority_classification(mention_data)
                
        except Exception as e:
            logger.error(f"Priority classification failed: {e}")
            return self._create_stub_priority_classification(mention_data)
    
    async def analyze_intent(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze intent in text for better response generation
        
        Args:
            text: Text to analyze
            context: Additional context information
            
        Returns:
            Intent analysis result
        """
        if not self.client:
            return self._create_stub_intent_analysis(text)
        
        try:
            context_info = ""
            if context:
                context_info = f"\nContext: {json.dumps(context, indent=2)}"
            
            request = {
                'messages': [
                    {
                        'role': 'system',
                        'content': '''You are an expert intent analysis system for social media.
                        Analyze text to understand user intent and recommend appropriate responses.
                        
                        Identify:
                        - primary_intent: main goal of the user
                        - intent_confidence: confidence in intent classification
                        - emotional_state: user's emotional state
                        - response_type: recommended type of response
                        - key_entities: important entities mentioned
                        - urgency_indicators: signs of urgency or time sensitivity
                        '''
                    },
                    {
                        'role': 'user',
                        'content': f'Analyze the intent in this text: "{text}"{context_info}'
                    }
                ],
                'model': self.model,
                'temperature': 0.2,
                'max_tokens': 300
            }
            
            result = await self.generate_content(request)
            
            if result.get('success'):
                return {
                    'success': True,
                    'analyzed_text': text,
                    'intent_analysis': result['content'],
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return self._create_stub_intent_analysis(text)
                
        except Exception as e:
            logger.error(f"Intent analysis failed: {e}")
            return self._create_stub_intent_analysis(text)
    
    async def process_technical_data(self, data: Dict[str, Any], target_format: str = "natural_language") -> Dict[str, Any]:
        """
        Process technical data for Maya consumption
        
        Args:
            data: Technical data to process
            target_format: Format for output (natural_language, summary, etc.)
            
        Returns:
            Processed data in target format
        """
        if not self.client:
            return self._create_stub_data_processing(data, target_format)
        
        try:
            data_text = json.dumps(data, indent=2)
            
            request = {
                'messages': [
                    {
                        'role': 'system',
                        'content': f'''You are a data translator that converts technical data into {target_format}.
                        
                        Your role is to:
                        - Convert complex technical data into easy-to-understand language
                        - Highlight key insights and patterns
                        - Provide actionable recommendations
                        - Maintain accuracy while improving clarity
                        - Focus on what matters most for social media decisions
                        '''
                    },
                    {
                        'role': 'user',
                        'content': f'Convert this technical data to {target_format}:\n\n{data_text}'
                    }
                ],
                'model': self.model,
                'temperature': 0.3,
                'max_tokens': 500
            }
            
            result = await self.generate_content(request)
            
            if result.get('success'):
                return {
                    'success': True,
                    'original_data_size': len(str(data)),
                    'target_format': target_format,
                    'processed_output': result['content'],
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return self._create_stub_data_processing(data, target_format)
                
        except Exception as e:
            logger.error(f"Technical data processing failed: {e}")
            return self._create_stub_data_processing(data, target_format)
    
    # Stub implementations for development
    
    def _create_stub_sentiment_analysis(self, tweet_text: str) -> Dict[str, Any]:
        """Create stub sentiment analysis"""
        # Simple keyword-based sentiment for demo
        positive_words = ['great', 'awesome', 'love', 'excellent', 'amazing']
        negative_words = ['bad', 'terrible', 'hate', 'awful', 'disappointed']
        
        text_lower = tweet_text.lower()
        
        if any(word in text_lower for word in positive_words):
            sentiment = 'positive'
            confidence = 0.85
        elif any(word in text_lower for word in negative_words):
            sentiment = 'negative'
            confidence = 0.80
        else:
            sentiment = 'neutral'
            confidence = 0.70
        
        return {
            'success': True,
            'tweet_text': tweet_text,
            'analysis': {
                'sentiment': sentiment,
                'confidence': confidence,
                'emotional_indicators': ['curiosity', 'engagement'],
                'context_clues': ['question marks', 'mentions'],
                'urgency_level': 'medium'
            },
            'timestamp': datetime.utcnow().isoformat(),
            'stub_mode': True
        }
    
    def _create_stub_conversation_context(self, conversation_thread: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create stub conversation context"""
        return {
            'success': True,
            'conversation_length': len(conversation_thread),
            'context_analysis': {
                'main_topics': ['AI technology', 'social media', 'innovation'],
                'sentiment_flow': 'positive trending upward',
                'key_participants': ['tech_enthusiast', 'ai_researcher'],
                'engagement_level': 'high',
                'suggested_responses': [
                    'Provide technical insights',
                    'Ask follow-up questions',
                    'Share relevant resources'
                ]
            },
            'timestamp': datetime.utcnow().isoformat(),
            'stub_mode': True
        }
    
    def _create_stub_trending_analysis(self, tweets: List[str]) -> Dict[str, Any]:
        """Create stub trending analysis"""
        return {
            'success': True,
            'tweets_analyzed': len(tweets),
            'trending_analysis': {
                'trending_topics': ['AI', 'Machine Learning', 'Social Media', 'Innovation'],
                'engagement_potential': 'high',
                'relevance_scores': [0.9, 0.8, 0.7, 0.6],
                'hashtag_suggestions': ['#AI', '#Innovation', '#TechTrends'],
                'timing_recommendations': 'Peak engagement: 2-4 PM EST'
            },
            'timestamp': datetime.utcnow().isoformat(),
            'stub_mode': True
        }
    
    def _create_stub_priority_classification(self, mention_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create stub priority classification"""
        # Simple priority calculation based on followers
        followers = mention_data.get('user', {}).get('followers_count', 0)
        verified = mention_data.get('user', {}).get('verified', False)
        
        if verified or followers > 50000:
            priority = 'high'
            score = 0.8
        elif followers > 10000:
            priority = 'medium'
            score = 0.6
        else:
            priority = 'low'
            score = 0.4
        
        return {
            'success': True,
            'mention_id': mention_data.get('id', 'unknown'),
            'priority_classification': {
                'priority_level': priority,
                'priority_score': score,
                'reasoning': f'Based on follower count ({followers}) and verification status',
                'suggested_response_time': '2-4 hours' if priority == 'high' else '24 hours'
            },
            'timestamp': datetime.utcnow().isoformat(),
            'stub_mode': True
        }
    
    def _create_stub_intent_analysis(self, text: str) -> Dict[str, Any]:
        """Create stub intent analysis"""
        # Simple intent classification
        if '?' in text:
            intent = 'question'
            response_type = 'informative_answer'
        elif any(word in text.lower() for word in ['help', 'support', 'issue']):
            intent = 'support_request'
            response_type = 'helpful_assistance'
        elif any(word in text.lower() for word in ['thanks', 'thank you', 'appreciate']):
            intent = 'gratitude'
            response_type = 'acknowledgment'
        else:
            intent = 'general_engagement'
            response_type = 'conversational'
        
        return {
            'success': True,
            'analyzed_text': text,
            'intent_analysis': {
                'primary_intent': intent,
                'intent_confidence': 0.8,
                'emotional_state': 'curious',
                'response_type': response_type,
                'key_entities': ['Maya', 'AI'],
                'urgency_indicators': []
            },
            'timestamp': datetime.utcnow().isoformat(),
            'stub_mode': True
        }
    
    def _create_stub_data_processing(self, data: Dict[str, Any], target_format: str) -> Dict[str, Any]:
        """Create stub data processing"""
        return {
            'success': True,
            'original_data_size': len(str(data)),
            'target_format': target_format,
            'processed_output': f"This technical data has been converted to {target_format}. "
                              f"Key insights: {len(data)} data points analyzed. "
                              "Recommendation: Engage with trending topics for optimal reach.",
            'timestamp': datetime.utcnow().isoformat(),
            'stub_mode': True
        }