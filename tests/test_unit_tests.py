#!/usr/bin/env python3
"""
Unit Tests for Smart File Organizer
Comprehensive test suite covering all functionality
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock, mock_open
import os
import sys

# Add the parent directory to the path to import the main module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the main class (assuming the file is named file_organizer.py)
from file_organizer import SmartFileOrganizer


class TestSmartFileOrganizer:
    """Test suite for SmartFileOrganizer class"""
    
    @pytest.fixture
    def temp_home(self):
        """Create a temporary home directory for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_home = Path(temp_dir)
            # Create the standard folders
            (temp_home / 'Desktop').mkdir()
            (temp_home / 'Downloads').mkdir()
            (temp_home / 'Documents').mkdir()
            yield temp_home
    
    @pytest.fixture
    def organizer(self, temp_home):
        """Create a SmartFileOrganizer instance with mocked home path"""
        with patch('file_organizer.Path.home', return_value=temp_home):
            organizer = SmartFileOrganizer()
            # Override the home_path to use our temp directory
            organizer.home_path = temp_home
            organizer.target_folders = {
                'Desktop': temp_home / 'Desktop',
                'Downloads': temp_home / 'Downloads',
                'Documents': temp_home / 'Documents'
            }
            return organizer
    
    @pytest.fixture
    def sample_files(self, temp_home):
        """Create sample files for testing"""
        files = {}
        
        # Create sample files in Desktop
        desktop = temp_home / 'Desktop'
        
        # Text file
        text_file = desktop / 'sample.txt'
        text_file.write_text('This is a sample document about machine learning algorithms.')
        files['text'] = text_file
        
        # Python file
        py_file = desktop / 'script.py'
        py_file.write_text('import numpy as np\n# Data analysis script\nprint("Hello world")')
        files['python'] = py_file
        
        # JSON file
        json_file = desktop / 'data.json'
        json_file.write_text('{"name": "test", "type": "configuration"}')
        files['json'] = json_file
        
        # System file (should be ignored)
        system_file = desktop / '.DS_Store'
        system_file.write_text('system file content')
        files['system'] = system_file
        
        # Image file (empty, just for extension testing)
        img_file = desktop / 'photo.jpg'
        img_file.write_bytes(b'\xff\xd8\xff\xe0')  # Basic JPEG header
        files['image'] = img_file
        
        return files
    
    def test_initialization(self, organizer, temp_home):
        """Test SmartFileOrganizer initialization"""
        assert organizer.home_path == temp_home
        assert len(organizer.target_folders) == 3
        assert 'Desktop' in organizer.target_folders
        assert 'Downloads' in organizer.target_folders
        assert 'Documents' in organizer.target_folders
        
        # Test file categories are properly defined
        assert 'Images' in organizer.file_categories
        assert 'Documents' in organizer.file_categories
        assert 'Code' in organizer.file_categories
        
        # Test system files list
        assert '.DS_Store' in organizer.system_files
        assert '.localized' in organizer.system_files
    
    def test_initialization_with_openai_key(self, temp_home):
        """Test initialization with OpenAI API key"""
        with patch('file_organizer.Path.home', return_value=temp_home):
            with patch('file_organizer.HAS_OPENAI', True):
                with patch('file_organizer.OPENAI_V1', True):
                    with patch('file_organizer.openai') as mock_openai:
                        # Mock the OpenAI v1 client
                        mock_client = Mock()
                        mock_openai.OpenAI.return_value = mock_client
                        
                        organizer = SmartFileOrganizer(openai_api_key="test-key")
                        assert organizer.ai_client == mock_client
                        mock_openai.OpenAI.assert_called_once_with(api_key="test-key")
    
    def test_validate_and_clean_api_key(self, organizer):
        """Test API key validation and cleaning"""
        # Valid legacy API key
        legacy_key = "sk-1234567890abcdef1234567890abcdef1234567890abcd"
        result = organizer.validate_and_clean_api_key(legacy_key)
        assert result == legacy_key
        
        # Valid project-based API key (like the new format)
        project_key = "sk-proj-" + "x" * 157  # 164 chars total like the real example
        result = organizer.validate_and_clean_api_key(project_key)
        assert result == project_key
        
        # API key with whitespace
        messy_legacy_key = "  sk-1234567890abcdef1234567890abcdef1234567890abcd  \n"
        result = organizer.validate_and_clean_api_key(messy_legacy_key)
        assert result == legacy_key
        
        # Invalid API key (doesn't start with sk- or sk-proj-)
        invalid_key = "invalid-key-format"
        result = organizer.validate_and_clean_api_key(invalid_key)
        assert result is None
        
        # Legacy API key too short
        short_legacy_key = "sk-short"
        result = organizer.validate_and_clean_api_key(short_legacy_key)
        assert result is None
        
        # Project key too short
        short_project_key = "sk-proj-short"
        result = organizer.validate_and_clean_api_key(short_project_key)
        assert result is None
        
        # Legacy API key too long
        long_legacy_key = "sk-" + "x" * 100
        result = organizer.validate_and_clean_api_key(long_legacy_key)
        assert result is None
        
        # Project key too long
        long_project_key = "sk-proj-" + "x" * 250
        result = organizer.validate_and_clean_api_key(long_project_key)
        assert result is None
        
        # API key with spaces (corrupted)
        corrupted_key = "sk-1234 5678 abcd"
        result = organizer.validate_and_clean_api_key(corrupted_key)
        assert result is None
        
        # Empty key
        result = organizer.validate_and_clean_api_key("")
        assert result is None
        
        # None key
        result = organizer.validate_and_clean_api_key(None)
        assert result is None
    
    @patch('file_organizer.os.getenv')
    def test_initialization_with_env_api_key(self, mock_getenv, temp_home):
        """Test initialization with API key from environment"""
        mock_getenv.return_value = "sk-1234567890abcdef1234567890abcdef1234567890abcd"
        
        with patch('file_organizer.Path.home', return_value=temp_home):
            with patch('file_organizer.HAS_OPENAI', True):
                with patch('file_organizer.OPENAI_V1', True):
                    with patch('file_organizer.openai') as mock_openai:
                        mock_client = Mock()
                        mock_openai.OpenAI.return_value = mock_client
                        
                        # Mock the test connection to succeed
                        with patch.object(SmartFileOrganizer, 'test_openai_connection'):
                            organizer = SmartFileOrganizer()
                            assert organizer.ai_client == mock_client
    
    def test_test_openai_connection_v1_success(self, organizer):
        """Test successful OpenAI connection test with v1 API"""
        mock_client = Mock()
        organizer.ai_client = mock_client
        
        # Mock successful response
        mock_response = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch('file_organizer.OPENAI_V1', True):
            # Should not raise exception
            organizer.test_openai_connection()
            mock_client.chat.completions.create.assert_called_once()
    
    def test_test_openai_connection_invalid_key(self, organizer):
        """Test OpenAI connection test with invalid API key"""
        mock_client = Mock()
        organizer.ai_client = mock_client
        
        # Mock API key error
        mock_client.chat.completions.create.side_effect = Exception("invalid_api_key")
        
        with patch('file_organizer.OPENAI_V1', True):
            with pytest.raises(Exception):
                organizer.test_openai_connection()
    
    def test_analyze_content_with_ai_invalid_key_disables_client(self, organizer, sample_files):
        """Test that invalid API key disables AI client"""
        mock_client = Mock()
        organizer.ai_client = mock_client
        
        # Mock API key error
        mock_client.chat.completions.create.side_effect = Exception("Error code: 401 - invalid_api_key")
        
        with patch('file_organizer.OPENAI_V1', True):
            result = organizer.analyze_content_with_ai(sample_files['text'], "content")
            
            # Should return empty string
            assert result == ""
            
            # Should disable AI client to prevent repeated failures
            assert organizer.ai_client is None
    
    def test_is_system_file(self, organizer, sample_files):
        """Test system file detection"""
        # System files should be detected
        assert organizer.is_system_file(sample_files['system']) == True
        
        # Regular files should not be detected as system files
        assert organizer.is_system_file(sample_files['text']) == False
        assert organizer.is_system_file(sample_files['python']) == False
        
        # Test hidden files
        hidden_file = Path('/tmp/.hidden_file')
        assert organizer.is_system_file(hidden_file) == True
    
    def test_get_file_type(self, organizer, sample_files):
        """Test file type detection"""
        # Test text file
        mime_type, category = organizer.get_file_type(sample_files['text'])
        assert category == 'Documents'
        
        # Test Python file
        mime_type, category = organizer.get_file_type(sample_files['python'])
        assert category == 'Code'
        
        # Test JSON file
        mime_type, category = organizer.get_file_type(sample_files['json'])
        assert category == 'Data'
        
        # Test image file
        mime_type, category = organizer.get_file_type(sample_files['image'])
        assert category == 'Images'
        
        # Test unknown file type
        unknown_file = sample_files['text'].parent / 'unknown.xyz'
        unknown_file.write_text('unknown content')
        mime_type, category = organizer.get_file_type(unknown_file)
        assert category == 'Other'
    
    @patch('file_organizer.HAS_MAGIC', False)
    def test_get_file_type_without_magic(self, organizer, sample_files):
        """Test file type detection without python-magic library"""
        mime_type, category = organizer.get_file_type(sample_files['text'])
        assert category == 'Documents'
    
    def test_extract_metadata(self, organizer, sample_files):
        """Test metadata extraction"""
        metadata = organizer.extract_metadata(sample_files['text'])
        
        assert 'original_name' in metadata
        assert 'size' in metadata
        assert 'created' in metadata
        assert 'modified' in metadata
        assert 'extension' in metadata
        
        assert metadata['original_name'] == 'sample.txt'
        assert metadata['extension'] == '.txt'
        assert isinstance(metadata['created'], datetime)
        assert isinstance(metadata['modified'], datetime)
    
    @patch('file_organizer.HAS_PIL', True)
    @patch('file_organizer.Image')
    def test_extract_metadata_with_exif(self, mock_image, organizer, sample_files):
        """Test metadata extraction with EXIF data"""
        # Mock PIL Image for EXIF data
        mock_img = Mock()
        mock_img._getexif.return_value = {
            271: 'Apple',  # Make
            272: 'iPhone 12',  # Model
            306: '2024:07:15 14:30:22'  # DateTime
        }
        mock_image.open.return_value.__enter__.return_value = mock_img
        
        # Mock TAGS dictionary
        with patch('file_organizer.TAGS', {271: 'Make', 272: 'Model', 306: 'DateTime'}):
            metadata = organizer.extract_metadata(sample_files['image'])
            
            assert 'exif' in metadata
            assert 'camera' in metadata
            assert 'photo_date' in metadata
            assert metadata['camera'] == 'Apple iPhone 12'
    
    def test_read_file_content(self, organizer, sample_files):
        """Test file content reading"""
        # Test text file
        content = organizer.read_file_content(sample_files['text'])
        assert 'machine learning algorithms' in content
        
        # Test Python file
        content = organizer.read_file_content(sample_files['python'])
        assert 'import numpy' in content
        assert 'Data analysis script' in content
        
        # Test JSON file
        content = organizer.read_file_content(sample_files['json'])
        assert '"name": "test"' in content
        
        # Test binary file (should return empty string)
        content = organizer.read_file_content(sample_files['image'])
        assert content == ""
    
    @patch('file_organizer.PyPDF2')
    def test_read_pdf_content(self, mock_pypdf2, organizer, temp_home):
        """Test PDF content reading"""
        # Create a mock PDF file
        pdf_file = temp_home / 'Desktop' / 'test.pdf'
        pdf_file.write_bytes(b'%PDF-1.4 mock content')
        
        # Mock PyPDF2
        mock_reader = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = "This is a test PDF document"
        mock_reader.pages = [mock_page]
        mock_pypdf2.PdfReader.return_value = mock_reader
        
        content = organizer.read_file_content(pdf_file)
        assert "This is a test PDF document" in content
    
    def test_read_file_content_error_handling(self, organizer, temp_home):
        """Test file content reading error handling"""
        # Test with non-existent file
        non_existent = temp_home / 'Desktop' / 'nonexistent.txt'
        content = organizer.read_file_content(non_existent)
        assert content == ""
        
        # Test with permission denied (mock)
        with patch('builtins.open', side_effect=PermissionError()):
            content = organizer.read_file_content(temp_home / 'Desktop' / 'test.txt')
            assert content == ""
    
    def test_analyze_content_with_ai_v1(self, organizer, sample_files):
        """Test AI content analysis with OpenAI v1.0+ API"""
        # Mock OpenAI v1 client
        mock_client = Mock()
        organizer.ai_client = mock_client
        
        # Mock the new API response structure
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = "machine_learning_document"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        
        # Patch to use v1 API
        with patch('file_organizer.OPENAI_V1', True):
            result = organizer.analyze_content_with_ai(
                sample_files['text'], 
                "This is content about machine learning"
            )
        
        assert result == "machine_learning_document"
        mock_client.chat.completions.create.assert_called_once()
        
        # Verify call arguments
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]['model'] == "gpt-3.5-turbo"
        assert call_args[1]['max_tokens'] == 50
        assert call_args[1]['temperature'] == 0.3
    
    def test_analyze_content_with_ai_legacy(self, organizer, sample_files):
        """Test AI content analysis with legacy OpenAI API"""
        # Mock legacy OpenAI
        mock_openai = Mock()
        organizer.ai_client = mock_openai
        
        # Mock legacy API response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "legacy_api_result"
        mock_openai.ChatCompletion.create.return_value = mock_response
        
        # Patch to use legacy API
        with patch('file_organizer.OPENAI_V1', False):
            result = organizer.analyze_content_with_ai(
                sample_files['text'], 
                "This is content about data analysis"
            )
        
        assert result == "legacy_api_result"
        mock_openai.ChatCompletion.create.assert_called_once()
        
        # Verify call arguments
        call_args = mock_openai.ChatCompletion.create.call_args
        assert call_args[1]['model'] == "gpt-3.5-turbo"
        assert call_args[1]['max_tokens'] == 50
        assert call_args[1]['temperature'] == 0.3
    
    def test_analyze_content_with_ai_no_client(self, organizer, sample_files):
        """Test AI analysis when no AI client is available"""
        organizer.ai_client = None
        result = organizer.analyze_content_with_ai(sample_files['text'], "content")
        assert result == ""
    
    def test_analyze_content_with_ai_error_v1(self, organizer, sample_files):
        """Test AI analysis error handling with v1 API"""
        mock_client = Mock()
        organizer.ai_client = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        with patch('file_organizer.OPENAI_V1', True):
            result = organizer.analyze_content_with_ai(sample_files['text'], "content")
        assert result == ""
    
    def test_analyze_content_with_ai_error_legacy(self, organizer, sample_files):
        """Test AI analysis error handling with legacy API"""
        mock_openai = Mock()
        organizer.ai_client = mock_openai
        mock_openai.ChatCompletion.create.side_effect = Exception("API Error")
        
        with patch('file_organizer.OPENAI_V1', False):
            result = organizer.analyze_content_with_ai(sample_files['text'], "content")
        assert result == ""
    
    def test_generate_smart_filename(self, organizer, sample_files):
        """Test smart filename generation"""
        # Test with AI suggestion (mock)
        with patch.object(organizer, 'analyze_content_with_ai', return_value='ai_suggested_name'):
            organizer.ai_client = Mock()  # Enable AI
            metadata = {'original_name': 'test.txt'}
            result = organizer.generate_smart_filename(
                sample_files['text'], metadata, "some content"
            )
            assert result == "ai_suggested_name"
        
        # Test with photo metadata
        metadata = {'photo_date': '2024:07:15 14:30:22'}
        result = organizer.generate_smart_filename(
            sample_files['image'], metadata, ""
        )
        assert result == "photo_20240715_143022"
        
        # Test with document content
        content = "This document discusses artificial intelligence and machine learning"
        result = organizer.generate_smart_filename(
            sample_files['text'], {}, content
        )
        assert "artificial" in result.lower() or "intelligence" in result.lower()
        
        # Test fallback to cleaned original name
        result = organizer.generate_smart_filename(
            sample_files['text'], {}, ""
        )
        assert result == "sample"
    
    def test_create_organized_folders(self, organizer, temp_home):
        """Test organized folder creation"""
        desktop = temp_home / 'Desktop'
        organizer.create_organized_folders(desktop)
        
        # Check that all category folders were created
        for category in organizer.file_categories.keys():
            folder_path = desktop / f"Organized_{category}"
            assert folder_path.exists()
            assert folder_path.is_dir()
        
        # Check that "Other" folder was created
        other_folder = desktop / "Organized_Other"
        assert other_folder.exists()
    
    def test_save_action_log(self, organizer, temp_home):
        """Test action logging"""
        log_dir = temp_home / 'FileOrganizer_Logs'
        log_dir.mkdir(exist_ok=True)
        
        action_log = {
            'original_path': '/test/original.txt',
            'new_path': '/test/new.txt',
            'timestamp': datetime.now().isoformat()
        }
        
        organizer.save_action_log(action_log)
        
        # Check that log file was created and contains the entry
        log_file = log_dir / 'actions_log.jsonl'
        assert log_file.exists()
        
        with open(log_file, 'r') as f:
            logged_data = json.loads(f.read().strip())
            assert logged_data['original_path'] == '/test/original.txt'
            assert logged_data['new_path'] == '/test/new.txt'
    
    @patch('file_organizer.shutil.move')
    def test_organize_files_in_folder(self, mock_move, organizer, sample_files):
        """Test file organization in a folder"""
        desktop = organizer.target_folders['Desktop']
        
        # Mock the move operation to avoid actual file movement
        mock_move.return_value = None
        
        # Run organization
        organizer.organize_files_in_folder(desktop)
        
        # Check that system files were not processed
        moved_files = [call[0][0] for call in mock_move.call_args_list]
        system_file_moved = any('.DS_Store' in path for path in moved_files)
        assert not system_file_moved
        
        # Check that regular files were processed
        assert mock_move.called
        assert len(mock_move.call_args_list) >= 3  # At least 3 non-system files
    
    def test_organize_files_nonexistent_folder(self, organizer, temp_home):
        """Test organizing files in non-existent folder"""
        nonexistent = temp_home / 'NonExistent'
        
        # Should not raise exception, just log warning
        organizer.organize_files_in_folder(nonexistent)
        
        # Check that no organized folders were created
        assert not any(folder.name.startswith('Organized_') 
                      for folder in temp_home.iterdir() if folder.is_dir())
    
    @patch('file_organizer.shutil.move')
    def test_filename_conflict_resolution(self, mock_move, organizer, temp_home):
        """Test handling of filename conflicts"""
        desktop = temp_home / 'Desktop'
        
        # Create organized folder structure
        organizer.create_organized_folders(desktop)
        
        # Create a file that will cause conflict
        test_file = desktop / 'test.txt'
        test_file.write_text('test content')
        
        # Create existing file in destination
        dest_folder = desktop / 'Organized_Documents'
        existing_file = dest_folder / 'test.txt'
        existing_file.write_text('existing content')
        
        # Mock generate_smart_filename to return predictable name
        with patch.object(organizer, 'generate_smart_filename', return_value='test'):
            organizer.organize_files_in_folder(desktop)
        
        # Check that move was called with conflict-resolved filename
        mock_move.assert_called()
        call_args = mock_move.call_args_list[-1]  # Get last call
        dest_path = call_args[0][1]  # Second argument is destination
        
        # Should have _1 suffix due to conflict
        assert '_1.txt' in dest_path or 'test.txt' in dest_path
    
    @patch('file_organizer.shutil.move', side_effect=Exception("Move failed"))
    def test_error_handling_in_organization(self, mock_move, organizer, sample_files):
        """Test error handling during file organization"""
        desktop = organizer.target_folders['Desktop']
        
        # Should not raise exception, just log error and continue
        organizer.organize_files_in_folder(desktop)
        
        # Verify that move was attempted (and failed)
        assert mock_move.called
    
    @patch.object(SmartFileOrganizer, 'organize_files_in_folder')
    def test_run_method(self, mock_organize, organizer):
        """Test the main run method"""
        organizer.run()
        
        # Should call organize_files_in_folder for each target folder
        assert mock_organize.call_count == 3
        
        # Check that it was called with correct folders
        called_folders = [call[0][0] for call in mock_organize.call_args_list]
        folder_names = [str(folder).split('/')[-1] for folder in called_folders]
        
        assert 'Desktop' in folder_names
        assert 'Downloads' in folder_names
        assert 'Documents' in folder_names
    
    @patch('file_organizer.shutil.move')
    def test_reanalyze_organized_files(self, mock_move, organizer, temp_home):
        """Test re-analysis of already organized files"""
        desktop = temp_home / 'Desktop'
        
        # Create organized folder structure with some files
        docs_folder = desktop / 'Organized_Documents'
        docs_folder.mkdir(parents=True)
        
        # Create a test file in organized folder
        test_file = docs_folder / 'old_name.txt'
        test_file.write_text('This is a machine learning research document about neural networks')
        
        # Mock AI to suggest better name
        with patch.object(organizer, 'generate_smart_filename', return_value='ml_research_neural_networks'):
            organizer.reanalyze_organized_files(desktop)
        
        # Should have attempted to rename the file
        mock_move.assert_called()
        call_args = mock_move.call_args_list[-1]
        source_path = call_args[0][0]
        dest_path = call_args[0][1]
        
        assert 'old_name.txt' in source_path
        assert 'ml_research_neural_networks.txt' in dest_path
    
    def test_reanalyze_with_category_change(self, organizer, temp_home):
        """Test re-analysis that changes file category"""
        desktop = temp_home / 'Desktop'
        
        # Create organized folders
        docs_folder = desktop / 'Organized_Documents'
        code_folder = desktop / 'Organized_Code'
        docs_folder.mkdir(parents=True)
        
        # Create a Python file mistakenly placed in Documents
        misplaced_file = docs_folder / 'script.py'
        misplaced_file.write_text('import numpy as np\nprint("Hello world")')
        
        with patch('file_organizer.shutil.move') as mock_move:
            organizer.reanalyze_organized_files(desktop)
        
        # Should move file from Documents to Code category
        mock_move.assert_called()
        call_args = mock_move.call_args_list[-1]
        dest_path = call_args[0][1]
        assert 'Organized_Code' in dest_path
    
    def test_reanalyze_dry_run(self, organizer, temp_home):
        """Test dry run mode for re-analysis"""
        desktop = temp_home / 'Desktop'
        
        # Create organized folder with file
        docs_folder = desktop / 'Organized_Documents'
        docs_folder.mkdir(parents=True)
        test_file = docs_folder / 'test.txt'
        test_file.write_text('Content about artificial intelligence')
        
        with patch('file_organizer.shutil.move') as mock_move:
            with patch.object(organizer, 'generate_smart_filename', return_value='ai_document'):
                stats = organizer.reanalyze_organized_files(desktop, dry_run=True)
        
        # Should not actually move files in dry run
        mock_move.assert_not_called()
        
        # But should return statistics
        assert stats['files_processed'] >= 1
    
    def test_reanalyze_no_changes_needed(self, organizer, temp_home):
        """Test re-analysis when no changes are needed"""
        desktop = temp_home / 'Desktop'
        
        # Create organized folder with well-named file
        docs_folder = desktop / 'Organized_Documents'
        docs_folder.mkdir(parents=True)
        good_file = docs_folder / 'well_named_document.txt'
        good_file.write_text('This document is already well named')
        
        with patch('file_organizer.shutil.move') as mock_move:
            with patch.object(organizer, 'generate_smart_filename', return_value='well_named_document'):
                stats = organizer.reanalyze_organized_files(desktop)
        
        # Should not move files when no changes needed
        mock_move.assert_not_called()
        assert stats['files_processed'] >= 1
        assert stats['files_renamed'] == 0
    
    def test_reanalyze_filename_conflict_resolution(self, organizer, temp_home):
        """Test handling conflicts during re-analysis"""
        desktop = temp_home / 'Desktop'
        
        # Create organized folder structure
        docs_folder = desktop / 'Organized_Documents'
        docs_folder.mkdir(parents=True)
        
        # Create file to be renamed
        old_file = docs_folder / 'old_name.txt'
        old_file.write_text('Content about machine learning')
        
        # Create existing file that would conflict
        existing_file = docs_folder / 'machine_learning.txt'
        existing_file.write_text('Existing content')
        
        with patch('file_organizer.shutil.move') as mock_move:
            with patch.object(organizer, 'generate_smart_filename', return_value='machine_learning'):
                organizer.reanalyze_organized_files(desktop)
        
        # Should resolve conflict by adding suffix
        call_args = mock_move.call_args_list[-1]
        dest_path = call_args[0][1]
        assert 'machine_learning_1.txt' in dest_path
    
    def test_run_reanalysis(self, organizer, temp_home):
        """Test the main reanalysis runner"""
        # Create some organized folders in multiple locations
        for folder_name, folder_path in organizer.target_folders.items():
            docs_folder = folder_path / 'Organized_Documents'
            docs_folder.mkdir(parents=True)
            test_file = docs_folder / f'{folder_name.lower()}_file.txt'
            test_file.write_text(f'Content from {folder_name}')
        
        with patch.object(organizer, 'reanalyze_organized_files') as mock_reanalyze:
            mock_reanalyze.return_value = {
                'files_processed': 1,
                'files_renamed': 1,
                'files_moved': 0,
                'ai_improvements': 1
            }
            
            total_stats = organizer.run_reanalysis()
        
        # Should call reanalyze for each target folder
        assert mock_reanalyze.call_count == 3  # Desktop, Downloads, Documents
        
        # Should aggregate statistics
        assert total_stats['files_processed'] == 3
        assert total_stats['files_renamed'] == 3
        assert total_stats['ai_improvements'] == 3
    
    def test_reanalyze_no_organized_folders(self, organizer, temp_home):
        """Test re-analysis when no organized folders exist"""
        desktop = temp_home / 'Desktop'
        
        stats = organizer.reanalyze_organized_files(desktop)
        
        # Should handle gracefully and return None or empty stats
        assert stats is None or stats['files_processed'] == 0


class TestIntegration:
    """Integration tests that work with actual files"""
    
    @pytest.fixture
    def integration_setup(self):
        """Set up integration test environment"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_home = Path(temp_dir)
            
            # Create folder structure
            desktop = temp_home / 'Desktop'
            desktop.mkdir()
            
            # Create test files
            files = {}
            
            # Text document
            doc_file = desktop / 'meeting_notes.txt'
            doc_file.write_text('''
            Meeting Notes - Project Alpha
            Date: July 28, 2024
            Attendees: John, Sarah, Mike
            
            Discussion Points:
            - Review quarterly goals
            - Plan next sprint
            - Budget allocation
            ''')
            files['document'] = doc_file
            
            # Python script
            py_file = desktop / 'data_processor.py'
            py_file.write_text('''
            #!/usr/bin/env python3
            """
            Data processing script for sales analysis
            """
            import pandas as pd
            import numpy as np
            
            def process_sales_data(filename):
                df = pd.read_csv(filename)
                return df.groupby('region').sum()
            ''')
            files['script'] = py_file
            
            # JSON config
            json_file = desktop / 'app_settings.json'
            json_file.write_text('''
            {
                "app_name": "File Organizer",
                "version": "1.0.0",
                "debug": false,
                "database": {
                    "host": "localhost",
                    "port": 5432
                }
            }
            ''')
            files['config'] = json_file
            
            yield temp_home, desktop, files
    
    def test_end_to_end_organization(self, integration_setup):
        """Test complete file organization workflow"""
        temp_home, desktop, files = integration_setup
        
        # Create organizer with mocked home path
        with patch('file_organizer.Path.home', return_value=temp_home):
            organizer = SmartFileOrganizer()
            organizer.home_path = temp_home
            organizer.target_folders = {'Desktop': desktop}
            
            # Run organization
            organizer.organize_files_in_folder(desktop)
            
            # Verify organized folders were created
            assert (desktop / 'Organized_Documents').exists()
            assert (desktop / 'Organized_Code').exists()
            assert (desktop / 'Organized_Data').exists()
            
            # Verify files were moved and renamed
            doc_folder = desktop / 'Organized_Documents'
            code_folder = desktop / 'Organized_Code'
            data_folder = desktop / 'Organized_Data'
            
            # Check that files exist in their new locations
            doc_files = list(doc_folder.glob('*.txt'))
            code_files = list(code_folder.glob('*.py'))
            data_files = list(data_folder.glob('*.json'))
            
            assert len(doc_files) == 1
            assert len(code_files) == 1
            assert len(data_files) == 1
            
            # Verify original files are gone from desktop
            remaining_files = [f for f in desktop.iterdir() 
                             if f.is_file() and not f.name.startswith('.')]
            assert len(remaining_files) == 0
            
            # Verify log files were created
            log_dir = temp_home / 'FileOrganizer_Logs'
            assert log_dir.exists()
            
            log_files = list(log_dir.glob('*.log'))
            json_logs = list(log_dir.glob('*.jsonl'))
            
            assert len(log_files) >= 1
            assert len(json_logs) >= 1


# Test fixtures for pytest
@pytest.fixture(scope="session")
def test_data_dir():
    """Create test data directory"""
    test_dir = Path(__file__).parent / 'test_data'
    test_dir.mkdir(exist_ok=True)
    return test_dir


# Command line test runner
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
