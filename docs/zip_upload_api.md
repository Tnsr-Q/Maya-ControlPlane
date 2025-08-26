# Zip File Upload API Documentation

## Overview

The Maya ControlPlane now supports secure zip file uploads for processing and content extraction. This feature allows users to upload zip archives containing various file types for analysis and management.

## API Endpoints

### POST `/upload/zip`

Upload and process a zip file.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: Form data with file field containing the zip file

**Response:**
```json
{
  "success": true,
  "message": "Zip file uploaded and processed successfully",
  "data": {
    "success": true,
    "extract_dir": "/tmp/maya_zip_extract_20240826_123456",
    "validation": {
      "valid": true,
      "file_count": 3,
      "total_size": 1024,
      "extracted_size": 2048,
      "files": [...]
    },
    "extracted_files": [
      {
        "original_name": "test.txt",
        "extracted_path": "/tmp/maya_zip_extract_20240826_123456/test.txt",
        "size": 512,
        "extension": ".txt",
        "allowed": true,
        "hash": "abc123..."
      }
    ],
    "upload_info": {
      "original_filename": "example.zip",
      "stored_filename": "20240826_123456_example.zip",
      "upload_path": "/uploads/20240826_123456_example.zip",
      "upload_size": 1024
    },
    "timestamp": "2024-08-26T12:34:56"
  },
  "timestamp": "2024-08-26T12:34:56"
}
```

### GET `/upload/zip/{extract_dir}/files`

Get detailed information about extracted files.

**Parameters:**
- `extract_dir`: Path to the extraction directory (URL encoded)

**Response:**
```json
{
  "success": true,
  "data": {
    "extract_dir": "/tmp/maya_zip_extract_20240826_123456",
    "files": [
      {
        "name": "test.txt",
        "relative_path": "test.txt",
        "size": 512,
        "extension": ".txt",
        "modified": "2024-08-26T12:34:56",
        "hash": "abc123..."
      }
    ],
    "file_count": 1
  },
  "timestamp": "2024-08-26T12:34:56"
}
```

### DELETE `/upload/zip/{extract_dir}`

Clean up extracted files and directories.

**Parameters:**
- `extract_dir`: Path to the extraction directory (URL encoded)

**Response:**
```json
{
  "success": true,
  "message": "Files cleaned up successfully",
  "timestamp": "2024-08-26T12:34:56"
}
```

## Security Features

### File Validation
- **File Type**: Only `.zip` files are accepted
- **Size Limits**: 
  - Maximum zip file size: 50MB (configurable)
  - Maximum extracted content: 200MB (configurable)
- **Path Security**: Prevents path traversal attacks (e.g., `../../../etc/passwd`)

### Content Analysis
- **File Extension Checking**: Validates extracted file types against allowlist
- **Hash Generation**: SHA256 checksums for all extracted files
- **Metadata Extraction**: File sizes, modification times, compression ratios

### Safe Extraction
- **Temporary Storage**: Files are extracted to secure temporary directories
- **Automatic Cleanup**: Extracted files are automatically cleaned up after processing
- **Zip Bomb Protection**: Prevents extraction of excessively large archives

## Configuration

The zip upload functionality can be configured through the `file_upload` section in the config:

```yaml
file_upload:
  max_file_size: 52428800  # 50MB in bytes
  max_extracted_size: 209715200  # 200MB in bytes
  upload_dir: "uploads"
  allowed_extensions:
    - ".txt"
    - ".md" 
    - ".json"
    - ".yaml"
    - ".yml"
    - ".py"
    - ".js"
    - ".html"
    - ".css"
    - ".jpg"
    - ".jpeg"
    - ".png"
    - ".gif"
    - ".mp4"
    - ".mp3"
    - ".wav"
    - ".pdf"
```

## Error Handling

### Common Error Codes

- **400 Bad Request**: Invalid file type, malicious content, or file too large
- **500 Internal Server Error**: Processing error or system failure

### Error Response Format

```json
{
  "detail": "Error description",
  "status_code": 400
}
```

## Usage Examples

### Python (using requests)

```python
import requests

# Upload a zip file
with open('example.zip', 'rb') as f:
    files = {'file': ('example.zip', f, 'application/zip')}
    response = requests.post('http://localhost:8000/upload/zip', files=files)
    result = response.json()

# Get file information
extract_dir = result['data']['extract_dir']
info_response = requests.get(f'http://localhost:8000/upload/zip/{extract_dir}/files')

# Clean up
cleanup_response = requests.delete(f'http://localhost:8000/upload/zip/{extract_dir}')
```

### cURL

```bash
# Upload zip file
curl -X POST "http://localhost:8000/upload/zip" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@example.zip;type=application/zip"

# Get file info (replace extract_dir with actual path)
curl -X GET "http://localhost:8000/upload/zip/{extract_dir}/files"

# Clean up
curl -X DELETE "http://localhost:8000/upload/zip/{extract_dir}"
```

## Integration

The zip upload functionality is integrated into the Maya ControlPlane orchestrator and can be combined with other platform adapters for content processing workflows.

## Limitations

- Only zip files are supported (no RAR, 7z, etc.)
- File content is not automatically processed beyond extraction
- Extracted files are stored temporarily and should be processed promptly
- No virus scanning is performed (implement separately if needed)