# Project Structure

This is the clean, production-ready AI media sorter. 

## Core Files

```
media_sorter/
├── main.py                 # CLI interface and main application logic
├── analyze_collection.py   # Collection analysis utility
├── requirements.txt        # Python dependencies
├── README.md              # Documentation and usage guide
├── models/
│   ├── __init__.py
│   └── vision_model.py    # Moondream2 integration with HEIC support
└── utils/
    ├── __init__.py
    ├── file_manager.py     # File operations and selection methods
    └── logger.py          # Logging configuration
```

## Essential Components

1. **main.py** - The heart of the application
   - CLI interface with Click
   - File selection methods integration
   - Pure AI-based decision making (no confidence threshold)
   - Dry-run and batch processing support

2. **models/vision_model.py** - AI engine
   - Moondream2 vision-language model
   - HEIC support via pillow-heif
   - Enhanced confidence calculation
   - Apple Silicon (MPS) optimization

3. **utils/file_manager.py** - File operations
   - 6 file selection methods (filesystem, random, newest, oldest, name_asc, name_desc)
   - Media file discovery and validation
   - Safe file copying operations

4. **analyze_collection.py** - Analysis utility
   - Collection overview and statistics
   - File type distribution
   - Selection method previews

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Analyze collection
python3 analyze_collection.py /path/to/photos

# Sort photos with AI
python3 main.py /path/to/photos "dog photos" --target-dir dogs --dry-run
```

## Key Features

- Local AI processing (no internet required)
- Pure model-based decision making
- Multiple file selection strategies
- HEIC and video support
- Apple Silicon optimized
- Safe operations (copy-only)
