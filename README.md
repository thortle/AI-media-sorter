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
│   ├── embeddings/               # Phase 3a: Semantic Search
│   │   ├── create_embeddings.py  # One-time embedding generation
│   │   └── semantic_search.py    # Semantic search engine
│   ├── search/                   # Phase 2 & 3b: Keywords & Search
│   │   ├── json_converter.py     # Convert descriptions to JSON
│   │   ├── process_keywords.py   # AI keyword extraction (optional)
│   │   └── search_photos.py      # Keyword-based search engine
│   └── facial_recognition/       # Phase 4: Facial Recognition (optional)
│       ├── main.py               # CLI for face recognition processing
│       └── face_processor.py     # DeepFace integration
├── data/                         # Data files (local only)
│   └── .gitkeep                  # Keep directory in git
└── docs/                         # Documentation
    ├── example.json              # Example JSON structure
    └── facial-recognition-guide.md  # Facial recognition setup guide
```

## How It Works

### Phase 1: AI Description Generation
Uses Moondream2 vision model to generate detailed descriptions of images. Supports multiple file formats (JPG, PNG, HEIC, etc.) with configurable selection methods (random, newest, alphabetical). Outputs to text file with validation.

### Phase 2: Keyword Extraction (OPTIONAL)
Uses Ollama (llama3.2:3b) to add metadata flags (`has_dogs`, `has_cars`, etc.) for filtering. **Not required for search to work.**

### Phase 3a: Semantic Embeddings (OPTIONAL)
Converts descriptions to 384-dimensional vectors using Sentence Transformers (all-MiniLM-L6-v2). Enables semantic search with synonym understanding. **Offline after initial model download (~80MB).**

### Phase 3b: Search
- **Keyword Search:** Direct string matching with proximity logic and AND/OR support
- **Semantic Search:** Vector similarity (cosine distance) for conceptual matching

### Phase 4: Facial Recognition (OPTIONAL)
Uses DeepFace (Facenet512) to detect and match faces against reference photos. Adds metadata enabling "me" query in both search methods. **Requires reference photos in `data/face_recognition_dataset/`.**

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

# 4. (OPTIONAL) Create semantic embeddings for semantic search
cd scripts/embeddings && python3 create_embeddings.py
# This enables semantic search that understands meaning, not just keywords

# 5. (OPTIONAL) Add facial recognition for "me" search
cd scripts/facial_recognition && python3 main.py
# This enables searching for photos of yourself with "me" in both search methods

# 6. Search your photos - Choose your method:
# Option A: Keyword search (fast, exact matching)
cd scripts/search && python3 search_photos.py

# Option B: Semantic search (understands meaning and synonyms)
cd scripts/embeddings && python3 semantic_search.py
```

## Search Methods Comparison

Two search methods available - see [docs/search-comparison.md](docs/search-comparison.md) for detailed comparison.

### Keyword Search (`search_photos.py`)
- **Algorithm:** Exact text matching with fuzzy logic and proximity search
- **Best for:** Exact terms, fast lookups, complex boolean queries (AND/OR)
- **Example:** `"red hair and dog"` finds "red" near "hair" AND "dog" anywhere

### Semantic Search (`semantic_search.py`)
- **Algorithm:** Vector embeddings with cosine similarity (0.0-1.0)
- **Best for:** Natural language, synonyms, conceptual matching
- **Example:** `"red hair and dog"` also finds "ginger-haired person with puppy", "auburn hair with canine"

### Face Recognition ("me" query)
Both search methods support searching for photos of yourself using query **"me"** after running facial recognition setup.

## Query Syntax (Keyword Search)

| Query | Behavior |
|-------|----------|
| `red hair` | "red" AND "hair" within 3 words |
| `dog or cat` | EITHER "dog" OR "cat" |
| `red hair and woman` | ("red" + "hair" within 3 words) AND "woman" anywhere |
| `red hair or blue eyes` | ("red" + "hair" within 3 words) OR ("blue" + "eyes" within 3 words) |

**Commands:**
- `proximity N` - Set max word distance
- `stats` - Show collection statistics  
- `quit` - Exit search

## Optional Features

### Keyword Extraction (Ollama required)
Adds metadata flags using llama3.2:3b via Ollama for filtering and statistics. Detects people, dogs, and cars semantically (handles vocabulary variations like man/woman/hiker or dog/puppy/canine).

```bash
cd scripts/search && python3 process_keywords.py
cd scripts/search && python3 process_keywords.py --test 10  # Test mode
```

**Not required for search** - only adds boolean flags like `has_characters`, `has_dogs`, `has_cars`.

### Facial Recognition (DeepFace required)
Enables searching for photos of yourself using the query **"me"** in both search methods.

```bash
cd scripts/facial_recognition && python3 main.py
cd scripts/facial_recognition && python3 main.py --max-photos 100  # Test mode
```

**Requirements:**
1. Install: `pip install deepface tf-keras tensorflow scipy`
2. Add 20-50 clear photos to `data/face_recognition_dataset/`
3. Run processor to build face embeddings

**Options:** `--model` (Facenet512, VGG-Face, ArcFace), `--detector` (retinaface, mtcnn, opencv), `--threshold` (0.4 default)

See [docs/facial-recognition-guide.md](docs/facial-recognition-guide.md) for detailed setup.

## Quality Verification & File Selection

**Check/Fix Incomplete Descriptions:**
```bash
cd scripts/generate && python3 test_incomplete.py
cd scripts/generate && python3 complete_descriptions.py  # Auto-regenerate with backup
```

**File Selection Methods:** `filesystem` (default), `random`, `newest`, `oldest`, `name_asc`, `name_desc`

**Command Line Options:**
```bash
# Examples
python3 main.py "/path/to/photos"
python3 main.py "/path/to/photos" --max-files 50 --selection-method random
python3 main.py "/path/to/photos" --selection-method newest --descriptions-file custom.txt
```

## Installation

```bash
# 1. Clone to internal drive (recommended for best performance)
cp -r /path/to/media_sorter ~/Desktop/media_sorter && cd ~/Desktop/media_sorter

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Install Ollama for keyword extraction
# Download from https://ollama.ai
ollama pull llama3.2:3b

# 4. (Optional) Install DeepFace for facial recognition
pip install deepface tf-keras tensorflow scipy

# 5. (Optional) Setup face recognition reference dataset
mkdir -p data/face_recognition_dataset
# Add 20-50 clear photos of yourself to this directory
```

**Note:** First run downloads Moondream2 model (~3GB). Use internal drive to avoid macOS resource fork issues on external drives.

## Data Structure

Example from `descriptions.json` - see [docs/example.json](docs/example.json) for full structure:

```json
{
  "filename": "IMG_1713.HEIC",
  "description": "A man stands confidently on a grassy hill...",
  "full_path": "/path/to/photo/IMG_1713.HEIC",
  "keywords": {
    "has_characters": true,
    "has_dogs": false,
    "has_cars": false
  },
  "face_recognition": {
    "has_known_faces": true,
    "known_faces": [{"match_confidence": 0.92, "reference_image": "IMG_1052.JPG"}]
  }
}
```

## Performance & Requirements

- **Description Generation:** ~8 seconds/image on Apple Silicon (M1 Pro)
- **Keyword Extraction:** ~2 seconds/description with llama3.2:3b
- **Search:** Sub-second response
- **Environment:** Internal drive recommended, Python 3.8+, Apple Silicon MPS acceleration support

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Unicode encoding errors | Move project to internal drive, recreate venv |
| Search unexpected results | Check query syntax, adjust proximity with `proximity N` |
| Keyword extraction fails | Verify Ollama running: `ollama serve`, check `ollama list` |
| Search not working | Verify `descriptions.json` exists, check file paths match actual locations |
| Performance issues | Use more specific queries, check available memory |
