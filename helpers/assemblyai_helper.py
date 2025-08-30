"""
AssemblyAI Integration Helper

Handles speech-to-text transcription, real-time audio processing,
and audio analysis for Maya control plane audio-first interactions.
"""

import asyncio
import json
import websockets
import aiofiles
from typing import Dict, Any, List, Optional, AsyncGenerator, Callable
from datetime import datetime
import logging
from pathlib import Path

# Simple logger setup to avoid dependency issues during development
logger = logging.getLogger("assemblyai_helper")


class AssemblyAIHelper:
    """
    AssemblyAI integration helper for Maya control plane
    
    Features:
    - Speech-to-text transcription with sentiment analysis
    - Real-time audio stream processing
    - Entity detection and highlight identification
    - Audio processing pipeline for Maya interactions
    - Live stream transcription capabilities
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url', 'https://api.assemblyai.com/v2')
        self.websocket_url = config.get('websocket_url', 'wss://api.assemblyai.com/v2/realtime/ws')
        
        self.session = None
        self.websocket = None
        
        if not self.api_key:
            logger.warning("AssemblyAI API key not provided, using stub mode")
    
    async def transcribe_audio_file(self, audio_path: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Transcribe an audio file with optional analysis
        
        Args:
            audio_path: Path to the audio file
            options: Additional transcription options
            
        Returns:
            Transcription result with analysis
        """
        if not self.api_key:
            return self._create_stub_transcription(audio_path, options)
        
        try:
            # Upload audio file
            upload_response = await self._upload_audio_file(audio_path)
            audio_url = upload_response.get('upload_url')
            
            # Request transcription
            transcription_request = {
                'audio_url': audio_url,
                'sentiment_analysis': options.get('sentiment_analysis', True),
                'entity_detection': options.get('entity_detection', True),
                'speaker_labels': options.get('speaker_labels', False),
                'auto_highlights': options.get('auto_highlights', True),
                'punctuate': options.get('punctuate', True),
                'format_text': options.get('format_text', True)
            }
            
            # Submit transcription job
            job_response = await self._submit_transcription_job(transcription_request)
            job_id = job_response.get('id')
            
            # Poll for completion
            result = await self._poll_transcription_job(job_id)
            
            return {
                'success': True,
                'transcription': result,
                'processing_time': result.get('audio_duration', 0),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Audio transcription failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def start_realtime_transcription(self, 
                                         on_transcript: Callable[[Dict[str, Any]], None],
                                         on_error: Callable[[str], None] = None) -> bool:
        """
        Start real-time audio transcription
        
        Args:
            on_transcript: Callback for transcript events
            on_error: Callback for error events
            
        Returns:
            Success status
        """
        if not self.api_key:
            return await self._start_stub_realtime_transcription(on_transcript)
        
        try:
            # Connect to real-time WebSocket
            headers = {'Authorization': self.api_key}
            
            self.websocket = await websockets.connect(
                self.websocket_url,
                extra_headers=headers,
                ping_interval=20
            )
            
            # Start listening for transcripts
            asyncio.create_task(self._handle_realtime_messages(on_transcript, on_error))
            
            logger.info("Real-time transcription started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start real-time transcription: {e}")
            if on_error:
                on_error(str(e))
            return False
    
    async def send_audio_chunk(self, audio_data: bytes) -> bool:
        """
        Send audio chunk for real-time transcription
        
        Args:
            audio_data: Audio data bytes
            
        Returns:
            Success status
        """
        if not self.websocket:
            logger.error("Real-time transcription not started")
            return False
        
        try:
            # Send audio data
            await self.websocket.send(audio_data)
            return True
            
        except Exception as e:
            logger.error(f"Failed to send audio chunk: {e}")
            return False
    
    async def stop_realtime_transcription(self) -> None:
        """Stop real-time transcription"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            logger.info("Real-time transcription stopped")
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of transcribed text
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment analysis result
        """
        if not self.api_key:
            return self._create_stub_sentiment(text)
        
        # This would use AssemblyAI's sentiment analysis
        # For now, return a stub implementation
        return self._create_stub_sentiment(text)
    
    async def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract entities from transcribed text
        
        Args:
            text: Text to analyze
            
        Returns:
            Entity extraction result
        """
        if not self.api_key:
            return self._create_stub_entities(text)
        
        # This would use AssemblyAI's entity detection
        # For now, return a stub implementation
        return self._create_stub_entities(text)
    
    async def identify_highlights(self, transcript: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify key highlights from transcript
        
        Args:
            transcript: Transcript data
            
        Returns:
            List of highlighted moments
        """
        highlights = []
        
        # Extract auto-highlights from AssemblyAI response
        if 'auto_highlights_result' in transcript:
            for highlight in transcript['auto_highlights_result']['results']:
                highlights.append({
                    'text': highlight['text'],
                    'rank': highlight['rank'],
                    'timestamps': highlight['timestamps'],
                    'importance': highlight['rank'] / 10.0  # Normalize to 0-1
                })
        
        return highlights
    
    # Private helper methods
    
    async def _upload_audio_file(self, audio_path: str) -> Dict[str, Any]:
        """Upload audio file to AssemblyAI"""
        # This would implement actual file upload
        # For now, return stub response
        return {'upload_url': f'https://api.assemblyai.com/v2/upload/{audio_path}'}
    
    async def _submit_transcription_job(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Submit transcription job to AssemblyAI"""
        # This would submit actual job
        # For now, return stub response
        return {'id': f'job_{datetime.utcnow().timestamp()}'}
    
    async def _poll_transcription_job(self, job_id: str) -> Dict[str, Any]:
        """Poll transcription job until completion"""
        # This would poll actual job
        # For now, return stub response
        return {
            'id': job_id,
            'status': 'completed',
            'text': 'This is a sample transcription for development purposes.',
            'audio_duration': 30.5,
            'confidence': 0.95,
            'sentiment_analysis_results': [
                {'text': 'This is a sample transcription', 'sentiment': 'POSITIVE', 'confidence': 0.8}
            ],
            'entities': [
                {'entity_type': 'misc', 'text': 'sample', 'start': 10, 'end': 16}
            ],
            'auto_highlights_result': {
                'results': [
                    {
                        'text': 'sample transcription',
                        'rank': 8.5,
                        'timestamps': [{'start': 5000, 'end': 10000}]
                    }
                ]
            }
        }
    
    async def _handle_realtime_messages(self, 
                                      on_transcript: Callable[[Dict[str, Any]], None],
                                      on_error: Callable[[str], None] = None):
        """Handle real-time WebSocket messages"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                
                if data.get('message_type') == 'FinalTranscript':
                    transcript_data = {
                        'text': data.get('text', ''),
                        'confidence': data.get('confidence', 0.0),
                        'timestamp': datetime.utcnow().isoformat(),
                        'is_final': True
                    }
                    on_transcript(transcript_data)
                
                elif data.get('message_type') == 'PartialTranscript':
                    transcript_data = {
                        'text': data.get('text', ''),
                        'confidence': data.get('confidence', 0.0),
                        'timestamp': datetime.utcnow().isoformat(),
                        'is_final': False
                    }
                    on_transcript(transcript_data)
                    
        except Exception as e:
            logger.error(f"Real-time message handling error: {e}")
            if on_error:
                on_error(str(e))
    
    # Stub implementations for development
    
    def _create_stub_transcription(self, audio_path: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create stub transcription response"""
        return {
            'success': True,
            'transcription': {
                'id': f'stub_job_{datetime.utcnow().timestamp()}',
                'status': 'completed',
                'text': f'This is a stub transcription for audio file: {Path(audio_path).name}. '
                       'In production, this would contain the actual transcribed text from AssemblyAI.',
                'audio_duration': 45.2,
                'confidence': 0.92,
                'sentiment_analysis_results': [
                    {
                        'text': 'This is a stub transcription',
                        'sentiment': 'NEUTRAL',
                        'confidence': 0.85,
                        'start': 0,
                        'end': 1000
                    }
                ],
                'entities': [
                    {
                        'entity_type': 'misc',
                        'text': 'AssemblyAI',
                        'start': 500,
                        'end': 800
                    }
                ],
                'auto_highlights_result': {
                    'results': [
                        {
                            'text': 'stub transcription',
                            'rank': 7.5,
                            'timestamps': [{'start': 1000, 'end': 3000}]
                        }
                    ]
                }
            },
            'processing_time': 45.2,
            'timestamp': datetime.utcnow().isoformat(),
            'stub_mode': True
        }
    
    async def _start_stub_realtime_transcription(self, 
                                               on_transcript: Callable[[Dict[str, Any]], None]) -> bool:
        """Start stub real-time transcription for development"""
        async def simulate_realtime():
            """Simulate real-time transcription"""
            sample_phrases = [
                "Hello Maya,",
                "I need you to create",
                "a social media post",
                "about AI technology",
                "with a positive tone.",
                "Make it engaging",
                "for our audience."
            ]
            
            for i, phrase in enumerate(sample_phrases):
                await asyncio.sleep(2)  # Simulate real-time delay
                
                # Send partial transcript
                on_transcript({
                    'text': phrase,
                    'confidence': 0.85 + (i * 0.02),
                    'timestamp': datetime.utcnow().isoformat(),
                    'is_final': False,
                    'stub_mode': True
                })
                
                await asyncio.sleep(1)
                
                # Send final transcript
                on_transcript({
                    'text': phrase,
                    'confidence': 0.90 + (i * 0.01),
                    'timestamp': datetime.utcnow().isoformat(),
                    'is_final': True,
                    'stub_mode': True
                })
        
        # Start simulation in background
        asyncio.create_task(simulate_realtime())
        return True
    
    def _create_stub_sentiment(self, text: str) -> Dict[str, Any]:
        """Create stub sentiment analysis"""
        # Simple keyword-based sentiment for demo
        positive_words = ['good', 'great', 'awesome', 'excellent', 'positive']
        negative_words = ['bad', 'terrible', 'awful', 'negative', 'poor']
        
        text_lower = text.lower()
        
        if any(word in text_lower for word in positive_words):
            sentiment = 'POSITIVE'
            confidence = 0.85
        elif any(word in text_lower for word in negative_words):
            sentiment = 'NEGATIVE'
            confidence = 0.80
        else:
            sentiment = 'NEUTRAL'
            confidence = 0.75
        
        return {
            'text': text,
            'sentiment': sentiment,
            'confidence': confidence,
            'timestamp': datetime.utcnow().isoformat(),
            'stub_mode': True
        }
    
    def _create_stub_entities(self, text: str) -> Dict[str, Any]:
        """Create stub entity extraction"""
        # Simple entity detection for demo
        common_entities = {
            'Maya': 'person',
            'Twitter': 'organization',
            'YouTube': 'organization',
            'AI': 'technology',
            'social media': 'concept'
        }
        
        entities = []
        for entity, entity_type in common_entities.items():
            if entity.lower() in text.lower():
                start_pos = text.lower().find(entity.lower())
                entities.append({
                    'entity_type': entity_type,
                    'text': entity,
                    'start': start_pos,
                    'end': start_pos + len(entity),
                    'confidence': 0.90
                })
        
        return {
            'text': text,
            'entities': entities,
            'timestamp': datetime.utcnow().isoformat(),
            'stub_mode': True
        }


# Factory function for easy integration
def create_assemblyai_helper(config: Dict[str, Any] = None) -> AssemblyAIHelper:
    """
    Create AssemblyAI helper with configuration
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configured AssemblyAI helper instance
    """
    if config is None:
        config = {}
    
    return AssemblyAIHelper(config)


# Utility functions for audio processing

async def process_audio_for_maya(audio_path: str, 
                               assemblyai_helper: AssemblyAIHelper,
                               options: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Process audio file for Maya interaction
    
    Args:
        audio_path: Path to audio file
        assemblyai_helper: AssemblyAI helper instance
        options: Processing options
        
    Returns:
        Processed audio data ready for Maya
    """
    # Transcribe audio
    transcription_result = await assemblyai_helper.transcribe_audio_file(audio_path, options)
    
    if not transcription_result.get('success'):
        return transcription_result
    
    transcript = transcription_result['transcription']
    
    # Extract highlights for Maya
    highlights = await assemblyai_helper.identify_highlights(transcript)
    
    # Analyze sentiment
    sentiment = await assemblyai_helper.analyze_sentiment(transcript['text'])
    
    # Extract entities
    entities = await assemblyai_helper.extract_entities(transcript['text'])
    
    return {
        'success': True,
        'audio_file': audio_path,
        'transcript': {
            'text': transcript['text'],
            'confidence': transcript['confidence'],
            'duration': transcript['audio_duration']
        },
        'highlights': highlights,
        'sentiment': sentiment,
        'entities': entities,
        'maya_ready': True,
        'processing_time': transcription_result['processing_time'],
        'timestamp': datetime.utcnow().isoformat()
    }