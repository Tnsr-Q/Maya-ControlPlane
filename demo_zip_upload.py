#!/usr/bin/env python3
"""
Maya ControlPlane Zip Upload Demo

This script demonstrates the zip file upload functionality.
It creates a sample zip file and shows how to use the upload API.
"""

import sys
import os
import tempfile
import zipfile
import json
from pathlib import Path

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_demo_zip():
    """Create a demo zip file with sample content"""
    # Create temporary zip file
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
        with zipfile.ZipFile(temp_zip.name, 'w') as zip_file:
            # Add sample files
            zip_file.writestr('README.md', '''# Demo Project

This is a demonstration project for Maya ControlPlane zip upload.

## Contents

- Configuration files
- Sample data
- Documentation
''')
            
            zip_file.writestr('config/settings.json', json.dumps({
                "app_name": "Maya Demo",
                "version": "1.0.0",
                "features": ["zip_upload", "ai_processing", "social_media"]
            }, indent=2))
            
            zip_file.writestr('data/sample.txt', 'This is sample data for processing.')
            
            zip_file.writestr('scripts/process.py', '''#!/usr/bin/env python3
"""Sample processing script"""

def main():
    print("Processing data...")
    
if __name__ == "__main__":
    main()
''')
        
        print(f"Created demo zip: {temp_zip.name}")
        return temp_zip.name

def demo_zip_helper():
    """Demonstrate zip helper functionality"""
    print("=== Zip Helper Demo ===")
    
    try:
        from helpers.zip_helper import create_zip_helper
        
        # Create zip helper
        zip_helper = create_zip_helper({
            'max_file_size': 10 * 1024 * 1024,  # 10MB
            'max_extracted_size': 50 * 1024 * 1024,  # 50MB
        })
        print("✓ Zip helper created")
        
        # Create demo zip
        demo_zip_path = create_demo_zip()
        
        # Read zip content
        with open(demo_zip_path, 'rb') as f:
            zip_content = f.read()
        
        print(f"✓ Demo zip created ({len(zip_content)} bytes)")
        
        # Process zip file
        result = zip_helper.process_uploaded_zip(zip_content, 'demo.zip')
        
        print("✓ Zip processed successfully!")
        print(f"  Extract directory: {result['extract_dir']}")
        print(f"  Files extracted: {len(result['extracted_files'])}")
        
        # Show extracted files
        print("\n  Extracted files:")
        for file_info in result['extracted_files']:
            status = "✓" if file_info['allowed'] else "⚠"
            print(f"    {status} {file_info['original_name']} ({file_info['size']} bytes, {file_info['extension']})")
        
        # Get detailed file info
        files_info = zip_helper.get_file_info(result['extract_dir'])
        print(f"\n  Detailed file analysis:")
        for file_info in files_info:
            print(f"    - {file_info['relative_path']}")
            print(f"      Size: {file_info['size']} bytes")
            print(f"      Hash: {file_info['hash'][:16]}...")
            print(f"      Modified: {file_info['modified']}")
        
        # Cleanup
        zip_helper.cleanup_extraction(result['extract_dir'])
        os.unlink(demo_zip_path)
        print("\n✓ Cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def demo_upload_routes():
    """Demonstrate upload routes (import test)"""
    print("\n=== Upload Routes Demo ===")
    
    try:
        from src.orchestrator.routes.upload import router
        print("✓ Upload routes module imported successfully")
        
        # Show available routes
        routes = []
        for route in router.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                for method in route.methods:
                    routes.append(f"{method} {route.path}")
        
        print("✓ Available upload endpoints:")
        for route in routes:
            print(f"    {route}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error importing upload routes: {e}")
        return False

def demo_fastapi_app():
    """Demonstrate FastAPI app creation"""
    print("\n=== FastAPI Integration Demo ===")
    
    try:
        from fastapi import FastAPI
        from src.orchestrator.routes.upload import router
        
        # Create demo app
        app = FastAPI(title="Maya ControlPlane Demo")
        app.include_router(router)
        
        print("✓ FastAPI app created with upload routes")
        
        # Show all routes
        routes = []
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                for method in route.methods:
                    if method != 'HEAD':  # Skip HEAD methods
                        routes.append(f"{method} {route.path}")
        
        print("✓ Available API endpoints:")
        for route in sorted(routes):
            print(f"    {route}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error creating FastAPI app: {e}")
        return False

def main():
    """Run all demos"""
    print("Maya ControlPlane Zip Upload Demonstration")
    print("=" * 50)
    
    # Test zip helper
    helper_success = demo_zip_helper()
    
    # Test upload routes
    routes_success = demo_upload_routes()
    
    # Test FastAPI integration
    fastapi_success = demo_fastapi_app()
    
    print("\n" + "=" * 50)
    print("Demo Results:")
    print(f"  Zip Helper: {'✓ PASS' if helper_success else '✗ FAIL'}")
    print(f"  Upload Routes: {'✓ PASS' if routes_success else '✗ FAIL'}")
    print(f"  FastAPI Integration: {'✓ PASS' if fastapi_success else '✗ FAIL'}")
    
    if all([helper_success, routes_success, fastapi_success]):
        print("\n🎉 All demos passed! Zip upload functionality is ready.")
        print("\nNext steps:")
        print("1. Start the Maya ControlPlane server: python -m hub.orchestrator")
        print("2. Upload a zip file using the API: POST /upload/zip")
        print("3. View the API documentation at: http://localhost:8000/docs")
    else:
        print("\n⚠ Some demos failed. Check the errors above.")

if __name__ == "__main__":
    main()