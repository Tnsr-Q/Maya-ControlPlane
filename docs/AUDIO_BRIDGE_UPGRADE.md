# Maya Control Plane - BlackHole Audio Bridge System

## Overview

The Maya Control Plane now uses a professional BlackHole-based audio system instead of browser automation for audio capture. This provides superior audio quality, system-wide audio capture, and eliminates the need for complex browser automation.

## Key Improvements

### 🎵 Professional Audio Quality
- **48kHz sample rate** with 2-channel stereo
- **Real-time audio streaming** with 1024 sample blocks
- **Professional audio buffering** with queue-based processing
- **System-wide audio capture** (not just browser audio)

### 🖥️ Platform Support
- **macOS**: BlackHole 2ch virtual audio device
- **Windows**: VB-Cable virtual audio cable
- **Linux**: PulseAudio virtual sink

### 🚀 Streamlined Setup
- **One-command installation**: `python quick_setup.py`
- **Automated audio device setup** with platform detection
- **Audio system validation** and testing tools
- **No browser dependencies** required

## Quick Start

### 1. Install Audio System
```bash
# Full setup with installation and validation
python quick_setup.py

# Validation only
python quick_setup.py --validate

# Audio test
python quick_setup.py --test
```

### 2. Dependencies
The system requires these additional packages:
```bash
pip install sounddevice==0.4.6 pyttsx3==2.90 numpy>=1.21.0
```

### 3. Basic Usage
```python
from helpers.maya_audio_bridge import create_maya_audio_bridge

# Create audio bridge
bridge = create_maya_audio_bridge({
    'sample_rate': 48000,
    'channels': 2,
    'device_name': 'BlackHole 2ch'  # macOS
})

# Connect to Maya audio system
await bridge.connect_to_maya()

# Send message via TTS
response = await bridge.send_message_to_maya(
    "Hello Maya, analyze this social media trend",
    use_tts=True,
    wait_for_response=True
)

# Start continuous audio monitoring
def handle_audio_response(audio_data):
    print(f"Captured audio: {len(audio_data.get('audio_data', b''))} bytes")

await bridge.start_conversation_loop(handle_audio_response)
```

## Audio Device Setup

### macOS (BlackHole)
1. Install BlackHole: `brew install --cask blackhole-2ch`
2. Create Multi-Output Device in Audio MIDI Setup
3. Route system audio to both speakers and BlackHole

### Windows (VB-Cable)
1. Download from: https://vb-audio.com/Cable/
2. Install VB-Cable as Administrator
3. Set up multi-output audio routing
4. Configure CABLE Input as recording device

### Linux (PulseAudio)
1. Create virtual sink: `pactl load-module module-null-sink`
2. Install pavucontrol: `sudo apt install pavucontrol`
3. Route applications to virtual sink

## Architecture Changes

### Before (Browser-based)
```
Cerebras → TTS → Browser → Maya Website → Audio Capture → AssemblyAI
```

### After (BlackHole-based)
```
Cerebras → System TTS → BlackHole → System Audio Capture → AssemblyAI → Maya
```

### Key Benefits
- ✅ **No browser automation** - eliminates Selenium dependencies
- ✅ **System-wide audio** - captures all audio, not just browser
- ✅ **Professional quality** - 48kHz audio with proper buffering
- ✅ **Real-time processing** - continuous audio streaming
- ✅ **Cross-platform** - works on macOS, Windows, and Linux
- ✅ **Reliable operation** - no browser-specific quirks

## API Compatibility

The new `MayaSystemAudioBridge` maintains full backward compatibility with the existing API:

```python
# All existing code continues to work
bridge = create_maya_audio_bridge(config)
await bridge.connect_to_maya()
await bridge.send_message_to_maya(message)
await bridge.start_conversation_loop(callback)
```

## Troubleshooting

### Audio Device Not Found
```bash
# List available audio devices
python quick_setup.py --validate

# Check device configuration
python -c "import sounddevice as sd; print(sd.query_devices())"
```

### TTS Issues
- Ensure pyttsx3 is installed: `pip install pyttsx3`
- Check system TTS voices are available
- Verify audio output device is working

### Audio Quality Issues
- Confirm 48kHz sample rate support
- Check audio buffer settings
- Verify multi-output device configuration

## Testing

Run the comprehensive test suite:
```bash
python test_audio_bridge.py
```

This validates:
- Audio bridge creation and connection
- Message sending and TTS
- Conversation loop functionality
- Backward compatibility
- Audio system validation