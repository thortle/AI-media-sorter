# AI Media Description Generator

## **Current Status: Phase 2 Development**

**Phase 1 Complete**: AI description generation for 8,330 photos ✅  
**Phase 2 In Progress**: AI-powered keyword extraction and interactive photo search 🔄

### **Recent Achievements**
- ✅ **8,330 photos processed** with detailed AI descriptions
- ✅ **JSON database created** with searchable structured format
- ✅ **Multi-paragraph descriptions** properly captured and formatted
- ✅ **AI keyword extraction system** using llama3.2:3b for human character detection
- ✅ **Semantic character recognition** handling diverse descriptive vocabulary 

## **Phase 2: Interactive Photo Search**

Build an interactive search application using the generated descriptions:

### **JSON Database Creation**
```bash
# Convert descriptions to searchable JSON format
cd sorting && python3 json_converter.py

# With custom input/output files
cd sorting && python3 json_converter.py ../description/complete_descriptions.txt custom_output.json
```

### **AI-Powered Keyword Extraction**
Uses Ollama with llama3.2:3b model to intelligently detect human characters in photo descriptions:

```bash
# Process all photos for character detection
cd sorting && python3 process_keywords.py

# Test mode: process only specific number of photos
cd sorting && python3 process_keywords.py --test 10
cd sorting && python3 process_keywords.py --test 50
```

**Character Detection Features:**
- **🤖 LLM-Powered Analysis**: Uses llama3.2:3b via Ollama for intelligent text analysis
- **👥 Human Character Detection**: Identifies mentions of people using descriptive terms from descriptions
- **� Structured Keywords**: Adds `has_characters` boolean and detailed character array to JSON
- **🎯 Adaptive Recognition**: Handles varied descriptive language that manual parsing cannot catch
- **⚡ Batch Processing**: Processes photos in configurable batches with progress saving

**Why LLM for Keyword Extraction:**
The initial vision model used diverse vocabulary when describing people (man, woman, child, hiker, gentleman, tourist, couple, student, individuals, etc.). Manual keyword matching would miss many variations, but LLMs excel at understanding semantic meaning regardless of specific word choice.

### **Features In Development**
- **🔍 Character-Based Search**: Find photos containing people using the new boolean flags
- **📝 Description Search**: Search within full AI-generated descriptions
- **👤 Face Recognition Training**: Train model to identify recurring faces using photos flagged as containing people

### **JSON Database Stats**
- **8,330 photos** with structured metadata (local database only)
- **510 characters** average description length
- **AI-powered character detection** with semantic understanding
- **example.json** provided in repository for structure reference

## **Key Features**

- **🤖 Local AI Processing** - All analysis happens on Apple Silicon, no internet required
- **📝 Description Generation** - Generates detailed descriptions for all images
- **💾 HEIC Support** - Handles iPhone HEIC photos alongside JPG/PNG/TIFF
- **🎲 Flexible File Selection** - 6 different methods for processing files (random, newest, etc.)
- **📊 Complete Analysis** - Processes images only, automatically skips unsupported file types
- **✅ Production Tested** - Successfully processing 8,330+ image collections

## **Purpose**

This tool generates detailed AI-powered descriptions for image collections. Creates a comprehensive catalog of descriptions that can be used for:

- Content analysis and search
- Building datasets for machine learning
- Creating searchable metadata for large photo collections

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

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **The first run will download Moondream2 model (~3GB)**

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
│   ├── complete_descriptions.txt # Generated descriptions output (local only)
│   ├── models/
│   │   ├── __init__.py
│   │   └── vision_model.py       # Simplified Moondream2 integration for image description
│   └── utils/
│       ├── __init__.py
│       ├── file_manager.py       # File discovery and selection methods
│       └── logger.py             # Logging configuration
└── sorting/                      # Phase 2: Photo Search & Display (In Development)
    ├── json_converter.py         # Convert descriptions.txt to searchable JSON format
    ├── process_keywords.py       # AI-powered keyword extraction using llama3.2:3b via Ollama
    ├── example.json              # Example JSON structure for reference (in repo)
    ├── descriptions.json         # Full JSON database with private photo data (local only, not in repo)
    ├── __init__.py
    └── utils/
        └── __init__.py
```

## **How It Works**

### **Phase 1: AI Description Generation**
1. **Discover**: Scans the source directory recursively to find all supported image files (JPG, JPEG, PNG, TIFF, HEIC)
2. **Select**: Applies the chosen selection method (filesystem order, random, newest, oldest, etc.) and limits to max-files if specified
3. **Load Model**: Initializes Moondream2 vision model with Apple Silicon MPS acceleration for optimal performance
4. **Analyze**: For each image, generates detailed descriptions using multiple prompt strategies to ensure completeness (tries 3 different prompts: "Describe this image in complete sentences", "What do you see in this image?", and "Describe this image in detail" - returns the first complete description that ends with proper punctuation, or keeps the longest as fallback)
5. **Validate**: Automatically checks descriptions for proper completion (ending with punctuation) and attempts continuation if needed
6. **Output**: Saves filename and description pairs to the specified text file in a structured format

### **Phase 2: AI-Powered Keyword Extraction**
1. **Load JSON Database**: Reads the structured photo descriptions from `descriptions.json`
2. **Initialize LLM**: Connects to Ollama running llama3.2:3b model locally
3. **Semantic Analysis**: For each photo description, sends carefully crafted prompt to detect human characters
4. **Character Detection**: LLM identifies presence of people using semantic understanding, not keyword matching
5. **Structure Results**: Adds `keywords` object with `has_characters` boolean and detailed `characters` array
6. **Batch Processing**: Processes photos in configurable batches (default 50) with automatic progress saving
7. **Update Database**: Saves enhanced JSON with character detection metadata

**Keyword Extraction Example:**
```json
{
  "filename": "IMG_1713.HEIC",
  "description": "A man stands confidently on a grassy hill, holding a bouquet of vibrant purple flowers...",
  "keywords": {
    "has_characters": true,
    "characters": [
      {
        "type": "man",
        "count": 1
      }
    ]
  }
}
```

**Note:** The full `descriptions.json` database containing private photo data is kept locally only. The repository includes `example.json` showing the data structure for reference.

## **Future Development Roadmap**

### **Phase 3: Advanced Features (Planned)**
- **👤 Face Recognition Training**: Train a custom model to identify recurring faces across the photo collection
  - Use `has_characters: true` photos as training dataset
  - Focus computational resources only on photos containing people
  - Build face embeddings for clustering and identification
- **🔍 Advanced Search Interface**: Web-based search application with filters
- **📊 Analytics Dashboard**: Statistics about photo collection content
- **🏷️ Extended Keyword Categories**: Expand beyond character detection to objects, scenes, activities

## **Performance**

- **Speed**: ~8 seconds per image on Apple Silicon (M1 Pro)
- **Accuracy**: Detailed, complete descriptions with multi-prompt validation
- **Production Status**: Successfully processed 8,330+ image collections

## **Environment Requirements**

- **Best Performance**: Internal drive
- **External Drive Issues**: macOS resource fork files can corrupt Python packages
- **Apple Silicon**: Optimized for M1/M2 with MPS acceleration
- **Python**: 3.8+ with virtual environment recommended
- **Ollama**: Required for keyword extraction (llama3.2:3b model)
  - Install from: https://ollama.ai
  - Run: `ollama pull llama3.2:3b`

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

**Ollama/Keyword extraction issues:**
- Ensure Ollama is running: `ollama serve`
- Verify model is installed: `ollama list` (should show llama3.2:3b)
- Check Ollama connection: `curl http://localhost:11434/api/generate`
- If connection fails, restart Ollama service
