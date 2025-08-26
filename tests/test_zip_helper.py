"""
Test suite for Zip Helper functionality

Tests for secure zip file upload, validation, and processing.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tempfile
import zipfile
from pathlib import Path
from helpers.zip_helper import ZipHelper, ZipProcessingError, create_zip_helper


class TestZipHelper:
    """Test ZIP file processing functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.zip_helper = create_zip_helper()
        
    def test_create_zip_helper(self):
        """Test zip helper creation"""
        helper = create_zip_helper()
        assert isinstance(helper, ZipHelper)
        assert helper.max_file_size == 50 * 1024 * 1024  # 50MB default
        
    def test_create_test_zip(self):
        """Test creation of a valid zip file"""
        # Create a temporary zip file for testing
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
            with zipfile.ZipFile(temp_zip.name, 'w') as zip_file:
                zip_file.writestr('test.txt', 'Hello, World!')
                zip_file.writestr('folder/nested.txt', 'Nested content')
            
            # Validate the test zip
            validation_result = self.zip_helper.validate_zip_file(Path(temp_zip.name))
            
            assert validation_result['valid'] is True
            assert validation_result['file_count'] == 2
            assert len(validation_result['files']) == 2
            
            # Clean up
            Path(temp_zip.name).unlink()
    
    def test_invalid_zip_file(self):
        """Test handling of invalid zip files"""
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
            temp_file.write(b'This is not a zip file')
            temp_file.flush()
            
            try:
                self.zip_helper.validate_zip_file(Path(temp_file.name))
                assert False, "Should have raised ZipProcessingError"
            except ZipProcessingError as e:
                assert "File is not a valid zip archive" in str(e)
            
            # Clean up
            Path(temp_file.name).unlink()
    
    def test_process_uploaded_zip(self):
        """Test processing uploaded zip content"""
        # Create test zip content
        with tempfile.NamedTemporaryFile() as temp_zip:
            with zipfile.ZipFile(temp_zip.name, 'w') as zip_file:
                zip_file.writestr('test.txt', 'Test content')
                zip_file.writestr('data.json', '{"key": "value"}')
            
            # Read the zip content
            with open(temp_zip.name, 'rb') as f:
                zip_content = f.read()
            
            # Process the zip
            result = self.zip_helper.process_uploaded_zip(zip_content, 'test.zip')
            
            assert result['success'] is True
            assert 'extract_dir' in result
            assert 'extracted_files' in result
            assert len(result['extracted_files']) == 2
            assert 'upload_info' in result
            assert result['upload_info']['original_filename'] == 'test.zip'
            
            # Clean up
            if 'extract_dir' in result:
                self.zip_helper.cleanup_extraction(result['extract_dir'])


if __name__ == "__main__":
    # Run basic tests without pytest
    test_instance = TestZipHelper()
    test_instance.setup_method()
    
    print("Testing zip helper creation...")
    test_instance.test_create_zip_helper()
    print("✓ Zip helper creation test passed")
    
    print("Testing valid zip file...")
    test_instance.test_create_test_zip()
    print("✓ Valid zip file test passed")
    
    print("Testing invalid zip file...")
    test_instance.test_invalid_zip_file()
    print("✓ Invalid zip file test passed")
    
    print("Testing zip processing...")
    test_instance.test_process_uploaded_zip()
    print("✓ Zip processing test passed")
    
    print("All basic tests passed!")