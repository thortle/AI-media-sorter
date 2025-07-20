# AI Media Description Generator

Successfully processing large photo collections using Moondream2 vision model on Apple Silicon.

## **Current Status: Phase 2 Development**

**Phase 1 Complete**: AI description generation for 8,330 photos ✅  
**Phase 2 In Progress**: Interactive photo search application using generated descriptions 🔄

### **Recent Achievements**
- ✅ **8,330 photos processed** with detailed AI descriptions
- ✅ **JSON database created** with searchable structured format
- ✅ **Multi-paragraph descriptions** properly captured and formatted
- ✅ **Keyword extraction system** implemented (4.2 avg keywords per photo)
- 🔄 **Keyword refinement** in progress for improved search accuracy

## **Phase 2: Interactive Photo Search**

Build an interactive search application using the generated descriptions:

### **JSON Database Creation**
```bash
# Convert descriptions to searchable JSON format
cd sorting && python3 json_converter.py

# With custom input/output files
cd sorting && python3 json_converter.py ../description/complete_descriptions.txt custom_output.json
```

### **Features In Development**
- **🔍 Keyword Search**: Find photos by content keywords
- **📝 Description Search**: Search within full AI-generated descriptions  
- **🏷️ Smart Tagging**: Improved keyword classification and accuracy
- **👤 Human Detection**: Proper gender classification (human + man/woman when appropriate)
- **🖼️ Photo Display**: View matching photos directly from search results

### **JSON Database Stats**
- **8,330 photos** with structured metadata
- **510 characters** average description length
- **4.2 keywords** per photo on average
- **Multi-paragraph descriptions** preserved with proper formatting
- **File path mapping** for direct photo access

## **Key Features**

- **🤖 Local AI Processing** - All analysis happens on Apple Silicon, no internet required
- **📝 Description Generation** - Generates detailed descriptions for all images in a directory
- **💾 HEIC Support** - Handles iPhone HEIC photos alongside JPG/PNG/TIFF
- **🎲 Flexible File Selection** - 6 different methods for processing files (random, newest, etc.)
- **📊 Complete Analysis** - Processes images only, automatically skips unsupported file types
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
cd description && python3 main.py "/path/to/your/photos"

# Limit to 100 files for testing
cd description && python3 main.py "/path/to/your/photos" --max-files 100

# Use random sampling with seed for reproducible results
cd description && python3 main.py "/path/to/your/photos" --selection-method random --random-seed 12345
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
cd description && python3 main.py "/Volumes/T7_SSD/G-photos"

# Test with small sample first
cd description && python3 main.py "/Volumes/T7_SSD/G-photos" --max-files 50

# Random sampling for unbiased testing
cd description && python3 main.py "/Volumes/T7_SSD/G-photos" --selection-method random --max-files 100 --random-seed 12345

# Process newest photos first
cd description && python3 main.py "/Volumes/T7_SSD/G-photos" --selection-method newest --max-files 200

# Custom output file
cd description && python3 main.py "/Volumes/T7_SSD/G-photos" --descriptions-file custom_descriptions.txt
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
├── CLAUDE.md                     # Development workflow guidance
├── README.md                     # Project documentation  
├── todo.md                       # Project status and planning
├── requirements.txt              # Python dependencies
├── description/                  # Phase 1: AI Description Generation
│   ├── main.py                   # Main CLI application for generating descriptions
│   ├── analyze_collection.py     # Collection analysis utility
│   ├── monitor_progress.py       # Progress monitoring utility
│   ├── check_progress.sh         # Shell script for progress checking
│   ├── complete_descriptions.txt # Generated descriptions output
│   ├── models/
│   │   ├── __init__.py
│   │   └── vision_model.py       # Simplified Moondream2 integration for image description
│   └── utils/
│       ├── __init__.py
│       ├── file_manager.py       # File discovery and selection methods
│       └── logger.py             # Logging configuration
└── sorting/                      # Phase 2: Photo Search & Display (In Development)
    ├── json_converter.py         # Convert descriptions.txt to searchable JSON format
    ├── descriptions.json         # JSON database of 8,330 photo descriptions with keywords
    ├── __init__.py
    └── utils/
        └── __init__.py
```

## **How It Works**

1. **Discover**: Scans the source directory recursively to find all supported image files (JPG, JPEG, PNG, TIFF, HEIC)
2. **Select**: Applies the chosen selection method (filesystem order, random, newest, oldest, etc.) and limits to max-files if specified
3. **Load Model**: Initializes Moondream2 vision model with Apple Silicon MPS acceleration for optimal performance
4. **Analyze**: For each image, generates detailed descriptions using multiple prompt strategies to ensure completeness (tries 3 different prompts: "Describe this image in complete sentences", "What do you see in this image?", and "Describe this image in detail" - returns the first complete description that ends with proper punctuation, or keeps the longest as fallback)
5. **Validate**: Automatically checks descriptions for proper completion (ending with punctuation) and attempts continuation if needed
6. **Output**: Saves filename and description pairs to the specified text file in a structured format

## **Performance**

- **Speed**: ~8 seconds per image on Apple Silicon (M1 Pro)
- **Memory**: ~4-6GB for Moondream2 model + processing
- **Accuracy**: Detailed, complete descriptions with multi-prompt validation
- **Production Status**: Successfully processing 8,330+ image collections

## **Environment Requirements**

- **Best Performance**: Internal drive
- **External Drive Issues**: macOS resource fork files can corrupt Python packages
- **Apple Silicon**: Optimized for M1/M2 with MPS acceleration
- **Python**: 3.8+ with virtual environment recommended

## **Troubleshooting**

**Environment issues on external drive:**
- Move project to internal drive
- Create fresh virtual environment on internal drive
- External drives can cause Unicode encoding errors

**Model download fails:**
- Check internet connection
- Ensure ~4GB free space

**Out of memory:**
- Close other applications
- Use smaller batch sizes with `--max-files`

**Incomplete descriptions:**
- Tool automatically handles this with multi-prompt validation (tries multiple prompts sequentially, validates each response for completeness by checking proper punctuation endings, and attempts to complete truncated descriptions)
- All descriptions verified to end with proper punctuation
