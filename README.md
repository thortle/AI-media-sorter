# AI Media Description Generator

## **Current Status: Phase 2 Advanced Development**

**Phase 1 Complete**: AI description generation for 8,330 photos ✅  
**Phase 2 Advanced**: Smart search with intelligent query parsing and proximity matching 🔄

### **Recent Achievements**
- ✅ **8,330 photos processed** with detailed AI descriptions
- ✅ **JSON database created** with searchable structured format
- ✅ **Multi-paragraph descriptions** properly captured and formatted
- ✅ **AI keyword extraction system** using llama3.2:3b for human character, dog, and car detection
- ✅ **Semantic recognition** handling diverse descriptive vocabulary for people, dogs, and vehicles
- ✅ **Smart photo search engine** with intelligent query parsing and proximity matching
- ✅ **Interactive CLI search tool** with flexible AND/OR logic and contextual results

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
Uses Ollama with llama3.2:3b model to intelligently detect human characters, dogs, and cars in photo descriptions:

```bash
# Process all photos for character, dog, and car detection
cd sorting && python3 process_keywords.py

# Test mode: process only specific number of photos
cd sorting && python3 process_keywords.py --test 10
cd sorting && python3 process_keywords.py --test 50
```

**Character Detection Features:**
- **🤖 LLM-Powered Analysis**: Uses llama3.2:3b via Ollama for intelligent text analysis
- **👥 Human Character Detection**: Identifies mentions of people using descriptive terms from descriptions
- **🐕 Dog Detection**: Identifies mentions of dogs using semantic understanding of various dog-related terms
- **🚗 Car Detection**: Identifies mentions of cars and vehicles using semantic understanding of automotive terms
- **📊 Structured Keywords**: Adds boolean flags and detailed arrays for characters, dogs, and cars to JSON
- **🎯 Adaptive Recognition**: Handles varied descriptive language that manual parsing cannot catch
- **⚡ Batch Processing**: Processes photos in configurable batches with progress saving

**Why LLM for Keyword Extraction:**
The initial vision model used diverse vocabulary when describing people (man, woman, child, hiker, gentleman, tourist, couple, student, individuals, etc.), dogs (dog, puppy, canine, pet, breed names like Golden Retriever, etc.), and cars (car, vehicle, sedan, SUV, truck, automobile, convertible, etc.). Manual keyword matching would miss many variations, but LLMs excel at understanding semantic meaning regardless of specific word choice.

### **Smart Photo Search Engine**

Interactive search tool with intelligent query parsing and proximity matching:

```bash
# Launch interactive search tool
cd sorting && python3 search_photos.py
```

**🧠 Smart Query Features:**
- **Proximity Search**: `'red hair'` → finds red AND hair close together (≤3 words apart)
- **OR Logic**: `'red or hair'` → finds photos with EITHER red OR hair
- **Mixed Logic**: `'red hair and dog'` → finds (red + hair close) AND dog anywhere in description
- **Complex Queries**: `'red hair or blue eyes'` → finds (red + hair) OR (blue + eyes close)

**🔧 Search Commands:**
```bash
# Basic proximity search (default)
Search: red hair
🔍 Searching for: 'red + hair' (≤3 apart)

# OR search for broader results
Search: dog or cat
🔍 Searching for: 'dog' OR 'cat'

# Mixed logic: proximity + standalone
Search: red hair and woman
🔍 Searching for: 'red + hair' (≤3 apart) AND 'woman' (anywhere)

# Adjust proximity distance
Search: proximity 5
🔧 Proximity distance set to: 5 words

# Collection statistics
Search: stats
📊 Collection Statistics:
   Total photos: 8330
   Photos with dogs: 245
   Photos with cars: 89
   Photos with people: 1537
```

**🎯 Smart Matching Features:**
- **Intelligent Partial Matching**: Avoids false positives (e.g., 'hair' won't match 'chair')
- **Contextual Results**: Shows 3 words before and after each match
- **Multiple Contexts**: Displays all occurrences of keywords in each photo
- **Highlighted Keywords**: Bold formatting for matched words in context
- **File Metadata**: Shows word count, description length, and full file path

**📊 Boolean Section Usage:**
The boolean flags (`has_characters`, `has_dogs`, `has_cars`) serve multiple purposes:
- **Collection Statistics**: Quick overview of photo content distribution
- **Performance Optimization**: Fast filtering without text search
- **Future Dataset Creation**: Pre-identified photos for face recognition training
  - `has_characters: true` photos (~1,537) will be training dataset for face recognition
  - Focused computational resources on photos containing people
  - Foundation for building face embeddings and clustering

### **Example Search Sessions**

**Proximity Search Example:**
```
Search (≤3): red hair
🔍 Searching for: 'red + hair' (≤3 apart)
✅ Found 12 result(s):

 1. 📁 IMG_2534.HEIC
    🔎 'red hair':
       ...woman with short **red** **hair** wearing a...
       ...her **red** curly **hair** flows in...
    📊 89 words, 456 chars
    📂 /Volumes/T7_SSD/G-photos/IMG_2534.HEIC
```

**Mixed Logic Example:**
```
Search (≤3): red hair and woman
🔍 Searching for: 'red + hair' (≤3 apart) AND 'woman' (anywhere)
✅ Found 8 result(s):

 1. 📁 IMG_1847.JPG
    🔎 'red hair':
       ...short light **red** **hair** and is...
    🔎 'woman':
       ...The **woman** is wearing dark...
    📊 103 words, 521 chars
```

**OR Logic Example:**
```
Search (≤3): dog or cat
🔍 Searching for: 'dog' OR 'cat'
✅ Found 267 result(s):

 1. 📁 IMG_4482.HEIC
    🔎 'dog':
       ...white and brown **dog** possibly a Jack...
       ...tiled patio The **dog** s gaze is...
    📊 69 words, 383 chars
```

### **JSON Database Stats**
- **8,330 photos** with structured metadata (local database only)
- **510 characters** average description length
- **AI-powered detection** for human characters, dogs, and cars with semantic understanding
- **1,537 photos with people** (18.5% of collection) - future face recognition dataset
- **245 photos with dogs** (2.9% of collection)
- **89 photos with cars** (1.1% of collection)
- **example.json** provided in repository for structure reference

## **Key Features**

- **🤖 Local AI Processing** - All analysis happens on Apple Silicon, no internet required
- **📝 Description Generation** - Generates detailed descriptions for all images
- **🔍 Smart Search Engine** - Intelligent query parsing with proximity and boolean logic
- **💾 HEIC Support** - Handles iPhone HEIC photos alongside JPG/PNG/TIFF
- **🎲 Flexible File Selection** - 6 different methods for processing files (random, newest, etc.)
- **📊 Complete Analysis** - Processes images only, automatically skips unsupported file types
- **✅ Production Tested** - Successfully processing 8,330+ image collections

## **Purpose**

This tool generates detailed AI-powered descriptions for image collections and provides intelligent search capabilities. Creates a comprehensive catalog that can be used for:

- **Content analysis and search** with natural language queries
- **Building datasets for machine learning** (especially face recognition using character-flagged photos)
- **Creating searchable metadata** for large photo collections
- **Intelligent photo organization** and discovery

## **Quick Start**

### **Basic Usage**
```bash
# Generate descriptions for all images
cd description && python3 main.py "/path/to/your/photos"

# Add AI-powered keyword extraction
cd sorting && python3 process_keywords.py

# Search your photos interactively
cd sorting && python3 search_photos.py
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

# Add keyword extraction for all photos
cd sorting && python3 process_keywords.py

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

3. **Install Ollama for keyword extraction:**
   ```bash
   # Install from https://ollama.ai
   ollama pull llama3.2:3b
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
│   ├── complete_descriptions.txt # Generated descriptions output (local only)
│   ├── models/
│   │   ├── __init__.py
│   │   └── vision_model.py       # Simplified Moondream2 integration for image description
│   └── utils/
│       ├── __init__.py
│       ├── file_manager.py       # File discovery and selection methods
│       └── logger.py             # Logging configuration
└── sorting/                      # Phase 2: Photo Search & Display
    ├── json_converter.py         # Convert descriptions.txt to searchable JSON format
    ├── process_keywords.py       # AI-powered keyword extraction using llama3.2:3b
    ├── search_photos.py          # Smart search engine with intelligent query parsing
    ├── example.json              # Example JSON structure for reference (in repo)
    ├── descriptions.json         # Full JSON database with private photo data (local only)
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
3. **Semantic Analysis**: For each photo description, sends carefully crafted prompt to detect human characters, dogs, and cars
4. **Detection**: LLM identifies presence of people, dogs, and vehicles using semantic understanding, not keyword matching
5. **Structure Results**: Adds `keywords` object with boolean flags and detailed arrays for characters, dogs, and cars
6. **Batch Processing**: Processes photos in configurable batches (default 50) with automatic progress saving
7. **Update Database**: Saves enhanced JSON with character, dog, and car detection metadata

### **Phase 2: Smart Photo Search Engine**
1. **Query Parsing**: Intelligently parses natural language queries for AND/OR logic and proximity requirements
2. **Smart Matching**: Uses improved partial matching that avoids false positives (e.g., 'hair' vs 'chair')
3. **Proximity Search**: Finds keywords within configurable word distance (default 3 words apart)
4. **Context Extraction**: Shows 3 words before and after matches with smart padding
5. **Result Ranking**: Returns photos with highlighted contexts and metadata
6. **Interactive CLI**: Real-time search with command support and statistics

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
    ],
    "has_dogs": false,
    "dogs": [],
    "has_cars": false,
    "cars": []
  }
}
```

**Smart Search Query Examples:**
- `'red hair'` → Proximity search (red + hair within 3 words)
- `'red or hair'` → OR search (either keyword)
- `'red hair and dog'` → Mixed logic ((red + hair close) AND dog anywhere)
- `'red hair or blue eyes'` → Complex OR ((red + hair) OR (blue + eyes))

**Note:** The full `descriptions.json` database containing private photo data is kept locally only. The repository includes `example.json` showing the data structure for reference.

## **Future Development Roadmap**

### **Phase 3: Advanced Features (Planned)**
- **👤 Face Recognition Training**: Train a custom model to identify recurring faces across the photo collection
  - Use `has_characters: true` photos (1,537 photos) as focused training dataset
  - Efficient processing by targeting only photos containing people
  - Build face embeddings for clustering and identification
- **🔍 Web-based Search Interface**: Enhanced UI with filters and advanced search options
- **📊 Analytics Dashboard**: Statistics about photo collection content and trends
- **🏷️ Extended Keyword Categories**: Expand beyond character, dog, and car detection to objects, scenes, activities
- **🤖 Custom Model Training**: Use the structured dataset for training domain-specific vision models

## **Performance**

- **Description Generation**: ~8 seconds per image on Apple Silicon (M1 Pro)
- **Keyword Extraction**: ~2 seconds per photo description with llama3.2:3b
- **Search Performance**: Sub-second response for most queries on 8,330 photo database
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

**Search returns unexpected results:**
- Check query syntax for AND/OR logic
- Adjust proximity distance with `proximity N` command
- Use `stats` command to understand collection content

**Incomplete descriptions:**
- Tool automatically handles this with multi-prompt validation (tries multiple prompts sequentially, validates each response for completeness by checking proper punctuation endings, and attempts to complete truncated descriptions)
- All descriptions verified to end with proper punctuation

**Ollama/Keyword extraction issues:**
- Ensure Ollama is running: `ollama serve`
- Verify model is installed: `ollama list` (should show llama3.2:3b)
- Check Ollama connection: `curl http://localhost:11434/api/generate`
- If connection fails, restart Ollama service

**Search performance issues:**
- Consider implementing pre-indexing for very large collections (>10k photos)
- Use more specific queries to reduce result set size
- Check available memory if processing large descriptions
