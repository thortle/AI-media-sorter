# Local AI Photo Library

A self-hosted photo library with semantic search powered by AI-generated descriptions.

## Current Status

- **8,318 photos** indexed with AI descriptions (Moondream2 VLM)
- **Semantic search** using `all-MiniLM-L12-v2` embeddings
- **Query expansion** for compound concepts ("family dinner", "sad people")
- **FastAPI server** in Docker with HEIC support
- **Thumbnail validation** using CLIP

## Quick Start

```bash
# Start the server
cd photo-server
docker compose up -d

# Access at http://localhost:8000
```

## Architecture

```
Original Photo → VLM Description → Sentence Embeddings → Cosine Similarity Search
      ↓
   Thumbnail
```

## Project Structure

```
media_sorter/
├── photo-server/           # FastAPI Docker server
│   ├── app/
│   │   ├── main.py         # API endpoints
│   │   ├── search.py       # Semantic search + query expansion
│   │   └── search_logger.py
│   ├── thumbnails/         # Generated thumbnails (400x400)
│   └── docker-compose.yml
├── data/
│   ├── descriptions.json   # Photo metadata (8,318 entries)
│   ├── embeddings.npy      # L12 embeddings (8318, 384)
│   └── search_history.jsonl
├── scripts/
│   ├── generate/           # VLM description generation
│   ├── embeddings/         # Embedding creation
│   ├── facial_recognition/ # Face recognition (optional)
│   ├── detect_mismatches_fast.py  # CLIP thumbnail validation
│   └── fix_thumbnails.py   # Regenerate bad thumbnails
└── docs/                   # Additional documentation
```

## Search Features

### Semantic Search
Uses sentence-transformers to understand meaning, not just keywords:
- "red hair" finds "ginger", "auburn", "copper-colored"
- "dog" finds "puppy", "canine", "retriever"

### Query Expansion
Compound concepts are expanded for better matching:
```python
"family dinner" → "group of people gathered around table eating food together"
"sad people"    → "unhappy person crying melancholic distressed face sorrowful"
```

### Keyword Boosting
Exact phrase matches get a small boost (3-5%) to break ties between semantically similar results.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web UI |
| `/api/search` | GET | Semantic search (`?q=query&limit=50`) |
| `/api/photos` | GET | List photos (`?limit=100&offset=0`) |
| `/api/stats` | GET | Photo statistics |
| `/photo/{filename}` | GET | Serve photo (HEIC→JPEG conversion) |
| `/thumbnail/{filename}` | GET | Serve thumbnail |
| `/api/photo/{filename}` | DELETE | Move photo to trash |

## Maintenance

### Regenerate Embeddings
If descriptions change:
```bash
cd scripts/embeddings
python3 create_embeddings.py
docker compose -f ../../photo-server/docker-compose.yml restart
```

### Detect Thumbnail Mismatches
```bash
python3 scripts/detect_mismatches_fast.py --batch-size 32
```

### Fix Mismatched Thumbnails
```bash
python3 scripts/fix_thumbnails.py
```

### Add Query Expansions
Edit `QUERY_EXPANSIONS` dict in `photo-server/app/search.py` when searches return poor results.

## Data Locations

| Data | Path |
|------|------|
| Photos | `/Volumes/T7_SSD/G-photos/` |
| Thumbnails | `photo-server/thumbnails/` |
| Descriptions | `data/descriptions.json` |
| Embeddings | `data/embeddings.npy` |
| Trash | `/Volumes/T7_SSD/G-photos/_trash/` |

## Tech Stack

- **VLM**: Moondream2 (description generation)
- **Embeddings**: sentence-transformers/all-MiniLM-L12-v2
- **Server**: FastAPI + Uvicorn
- **HEIC Support**: pillow-heif
- **Thumbnail Validation**: CLIP (openai/clip-vit-base-patch32)
- **Container**: Docker

## Security Note

Current setup has basic authentication. For production use on untrusted networks, consider:
- Rate limiting
- Input validation for filenames
- Audit logging for deletions
