
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
