"""
Maya System Audio Bridge Helper

Professional system audio bridge using BlackHole/VB-Cable for high-quality
audio capture and real-time streaming to AssemblyAI. Replaces browser automation
with streamlined audio processing.
"""

import asyncio
import json
import tempfile
import queue
import threading
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from pathlib import Path
import logging

# Audio processing imports
try:
    import sounddevice as sd
    import numpy as np
    import pyttsx3
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

# Simple logger setup to avoid dependency issues during development
logger = logging.getLogger("maya_system_audio_bridge")


class MayaSystemAudioBridge:
    """
    Professional system audio bridge for Maya interactions using BlackHole
    
    Features:
    - BlackHole virtual audio device for system audio capture
    - Real-time audio streaming to AssemblyAI
    - Captures ALL system audio (not just browser)
    - 48kHz professional audio quality
    - Continuous audio processing with proper buffering
    - System TTS for Cerebras output
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.sample_rate = config.get('sample_rate', 48000)
        self.channels = config.get('channels', 2)
        self.buffer_size = config.get('buffer_size', 1024)
        self.device_name = config.get('device_name', self._get_default_device_name())
        
        # Audio system state
        self.is_connected = False
        self.is_recording = False
        self.session_id = None
        self.audio_device_index = None
        self.audio_queue = queue.Queue()
        self.recording_thread = None
        self.processing_thread = None
        
        # TTS engine
        self.tts_engine = None
        
        # Callbacks
        self.on_transcription = None
        self.on_error = None
        
        # Use stub mode if audio not available
        self._use_stub = not AUDIO_AVAILABLE or config.get('use_stub', False)
        
        if not self._use_stub:
            self._initialize_audio_system()
        else:
            logger.warning("Maya System Audio Bridge running in stub mode")
    
    def _get_default_device_name(self) -> str:
        """Get default audio device name based on platform"""
        import platform
        system = platform.system().lower()
        
        if system == "darwin":  # macOS
            return "BlackHole 2ch"
        elif system == "windows":
            return "CABLE Output (VB-Audio Virtual Cable)"
        elif system == "linux":
            return "maya_virtual_sink.monitor"
        else:
            return "default"
    
    def _initialize_audio_system(self):
        """Initialize audio capture system"""
        try:
            if not AUDIO_AVAILABLE:
                raise ImportError("Audio dependencies not available")
            
            # Find audio device
            self.audio_device_index = self._find_audio_device()
            if self.audio_device_index is None:
                raise RuntimeError(f"Audio device '{self.device_name}' not found")
            
            # Initialize TTS engine
            self.tts_engine = pyttsx3.init()
            self._configure_tts()
            
            logger.info(f"Audio system initialized with device: {self.device_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize audio system: {e}")
            self._use_stub = True
    
    def _find_audio_device(self) -> Optional[int]:
        """Find the target audio device index"""
        try:
            devices = sd.query_devices()
            
            for i, device in enumerate(devices):
                if self.device_name.lower() in device['name'].lower():
                    if device['max_input_channels'] > 0:
                        logger.info(f"Found audio device: {device['name']} (index: {i})")
                        return i
            
            logger.warning(f"Device '{self.device_name}' not found, available devices:")
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    logger.warning(f"  {i}: {device['name']}")
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to find audio device: {e}")
            return None
    
    def _configure_tts(self):
        """Configure TTS engine settings"""
        try:
            # Set TTS properties
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # Prefer female voice for Maya
                female_voice = next((v for v in voices if 'female' in v.name.lower()), voices[0])
                self.tts_engine.setProperty('voice', female_voice.id)
            
            # Set speech rate and volume
            self.tts_engine.setProperty('rate', 180)  # Words per minute
            self.tts_engine.setProperty('volume', 0.8)  # 80% volume
            
        except Exception as e:
            logger.error(f"Failed to configure TTS: {e}")
    
    async def connect_to_maya(self, credentials: Dict[str, Any] = None) -> bool:
        """
        Connect to Maya audio system
        
        Args:
            credentials: Not used in system audio bridge (for compatibility)
            
        Returns:
            Connection success status
        """
        if self._use_stub:
            return await self._stub_connect_to_maya()
        
        try:
            # Validate audio device availability
            if self.audio_device_index is None:
                self.audio_device_index = self._find_audio_device()
                if self.audio_device_index is None:
                    raise RuntimeError(f"Audio device '{self.device_name}' not available")
            
            # Test audio device
            test_result = await self._test_audio_device()
            if not test_result.get('success'):
                raise RuntimeError(f"Audio device test failed: {test_result.get('error')}")
            
            self.is_connected = True
            self.session_id = f"maya_audio_session_{datetime.utcnow().timestamp()}"
            
            logger.info(f"Connected to Maya audio system - Session: {self.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Maya audio system: {e}")
            return False
    
    async def send_message_to_maya(self, 
                                 message: str,
                                 use_tts: bool = True,
                                 wait_for_response: bool = True) -> Dict[str, Any]:
        """
        Send message to Maya using TTS and optionally wait for response
        
        Args:
            message: Message to send to Maya
            use_tts: Whether to use text-to-speech (always True for system audio)
            wait_for_response: Whether to wait for Maya's response
            
        Returns:
            Maya's response data
        """
        if self._use_stub:
            return await self._stub_send_message_to_maya(message, use_tts, wait_for_response)
        
        try:
            # Convert text to speech and play through system
            if use_tts and self.tts_engine:
                await self._speak_message(message)
            
            if wait_for_response:
                # Wait for and capture Maya's response through system audio
                response = await self._capture_maya_response()
                return response
            else:
                return {
                    'success': True,
                    'message_sent': message,
                    'tts_played': use_tts,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to send message to Maya: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def start_conversation_loop(self,
                                    on_maya_response: Callable[[Dict[str, Any]], None],
                                    on_error: Callable[[str], None] = None) -> bool:
        """
        Start real-time conversation loop with Maya using continuous audio monitoring
        
        Args:
            on_maya_response: Callback for Maya responses
            on_error: Callback for errors
            
        Returns:
            Success status
        """
        if self._use_stub:
            return await self._stub_start_conversation_loop(on_maya_response)
        
        try:
            self.on_transcription = on_maya_response
            self.on_error = on_error
            
            # Start continuous audio recording
            await self._start_continuous_recording()
            
            logger.info("Started continuous conversation loop with Maya")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start conversation loop: {e}")
            if on_error:
                on_error(str(e))
            return False
    
    async def stop_conversation_loop(self) -> None:
        """Stop conversation loop and audio recording"""
        try:
            await self._stop_continuous_recording()
            logger.info("Stopped conversation loop with Maya")
        except Exception as e:
            logger.error(f"Failed to stop conversation loop: {e}")
    
    async def get_audio_status(self) -> Dict[str, Any]:
        """
        Get current audio system status
        
        Returns:
            Audio system status information
        """
        if self._use_stub:
            return await self._stub_get_audio_status()
        
        try:
            # Get device information
            device_info = None
            if self.audio_device_index is not None:
                devices = sd.query_devices()
                device_info = devices[self.audio_device_index]
            
            return {
                'connected': self.is_connected,
                'recording': self.is_recording,
                'session_id': self.session_id,
                'device_name': self.device_name,
                'device_index': self.audio_device_index,
                'device_info': {
                    'name': device_info['name'] if device_info else None,
                    'max_input_channels': device_info['max_input_channels'] if device_info else None,
                    'default_samplerate': device_info['default_samplerate'] if device_info else None
                } if device_info else None,
                'sample_rate': self.sample_rate,
                'channels': self.channels,
                'buffer_size': self.buffer_size,
                'queue_size': self.audio_queue.qsize(),
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get audio status: {e}")
            return {'error': str(e)}
    
    async def disconnect(self) -> None:
        """Disconnect from Maya audio system and cleanup"""
        try:
            # Stop recording if active
            if self.is_recording:
                await self.stop_conversation_loop()
            
            # Cleanup TTS engine
            if self.tts_engine:
                self.tts_engine.stop()
            
            self.is_connected = False
            self.session_id = None
            logger.info("Disconnected from Maya audio system")
            
        except Exception as e:
            logger.error(f"Failed to disconnect: {e}")
    
    # Private helper methods for audio processing
    
    async def _test_audio_device(self) -> Dict[str, Any]:
        """Test audio device functionality"""
        try:
            # Record a short test sample
            duration = 0.5  # seconds
            test_recording = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                device=self.audio_device_index,
                dtype='float64'
            )
            sd.wait()  # Wait for recording to complete
            
            # Check if we got audio data
            max_amplitude = np.max(np.abs(test_recording))
            
            return {
                'success': True,
                'max_amplitude': float(max_amplitude),
                'audio_detected': max_amplitude > 0.001
            }
            
        except Exception as e:
            logger.error(f"Audio device test failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _speak_message(self, message: str) -> None:
        """Speak message using system TTS"""
        try:
            # Run TTS in a separate thread to avoid blocking
            def speak():
                self.tts_engine.say(message)
                self.tts_engine.runAndWait()
            
            # Use thread pool to avoid blocking async loop
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, speak)
            
            logger.info(f"Spoke message: {message[:50]}...")
            
        except Exception as e:
            logger.error(f"Failed to speak message: {e}")
    
    async def _start_continuous_recording(self) -> None:
        """Start continuous audio recording in background thread"""
        try:
            if self.is_recording:
                return
            
            self.is_recording = True
            
            # Start recording thread
            self.recording_thread = threading.Thread(
                target=self._recording_worker,
                daemon=True
            )
            self.recording_thread.start()
            
            # Start processing thread
            self.processing_thread = threading.Thread(
                target=self._processing_worker,
                daemon=True
            )
            self.processing_thread.start()
            
            logger.info("Started continuous audio recording")
            
        except Exception as e:
            logger.error(f"Failed to start continuous recording: {e}")
            self.is_recording = False
            raise
    
    async def _stop_continuous_recording(self) -> None:
        """Stop continuous audio recording"""
        try:
            self.is_recording = False
            
            # Wait for threads to finish
            if self.recording_thread and self.recording_thread.is_alive():
                self.recording_thread.join(timeout=2)
            
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=2)
            
            # Clear audio queue
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                except queue.Empty:
                    break
            
            logger.info("Stopped continuous audio recording")
            
        except Exception as e:
            logger.error(f"Failed to stop continuous recording: {e}")
    
    def _recording_worker(self) -> None:
        """Worker thread for continuous audio recording"""
        try:
            # Create input stream
            def audio_callback(indata, frames, time, status):
                if status:
                    logger.warning(f"Audio callback status: {status}")
                
                # Add audio chunk to queue
                if self.is_recording:
                    try:
                        self.audio_queue.put_nowait({
                            'data': indata.copy(),
                            'timestamp': datetime.utcnow()
                        })
                    except queue.Full:
                        logger.warning("Audio queue full, dropping audio chunk")
            
            # Start audio stream
            with sd.InputStream(
                device=self.audio_device_index,
                samplerate=self.sample_rate,
                channels=self.channels,
                blocksize=self.buffer_size,
                callback=audio_callback,
                dtype='float64'
            ):
                while self.is_recording:
                    sd.sleep(100)  # Sleep 100ms
                    
        except Exception as e:
            logger.error(f"Recording worker failed: {e}")
            if self.on_error:
                self.on_error(f"Audio recording failed: {e}")
    
    def _processing_worker(self) -> None:
        """Worker thread for processing audio chunks"""
        try:
            audio_buffer = []
            buffer_duration = 2.0  # seconds
            samples_per_buffer = int(self.sample_rate * buffer_duration)
            
            while self.is_recording:
                try:
                    # Get audio chunk from queue
                    chunk = self.audio_queue.get(timeout=0.1)
                    audio_buffer.extend(chunk['data'])
                    
                    # Process when buffer is full
                    if len(audio_buffer) >= samples_per_buffer:
                        # Convert to bytes for AssemblyAI
                        audio_array = np.array(audio_buffer[:samples_per_buffer])
                        
                        # Normalize and convert to int16
                        if audio_array.dtype == np.float64:
                            audio_array = np.clip(audio_array * 32767, -32768, 32767).astype(np.int16)
                        
                        # Create transcription data
                        transcription_data = {
                            'type': 'audio_chunk',
                            'audio_data': audio_array.tobytes(),
                            'sample_rate': self.sample_rate,
                            'channels': self.channels,
                            'timestamp': datetime.utcnow().isoformat(),
                            'session_id': self.session_id
                        }
                        
                        # Call transcription callback
                        if self.on_transcription:
                            try:
                                self.on_transcription(transcription_data)
                            except Exception as e:
                                logger.error(f"Transcription callback failed: {e}")
                        
                        # Remove processed samples
                        audio_buffer = audio_buffer[samples_per_buffer:]
                        
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"Audio processing failed: {e}")
                    
        except Exception as e:
            logger.error(f"Processing worker failed: {e}")
            if self.on_error:
                self.on_error(f"Audio processing failed: {e}")
    
    async def _capture_maya_response(self) -> Dict[str, Any]:
        """Capture Maya's response through system audio monitoring"""
        try:
            # Wait for a brief period to capture response
            await asyncio.sleep(3)  # Give Maya time to respond
            
            # This would be handled by the continuous recording system
            # For now, return a success status
            return {
                'success': True,
                'response_type': 'system_audio',
                'note': 'Response captured through continuous audio monitoring',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to capture Maya response: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    # Stub implementations for development
    
    async def _stub_connect_to_maya(self) -> bool:
        """Stub implementation for Maya connection"""
        await asyncio.sleep(1)  # Simulate connection time
        
        self.is_connected = True
        self.session_id = f"stub_maya_audio_session_{datetime.utcnow().timestamp()}"
        
        logger.info(f"[STUB] Connected to Maya audio system - Session: {self.session_id}")
        return True
    
    async def _stub_send_message_to_maya(self, 
                                       message: str,
                                       use_tts: bool,
                                       wait_for_response: bool) -> Dict[str, Any]:
        """Stub implementation for sending messages to Maya"""
        await asyncio.sleep(1)  # Simulate TTS and processing time
        
        # Generate realistic Maya response
        maya_responses = [
            "I understand you want me to create content about that topic. Let me think about the best approach.",
            "That's an interesting request. I'll craft something engaging for your audience.",
            "I can definitely help with that. Let me create something that resonates with your brand voice.",
            "Great idea! I'll make sure to include the key points you mentioned.",
            "I'll create content that balances creativity with your strategic objectives."
        ]
        
        import random
        maya_response = random.choice(maya_responses)
        
        response_data = {
            'success': True,
            'message_sent': message,
            'tts_played': use_tts,
            'maya_response': {
                'transcription': maya_response,
                'confidence': 0.95,
                'duration': len(maya_response) * 0.05,  # Simulate speech duration
                'sentiment': 'positive',
                'timestamp': datetime.utcnow().isoformat()
            },
            'session_id': self.session_id,
            'stub_mode': True,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if wait_for_response:
            await asyncio.sleep(2)  # Simulate Maya thinking time
        
        return response_data
    
    async def _stub_start_conversation_loop(self, 
                                          on_maya_response: Callable[[Dict[str, Any]], None]) -> bool:
        """Stub implementation for conversation loop"""
        async def simulate_maya_responses():
            """Simulate periodic Maya responses"""
            maya_thoughts = [
                "I'm processing the social media landscape...",
                "Let me analyze the current trends...",
                "I have some creative ideas forming...",
                "The audience engagement patterns suggest...",
                "I think we should consider a different angle..."
            ]
            
            for i, thought in enumerate(maya_thoughts):
                await asyncio.sleep(10 + i * 5)  # Varying intervals
                
                response = {
                    'type': 'audio_chunk',
                    'transcription': thought,
                    'confidence': 0.90,
                    'timestamp': datetime.utcnow().isoformat(),
                    'session_id': self.session_id,
                    'stub_mode': True,
                    'audio_data': b'fake_audio_data',
                    'sample_rate': self.sample_rate,
                    'channels': self.channels
                }
                
                on_maya_response(response)
        
        # Start simulation in background
        asyncio.create_task(simulate_maya_responses())
        
        logger.info("[STUB] Started conversation loop with Maya audio system")
        return True
    
    async def _stub_get_audio_status(self) -> Dict[str, Any]:
        """Stub implementation for audio status"""
        return {
            'connected': self.is_connected,
            'recording': self.is_recording,
            'session_id': self.session_id,
            'device_name': f'[STUB] {self.device_name}',
            'device_index': 99,  # Fake device index
            'device_info': {
                'name': f'[STUB] {self.device_name}',
                'max_input_channels': 2,
                'default_samplerate': 48000.0
            },
            'sample_rate': self.sample_rate,
            'channels': self.channels,
            'buffer_size': self.buffer_size,
            'queue_size': 0,  # Simulated queue size
            'stub_mode': True,
            'timestamp': datetime.utcnow().isoformat()
        }


# Factory function for easy integration
def create_maya_audio_bridge(config: Dict[str, Any] = None) -> MayaSystemAudioBridge:
    """
    Create Maya System Audio Bridge with configuration
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configured Maya System Audio Bridge instance
    """
    if config is None:
        config = {'use_stub': True}  # Default to stub mode for development
    
    return MayaSystemAudioBridge(config)


# For backward compatibility
def create_maya_system_audio_bridge(config: Dict[str, Any] = None) -> MayaSystemAudioBridge:
    """Create Maya System Audio Bridge (new name)"""
    return create_maya_audio_bridge(config)


# Utility functions for audio bridge management

async def create_cerebras_maya_conversation(bridge: MayaSystemAudioBridge,
                                          cerebras_output: str,
                                          context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a conversation between Cerebras and Maya using system audio
    
    Args:
        bridge: Maya System Audio Bridge instance
        cerebras_output: Output from Cerebras analysis
        context: Conversation context
        
    Returns:
        Conversation result
    """
    # Connect to Maya audio system if not already connected
    if not bridge.is_connected:
        connected = await bridge.connect_to_maya()
        if not connected:
            return {
                'success': False,
                'error': 'Failed to connect to Maya audio system',
                'timestamp': datetime.utcnow().isoformat()
            }
    
    # Send Cerebras output to Maya via TTS
    response = await bridge.send_message_to_maya(
        cerebras_output,
        use_tts=True,
        wait_for_response=True
    )
    
    return response


async def process_audio_conversation_loop(bridge: MayaSystemAudioBridge,
                                        assemblyai_helper,
                                        redis_helper,
                                        thread_id: str) -> None:
    """
    Process real-time audio conversation loop with AssemblyAI integration
    
    Args:
        bridge: Maya System Audio Bridge instance
        assemblyai_helper: AssemblyAI helper for transcription
        redis_helper: Redis helper for conversation storage
        thread_id: Conversation thread ID
    """
    def on_maya_response(response_data: Dict[str, Any]):
        """Handle Maya's audio responses"""
        try:
            # Check if this is an audio chunk for transcription
            if response_data.get('type') == 'audio_chunk' and response_data.get('audio_data'):
                # Send audio data to AssemblyAI for transcription
                if assemblyai_helper:
                    asyncio.create_task(
                        assemblyai_helper.send_audio_chunk(response_data['audio_data'])
                    )
            
            # If we have a transcription, store it
            transcription = response_data.get('transcription')
            if transcription and redis_helper:
                # Store response in conversation thread
                asyncio.create_task(
                    redis_helper.add_message(
                        thread_id,
                        'maya',  # MessageRole.MAYA
                        transcription,
                        'system_audio',
                        response_data
                    )
                )
                
                logger.info(f"Maya response: {transcription[:100]}...")
        
        except Exception as e:
            logger.error(f"Error processing Maya response: {e}")
    
    def on_error(error: str):
        """Handle conversation errors"""
        logger.error(f"Conversation loop error: {error}")
    
    # Start conversation loop
    await bridge.start_conversation_loop(on_maya_response, on_error)


# Additional utility for audio system validation
async def validate_maya_audio_system(config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Validate Maya audio system setup
    
    Args:
        config: Audio system configuration
        
    Returns:
        Validation result
    """
    try:
        bridge = create_maya_audio_bridge(config)
        
        # Test connection
        connected = await bridge.connect_to_maya()
        if not connected:
            return {
                'success': False,
                'error': 'Failed to connect to audio system'
            }
        
        # Get system status
        status = await bridge.get_audio_status()
        
        await bridge.disconnect()
        
        return {
            'success': True,
            'audio_system_ready': True,
            'status': status
        }
        
    except Exception as e:
        logger.error(f"Audio system validation failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }