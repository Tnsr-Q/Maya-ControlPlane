"""
Audio Setup Module for Maya Control Plane

Automated BlackHole installation and configuration system for professional
system audio capture. Supports macOS BlackHole and Windows VB-Cable.
"""

import os
import sys
import platform
import subprocess
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import tempfile
import urllib.request
import json

logger = logging.getLogger("audio_setup")


class AudioSetup:
    """
    Audio device setup and configuration for Maya Control Plane
    
    Features:
    - Automated BlackHole installation for macOS
    - VB-Cable setup instructions for Windows
    - Audio routing configuration
    - Multi-output device setup instructions
    - Platform-specific setup validation
    """
    
    def __init__(self):
        self.platform = platform.system().lower()
        self.is_macos = self.platform == "darwin"
        self.is_windows = self.platform == "windows"
        self.is_linux = self.platform == "linux"
        
        # Audio device configurations
        self.blackhole_device_name = "BlackHole 2ch"
        self.vb_cable_device_name = "CABLE Input (VB-Audio Virtual Cable)"
        self.sample_rate = 48000
        self.channels = 2
        self.buffer_size = 1024
        
    async def install_audio_system(self) -> Dict[str, Any]:
        """
        Install and configure audio system based on platform
        
        Returns:
            Installation result with status and next steps
        """
        logger.info(f"Installing audio system for {self.platform}")
        
        if self.is_macos:
            return await self._install_blackhole_macos()
        elif self.is_windows:
            return await self._setup_vb_cable_windows()
        elif self.is_linux:
            return await self._setup_pulseaudio_linux()
        else:
            return {
                'success': False,
                'error': f'Unsupported platform: {self.platform}',
                'platform': self.platform
            }
    
    async def _install_blackhole_macos(self) -> Dict[str, Any]:
        """Install BlackHole on macOS using Homebrew"""
        try:
            # Check if Homebrew is installed
            brew_check = subprocess.run(['which', 'brew'], 
                                      capture_output=True, text=True)
            
            if brew_check.returncode != 0:
                return {
                    'success': False,
                    'error': 'Homebrew not found',
                    'instructions': [
                        'Install Homebrew first: /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"',
                        'Then run this setup again'
                    ]
                }
            
            # Install BlackHole
            logger.info("Installing BlackHole via Homebrew...")
            install_result = subprocess.run([
                'brew', 'install', '--cask', 'blackhole-2ch'
            ], capture_output=True, text=True)
            
            if install_result.returncode == 0:
                # Verify installation
                devices = await self._list_audio_devices()
                blackhole_found = any(self.blackhole_device_name in device.get('name', '') 
                                    for device in devices)
                
                if blackhole_found:
                    return {
                        'success': True,
                        'device_name': self.blackhole_device_name,
                        'platform': 'macOS',
                        'next_steps': await self._get_macos_setup_instructions()
                    }
                else:
                    return {
                        'success': False,
                        'error': 'BlackHole installed but device not found',
                        'install_output': install_result.stdout
                    }
            else:
                # Check if already installed
                if "already installed" in install_result.stderr.lower():
                    return {
                        'success': True,
                        'device_name': self.blackhole_device_name,
                        'platform': 'macOS',
                        'message': 'BlackHole already installed',
                        'next_steps': await self._get_macos_setup_instructions()
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Failed to install BlackHole',
                        'install_error': install_result.stderr
                    }
                    
        except Exception as e:
            logger.error(f"BlackHole installation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'manual_instructions': await self._get_manual_blackhole_instructions()
            }
    
    async def _setup_vb_cable_windows(self) -> Dict[str, Any]:
        """Provide VB-Cable setup instructions for Windows"""
        return {
            'success': True,
            'platform': 'Windows',
            'device_name': self.vb_cable_device_name,
            'manual_installation_required': True,
            'instructions': [
                '1. Download VB-Cable from: https://vb-audio.com/Cable/',
                '2. Extract and run VBCABLE_Setup_x64.exe as Administrator',
                '3. Restart your computer after installation',
                '4. Set "CABLE Input" as your default recording device',
                '5. Configure multi-output device (see setup instructions)',
                '6. Run audio validation after setup'
            ],
            'next_steps': await self._get_windows_setup_instructions()
        }
    
    async def _setup_pulseaudio_linux(self) -> Dict[str, Any]:
        """Setup PulseAudio virtual devices on Linux"""
        try:
            # Create virtual audio devices using PulseAudio
            logger.info("Setting up PulseAudio virtual devices...")
            
            # Load null-sink module for virtual device
            null_sink_cmd = [
                'pactl', 'load-module', 'module-null-sink',
                'sink_name=maya_virtual_sink',
                'sink_properties=device.description="Maya Virtual Audio Device"'
            ]
            
            result = subprocess.run(null_sink_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'platform': 'Linux',
                    'device_name': 'maya_virtual_sink',
                    'next_steps': await self._get_linux_setup_instructions()
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to create PulseAudio virtual device',
                    'stderr': result.stderr
                }
                
        except Exception as e:
            logger.error(f"Linux audio setup failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _list_audio_devices(self) -> List[Dict[str, Any]]:
        """List available audio devices"""
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            
            device_list = []
            for i, device in enumerate(devices):
                device_list.append({
                    'index': i,
                    'name': device['name'],
                    'max_input_channels': device['max_input_channels'],
                    'max_output_channels': device['max_output_channels'],
                    'default_samplerate': device['default_samplerate']
                })
            
            return device_list
            
        except ImportError:
            logger.warning("sounddevice not available for device listing")
            return []
        except Exception as e:
            logger.error(f"Failed to list audio devices: {e}")
            return []
    
    async def validate_audio_setup(self) -> Dict[str, Any]:
        """
        Validate audio system configuration
        
        Returns:
            Validation result with device status and recommendations
        """
        try:
            devices = await self._list_audio_devices()
            
            # Find target audio device
            target_device = None
            if self.is_macos:
                target_device = next((d for d in devices 
                                    if self.blackhole_device_name in d['name']), None)
            elif self.is_windows:
                target_device = next((d for d in devices 
                                    if 'cable' in d['name'].lower()), None)
            elif self.is_linux:
                target_device = next((d for d in devices 
                                    if 'maya_virtual' in d['name'].lower()), None)
            
            if target_device:
                # Test audio device access
                test_result = await self._test_audio_device(target_device)
                
                return {
                    'success': True,
                    'device_found': True,
                    'device_info': target_device,
                    'audio_test': test_result,
                    'ready_for_maya': test_result.get('success', False)
                }
            else:
                return {
                    'success': False,
                    'device_found': False,
                    'available_devices': devices,
                    'recommendation': await self._get_device_recommendation()
                }
                
        except Exception as e:
            logger.error(f"Audio validation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _test_audio_device(self, device: Dict[str, Any]) -> Dict[str, Any]:
        """Test audio device functionality"""
        try:
            import sounddevice as sd
            import numpy as np
            
            device_index = device['index']
            
            # Test recording capability
            logger.info(f"Testing audio device: {device['name']}")
            
            # Record a short test sample
            duration = 1.0  # seconds
            test_recording = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=min(self.channels, device['max_input_channels']),
                device=device_index,
                dtype='float64'
            )
            sd.wait()  # Wait for recording to complete
            
            # Check if we got actual audio data
            max_amplitude = np.max(np.abs(test_recording))
            
            return {
                'success': True,
                'device_index': device_index,
                'sample_rate': self.sample_rate,
                'channels_tested': min(self.channels, device['max_input_channels']),
                'max_amplitude': float(max_amplitude),
                'audio_detected': max_amplitude > 0.001  # Basic noise threshold
            }
            
        except ImportError:
            return {
                'success': False,
                'error': 'sounddevice not available for testing'
            }
        except Exception as e:
            logger.error(f"Audio device test failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _get_macos_setup_instructions(self) -> List[str]:
        """Get macOS-specific setup instructions"""
        return [
            "1. Open Audio MIDI Setup (Applications > Utilities)",
            "2. Create a Multi-Output Device:",
            "   - Click the '+' button and select 'Create Multi-Output Device'",
            "   - Check both 'BlackHole 2ch' and your built-in speakers",
            "   - Right-click the Multi-Output Device and 'Use This Device For Sound Output'",
            "3. System audio will now play through both speakers and BlackHole",
            "4. Maya will capture audio from BlackHole device",
            "5. Run 'python quick_setup.py --validate' to test the setup"
        ]
    
    async def _get_windows_setup_instructions(self) -> List[str]:
        """Get Windows-specific setup instructions"""
        return [
            "1. After installing VB-Cable, restart your computer",
            "2. Right-click the sound icon in system tray > 'Open Sound settings'",
            "3. Set up multi-output:",
            "   - Under 'Choose your output device', keep your speakers selected",
            "   - Install 'Audio Router' or similar software for multi-output",
            "   - Route system audio to both speakers and CABLE Input",
            "4. Set CABLE Output as Maya's input device",
            "5. Run 'python quick_setup.py --validate' to test the setup"
        ]
    
    async def _get_linux_setup_instructions(self) -> List[str]:
        """Get Linux-specific setup instructions"""
        return [
            "1. Virtual sink 'maya_virtual_sink' has been created",
            "2. Set up audio routing:",
            "   - Install pavucontrol: sudo apt install pavucontrol",
            "   - Open pavucontrol and go to 'Recording' tab",
            "   - Set applications to record from 'Maya Virtual Audio Device'",
            "3. Route system audio to both speakers and virtual sink",
            "4. Run 'python quick_setup.py --validate' to test the setup"
        ]
    
    async def _get_device_recommendation(self) -> Dict[str, Any]:
        """Get device setup recommendation based on platform"""
        if self.is_macos:
            return {
                'platform': 'macOS',
                'recommended_device': 'BlackHole 2ch',
                'install_command': 'brew install --cask blackhole-2ch',
                'note': 'Professional virtual audio driver for macOS'
            }
        elif self.is_windows:
            return {
                'platform': 'Windows',
                'recommended_device': 'VB-Cable',
                'download_url': 'https://vb-audio.com/Cable/',
                'note': 'Free virtual audio cable for Windows'
            }
        elif self.is_linux:
            return {
                'platform': 'Linux',
                'recommended_device': 'PulseAudio Virtual Sink',
                'setup_command': 'pactl load-module module-null-sink',
                'note': 'Built-in PulseAudio virtual device'
            }
        else:
            return {
                'platform': self.platform,
                'note': 'Platform not supported for automated setup'
            }
    
    async def _get_manual_blackhole_instructions(self) -> List[str]:
        """Get manual BlackHole installation instructions"""
        return [
            "Manual BlackHole installation:",
            "1. Download BlackHole from: https://existential.audio/blackhole/",
            "2. Run the installer package",
            "3. Restart your computer",
            "4. Verify installation in Audio MIDI Setup",
            "5. Run audio setup validation"
        ]


# Factory function
def create_audio_setup() -> AudioSetup:
    """Create audio setup instance"""
    return AudioSetup()


# Utility functions
async def quick_install_audio_system() -> Dict[str, Any]:
    """Quick audio system installation"""
    setup = create_audio_setup()
    return await setup.install_audio_system()


async def validate_audio_configuration() -> Dict[str, Any]:
    """Quick audio configuration validation"""
    setup = create_audio_setup()
    return await setup.validate_audio_setup()