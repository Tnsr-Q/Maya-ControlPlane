"""
Zip File Upload Routes

FastAPI routes for handling zip file uploads and processing in Maya ControlPlane.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Dict, Any
from datetime import datetime
import structlog

from helpers.zip_helper import ZipProcessingError

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/upload", tags=["file-upload"])


@router.post("/zip")
async def upload_zip_file(file: UploadFile = File(...)):
    """Upload and process zip files"""
    try:
        # Validate file type
        if not file.filename or not file.filename.endswith('.zip'):
            raise HTTPException(status_code=400, detail="Only ZIP files are allowed")
        
        # Import here to avoid circular imports
        from hub.orchestrator import get_orchestrator
        orchestrator = get_orchestrator()
        await orchestrator.initialize()
        
        # Read file content
        file_content = await file.read()
        
        # Process with zip helper
        result = orchestrator.helpers['zip'].process_uploaded_zip(file_content, file.filename)
        
        logger.info("Zip file uploaded successfully", 
                   filename=file.filename, 
                   size=len(file_content),
                   extracted_files=len(result.get('extracted_files', [])))
        
        return {
            "success": True,
            "message": "Zip file uploaded and processed successfully",
            "data": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except ZipProcessingError as e:
        logger.error("Zip processing failed", filename=file.filename, error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Zip upload failed", filename=file.filename, error=str(e))
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/zip/{extract_dir:path}/files")
async def get_extracted_files(extract_dir: str):
    """Get information about extracted files"""
    try:
        from hub.orchestrator import get_orchestrator
        orchestrator = get_orchestrator()
        await orchestrator.initialize()
        
        files_info = orchestrator.helpers['zip'].get_file_info(extract_dir)
        return {
            "success": True,
            "data": {
                "extract_dir": extract_dir,
                "files": files_info,
                "file_count": len(files_info)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error("Failed to get file info", extract_dir=extract_dir, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/zip/{extract_dir:path}")
async def cleanup_extracted_files(extract_dir: str):
    """Clean up extracted files"""
    try:
        from hub.orchestrator import get_orchestrator
        orchestrator = get_orchestrator()
        await orchestrator.initialize()
        
        orchestrator.helpers['zip'].cleanup_extraction(extract_dir)
        return {
            "success": True,
            "message": "Files cleaned up successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error("Failed to cleanup files", extract_dir=extract_dir, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))