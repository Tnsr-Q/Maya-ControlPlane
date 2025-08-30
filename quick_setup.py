#!/usr/bin/env python3
"""
Quick Setup Script for Maya Control Plane Audio System

One-command setup for BlackHole/VB-Cable audio capture system.
Handles installation, configuration, and validation.
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from setup.audio_setup import create_audio_setup, quick_install_audio_system, validate_audio_configuration
from helpers.maya_audio_bridge import create_maya_audio_bridge, validate_maya_audio_system

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("quick_setup")

BANNER = """
╔═══════════════════════════════════════════════════════════════╗
║                Maya Control Plane Audio Setup                ║
║               Professional Audio Bridge System               ║
╚═══════════════════════════════════════════════════════════════╝
"""


class QuickSetup:
    """Quick setup orchestrator for Maya audio system"""
    
    def __init__(self):
        self.audio_setup = create_audio_setup()
    
    async def run_full_setup(self) -> Dict[str, Any]:
        """Run complete audio system setup"""
        print(BANNER)
        print("🚀 Starting Maya Control Plane audio system setup...\n")
        
        results = {
            'steps': [],
            'success': True,
            'errors': []
        }
        
        # Step 1: Platform detection
        print("📍 Step 1: Detecting platform and requirements...")
        platform_info = await self._detect_platform()
        results['steps'].append({
            'step': 'platform_detection',
            'success': True,
            'data': platform_info
        })
        print(f"   Platform: {platform_info['platform']}")
        print(f"   Recommended device: {platform_info['recommended_device']}")
        
        # Step 2: Install audio system
        print("\n🔧 Step 2: Installing audio system...")
        install_result = await quick_install_audio_system()
        results['steps'].append({
            'step': 'audio_installation',
            'success': install_result.get('success', False),
            'data': install_result
        })
        
        if install_result.get('success'):
            print("   ✅ Audio system installed successfully")
            if 'next_steps' in install_result:
                print("   📋 Next steps:")
                for step in install_result['next_steps']:
                    print(f"      • {step}")
        else:
            print(f"   ❌ Audio installation failed: {install_result.get('error', 'Unknown error')}")
            results['success'] = False
            results['errors'].append(install_result.get('error', 'Audio installation failed'))
            
            if 'instructions' in install_result:
                print("   📋 Manual installation required:")
                for instruction in install_result['instructions']:
                    print(f"      • {instruction}")
        
        # Step 3: Validate configuration
        print("\n🔍 Step 3: Validating audio configuration...")
        validation_result = await validate_audio_configuration()
        results['steps'].append({
            'step': 'audio_validation',
            'success': validation_result.get('success', False),
            'data': validation_result
        })
        
        if validation_result.get('success'):
            if validation_result.get('device_found'):
                print("   ✅ Audio device found and validated")
                device_info = validation_result.get('device_info', {})
                print(f"      Device: {device_info.get('name', 'Unknown')}")
                print(f"      Channels: {device_info.get('max_input_channels', 'Unknown')}")
                
                if validation_result.get('ready_for_maya'):
                    print("   ✅ Audio system ready for Maya")
                else:
                    print("   ⚠️  Audio device found but needs configuration")
            else:
                print("   ❌ Required audio device not found")
                results['success'] = False
                results['errors'].append("Audio device not found")
        else:
            print(f"   ❌ Validation failed: {validation_result.get('error', 'Unknown error')}")
            results['success'] = False
            results['errors'].append(validation_result.get('error', 'Validation failed'))
        
        # Step 4: Test Maya audio bridge
        print("\n🎭 Step 4: Testing Maya audio bridge...")
        maya_test_result = await validate_maya_audio_system()
        results['steps'].append({
            'step': 'maya_bridge_test',
            'success': maya_test_result.get('success', False),
            'data': maya_test_result
        })
        
        if maya_test_result.get('success'):
            print("   ✅ Maya audio bridge validated successfully")
        else:
            print(f"   ❌ Maya bridge test failed: {maya_test_result.get('error', 'Unknown error')}")
            # Don't fail overall setup for Maya bridge issues
        
        # Step 5: Dependencies check
        print("\n📦 Step 5: Checking Python dependencies...")
        deps_result = await self._check_dependencies()
        results['steps'].append({
            'step': 'dependencies_check',
            'success': deps_result.get('success', False),
            'data': deps_result
        })
        
        if deps_result.get('success'):
            print("   ✅ All dependencies satisfied")
        else:
            print("   ⚠️  Some dependencies missing:")
            for missing in deps_result.get('missing', []):
                print(f"      • {missing}")
            print("   💡 Run: pip install -r requirements.txt")
        
        # Summary
        print("\n" + "="*60)
        if results['success']:
            print("🎉 Setup completed successfully!")
            print("\n📋 Next steps:")
            print("   1. Configure multi-output device (see platform instructions above)")
            print("   2. Test audio routing with: python quick_setup.py --test")
            print("   3. Start Maya Control Plane with audio support")
        else:
            print("❌ Setup completed with errors:")
            for error in results['errors']:
                print(f"   • {error}")
            print("\n💡 Check the instructions above and try again")
        
        return results
    
    async def run_validation_only(self) -> Dict[str, Any]:
        """Run validation checks only"""
        print(BANNER)
        print("🔍 Running Maya audio system validation...\n")
        
        # Audio configuration validation
        print("🔧 Validating audio configuration...")
        validation_result = await validate_audio_configuration()
        
        if validation_result.get('success'):
            print("✅ Audio system validation passed")
            device_info = validation_result.get('device_info', {})
            print(f"   Device: {device_info.get('name', 'Unknown')}")
            print(f"   Sample rate: {device_info.get('default_samplerate', 'Unknown')} Hz")
            print(f"   Channels: {device_info.get('max_input_channels', 'Unknown')}")
        else:
            print(f"❌ Audio validation failed: {validation_result.get('error', 'Unknown')}")
            if 'available_devices' in validation_result:
                print("\n📋 Available audio devices:")
                for device in validation_result['available_devices'][:5]:  # Show first 5
                    print(f"   • {device.get('name', 'Unknown')} (channels: {device.get('max_input_channels', 0)})")
        
        # Maya bridge validation
        print("\n🎭 Validating Maya audio bridge...")
        maya_result = await validate_maya_audio_system()
        
        if maya_result.get('success'):
            print("✅ Maya audio bridge validation passed")
        else:
            print(f"❌ Maya bridge validation failed: {maya_result.get('error', 'Unknown')}")
        
        return {
            'audio_validation': validation_result,
            'maya_validation': maya_result,
            'overall_success': validation_result.get('success', False) and maya_result.get('success', False)
        }
    
    async def run_audio_test(self) -> Dict[str, Any]:
        """Run audio capture test"""
        print(BANNER)
        print("🎤 Running audio capture test...\n")
        
        try:
            # Create audio bridge in non-stub mode for testing
            config = {'use_stub': False}
            bridge = create_maya_audio_bridge(config)
            
            # Connect to audio system
            print("🔌 Connecting to audio system...")
            connected = await bridge.connect_to_maya()
            
            if not connected:
                print("❌ Failed to connect to audio system")
                return {'success': False, 'error': 'Connection failed'}
            
            print("✅ Connected to audio system")
            
            # Get audio status
            status = await bridge.get_audio_status()
            print(f"📊 Audio status:")
            print(f"   Device: {status.get('device_name', 'Unknown')}")
            print(f"   Sample rate: {status.get('sample_rate', 'Unknown')} Hz")
            print(f"   Channels: {status.get('channels', 'Unknown')}")
            
            # Start brief recording test
            print("\n🎤 Starting 5-second audio test...")
            print("   Please make some noise or speak to test audio capture...")
            
            responses = []
            def capture_response(response_data):
                responses.append(response_data)
                print(f"   📥 Audio chunk captured: {len(response_data.get('audio_data', b''))} bytes")
            
            # Start recording
            await bridge.start_conversation_loop(capture_response)
            await asyncio.sleep(5)  # Record for 5 seconds
            await bridge.stop_conversation_loop()
            
            print(f"\n✅ Audio test completed")
            print(f"   Captured {len(responses)} audio chunks")
            
            await bridge.disconnect()
            
            return {
                'success': True,
                'chunks_captured': len(responses),
                'audio_status': status
            }
            
        except Exception as e:
            logger.error(f"Audio test failed: {e}")
            print(f"❌ Audio test failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _detect_platform(self) -> Dict[str, Any]:
        """Detect platform and get setup recommendations"""
        import platform
        
        system = platform.system().lower()
        
        if system == "darwin":  # macOS
            return {
                'platform': 'macOS',
                'recommended_device': 'BlackHole 2ch',
                'install_method': 'Homebrew',
                'install_command': 'brew install --cask blackhole-2ch'
            }
        elif system == "windows":
            return {
                'platform': 'Windows',
                'recommended_device': 'VB-Cable',
                'install_method': 'Manual download',
                'download_url': 'https://vb-audio.com/Cable/'
            }
        elif system == "linux":
            return {
                'platform': 'Linux',
                'recommended_device': 'PulseAudio Virtual Sink',
                'install_method': 'PulseAudio module',
                'install_command': 'pactl load-module module-null-sink'
            }
        else:
            return {
                'platform': system,
                'recommended_device': 'Unknown',
                'install_method': 'Manual setup required'
            }
    
    async def _check_dependencies(self) -> Dict[str, Any]:
        """Check Python dependencies"""
        required_deps = [
            'sounddevice',
            'numpy',
            'pyttsx3'
        ]
        
        missing = []
        available = []
        
        for dep in required_deps:
            try:
                __import__(dep)
                available.append(dep)
            except ImportError:
                missing.append(dep)
        
        return {
            'success': len(missing) == 0,
            'available': available,
            'missing': missing,
            'total_required': len(required_deps)
        }


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Maya Control Plane Audio System Quick Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python quick_setup.py                 # Full setup
  python quick_setup.py --validate      # Validation only
  python quick_setup.py --test          # Audio test
  python quick_setup.py --install       # Install only
        """
    )
    
    parser.add_argument('--validate', action='store_true',
                       help='Run validation checks only')
    parser.add_argument('--test', action='store_true',
                       help='Run audio capture test')
    parser.add_argument('--install', action='store_true',
                       help='Run installation only')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    setup = QuickSetup()
    
    try:
        if args.validate:
            result = await setup.run_validation_only()
        elif args.test:
            result = await setup.run_audio_test()
        elif args.install:
            result = await quick_install_audio_system()
            print(f"Installation result: {result}")
        else:
            result = await setup.run_full_setup()
        
        # Exit with appropriate code
        if isinstance(result, dict):
            if result.get('success') or result.get('overall_success'):
                sys.exit(0)
            else:
                sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n\n🛑 Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())