"""
Final Integration Script for Zip Upload Functionality

This script ensures the upload routes are properly integrated into the orchestrator.
"""

import re
import os

def integrate_upload_routes():
    """Integrate upload routes into the orchestrator"""
    
    orchestrator_path = "hub/orchestrator.py"
    
    # Read the current orchestrator file
    with open(orchestrator_path, 'r') as f:
        content = f.read()
    
    # Check if upload routes are already integrated
    if "upload_router" in content:
        print("Upload routes already integrated")
        return True
    
    # Find the location after the health endpoint definition
    # We'll add it before the @self.app.post("/orchestrate"... line
    pattern = r'(\s+@self\.app\.post\("/orchestrate")'
    
    upload_routes_code = '''
        # Include Upload routes
        try:
            from src.orchestrator.routes.upload import router as upload_router
            self.app.include_router(upload_router)
            logger.info("Upload routes included successfully")
        except ImportError as e:
            logger.warning(f"Failed to import Upload routes: {e}")
        '''
    
    replacement = upload_routes_code + r'\1'
    
    new_content = re.sub(pattern, replacement, content)
    
    if new_content != content:
        # Write the updated content
        with open(orchestrator_path, 'w') as f:
            f.write(new_content)
        print("✓ Upload routes integrated into orchestrator")
        return True
    else:
        print("✗ Failed to integrate upload routes")
        return False

def create_minimal_integration():
    """Create a minimal integration file that can be imported"""
    
    integration_code = '''
"""
Zip Upload Integration for Maya ControlPlane

Import this module to add zip upload functionality to an existing FastAPI app.
"""

from fastapi import FastAPI
from src.orchestrator.routes.upload import router as upload_router

def add_zip_upload_to_app(app: FastAPI):
    """Add zip upload routes to an existing FastAPI application"""
    try:
        app.include_router(upload_router)
        print("✓ Zip upload routes added to FastAPI app")
        return True
    except Exception as e:
        print(f"✗ Failed to add zip upload routes: {e}")
        return False

# Auto-integration for the main orchestrator
def auto_integrate():
    """Automatically integrate with Maya orchestrator if available"""
    try:
        from hub.orchestrator import get_orchestrator
        orchestrator = get_orchestrator()
        return add_zip_upload_to_app(orchestrator.app)
    except Exception as e:
        print(f"Note: Auto-integration not available: {e}")
        return False

if __name__ == "__main__":
    auto_integrate()
'''
    
    with open("src/orchestrator/zip_integration.py", 'w') as f:
        f.write(integration_code)
    
    print("✓ Created zip integration helper")

def main():
    """Main integration function"""
    print("Integrating Zip Upload Functionality")
    print("=" * 40)
    
    # Try to integrate directly
    if integrate_upload_routes():
        print("✓ Direct integration successful")
    else:
        print("⚠ Direct integration failed, creating helper")
        create_minimal_integration()
    
    # Create uploads directory
    os.makedirs("uploads", exist_ok=True)
    print("✓ Created uploads directory")
    
    print("\nIntegration complete!")
    print("\nTo use the zip upload functionality:")
    print("1. Start the server: python -m hub.orchestrator")
    print("2. Upload files to: POST /upload/zip")
    print("3. View API docs at: http://localhost:8000/docs")

if __name__ == "__main__":
    main()