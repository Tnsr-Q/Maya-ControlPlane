#!/usr/bin/env python3
"""
Simple test script for Maya ControlPlane zip upload functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import tempfile
import zipfile

def create_test_zip():
    """Create a test zip file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
        with zipfile.ZipFile(temp_zip.name, 'w') as zip_file:
            zip_file.writestr('test.txt', 'Hello from test zip!')
            zip_file.writestr('data/info.json', '{"message": "Test data"}')
            zip_file.writestr('README.md', '# Test Project\n\nThis is a test project.')
        
        print(f"Created test zip: {temp_zip.name}")
        return temp_zip.name

def test_zip_helper():
    """Test the zip helper functionality"""
    try:
        from helpers.zip_helper import create_zip_helper
        
        # Create zip helper
        zip_helper = create_zip_helper()
        print("✓ Zip helper created successfully")
        
        # Create test zip
        test_zip_path = create_test_zip()
        
        # Read zip content
        with open(test_zip_path, 'rb') as f:
            zip_content = f.read()
        
        # Process zip
        result = zip_helper.process_uploaded_zip(zip_content, 'test.zip')
        
        print(f"✓ Zip processed successfully")
        print(f"  - Files extracted: {len(result['extracted_files'])}")
        print(f"  - Extract directory: {result['extract_dir']}")
        
        # List extracted files
        for file_info in result['extracted_files']:
            print(f"    - {file_info['original_name']} ({file_info['size']} bytes)")
        
        # Clean up
        zip_helper.cleanup_extraction(result['extract_dir'])
        os.unlink(test_zip_path)
        print("✓ Cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_orchestrator_basic():
    """Test basic orchestrator functionality"""
    try:
        # Test importing our upload routes
        from src.orchestrator.routes.upload import router
        print("✓ Upload routes imported successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Error importing upload routes: {e}")
        return False

if __name__ == "__main__":
    print("Testing Maya ControlPlane Zip Upload Functionality")
    print("=" * 50)
    
    print("\n1. Testing Zip Helper...")
    zip_test_passed = test_zip_helper()
    
    print("\n2. Testing Orchestrator Routes...")
    routes_test_passed = test_orchestrator_basic()
    
    print("\n" + "=" * 50)
    if zip_test_passed and routes_test_passed:
        print("✓ All tests passed! Zip upload functionality is working.")
    else:
        print("✗ Some tests failed. Check the errors above.")