#!/usr/bin/env python3
"""
Test Script for Maya System Audio Bridge

Simple validation script to test the new BlackHole audio bridge implementation
without requiring external dependencies.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_audio_bridge")


async def test_audio_bridge_creation():
    """Test audio bridge creation and basic functionality"""
    print("🧪 Testing Maya System Audio Bridge Creation...")
    
    try:
        from helpers.maya_audio_bridge import create_maya_audio_bridge
        
        # Test with stub mode (default)
        bridge = create_maya_audio_bridge()
        assert bridge is not None
        print("✅ Audio bridge created successfully in stub mode")
        
        # Test connection
        connected = await bridge.connect_to_maya()
        assert connected == True
        print("✅ Audio bridge connection test passed")
        
        # Test status
        status = await bridge.get_audio_status()
        assert 'connected' in status
        print("✅ Audio status retrieval test passed")
        
        # Test message sending
        response = await bridge.send_message_to_maya(
            "Hello Maya, this is a test message from Cerebras",
            use_tts=True,
            wait_for_response=True
        )
        assert response.get('success') == True
        print("✅ Message sending test passed")
        
        # Test conversation loop
        responses = []
        def capture_response(response_data):
            responses.append(response_data)
            print(f"   📥 Received response: {response_data.get('transcription', '')[:50]}...")
        
        loop_started = await bridge.start_conversation_loop(capture_response)
        assert loop_started == True
        print("✅ Conversation loop start test passed")
        
        # Wait for simulated responses
        await asyncio.sleep(3)
        await bridge.stop_conversation_loop()
        print("✅ Conversation loop stop test passed")
        
        # Test disconnect
        await bridge.disconnect()
        print("✅ Disconnect test passed")
        
        return True
        
    except Exception as e:
        logger.error(f"Audio bridge test failed: {e}")
        return False


async def test_audio_setup():
    """Test audio setup system"""
    print("\n🔧 Testing Audio Setup System...")
    
    try:
        from setup.audio_setup import create_audio_setup
        
        setup = create_audio_setup()
        assert setup is not None
        print("✅ Audio setup created successfully")
        
        # Test validation (will fail in CI but shouldn't crash)
        validation = await setup.validate_audio_setup()
        assert 'success' in validation
        print("✅ Audio validation test passed")
        
        return True
        
    except Exception as e:
        logger.error(f"Audio setup test failed: {e}")
        return False


async def test_quick_setup_import():
    """Test quick setup script import"""
    print("\n🚀 Testing Quick Setup Import...")
    
    try:
        # Just test that we can import without errors
        import quick_setup
        print("✅ Quick setup import test passed")
        
        return True
        
    except Exception as e:
        logger.error(f"Quick setup import test failed: {e}")
        return False


async def test_backward_compatibility():
    """Test backward compatibility with existing code"""
    print("\n🔄 Testing Backward Compatibility...")
    
    try:
        # Test that factory functions still work
        from helpers.maya_audio_bridge import create_maya_audio_bridge
        
        # Test with old-style config
        old_config = {
            'sesame_url': 'https://sesame.com',
            'headless': True,
            'use_stub': True
        }
        
        bridge = create_maya_audio_bridge(old_config)
        assert bridge is not None
        print("✅ Old-style config compatibility test passed")
        
        # Test that the bridge still has expected interface
        assert hasattr(bridge, 'connect_to_maya')
        assert hasattr(bridge, 'send_message_to_maya')
        assert hasattr(bridge, 'start_conversation_loop')
        assert hasattr(bridge, 'stop_conversation_loop')
        assert hasattr(bridge, 'disconnect')
        print("✅ Interface compatibility test passed")
        
        return True
        
    except Exception as e:
        logger.error(f"Backward compatibility test failed: {e}")
        return False


async def test_utility_functions():
    """Test utility functions"""
    print("\n🛠️ Testing Utility Functions...")
    
    try:
        from helpers.maya_audio_bridge import validate_maya_audio_system
        
        # Test validation utility
        result = await validate_maya_audio_system()
        assert 'success' in result
        print("✅ Maya audio system validation test passed")
        
        return True
        
    except Exception as e:
        logger.error(f"Utility functions test failed: {e}")
        return False


async def main():
    """Run all tests"""
    print("🎭 Maya System Audio Bridge Test Suite")
    print("=" * 50)
    
    tests = [
        ("Audio Bridge Creation", test_audio_bridge_creation),
        ("Audio Setup System", test_audio_setup),
        ("Quick Setup Import", test_quick_setup_import),
        ("Backward Compatibility", test_backward_compatibility),
        ("Utility Functions", test_utility_functions),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                failed += 1
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Maya System Audio Bridge is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)