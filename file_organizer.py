#!/usr/bin/env python3
"""
Smart File Organizer for Mac
Organizes files in Desktop, Downloads, and Documents folders with AI-powered content analysis
"""

import os
import shutil
import logging
import mimetypes
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import json
import re

# Optional imports for enhanced functionality
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False
    print("Warning: python-magic not installed. Install with: pip install python-magic")

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("Warning: Pillow not installed. Install with: pip install Pillow")

try:
    import openai
    # Check OpenAI version to determine API usage
    OPENAI_VERSION = openai.__version__
    OPENAI_V1 = int(OPENAI_VERSION.split('.')[0]) >= 1
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    OPENAI_V1 = False
    OPENAI_VERSION = None
    print("Warning: OpenAI not installed. Install with: pip install openai")


class SmartFileOrganizer:
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize the file organizer"""
        self.home_path = Path.home()
        self.target_folders = {
            'Desktop': self.home_path / 'Desktop',
            'Downloads': self.home_path / 'Downloads', 
            'Documents': self.home_path / 'Documents'
        }
        
        # Setup logging
        self.setup_logging()
        
        # Initialize AI client if available
        self.ai_client = None
        if HAS_OPENAI and openai_api_key:
            # Validate and clean the API key
            cleaned_key = self.validate_and_clean_api_key(openai_api_key)
            if cleaned_key:
                try:
                    if OPENAI_V1:
                        # OpenAI v1.0.0+ (new client-based API)
                        self.ai_client = openai.OpenAI(api_key=cleaned_key)
                        # Test the API key with a simple request
                        self.test_openai_connection()
                    else:
                        # OpenAI v0.x (legacy API)
                        openai.api_key = cleaned_key
                        self.ai_client = openai
                        # Test the API key
                        self.test_openai_connection()
                    
                    self.logger.info("OpenAI API client initialized successfully")
                except Exception as e:
                    self.logger.error(f"Failed to initialize OpenAI client: {e}")
                    self.ai_client = None
            else:
                self.logger.warning("Invalid OpenAI API key provided - AI features disabled")
        elif HAS_OPENAI:
            # Check for API key in environment
            env_key = os.getenv('OPENAI_API_KEY')
            if env_key:
                self.logger.info("Using OpenAI API key from environment variable")
                # Use the environment key
                cleaned_key = self.validate_and_clean_api_key(env_key)
                if cleaned_key:
                    try:
                        if OPENAI_V1:
                            self.ai_client = openai.OpenAI(api_key=cleaned_key)
                            self.test_openai_connection()
                        else:
                            openai.api_key = cleaned_key
                            self.ai_client = openai
                            self.test_openai_connection()
                        self.logger.info("OpenAI API client initialized from environment")
                    except Exception as e:
                        self.logger.error(f"Failed to use environment API key: {e}")
                        self.ai_client = None
        
        # File type categories for organization
        self.file_categories = {
            'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.webp', '.ico'],
            'Documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.pages'],
            'Spreadsheets': ['.xls', '.xlsx', '.csv', '.numbers', '.ods'],
            'Presentations': ['.ppt', '.pptx', '.key', '.odp'],
            'Audio': ['.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a'],
            'Video': ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'],
            'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.dmg', '.pkg'],
            'Code': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.php', '.rb', '.go', '.swift'],
            'Data': ['.json', '.xml', '.yaml', '.yml', '.sql', '.db', '.sqlite']
        }
        
        # System files to ignore
        self.system_files = {'.DS_Store', '.localized', 'Thumbs.db', '.Trashes', '.fseventsd'}
    
    def validate_and_clean_api_key(self, api_key: str) -> Optional[str]:
        """Validate and clean the OpenAI API key"""
        if not api_key:
            return None
        
        # Strip whitespace and common problematic characters
        cleaned_key = api_key.strip().replace('\n', '').replace('\r', '').replace('\t', '')
        
        # Check if it looks like a valid OpenAI API key
        # OpenAI now supports multiple formats:
        # - Legacy: sk-... (48-51 chars)
        # - Project-based: sk-proj-... (longer, ~164 chars)
        valid_prefixes = ['sk-', 'sk-proj-']
        if not any(cleaned_key.startswith(prefix) for prefix in valid_prefixes):
            self.logger.error("OpenAI API key must start with 'sk-' or 'sk-proj-'")
            return None
        
        # Determine expected length based on key type
        if cleaned_key.startswith('sk-proj-'):
            # Project-based keys are much longer (around 164 characters)
            min_length, max_length = 150, 200
            key_type = "project-based"
        else:
            # Legacy keys are shorter (48-51 characters)
            min_length, max_length = 45, 60
            key_type = "legacy"
        
        # Check reasonable length for the key type
        if len(cleaned_key) < min_length or len(cleaned_key) > max_length:
            self.logger.error(f"OpenAI {key_type} API key has unusual length: {len(cleaned_key)} characters")
            self.logger.error(f"{key_type.title()} keys are typically {min_length}-{max_length} characters long")
            return None
        
        # Check for obvious corruption (no spaces or unusual characters in middle)
        if ' ' in cleaned_key or '\t' in cleaned_key:
            self.logger.error("OpenAI API key contains spaces or tabs - this is likely corrupted")
            return None
        
        # Log key info for debugging (without exposing the key)
        prefix_len = 12 if cleaned_key.startswith('sk-proj-') else 8
        self.logger.debug(f"API key validated: {key_type} key starts with '{cleaned_key[:prefix_len]}...', length: {len(cleaned_key)}")
        
        return cleaned_key
    
    def test_openai_connection(self):
        """Test the OpenAI API connection with a minimal request"""
        try:
            if OPENAI_V1:
                # Test with minimal request
                response = self.ai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=1
                )
            else:
                # Legacy API test
                response = self.ai_client.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=1
                )
            self.logger.info("OpenAI API connection test successful")
        except Exception as e:
            self.logger.error(f"OpenAI API connection test failed: {e}")
            # Parse the error to give better feedback
            if "invalid_api_key" in str(e):
                self.logger.error("API key is invalid. Please check your OpenAI API key.")
                self.logger.error("Get your API key from: https://platform.openai.com/account/api-keys")
            elif "insufficient_quota" in str(e):
                self.logger.error("OpenAI API quota exceeded. Please check your billing.")
            elif "rate_limit" in str(e):
                self.logger.error("OpenAI API rate limit exceeded. Please try again later.")
            raise
        
    def setup_logging(self):
        """Setup comprehensive logging"""
        log_dir = self.home_path / 'FileOrganizer_Logs'
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f'file_organizer_{timestamp}.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("File Organizer started")
        
    def is_system_file(self, file_path: Path) -> bool:
        """Check if file is a system file to ignore"""
        return (file_path.name in self.system_files or 
                file_path.name.startswith('.') or
                file_path.is_symlink())
    
    def get_file_type(self, file_path: Path) -> Tuple[str, str]:
        """Determine file type and category"""
        if not file_path.is_file():
            return "Unknown", "Other"
            
        # Get file extension
        ext = file_path.suffix.lower()
        
        # Use python-magic if available for better detection
        if HAS_MAGIC:
            try:
                mime_type = magic.from_file(str(file_path), mime=True)
                self.logger.debug(f"MIME type for {file_path.name}: {mime_type}")
            except Exception as e:
                self.logger.warning(f"Could not determine MIME type for {file_path.name}: {e}")
                mime_type = mimetypes.guess_type(str(file_path))[0]
        else:
            mime_type = mimetypes.guess_type(str(file_path))[0]
        
        # Categorize file
        for category, extensions in self.file_categories.items():
            if ext in extensions:
                return mime_type or "Unknown", category
        
        return mime_type or "Unknown", "Other"
    
    def extract_metadata(self, file_path: Path) -> Dict:
        """Extract metadata from files"""
        metadata = {
            'original_name': file_path.name,
            'size': file_path.stat().st_size,
            'created': datetime.fromtimestamp(file_path.stat().st_ctime),
            'modified': datetime.fromtimestamp(file_path.stat().st_mtime),
            'extension': file_path.suffix.lower()
        }
        
        # Extract EXIF data from images
        if HAS_PIL and file_path.suffix.lower() in ['.jpg', '.jpeg', '.tiff']:
            try:
                with Image.open(file_path) as img:
                    exif_data = img._getexif()
                    if exif_data:
                        exif = {TAGS.get(k, k): v for k, v in exif_data.items()}
                        metadata['exif'] = exif
                        # Extract useful info
                        if 'DateTime' in exif:
                            metadata['photo_date'] = exif['DateTime']
                        if 'Make' in exif and 'Model' in exif:
                            metadata['camera'] = f"{exif['Make']} {exif['Model']}"
            except Exception as e:
                self.logger.debug(f"Could not extract EXIF from {file_path.name}: {e}")
        
        return metadata
    
    def analyze_content_with_ai(self, file_path: Path, content_preview: str) -> str:
        """Use AI to analyze file content and suggest better name"""
        if not self.ai_client:
            return ""
            
        try:
            prompt = f"""
            Analyze this file content and suggest a descriptive filename (without extension).
            Original filename: {file_path.stem}
            File type: {file_path.suffix}
            Content preview: {content_preview[:500]}...
            
            Suggest a clear, descriptive filename that indicates the content. 
            Keep it under 50 characters and use underscores instead of spaces.
            Only return the suggested filename, nothing else.
            """
            
            if OPENAI_V1:
                # OpenAI v1.0.0+ API
                response = self.ai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=50,
                    temperature=0.3
                )
                suggested_name = response.choices[0].message.content.strip()
            else:
                # Legacy OpenAI API (v0.x)
                response = self.ai_client.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=50,
                    temperature=0.3
                )
                suggested_name = response.choices[0].message.content.strip()
            
            # Clean the suggested name
            suggested_name = re.sub(r'[^\w\-_]', '_', suggested_name)
            return suggested_name
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Provide specific error messages for common issues
            if "invalid_api_key" in error_msg or "401" in error_msg:
                self.logger.error(f"Invalid OpenAI API key for {file_path.name}")
                self.logger.error("Please check your API key at https://platform.openai.com/account/api-keys")
                # Disable AI client to prevent repeated failures
                self.ai_client = None
            elif "insufficient_quota" in error_msg or "429" in error_msg:
                self.logger.error(f"OpenAI quota/rate limit exceeded for {file_path.name}")
                self.logger.error("Please check your OpenAI billing or try again later")
            elif "model" in error_msg:
                self.logger.error(f"OpenAI model error for {file_path.name}: {e}")
            else:
                self.logger.warning(f"AI analysis failed for {file_path.name}: {e}")
            
            return ""
    
    def read_file_content(self, file_path: Path) -> str:
        """Read file content for analysis"""
        try:
            # Text files
            if file_path.suffix.lower() in ['.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.csv']:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read(1000)  # First 1000 chars
            
            # PDF files (basic text extraction)
            elif file_path.suffix.lower() == '.pdf':
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        text = ""
                        for page in reader.pages[:3]:  # First 3 pages
                            text += page.extract_text()
                        return text[:1000]
                except ImportError:
                    self.logger.debug("PyPDF2 not available for PDF reading")
                    return ""
            
            return ""
            
        except Exception as e:
            self.logger.debug(f"Could not read content from {file_path.name}: {e}")
            return ""
    
    def generate_smart_filename(self, file_path: Path, metadata: Dict, content: str) -> str:
        """Generate a smart filename based on content and metadata"""
        base_name = file_path.stem
        
        # Try AI analysis first
        if content and self.ai_client:
            ai_suggestion = self.analyze_content_with_ai(file_path, content)
            if ai_suggestion and len(ai_suggestion) > 3:
                return ai_suggestion
        
        # Fallback to metadata-based naming
        if 'photo_date' in metadata:
            date_str = metadata['photo_date'].replace(':', '').replace(' ', '_')
            return f"photo_{date_str}"
        
        # For documents, try to extract meaningful words from content
        if content and file_path.suffix.lower() in ['.txt', '.md', '.pdf', '.doc', '.docx']:
            words = re.findall(r'\b[A-Za-z]{4,}\b', content[:200])
            if len(words) >= 2:
                meaningful_name = '_'.join(words[:3]).lower()
                return meaningful_name
        
        # For code files, keep original name but clean it
        if file_path.suffix.lower() in ['.py', '.js', '.html', '.css', '.java', '.cpp']:
            cleaned_name = re.sub(r'[^\w\-_]', '_', base_name)
            return cleaned_name
        
        # Default: clean the original name
        return re.sub(r'[^\w\-_]', '_', base_name)
    
    def create_organized_folders(self, base_folder: Path):
        """Create organized folder structure"""
        for category in self.file_categories.keys():
            folder_path = base_folder / f"Organized_{category}"
            folder_path.mkdir(exist_ok=True)
            self.logger.info(f"Created/verified folder: {folder_path}")
        
        # Create "Other" folder for uncategorized files
        other_folder = base_folder / "Organized_Other"
        other_folder.mkdir(exist_ok=True)
    
    def organize_files_in_folder(self, folder_path: Path):
        """Organize all files in a specific folder"""
        if not folder_path.exists():
            self.logger.warning(f"Folder does not exist: {folder_path}")
            return
        
        self.logger.info(f"Processing folder: {folder_path}")
        
        # Create organized subfolders
        self.create_organized_folders(folder_path)
        
        # Get all files (not directories)
        files = [f for f in folder_path.iterdir() if f.is_file() and not f.name.startswith('Organized_')]
        
        self.logger.info(f"Found {len(files)} files to process")
        
        for file_path in files:
            try:
                # Skip system files
                if self.is_system_file(file_path):
                    self.logger.debug(f"Skipping system file: {file_path.name}")
                    continue
                
                # Get file type and category
                mime_type, category = self.get_file_type(file_path)
                self.logger.info(f"Processing: {file_path.name} (Type: {mime_type}, Category: {category})")
                
                # Extract metadata
                metadata = self.extract_metadata(file_path)
                
                # Read content for analysis
                content = self.read_file_content(file_path)
                
                # Generate smart filename
                new_name = self.generate_smart_filename(file_path, metadata, content)
                new_filename = f"{new_name}{file_path.suffix}"
                
                # Prepare destination
                dest_folder = folder_path / f"Organized_{category}"
                dest_path = dest_folder / new_filename
                
                # Handle filename conflicts
                counter = 1
                while dest_path.exists():
                    name_part = f"{new_name}_{counter}"
                    new_filename = f"{name_part}{file_path.suffix}"
                    dest_path = dest_folder / new_filename
                    counter += 1
                
                # Move and rename file
                shutil.move(str(file_path), str(dest_path))
                
                # Log the action
                action_log = {
                    'original_path': str(file_path),
                    'new_path': str(dest_path),
                    'original_name': file_path.name,
                    'new_name': new_filename,
                    'category': category,
                    'mime_type': mime_type,
                    'metadata': {k: str(v) for k, v in metadata.items()},  # Convert to strings for JSON
                    'timestamp': datetime.now().isoformat()
                }
                
                self.logger.info(f"Moved: {file_path.name} → {dest_path}")
                
                # Save detailed log to JSON file
                self.save_action_log(action_log)
                
            except Exception as e:
                self.logger.error(f"Error processing {file_path.name}: {e}")
    
    def save_action_log(self, action_log: Dict):
        """Save detailed action log to JSON file"""
        log_dir = self.home_path / 'FileOrganizer_Logs'
        actions_log_file = log_dir / 'actions_log.jsonl'
        
        with open(actions_log_file, 'a') as f:
            f.write(json.dumps(action_log) + '\n')
    
    def reanalyze_organized_files(self, folder_path: Path, dry_run: bool = False):
        """Re-analyze already organized files with AI and reorganize them"""
        if not folder_path.exists():
            self.logger.warning(f"Folder does not exist: {folder_path}")
            return
        
        self.logger.info(f"Re-analyzing organized files in: {folder_path}")
        
        # Find all Organized_* folders
        organized_folders = [f for f in folder_path.iterdir() 
                           if f.is_dir() and f.name.startswith('Organized_')]
        
        if not organized_folders:
            self.logger.info("No organized folders found - run initial organization first")
            return
        
        reanalysis_stats = {
            'files_processed': 0,
            'files_renamed': 0,
            'files_moved': 0,
            'ai_improvements': 0
        }
        
        for org_folder in organized_folders:
            current_category = org_folder.name.replace('Organized_', '')
            self.logger.info(f"Re-analyzing {current_category} files...")
            
            # Get all files in this organized folder
            files = [f for f in org_folder.iterdir() if f.is_file()]
            
            for file_path in files:
                try:
                    reanalysis_stats['files_processed'] += 1
                    
                    # Skip system files
                    if self.is_system_file(file_path):
                        continue
                    
                    self.logger.info(f"Re-analyzing: {file_path.name}")
                    
                    # Re-determine file type (might have changed categories)
                    mime_type, new_category = self.get_file_type(file_path)
                    
                    # Extract metadata again
                    metadata = self.extract_metadata(file_path)
                    
                    # Re-read content for AI analysis
                    content = self.read_file_content(file_path)
                    
                    # Generate new smart filename with AI
                    new_name = self.generate_smart_filename(file_path, metadata, content)
                    new_filename = f"{new_name}{file_path.suffix}"
                    
                    # Determine if we need to move to different category
                    needs_category_move = new_category != current_category
                    needs_rename = new_filename != file_path.name
                    
                    if needs_category_move or needs_rename:
                        # Prepare new destination
                        if needs_category_move:
                            new_dest_folder = folder_path / f"Organized_{new_category}"
                            new_dest_folder.mkdir(exist_ok=True)
                        else:
                            new_dest_folder = org_folder
                        
                        new_dest_path = new_dest_folder / new_filename
                        
                        # Handle filename conflicts
                        counter = 1
                        while new_dest_path.exists() and new_dest_path != file_path:
                            name_part = f"{new_name}_{counter}"
                            new_filename = f"{name_part}{file_path.suffix}"
                            new_dest_path = new_dest_folder / new_filename
                            counter += 1
                        
                        # Log the planned change
                        change_type = []
                        if needs_category_move:
                            change_type.append(f"category: {current_category} → {new_category}")
                            reanalysis_stats['files_moved'] += 1
                        if needs_rename:
                            change_type.append(f"name: {file_path.name} → {new_filename}")
                            reanalysis_stats['files_renamed'] += 1
                        
                        change_description = ", ".join(change_type)
                        
                        if dry_run:
                            self.logger.info(f"[DRY RUN] Would change {file_path.name}: {change_description}")
                        else:
                            # Actually move/rename the file
                            if new_dest_path != file_path:
                                shutil.move(str(file_path), str(new_dest_path))
                                self.logger.info(f"Updated: {change_description}")
                                
                                # Log the re-analysis action
                                reanalysis_log = {
                                    'action': 'reanalysis',
                                    'original_path': str(file_path),
                                    'new_path': str(new_dest_path),
                                    'original_name': file_path.name,
                                    'new_name': new_filename,
                                    'original_category': current_category,
                                    'new_category': new_category,
                                    'change_type': change_type,
                                    'mime_type': mime_type,
                                    'metadata': {k: str(v) for k, v in metadata.items()},
                                    'timestamp': datetime.now().isoformat()
                                }
                                self.save_action_log(reanalysis_log)
                        
                        # Count AI improvements (when filename significantly changes)
                        if needs_rename and len(new_name) > len(file_path.stem) + 5:
                            reanalysis_stats['ai_improvements'] += 1
                    
                    else:
                        if not dry_run:
                            self.logger.debug(f"No changes needed for: {file_path.name}")
                
                except Exception as e:
                    self.logger.error(f"Error re-analyzing {file_path.name}: {e}")
        
        # Log summary statistics
        action_word = "Would process" if dry_run else "Processed"
        self.logger.info(f"Re-analysis Summary:")
        self.logger.info(f"  {action_word} {reanalysis_stats['files_processed']} files")
        self.logger.info(f"  Files renamed: {reanalysis_stats['files_renamed']}")
        self.logger.info(f"  Files moved to new categories: {reanalysis_stats['files_moved']}")
        self.logger.info(f"  AI naming improvements: {reanalysis_stats['ai_improvements']}")
        
        return reanalysis_stats

    def run_reanalysis(self, dry_run: bool = False):
        """Run re-analysis on all target folders"""
        if not self.ai_client:
            self.logger.warning("AI client not available - re-analysis will use basic naming only")
        
        mode = "DRY RUN" if dry_run else "LIVE"
        self.logger.info(f"Starting File Re-analysis ({mode})")
        
        total_stats = {
            'files_processed': 0,
            'files_renamed': 0,
            'files_moved': 0,
            'ai_improvements': 0
        }
        
        for folder_name, folder_path in self.target_folders.items():
            try:
                self.logger.info(f"=" * 50)
                self.logger.info(f"Re-analyzing {folder_name} folder")
                folder_stats = self.reanalyze_organized_files(folder_path, dry_run)
                
                if folder_stats:
                    for key in total_stats:
                        total_stats[key] += folder_stats[key]
                        
            except Exception as e:
                self.logger.error(f"Error re-analyzing {folder_name}: {e}")
        
        self.logger.info("=" * 50)
        self.logger.info(f"Total Re-analysis Summary ({mode}):")
        self.logger.info(f"  Files processed: {total_stats['files_processed']}")
        self.logger.info(f"  Files renamed: {total_stats['files_renamed']}")
        self.logger.info(f"  Files moved: {total_stats['files_moved']}")
        self.logger.info(f"  AI improvements: {total_stats['ai_improvements']}")
        
        if dry_run:
            self.logger.info("This was a dry run - no files were actually changed")
            self.logger.info("Run without --dry-run to apply changes")
        else:
            self.logger.info("Re-analysis completed!")
        
        return total_stats

    def run(self):
        """Main execution method"""
        self.logger.info("Starting Smart File Organizer")
        
        for folder_name, folder_path in self.target_folders.items():
            try:
                self.logger.info(f"=" * 50)
                self.logger.info(f"Processing {folder_name} folder")
                self.organize_files_in_folder(folder_path)
            except Exception as e:
                self.logger.error(f"Error processing {folder_name}: {e}")
        
        self.logger.info("File organization completed!")
        self.logger.info(f"Logs saved to: {self.home_path / 'FileOrganizer_Logs'}")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Smart File Organizer for Mac - AI-powered file organization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python file_organizer.py                    # Normal organization
  python file_organizer.py --reanalyze        # Re-analyze organized files  
  python file_organizer.py --reanalyze --dry-run  # Preview re-analysis changes
  python file_organizer.py --api-key sk-...   # Use specific OpenAI key
  python file_organizer.py --test-api-key     # Test your OpenAI API key
  python file_organizer.py --no-ai            # Organize without AI
        """
    )
    
    parser.add_argument(
        '--reanalyze', 
        action='store_true',
        help='Re-analyze already organized files with AI and reorganize them'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true', 
        help='Preview changes without actually moving files (use with --reanalyze)'
    )
    
    parser.add_argument(
        '--api-key',
        type=str,
        help='OpenAI API key for AI-powered analysis'
    )
    
    parser.add_argument(
        '--no-ai',
        action='store_true',
        help='Disable AI analysis and use basic file organization only'
    )
    
    parser.add_argument(
        '--test-api-key',
        action='store_true',
        help='Test OpenAI API key and exit (useful for troubleshooting)'
    )
    
    parser.add_argument(
        '--folders',
        nargs='+',
        choices=['Desktop', 'Downloads', 'Documents'],
        help='Specify which folders to process (default: all)'
    )
    
    args = parser.parse_args()
    
    print("Smart File Organizer for Mac")
    print("=" * 40)
    
    # Special case: API key testing
    if args.test_api_key:
        print("🔑 OpenAI API Key Test Mode")
        print("=" * 40)
        
        test_key = args.api_key
        if not test_key:
            env_key = os.getenv('OPENAI_API_KEY')
            if env_key:
                print("✓ Found API key in environment variable")
                test_key = env_key
            else:
                test_key = input("Enter OpenAI API key to test: ").strip()
        
        if not test_key:
            print("❌ No API key provided")
            return
        
        # Test the key
        try:
            organizer = SmartFileOrganizer(openai_api_key=test_key)
            if organizer.ai_client:
                print("✅ API key is valid and working!")
                print("🎉 You can now use AI-powered file organization")
            else:
                print("❌ API key validation failed")
                print("📖 See API_KEY_TROUBLESHOOTING.md for help")
        except Exception as e:
            print(f"❌ API key test failed: {e}")
            print("📖 See API_KEY_TROUBLESHOOTING.md for troubleshooting")
        
        return
    
    # Handle API key
    openai_key = args.api_key
    if not openai_key and not args.no_ai:
        # Check environment variable first
        env_key = os.getenv('OPENAI_API_KEY')
        if env_key:
            print("✓ Using OpenAI API key from environment variable")
            openai_key = env_key
        else:
            print("\nOpenAI API Key Setup:")
            print("📋 You can get your API key from: https://platform.openai.com/account/api-keys")
            print("🔑 Your API key should start with 'sk-' (legacy) or 'sk-proj-' (project-based)")
            print("📏 Legacy keys: ~48-51 characters, Project keys: ~164 characters")
            print("💡 Tip: Set as environment variable with: export OPENAI_API_KEY='sk-your-key'")
            print()
            openai_key = input("Enter OpenAI API key (or press Enter to skip AI features): ").strip()
            
            if not openai_key:
                print("⚠️  Running without AI analysis - files will be organized by type only")
            elif not (openai_key.startswith('sk-') or openai_key.startswith('sk-proj-')):
                print("⚠️  Warning: API key should start with 'sk-' or 'sk-proj-'. Double-check your key format.")
                print("📖 See API_KEY_TROUBLESHOOTING.md if you're having issues")
            else:
                # Validate length based on key type
                if openai_key.startswith('sk-proj-'):
                    if len(openai_key) < 150 or len(openai_key) > 200:
                        print(f"⚠️  Warning: Project-based API key length ({len(openai_key)}) seems unusual.")
                        print("🔍 Project-based keys are typically ~164 characters long")
                elif len(openai_key) < 45 or len(openai_key) > 60:
                    print(f"⚠️  Warning: Legacy API key length ({len(openai_key)}) seems unusual.")
                    print("🔍 Legacy keys are typically 48-51 characters long")
    elif args.no_ai:
        openai_key = None
        print("🚫 AI analysis disabled by --no-ai flag")
    
    # Dry run is only valid with reanalyze
    if args.dry_run and not args.reanalyze:
        print("Error: --dry-run can only be used with --reanalyze")
        return
    
    # Create organizer
    organizer = SmartFileOrganizer(openai_api_key=openai_key)
    
    # Filter folders if specified
    if args.folders:
        filtered_folders = {name: path for name, path in organizer.target_folders.items() 
                          if name in args.folders}
        organizer.target_folders = filtered_folders
        print(f"Processing only: {', '.join(args.folders)}")
    
    if args.reanalyze:
        # Re-analysis mode
        print("\n🔄 RE-ANALYSIS MODE")
        print("This will re-analyze already organized files and improve their naming/categorization.")
        
        if args.dry_run:
            print("🔍 DRY RUN: No files will be actually moved - just showing what would change.")
        else:
            print("⚠️  This will actually move and rename files based on AI analysis.")
        
        if not args.dry_run:
            confirm = input("\nDo you want to proceed with re-analysis? (yes/no): ").strip().lower()
            if confirm != 'yes':
                print("Re-analysis cancelled.")
                return
        
        # Run re-analysis
        stats = organizer.run_reanalysis(dry_run=args.dry_run)
        
        if not args.dry_run and stats['files_renamed'] > 0:
            print(f"\n✅ Re-analysis complete! {stats['files_renamed']} files improved.")
    
    else:
        # Normal organization mode
        print("\n📁 ORGANIZATION MODE")
        print("This will organize files in your Desktop, Downloads, and Documents folders.")
        print("Files will be moved to organized subfolders and renamed based on content.")
        
        confirm = input("\nDo you want to proceed with organization? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Organization cancelled.")
            return
        
        # Run normal organization
        organizer.run()


if __name__ == "__main__":
    main()
