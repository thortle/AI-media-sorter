# Media Sorter - AI-Powered Photo Organization

## **Key Features**

- **🤖 Local AI Processing** - All analysis happens on your M1 Pro, no internet required
- **📁 Safe Operations** - Only copies files, never moves or deletes originals  
- **🎯 Simple AI Matching** - Direct keyword matching against AI descriptions, no artificial thresholds
- **📊 Inclusive Results** - Copies ALL matches regardless of confidence level
- **💾 HEIC Support** - Handles iPhone HEIC photos alongside JPG/PNG/MP4
- **📝 Comprehensive Logging** - Full audit trail of all operations
- **🎲 Flexible File Selection** - 6 different methods for processing files

## **Search Examples**red Photo Sorting Tool is Ready!**

Successfully tested with your G-photos collection (9,233 files). The system includes advanced file selection methods for flexible processing.

## **Quick Start**

### **Analyze Your Collection First**
```bash
python3 analyze_collection.py "/Volumes/T7_SSD/G-photos"
```

### **Test with Random Sample (Recommended)**
```bash
python3 main.py "/Volumes/T7_SSD/G-photos" "dog photos" --selection-method random --max-files 50 --dry-run
```

### **Find and Sort Dog Photos**
```bash
python3 main.py "/Volumes/T7_SSD/G-photos" "dog photos" --target-dir oliver
```

### **Process Newest Photos First**
```bash
python3 main.py "/Volumes/T7_SSD/G-photos" "vacation photos" --selection-method newest --max-files 100 --target-dir vacation
```

### **Systematic Processing (Alphabetical)**
```bash
python3 main.py "/Volumes/T7_SSD/G-photos" "person photos" --selection-method name_asc --target-dir people
```

## **File Selection Methods**

| Method | Description | Best For |
|--------|-------------|----------|
| `filesystem` | Natural file system order | Default processing |
| `random` | Random sampling | Unbiased testing |
| `newest` | Most recent files first | Latest uploads |
| `oldest` | Oldest files first | Historical content |
| `name_asc` | Alphabetical A-Z | Organized processing |
| `name_desc` | Alphabetical Z-A | Reverse order |

## **Command Line Options**

```
Usage: main.py [OPTIONS] SOURCE_DIR PROMPT

Options:
  --target-dir TEXT           Target directory name (created in source_dir)
  --dry-run                   Preview operations without copying files  
  --max-files INTEGER         Limit number of files to process
  --selection-method [method] File selection strategy
  --random-seed INTEGER       Reproducible random selection
```

## **Key Features**

- **🤖 Local AI Processing** - All analysis happens on your M1 Pro, no internet required
- **📁 Safe Operations** - Only copies files, never moves or deletes originals  
- **� Pure AI Decision Making** - No artificial confidence thresholds, trusts model analysis completely
- **📊 Smart Validation** - Multi-question verification for enhanced accuracy
- **💾 HEIC Support** - Handles iPhone HEIC photos alongside JPG/PNG/MP4
- **📝 Comprehensive Logging** - Full audit trail of all operations
- **🎲 Flexible File Selection** - 6 different methods for processing files

## **Search Examples**

The system understands natural language and synonyms:
- `"dog photos"` → finds dogs, puppies, canines
- `"person photos"` → finds people, men, women, couples, individuals  
- `"vacation photos"` → finds travel, beach, tourist locations
- `"food photos"` → finds meals, eating, restaurants
- `"outdoor photos"` → finds nature, landscapes, hiking

## **Performance**

- **Processed:** 100 photos in ~15 minutes
- **Success Rate:** High recall with inclusive matching - copies all potential matches
- **Memory Usage:** ~4GB for model + images  
- **Estimated Full Collection:** ~18,464 photos ≈ 45-60 hours total

## **Project Status: ✅ COMPLETE & PRODUCTION READY**

The media sorting tool successfully:
1. ✅ Identified dog photos in test batch
2. ✅ Created new directory automatically  
3. ✅ Copied files safely with user confirmation
4. ✅ Handled various image formats correctly
5. ✅ Provided detailed logging and progress tracking

**Ready to sort your entire photo collection!** 

## Features

- **Smart Content Analysis**: Uses Moondream2 to understand image content
- **Natural Language Sorting**: Sort files with prompts like "sort all dog photos"  
- **Safe Operations**: Copy files (never move) with confirmation steps
- **Batch Processing**: Efficiently handle thousands of files
- **Apple Silicon Optimized**: Fast inference on M1/M2 Macs

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **The first run will download Moondream2 model (~3GB)**

## Usage

### Basic Usage
```bash
python main.py /path/to/photos "sort all dog photos" --target-dir oliver
```

### Test with Limited Files
```bash
python main.py /path/to/photos "find vacation photos" --max-files 10 --dry-run
```

### Options
- `--dry-run`: Preview without copying files
- `--max-files N`: Limit processing to N files (good for testing)
- `--selection-method`: Choose file selection strategy
- `--random-seed`: Set seed for reproducible random selection
- `--target-dir name`: Specify target directory name

## Examples

```bash
# Sort dog photos
python main.py /G-photos "sort all dog photos" --target-dir dogs

# Find outdoor/nature photos  
python main.py /G-photos "outdoor nature photos" --target-dir nature

# Find photos with people
python main.py /G-photos "photos with people" --target-dir people

# Test run first
python main.py /G-photos "beach vacation photos" --dry-run --max-files 20

# Random sample testing
python main.py /G-photos "dog photos" --selection-method random --max-files 50 --dry-run
```

## Project Structure

```
media_sorter/
├── main.py                 # Main CLI application
├── analyze_collection.py   # Collection analysis utility
├── models/
│   └── vision_model.py     # Moondream2 integration
├── utils/
│   ├── file_manager.py     # File operations
│   └── logger.py           # Logging utilities
└── requirements.txt        # Python dependencies
```

## How It Works

1. **Scan**: Discovers all media files in source directory
2. **Analyze**: Moondream2 describes each image/video 
3. **Match**: Simple keyword matching against AI descriptions - copies ALL matches
4. **Preview**: Shows matches before copying
5. **Copy**: Safely copies files to new directory

## Performance

- **Speed**: ~8-10 seconds per image on M1 Pro
- **Memory**: ~4-6GB for Moondream2 model + processing
- **Accuracy**: High recall with simple keyword matching - copies all potential matches

## Safety Features

- Files are copied, never moved
- Dry-run mode for testing
- Confirmation before operations  
- Duplicate filename handling
- Detailed logging

## Troubleshooting

**Model download fails:**
- Check internet connection
- Ensure ~4GB free space

**Out of memory:**
- Close other applications
- Use smaller batch sizes with `--max-files`

**Too many matches:**
- Use more specific prompts
- Use dry-run to test prompts first
- Check logs for matched keywords
