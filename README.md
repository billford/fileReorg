# Smart File Organizer for Mac

🗂️ **An intelligent Python application that automatically organizes, renames, and categorizes files in your Desktop, Downloads, and Documents folders using AI-powered content analysis.**

## ✨ Features

- **🔍 Smart File Discovery**: Automatically scans Desktop, Downloads, and Documents folders
- **🔄 Re-analysis Mode**: Re-run AI analysis on already organized files for better naming
- **🔍 Dry Run Preview**: See what changes would be made before applying them
- **📂 Selective Processing**: Choose specific folders to organize
- **🧠 AI-Powered Analysis**: Uses OpenAI GPT to analyze file content and suggest meaningful names
- **📂 Intelligent Categorization**: Organizes files into logical categories (Images, Documents, Code, etc.)
- **🏷️ Content-Based Renaming**: Renames files based on their actual content, not just filenames
- **📸 Photo Intelligence**: Extracts EXIF data from photos for date-based organization
- **📋 Comprehensive Logging**: Detailed logs of every action for transparency and reversal
- **🛡️ Safe Operation**: Preserves original files and handles conflicts automatically
- **🚫 System File Protection**: Automatically ignores system files and hidden files

## 🎯 What It Does

### Before:
```
Desktop/
├── IMG_1234.jpg
├── document.pdf
├── untitled.py
├── data.csv
└── presentation.pptx
```

### After:
```
Desktop/
├── Organized_Images/
│   └── sunset_beach_vacation_2024.jpg
├── Organized_Documents/
│   └── project_proposal_analysis.pdf
├── Organized_Code/
│   └── data_processing_script.py
├── Organized_Data/
│   └── sales_report_q4.csv
└── Organized_Presentations/
    └── marketing_strategy_2024.pptx
```

## 🛠️ Installation

### Prerequisites
- **Python 3.7+**
- **macOS** (tested on macOS 10.15+)
- **OpenAI API Key** (optional, for AI-powered analysis)

### OpenAI API Compatibility

The application supports **both** OpenAI API versions:
- **OpenAI v1.x** (Latest): `pip install openai>=1.0.0` 
- **OpenAI v0.x** (Legacy): `pip install "openai<1.0.0"`

The correct API is automatically detected and used. See `OPENAI_COMPATIBILITY.md` for details.

### Required Python Packages

```bash
# Essential packages
pip install python-magic Pillow

# Optional but recommended
pip install openai PyPDF2
```

### System Dependencies (macOS)

```bash
# Install libmagic (required for python-magic)
brew install libmagic

# Alternative using MacPorts
sudo port install file
```

## 🚀 Quick Start

1. **Download the script:**
   ```bash
   curl -O https://raw.githubusercontent.com/your-repo/file-organizer.py
   # or save the provided code as file_organizer.py
   ```

2. **Make it executable:**
   ```bash
   chmod +x file_organizer.py
   ```

3. **Run the organizer:**
   ```bash
   python file_organizer.py
   ```

4. **Or use re-analysis mode** (for already organized files):
   ```bash
   # Preview what would change
   python file_organizer.py --reanalyze --dry-run
   
   # Actually re-organize with better AI naming
   python file_organizer.py --reanalyze
   ```

4. **Follow the prompts:**
   - Enter your OpenAI API key (optional)
   - Confirm to proceed with organization

## 🔄 Re-Analysis Mode

**Perfect your file organization with AI-powered re-analysis!**

### When to Use Re-Analysis

- **First run without AI**: You organized files initially but didn't use OpenAI
- **Better AI models**: Want to re-run with improved AI analysis  
- **Misorganized files**: Some files ended up in wrong categories
- **Improved naming**: Get better, more descriptive filenames

### How Re-Analysis Works

1. **Scans organized folders**: Finds all `Organized_*` folders in your directories
2. **Re-reads file content**: Analyzes content again for better understanding
3. **Runs fresh AI analysis**: Gets new filename suggestions based on content
4. **Re-categorizes if needed**: Moves files to correct categories (e.g., Python files from Documents to Code)
5. **Renames intelligently**: Updates filenames with AI suggestions
6. **Logs everything**: Tracks all changes for transparency

### Re-Analysis Commands

```bash
# Preview changes without actually moving files
python file_organizer.py --reanalyze --dry-run

# Apply AI-powered improvements to organized files  
python file_organizer.py --reanalyze

# Re-analyze only specific folders
python file_organizer.py --reanalyze --folders Desktop Downloads

# Re-analyze with specific API key
python file_organizer.py --reanalyze --api-key sk-your-key-here

# Skip AI and use basic improvements only
python file_organizer.py --reanalyze --no-ai
```

### Example Re-Analysis Results

**Before Re-Analysis:**
```
Desktop/Organized_Documents/
├── document1.pdf
├── IMG_1234.txt  
└── file.py

Desktop/Organized_Images/
└── screenshot.png
```

**After Re-Analysis:**
```
Desktop/Organized_Documents/
├── quarterly_sales_report.pdf
└── meeting_notes_project_alpha.txt

Desktop/Organized_Code/
└── data_processing_script.py

Desktop/Organized_Images/
└── dashboard_screenshot_analytics.png
```

### Safe Re-Analysis

- **Dry run first**: Always preview changes with `--dry-run`
- **Complete logging**: Every change is logged for potential reversal
- **Conflict resolution**: Handles filename conflicts automatically
- **No data loss**: Files are moved, never deleted

## 🔧 Configuration

### OpenAI API Setup (Optional but Recommended)

1. Get your API key from [OpenAI Platform](https://platform.openai.com)
2. Enter it when prompted, or set as environment variable:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

### Folder Customization

Modify the `target_folders` dictionary in the script to change which folders are processed:

```python
self.target_folders = {
    'Desktop': self.home_path / 'Desktop',
    'Downloads': self.home_path / 'Downloads', 
    'Documents': self.home_path / 'Documents',
    # Add custom folders:
    # 'Projects': self.home_path / 'Projects'
}
```

## 📁 File Categories

The organizer creates the following subfolders:

| Category | File Types | Examples |
|----------|------------|----------|
| **Images** | `.jpg`, `.png`, `.gif`, `.svg` | Photos, graphics, icons |
| **Documents** | `.pdf`, `.doc`, `.txt`, `.pages` | Reports, letters, notes |
| **Spreadsheets** | `.xlsx`, `.csv`, `.numbers` | Data files, budgets |
| **Presentations** | `.pptx`, `.key`, `.odp` | Slideshows, pitches |
| **Audio** | `.mp3`, `.wav`, `.m4a` | Music, podcasts, recordings |
| **Video** | `.mp4`, `.mov`, `.mkv` | Movies, clips, tutorials |
| **Archives** | `.zip`, `.rar`, `.dmg` | Compressed files, installers |
| **Code** | `.py`, `.js`, `.html`, `.css` | Scripts, web files, source code |
| **Data** | `.json`, `.xml`, `.sql` | Configuration, databases |
| **Other** | All other files | Miscellaneous files |

## 📊 Logging & Reports

### Log Files Location
```
~/FileOrganizer_Logs/
├── file_organizer_20240728_143022.log    # Main log file
└── actions_log.jsonl                     # Detailed JSON log
```

### Log Contents
- **Main Log**: Human-readable activity log with timestamps
- **JSON Log**: Machine-readable log with complete metadata for each file action

### Sample JSON Log Entry
```json
{
  "original_path": "/Users/john/Desktop/IMG_1234.jpg",
  "new_path": "/Users/john/Desktop/Organized_Images/sunset_beach_vacation.jpg",
  "original_name": "IMG_1234.jpg",
  "new_name": "sunset_beach_vacation.jpg",
  "category": "Images",
  "mime_type": "image/jpeg",
  "metadata": {
    "size": "2048576",
    "created": "2024-07-15 14:30:22",
    "camera": "Apple iPhone 12"
  },
  "timestamp": "2024-07-28T14:30:45.123456"
}
```

## 🧠 AI Content Analysis

When OpenAI API is configured, the organizer:

1. **Reads file content** (first 500 characters for text files)
2. **Analyzes context** using GPT-3.5-turbo
3. **Suggests descriptive names** based on actual content
4. **Falls back** to metadata-based naming if AI fails

### Example AI Transformations
- `document.pdf` → `quarterly_sales_report.pdf`
- `untitled.py` → `web_scraper_script.py`
- `IMG_1234.jpg` → `golden_gate_bridge_sunset.jpg`

## ⚙️ Advanced Usage

### Command Line Options

```bash
# Basic organization
python file_organizer.py

# Re-analyze already organized files  
python file_organizer.py --reanalyze

# Preview re-analysis changes (safe)
python file_organizer.py --reanalyze --dry-run

# Organize specific folders only
python file_organizer.py --folders Desktop Documents

# Use specific OpenAI API key
python file_organizer.py --api-key sk-your-openai-key

# Disable AI analysis entirely
python file_organizer.py --no-ai

# Combine options
python file_organizer.py --reanalyze --folders Desktop --dry-run
```

### Dry Run Mode
Perfect for testing before making changes:

```python
# Preview what re-analysis would change
python file_organizer.py --reanalyze --dry-run

# Sample output:
# [DRY RUN] Would change document.pdf: name: document.pdf → sales_forecast_q4.pdf
# [DRY RUN] Would change script.txt: category: Documents → Code, name: script.txt → data_analyzer.py
```

### Workflow Recommendations

1. **Initial Organization**:
   ```bash
   # Start without AI to organize by file type
   python file_organizer.py --no-ai
   ```

2. **Add AI Intelligence**:
   ```bash
   # Preview AI improvements
   python file_organizer.py --reanalyze --dry-run
   
   # Apply improvements
   python file_organizer.py --reanalyze
   ```

3. **Periodic Maintenance**:
   ```bash
   # Re-analyze with newer AI models
   python file_organizer.py --reanalyze --folders Downloads
   ```

### Custom File Categories
Add your own categories by modifying the `file_categories` dictionary:

```python
self.file_categories['Ebooks'] = ['.epub', '.mobi', '.azw']
self.file_categories['3D_Models'] = ['.obj', '.fbx', '.blend']
```

## 🛡️ Safety Features

- **No File Deletion**: Files are moved, never deleted
- **Conflict Resolution**: Automatically handles duplicate filenames
- **System File Protection**: Ignores `.DS_Store`, hidden files, and system directories
- **Comprehensive Logging**: Every action is logged for potential reversal
- **Error Recovery**: Continues processing even if individual files fail

## 🚨 Troubleshooting

### Common Issues

**"ImportError: No module named 'magic'"**
```bash
# Install python-magic and its dependencies
pip install python-magic
brew install libmagic  # macOS
```

**"Permission denied" errors**
```bash
# Ensure proper permissions
chmod +x file_organizer.py
# Run with appropriate permissions for your home directory
```

**"Invalid API key" errors (Error 401)**
- Check that your API key starts with `sk-` (legacy) or `sk-proj-` (project-based)
- Legacy keys: ~48-51 characters, Project keys: ~164 characters
- Make sure there are no spaces, line breaks, or extra characters
- Get a fresh key from [OpenAI Platform](https://platform.openai.com/account/api-keys)
- Try using environment variable: `export OPENAI_API_KEY="sk-your-key"`
- See `API_KEY_TROUBLESHOOTING.md` for detailed solutions

**"openai.ChatCompletion" error**
- This was fixed in the latest version
- The app now supports both OpenAI v0.x and v1.x APIs automatically
- Update to the latest code version

**"OpenAI API error"**
- Verify your API key is correct
- Check your OpenAI account has available credits
- The script works without OpenAI (just with reduced smart naming)

**Files not being processed**
- Check the file isn't a system file (hidden or starting with '.')
- Verify the file extension is recognized in `file_categories`
- Check the main log file for specific error messages

### Debug Mode

Enable debug logging by modifying the logging level:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO
    # ... rest of configuration
)
```

## 🔄 Reverting Changes

To undo the organization:

1. **Check the JSON log** (`~/FileOrganizer_Logs/actions_log.jsonl`)
2. **Create a reversal script** using the logged paths:

```python
import json
import shutil

with open('~/FileOrganizer_Logs/actions_log.jsonl', 'r') as f:
    for line in f:
        action = json.loads(line)
        shutil.move(action['new_path'], action['original_path'])
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

### Development Setup
```bash
git clone <repository-url>
cd smart-file-organizer
pip install -r requirements.txt
python -m pytest tests/  # Run tests
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

- **Test First**: Always test on a small set of files before running on important data
- **Backup Important Files**: Consider backing up critical files before running
- **Review Results**: Check the organized files and logs after completion
- **AI Limitations**: AI-generated names may not always be perfect

## 📞 Support

- **Issues**: Report bugs and request features via GitHub Issues
- **Documentation**: Check this README and inline code comments
- **Logs**: Always check the log files for detailed error information

---

**Happy Organizing! 🎉**

*Made with ❤️ for productivity and file management*%
