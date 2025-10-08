# Local AI Powered Media Sorting Tool

## Project Structure

```
media_sorter/
├── README.md                     # Project documentation  
├── requirements.txt              # Python dependencies
├── .gitignore                    # Git ignore rules
├── scripts/                      # All executable scripts
│   ├── generate/                 # Phase 1: Description generation
│   │   ├── main.py               # Main CLI for generating descriptions
│   │   ├── test_incomplete.py    # Quality verification tool
│   │   ├── complete_descriptions.py  # Auto-fix incomplete descriptions
│   │   ├── models/
│   │   │   └── vision_model.py   # Moondream2 integration
│   │   └── utils/
│   │       ├── file_manager.py   # File discovery and selection
│   │       └── logger.py         # Logging configuration
│   ├── search/                   # Phase 2 & 3: Keywords & Search
│   │   ├── json_converter.py     # Convert descriptions to JSON
│   │   ├── process_keywords.py   # AI keyword extraction (optional)
│   │   ├── search_photos.py      # Text-based search engine
│   │   └── utils/                # Package utilities
│   └── facial_recognition/       # Phase 4: Facial Recognition (optional)
│       ├── main.py               # CLI for face recognition processing
│       ├── face_processor.py     # DeepFace integration
│       └── utils/                # Package utilities
├── data/                         # Data files (gitignored)
│   ├── descriptions.json         # Full database (local only)
│   ├── face_recognition_dataset/ # Reference photos of yourself
│   └── .gitkeep                  # Keep directory in git
└── docs/                         # Documentation
    ├── example.json              # Example JSON structure
    └── facial-recognition-guide.md  # Facial recognition setup guide
```

## How It Works

### Phase 1: AI Description Generation
1. **Discover**: Scans directory recursively for supported image files (JPG, JPEG, PNG, TIFF, HEIC)
2. **Select**: Applies chosen selection method and file limit
3. **Load Model**: Initializes Moondream2 vision model with Apple Silicon MPS acceleration
4. **Analyze**: Generates detailed descriptions using multiple prompt strategies
5. **Validate**: Checks descriptions end with proper punctuation
6. **Output**: Saves filename and description pairs to text file

### Phase 2: Keyword Extraction (OPTIONAL - Requires Ollama)
1. **Load JSON**: Reads structured photo descriptions
2. **Initialize LLM**: Connects to Ollama running llama3.2:3b
3. **Semantic Analysis**: Detects people, dogs, and cars using semantic understanding
4. **Structure Results**: Adds boolean flags and detailed arrays
5. **Batch Processing**: Processes in configurable batches with progress saving
6. **Update Database**: Saves enhanced JSON with metadata

**Note:** This phase is entirely optional. It adds metadata like `has_dogs: true` for filtering, but is NOT required for search to work.

### Phase 3: Text-Based Search
1. **Query Parsing**: Parses queries for AND/OR logic and proximity requirements
2. **String Matching**: Uses fuzzy partial matching to avoid false positives
3. **Proximity Search**: Finds keywords within configurable word distance
4. **Context Extraction**: Shows surrounding words with smart padding
5. **Result Display**: Returns photos with highlighted contexts and metadata

### Phase 4: Facial Recognition (OPTIONAL - Requires DeepFace)
1. **Load Reference Dataset**: Builds face embeddings from your reference photos
2. **Face Detection**: Detects faces in photos using RetinaFace detector
3. **Face Matching**: Compares detected faces against reference using Facenet512
4. **MPS Acceleration**: Uses Apple Silicon GPU for faster processing
5. **Update Database**: Adds face recognition metadata to descriptions.json
6. **Enable "Me" Search**: Search for "me" to find all photos with your face

**Note:** This phase is entirely optional. It enables searching for photos of yourself by typing "me".

## Quick Start

### Basic Usage
```bash
# 1. Generate descriptions for images (one-time)
cd scripts/generate && python3 main.py "/path/to/your/photos"

# 2. Convert to JSON format
cd scripts/search && python3 json_converter.py

# 3. (OPTIONAL) Add keyword metadata using Ollama
cd scripts/search && python3 process_keywords.py
# This adds boolean flags (has_dogs, has_cars, etc.) but is NOT required for search

# 4. (OPTIONAL) Add facial recognition for "me" search
cd scripts/facial_recognition && python3 main.py
# This enables searching for photos of yourself with "me"

# 5. Search your photos (works offline, no AI needed)
cd scripts/search && python3 search_photos.py
```

## How Search Works
- Searches through pre-generated text descriptions
- Uses fuzzy string matching (e.g., "dog" matches "dogs", "doggy")
- Employs proximity logic (finds words within N words of each other)
- Works completely offline once descriptions are generated

## Search Query Syntax

### Proximity Search (default)
```
Search: red hair
```
Finds "red" AND "hair" within 3 words of each other

### OR Logic
```
Search: dog or cat
```
Finds photos with EITHER "dog" OR "cat"

### Mixed Logic
```
Search: red hair and woman
```
Finds (red + hair within 3 words) AND "woman" anywhere

### Complex Queries
```
Search: red hair or blue eyes
```
Finds (red + hair within 3 words) OR (blue + eyes within 3 words)

### Commands
```
proximity 5     # Set max word distance to 5
stats           # Show collection statistics
quit            # Exit search tool
```

## Search Features

- **Intelligent Partial Matching**: Avoids false positives (e.g., "hair" won't match "chair")
- **Contextual Results**: Shows words before and after each match
- **Multiple Contexts**: Displays all occurrences of keywords in each photo
- **Highlighted Keywords**: Bold formatting for matched words
- **File Metadata**: Shows word count, description length, and full file path

## Keyword Extraction

The keyword extraction phase adds metadata flags to help with filtering and statistics:

```bash
cd sorting && python3 process_keywords.py

# Test mode
cd sorting && python3 process_keywords.py --test 10
```

**What it does:**
- Uses llama3.2:3b via Ollama to analyze descriptions
- Detects mentions of people, dogs, and cars
- Adds boolean flags: `has_characters`, `has_dogs`, `has_cars`
- Only runs once during setup
- **OPTIONAL:** Search works perfectly without this step

**Why use an LLM:**
Vision models use diverse vocabulary (man/woman/child/hiker/gentleman/tourist for people, dog/puppy/canine/pet for dogs, car/vehicle/sedan/SUV for cars). Manual keyword matching misses variations. LLMs understand semantic meaning regardless of word choice.

**Boolean flags usage:**
- Quick statistics without text search

- Pre-identified photos for future face recognition training

## Facial Recognition

```bash
cd scripts/facial_recognition && python3 main.py

# Test mode with limited photos
cd scripts/facial_recognition && python3 main.py --max-photos 100

# Custom settings
cd scripts/facial_recognition && python3 main.py --threshold 0.35 --model Facenet512
```

**What it does:**
- Uses DeepFace library with Facenet512 model for face recognition
- Builds reference database from `data/face_recognition_dataset/` photos
- Detects faces in all photos and matches against your reference faces
- Uses Apple Silicon MPS acceleration for faster processing
- Adds face recognition metadata to descriptions.json
- Enables searching for "me" to find photos of yourself

**How it works:**
1. Load reference photos of yourself from `data/face_recognition_dataset/`
2. Extract face embeddings from reference photos
3. Detect faces in each photo from your collection
4. Compare detected faces against reference using cosine distance
5. If match confidence exceeds threshold, mark as "known face"
6. Save results to descriptions.json

**Search for yourself:**
```bash
cd scripts/search && python3 search_photos.py
Search: me
```

**Configuration options:**
- `--model`: Face recognition model (Facenet512, VGG-Face, ArcFace, etc.)
- `--detector`: Face detector backend (retinaface, mtcnn, opencv, etc.)
- `--threshold`: Match threshold (0.4 default, lower = stricter)
- `--reference-dataset`: Path to reference face photos
- `--force`: Reprocess all photos, even if already processed

**Setup:**
1. Create `data/face_recognition_dataset/` directory
2. Add 20-50 clear photos of yourself (diverse angles, lighting)
3. Install facial recognition dependencies: `pip install deepface tf-keras tensorflow scipy`
4. Run facial recognition processor

See [docs/facial-recognition-guide.md](docs/facial-recognition-guide.md) for detailed setup instructions.

## Quality Verification

### Check for Incomplete Descriptions
```bash
cd scripts/generate && python3 test_incomplete.py
```

### Fix Incomplete Descriptions
```bash
cd scripts/generate && python3 complete_descriptions.py
```

Features:
- Identifies descriptions without proper punctuation
- Uses vision model to regenerate incomplete descriptions
- Creates automatic backup before changes
- Validates completeness before saving

## File Selection Methods

| Method | Description | Best For |
|--------|-------------|----------|
| `filesystem` | Natural file system order | Default processing |
| `random` | Random sampling | Unbiased testing |
| `newest` | Most recent files first | Latest uploads |
| `oldest` | Oldest files first | Historical content |
| `name_asc` | Alphabetical A-Z | Organized processing |
| `name_desc` | Alphabetical Z-A | Reverse order |

## Command Line Options

```
Usage: main.py [OPTIONS] SOURCE_DIR

Options:
  --max-files INTEGER         Limit number of files to process
  --selection-method [method] File selection strategy
  --random-seed INTEGER       Random seed for reproducible selection
  --descriptions-file TEXT    Output file name (default: descriptions.txt)
  --help                      Show help message
```

## Example Usage

```bash
# Full-scale processing
cd scripts/generate && python3 main.py "/path/to/photos"

# Test with small sample
cd scripts/generate && python3 main.py "/path/to/photos" --max-files 50

# Random sampling
cd scripts/generate && python3 main.py "/path/to/photos" --selection-method random --max-files 100

# Process newest photos first
cd scripts/generate && python3 main.py "/path/to/photos" --selection-method newest --max-files 200

# Custom output file
cd scripts/generate && python3 main.py "/path/to/photos" --descriptions-file custom.txt
```

## Installation

1. **Clone or copy project to internal drive (recommended):**
   ```bash
   cp -r /path/to/media_sorter ~/Desktop/media_sorter
   cd ~/Desktop/media_sorter
   ```

2. **Install Python dependencies:**
   ```bash
   # Core dependencies (required)
   pip install -r requirements.txt
   
   # For facial recognition (optional)
   pip install deepface tf-keras tensorflow scipy
   ```

3. **Install Ollama (optional, for keyword extraction only):**
   ```bash
   # Install from https://ollama.ai
   ollama pull llama3.2:3b
   ```

4. **First run will download Moondream2 model (approximately 3GB)**

5. **Setup facial recognition (optional):**
   ```bash
   # Create reference dataset directory
   mkdir -p data/face_recognition_dataset
   
   # Add 20-50 clear photos of yourself to this directory
   # See docs/facial-recognition-guide.md for tips
   ```


## JSON Data Structure

Example entry from `descriptions.json`:

```json
{
  "filename": "IMG_1713.HEIC",
  "description": "A man stands confidently on a grassy hill...",
  "full_path": "/path/to/photo/IMG_1713.HEIC",
  "keywords": {
    "has_characters": true,
    "characters": [{"type": "man", "count": 1}],
    "has_dogs": false,
    "dogs": [],
    "has_cars": false,
    "cars": []
  },
  "metadata": {
    "line_number": 1,
    "file_extension": ".heic",
    "description_length": 448,
    "word_count": 81
  },
  "face_recognition": {
    "has_faces": true,
    "face_count": 1,
    "has_known_faces": true,
    "known_faces": [
      {
        "match_confidence": 0.92,
        "reference_image": "IMG_1052.JPG",
        "distance": 0.16
      }
    ]
  }
}
```

**Note:** The full `descriptions.json` database is kept locally only in the `data/` directory. The repository includes `docs/example.json` showing the structure.

## Performance Characteristics

- **Description Generation**: Approximately 8 seconds per image on Apple Silicon (M1 Pro)
- **Keyword Extraction**: Approximately 2 seconds per description with llama3.2:3b
- **Search Performance**: Sub-second response for most queries
- **Accuracy**: Detailed, complete descriptions with multi-prompt validation

## Environment Requirements

- **Best Performance**: Internal drive recommended
- **External Drive Issues**: macOS resource fork files can corrupt Python packages
- **Apple Silicon**: Optimized for M1/M2 with MPS acceleration
- **Python**: 3.8+ with virtual environment recommended
- **Ollama**: Only required for keyword extraction phase (llama3.2:3b model)

## Troubleshooting

**Environment issues on external drive:**
- Move project to internal drive
- Create fresh virtual environment on internal drive
- External drives can cause Unicode encoding errors

**Search returns unexpected results:**
- Check query syntax for AND/OR logic
- Adjust proximity distance with `proximity N` command
- Use `stats` command to understand collection content

**Keyword extraction issues:**
- Ensure Ollama is running: `ollama serve`
- Verify model is installed: `ollama list` (should show llama3.2:3b)
- Check connection: `curl http://localhost:11434/api/generate`
- Restart Ollama service if connection fails

**Search not working:**
- Verify `descriptions.json` exists in data/ directory
- Check file paths in JSON match actual photo locations
- Search does not require Ollama - it's pure text matching

**Performance issues:**
- Use more specific queries to reduce result set size
- Check available memory if processing large collections
- Consider implementing pre-indexing for very large collections
