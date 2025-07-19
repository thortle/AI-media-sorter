# AI Media Description Generator

## **Key Features**

- **🤖 Local AI Processing** - All analysis happens on Apple Silicon, no internet required
- **� Description Generation** - Generates detailed descriptions for all images in a directory
- **💾 HEIC Support** - Handles iPhone HEIC photos alongside JPG/PNG/TIFF
- **🎲 Flexible File Selection** - 6 different methods for processing files (random, newest, etc.)
- **📊 Complete Analysis** - Processes images only, skips video files automatically
- **🔧 Reproducible Results** - Use random seeds for consistent random sampling

## **Purpose**

This tool generates detailed AI-powered descriptions for image collections. Instead of sorting or organizing files, it creates a comprehensive catalog of descriptions that can be used for:

- Content analysis and search
- Building datasets for machine learning
- Creating searchable metadata for large photo collections
- Understanding what's in your photos without manually reviewing them

## **Quick Start**

### **Basic Usage**
```bash
# Generate descriptions for all images
python3 main.py "/path/to/your/photos"

# Limit to 100 files for testing
python3 main.py "/path/to/your/photos" --max-files 100

# Use random sampling with seed for reproducible results
python3 main.py "/path/to/your/photos" --selection-method random --random-seed 12345
```

### **Analyze Your Collection First**
```bash
python3 analyze_collection.py "/path/to/your/photos"
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
Usage: main.py [OPTIONS] SOURCE_DIR

Options:
  --max-files INTEGER         Limit number of files to process (for testing)
  --selection-method [method] File selection strategy
  --random-seed INTEGER       Random seed for reproducible random selection
  --descriptions-file TEXT    File to save descriptions to (default: descriptions.txt)
  --help                      Show help message and exit
```

## **Examples**

```bash
# Generate descriptions for all images in a directory
python3 main.py "/Volumes/T7_SSD/G-photos"

# Test with a small sample first
python3 main.py "/Volumes/T7_SSD/G-photos" --max-files 50

# Random sampling with custom output file
python3 main.py "/Volumes/T7_SSD/G-photos" --selection-method random --max-files 100 --descriptions-file sample_descriptions.txt

# Process newest photos first
python3 main.py "/Volumes/T7_SSD/G-photos" --selection-method newest --max-files 200

# Reproducible random sampling
python3 main.py "/Volumes/T7_SSD/G-photos" --selection-method random --random-seed 12345 --max-files 100
```
  ## **Output Format**

The tool generates a text file with the following format:
```
IMG_1234.HEIC - Description: A detailed AI-generated description of the image content...
IMG_5678.JPG - Description: Another detailed description...
```

## **Performance**

- **Speed**: ~8-10 seconds per image on Apple Silicon
- **Memory**: ~4-6GB for Moondream2 model + processing
- **Accuracy**: Detailed, complete descriptions with multi-prompt validation

## **Installation**

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **The first run will download Moondream2 model (~3GB)**

## **Project Structure**

```
media_sorter/
├── main.py                 # Main CLI application  
├── analyze_collection.py   # Collection analysis utility
├── models/
│   └── vision_model.py     # Moondream2 integration with enhanced description generation
├── utils/
│   ├── file_manager.py     # File operations and selection methods
│   └── logger.py           # Logging utilities
└── requirements.txt        # Python dependencies
```

## **How It Works**

1. **Scan**: Discovers all image files in source directory (skips videos automatically)
2. **Analyze**: Moondream2 generates detailed descriptions using multi-prompt strategy
3. **Validate**: Ensures descriptions are complete and properly formatted
4. **Save**: Writes filename + description pairs to output file

## **Troubleshooting**

**Model download fails:**
- Check internet connection
- Ensure ~4GB free space

**Out of memory:**
- Close other applications
- Use smaller batch sizes with `--max-files`

**Incomplete descriptions:**
- The tool now automatically handles this with multi-prompt validation
- All descriptions are verified to end with proper punctuation
```

## **Key Features**

- **🤖 Local AI Processing** - All analysis happens on Apple Silicon, no internet required
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

- **Processed:** Sample testing shows efficient processing rates
- **Success Rate:** High recall with inclusive matching - copies all potential matches
- **Memory Usage:** ~4GB for model + images  
- **Estimated Processing:** ~8-10 seconds per image on Apple Silicon

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
- **Apple Silicon Optimized**: Fast inference on Apple Silicon Macs

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **The first run will download Moondream2 model (~3GB)**

## Usage

### Basic Usage
```bash
python main.py /path/to/photos "sort all dog photos" --target-dir dogs
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
python main.py /path/to/photos "sort all dog photos" --target-dir dogs

# Find outdoor/nature photos  
python main.py /path/to/photos "outdoor nature photos" --target-dir nature

# Find photos with people
python main.py /path/to/photos "photos with people" --target-dir people

# Test run first
python main.py /path/to/photos "beach vacation photos" --dry-run --max-files 20

# Random sample testing
python main.py /path/to/photos "dog photos" --selection-method random --max-files 50 --dry-run
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

- **Speed**: ~8-10 seconds per image on Apple Silicon
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
