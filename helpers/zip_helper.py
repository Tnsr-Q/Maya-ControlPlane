"""
Zip File Helper

Handles secure upload, validation, and processing of zip files for Maya ControlPlane.
Provides safe extraction with security checks to prevent malicious archives.
"""

import os
import tempfile
import zipfile
from typing import Dict, Any, List, Optional
from pathlib import Path
import shutil
import hashlib
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)


class ZipProcessingError(Exception):
    """Custom exception for zip processing errors"""
    pass


class ZipHelper:
    """Helper class for processing zip files safely"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.max_file_size = self.config.get('max_file_size', 50 * 1024 * 1024)  # 50MB default
        self.max_extracted_size = self.config.get('max_extracted_size', 200 * 1024 * 1024)  # 200MB default
        self.allowed_extensions = self.config.get('allowed_extensions', [
            '.txt', '.md', '.json', '.yaml', '.yml', '.py', '.js', '.html', '.css',
            '.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mp3', '.wav', '.pdf'
        ])
        self.upload_dir = Path(self.config.get('upload_dir', 'uploads'))
        self.upload_dir.mkdir(exist_ok=True)
        
        logger.info("ZipHelper initialized", 
                   max_file_size=self.max_file_size,
                   max_extracted_size=self.max_extracted_size)
    
    def validate_zip_file(self, file_path: Path) -> Dict[str, Any]:
        """Validate zip file before processing"""
        try:
            # Check file size
            file_size = file_path.stat().st_size
            if file_size > self.max_file_size:
                raise ZipProcessingError(f"File too large: {file_size} bytes (max: {self.max_file_size})")
            
            # Check if it's a valid zip file
            if not zipfile.is_zipfile(file_path):
                raise ZipProcessingError("File is not a valid zip archive")
            
            # Analyze zip contents
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                files_info = []
                total_extracted_size = 0
                
                for info in zip_ref.infolist():
                    # Check for path traversal attacks
                    if '..' in info.filename or info.filename.startswith('/'):
                        raise ZipProcessingError(f"Unsafe file path detected: {info.filename}")
                    
                    # Check extracted size to prevent zip bombs
                    total_extracted_size += info.file_size
                    if total_extracted_size > self.max_extracted_size:
                        raise ZipProcessingError(f"Extracted content too large: {total_extracted_size} bytes")
                    
                    files_info.append({
                        'filename': info.filename,
                        'size': info.file_size,
                        'compressed_size': info.compress_size,
                        'modified': datetime(*info.date_time)
                    })
                
                return {
                    'valid': True,
                    'file_count': len(files_info),
                    'total_size': file_size,
                    'extracted_size': total_extracted_size,
                    'files': files_info
                }
                
        except zipfile.BadZipFile as e:
            raise ZipProcessingError(f"Corrupted zip file: {str(e)}")
        except Exception as e:
            logger.error("Zip validation failed", error=str(e))
            raise ZipProcessingError(f"Validation failed: {str(e)}")
    
    def extract_zip_file(self, file_path: Path) -> Dict[str, Any]:
        """Safely extract zip file contents"""
        temp_extract_dir = None
        try:
            # Validate first
            validation_result = self.validate_zip_file(file_path)
            
            # Create temporary extraction directory
            temp_extract_dir = Path(tempfile.mkdtemp(prefix='maya_zip_extract_'))
            
            # Extract files
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                extracted_files = []
                
                for info in zip_ref.infolist():
                    # Skip directories
                    if info.is_dir():
                        continue
                    
                    # Extract file
                    extracted_path = temp_extract_dir / info.filename
                    extracted_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with zip_ref.open(info) as source, open(extracted_path, 'wb') as target:
                        shutil.copyfileobj(source, target)
                    
                    # Check file extension
                    file_ext = extracted_path.suffix.lower()
                    is_allowed = file_ext in self.allowed_extensions
                    
                    extracted_files.append({
                        'original_name': info.filename,
                        'extracted_path': str(extracted_path),
                        'size': info.file_size,
                        'extension': file_ext,
                        'allowed': is_allowed,
                        'hash': self._calculate_file_hash(extracted_path)
                    })
                
                logger.info("Zip file extracted successfully", 
                           file_count=len(extracted_files),
                           extract_dir=str(temp_extract_dir))
                
                return {
                    'success': True,
                    'extract_dir': str(temp_extract_dir),
                    'validation': validation_result,
                    'extracted_files': extracted_files,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            # Clean up on error
            if temp_extract_dir and temp_extract_dir.exists():
                shutil.rmtree(temp_extract_dir, ignore_errors=True)
            logger.error("Zip extraction failed", error=str(e))
            raise ZipProcessingError(f"Extraction failed: {str(e)}")
    
    def process_uploaded_zip(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Process uploaded zip file from raw bytes"""
        temp_zip_path = None
        try:
            # Generate unique filename
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            safe_filename = f"{timestamp}_{filename}"
            temp_zip_path = self.upload_dir / safe_filename
            
            # Write uploaded content to temporary file
            with open(temp_zip_path, 'wb') as f:
                f.write(file_content)
            
            logger.info("Zip file uploaded", filename=safe_filename, size=len(file_content))
            
            # Extract and process
            result = self.extract_zip_file(temp_zip_path)
            result['upload_info'] = {
                'original_filename': filename,
                'stored_filename': safe_filename,
                'upload_path': str(temp_zip_path),
                'upload_size': len(file_content)
            }
            
            return result
            
        except Exception as e:
            # Clean up on error
            if temp_zip_path and temp_zip_path.exists():
                temp_zip_path.unlink(missing_ok=True)
            logger.error("Zip processing failed", filename=filename, error=str(e))
            raise
    
    def cleanup_extraction(self, extract_dir: str):
        """Clean up extracted files"""
        try:
            extract_path = Path(extract_dir)
            if extract_path.exists() and extract_path.is_dir():
                shutil.rmtree(extract_path)
                logger.info("Cleaned up extraction directory", path=extract_dir)
        except Exception as e:
            logger.warning("Failed to cleanup extraction directory", path=extract_dir, error=str(e))
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.warning("Failed to calculate file hash", file=str(file_path), error=str(e))
            return ""
    
    def get_file_info(self, extract_dir: str) -> List[Dict[str, Any]]:
        """Get information about extracted files"""
        try:
            extract_path = Path(extract_dir)
            if not extract_path.exists():
                return []
            
            files_info = []
            for file_path in extract_path.rglob('*'):
                if file_path.is_file():
                    stat = file_path.stat()
                    files_info.append({
                        'name': file_path.name,
                        'relative_path': str(file_path.relative_to(extract_path)),
                        'size': stat.st_size,
                        'extension': file_path.suffix.lower(),
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'hash': self._calculate_file_hash(file_path)
                    })
            
            return files_info
            
        except Exception as e:
            logger.error("Failed to get file info", extract_dir=extract_dir, error=str(e))
            return []


def create_zip_helper(config: Optional[Dict[str, Any]] = None) -> ZipHelper:
    """Factory function to create ZipHelper instance"""
    return ZipHelper(config)