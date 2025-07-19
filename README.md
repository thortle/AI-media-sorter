# AI Media Description Generator

## **Status: ✅ PRODUCTION READY & RUNNING**

Successfully processing large photo collections using Moondream2 vision model on Apple Silicon.

## **Key Features**

- **🤖 Local AI Processing** - All analysis happens on Apple Silicon, no internet required
- **📝 Description Generation** - Generates detailed descriptions for all images in a directory
- **💾 HEIC Support** - Handles iPhone HEIC photos alongside JPG/PNG/TIFF
- **🎲 Flexible File Selection** - 6 different methods for processing files (random, newest, etc.)
- **📊 Complete Analysis** - Processes images only, skips video files automatically
- **🔧 Reproducible Results** - Use random seeds for consistent random sampling
- **✅ Production Tested** - Successfully processing 8,330+ image collections

## **Purpose**

This tool generates detailed AI-powered descriptions for image collections. Creates a comprehensive catalog of descriptions that can be used for:

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

## **Production Examples**

```bash
# Full-scale processing (production)
python3 main.py "/Volumes/T7_SSD/G-photos"

# Test with small sample first
python3 main.py "/Volumes/T7_SSD/G-photos" --max-files 50

# Random sampling for unbiased testing
python3 main.py "/Volumes/T7_SSD/G-photos" --selection-method random --max-files 100 --random-seed 12345

# Process newest photos first
python3 main.py "/Volumes/T7_SSD/G-photos" --selection-method newest --max-files 200

# Custom output file
python3 main.py "/Volumes/T7_SSD/G-photos" --descriptions-file custom_descriptions.txt
```

## **Output Format**

The tool generates a text file with the following format:
```
IMG_1234.HEIC - Description: A detailed AI-generated description of the image content...
IMG_5678.JPG - Description: Another detailed description...
```

## **Installation**

1. **Clone or copy project to internal drive (recommended):**
   ```bash
   # Environment works best on internal drive
   cp -r /path/to/media_sorter ~/Desktop/media_sorter
   cd ~/Desktop/media_sorter
   ```

2. **Set up Python virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **The first run will download Moondream2 model (~3GB)**

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

## **Performance**

- **Speed**: ~8 seconds per image on Apple Silicon (M1 Pro)
- **Memory**: ~4-6GB for Moondream2 model + processing
- **Accuracy**: Detailed, complete descriptions with multi-prompt validation
- **Production Status**: Successfully processing 8,330+ image collections

## **Environment Requirements**

- **Best Performance**: Internal drive (~/Desktop/media_sorter)
- **External Drive Issues**: macOS resource fork files can corrupt Python packages
- **Apple Silicon**: Optimized for M1/M2 with MPS acceleration
- **Python**: 3.8+ with virtual environment recommended

## **Troubleshooting**

**Environment issues on external drive:**
- Move project to internal drive (~/Desktop/media_sorter)
- Create fresh virtual environment on internal drive
- External drives can cause Unicode encoding errors

**Model download fails:**
- Check internet connection
- Ensure ~4GB free space

**Out of memory:**
- Close other applications
- Use smaller batch sizes with `--max-files`

**Incomplete descriptions:**
- Tool automatically handles this with multi-prompt validation
- All descriptions verified to end with proper punctuation
