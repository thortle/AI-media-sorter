# Local AI Photo Library

A self-hosted photo library with semantic search powered by AI-generated descriptions.

## Current Status

- **8,313 photos** indexed with AI descriptions (Moondream2 VLM)
- **Semantic search** using `all-MiniLM-L12-v2` embeddings (384 dimensions)
- **Hybrid search** with 25% minimum threshold and 500 max results
- **Query expansion** for compound concepts ("family dinner", "sad people")
- **Keyword boosting** (+15% per match, max 30%)
- **FastAPI server** in Docker with HEIC support
- **CLIP tag corrections** applied (2,380 fixes for has_cars/has_dogs/has_characters)
- **Browse All** feature with pagination (500 photos per page)
- **Filter options** for People, Dogs, and Cars
- **Tailscale remote access** configured

## Access URLs

| Location | URL |
|----------|-----|
| Local | http://localhost:8000 |
| Tailscale (Mac) | http://100.74.155.87:8000 |

## Quick Start

```bash
# Start the server
cd photo-server
docker compose up -d

# Stop server
docker compose down

# Rebuild after changes
docker compose build && docker compose up -d

# View logs
docker compose logs -f

# Check SSD mounted
ls /Volumes/T7_SSD/G-photos
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
│   ├── descriptions.json   # Photo metadata (8,313 entries)
│   ├── embeddings.npy      # L12 embeddings (8313, 384)
│   └── search_history.jsonl
├── scripts/
│   ├── generate/           # VLM description generation
│   ├── embeddings/         # Embedding creation
│   └── facial_recognition/ # Face recognition (optional)
└── docs/                   # Additional documentation
```

## Search Features

### Semantic Search
Uses sentence-transformers to understand meaning, not just keywords:
- "red hair" finds "ginger", "auburn", "copper-colored"
- "dog" finds "puppy", "canine", "retriever"

**Settings:** 25% minimum similarity threshold, 500 max results per search.

### Query Expansion
Compound concepts are expanded for better matching:
```python
"family dinner" → "group of people gathered around table eating food together"
"sad people"    → "unhappy person crying melancholic distressed face sorrowful"
```

### Keyword Boosting
Exact phrase matches get a boost (+15% per match, max 30%) to prioritize direct matches.

### Browse All
Click the Browse All button to paginate through all photos (500 per page) with Next/Previous navigation.

### Filters
Quick filters available for:
- People (has_characters)
- Dogs (has_dogs)
- Cars (has_cars)

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
- **Embeddings**: sentence-transformers/all-MiniLM-L12-v2 (384 dimensions)
- **Server**: FastAPI + Uvicorn
- **HEIC Support**: pillow-heif
- **Tag Validation**: CLIP (openai/clip-vit-base-patch32)
- **Container**: Docker
- **Remote Access**: Tailscale

## Security Note

Current setup has basic authentication. For production use on untrusted networks, consider:
- Rate limiting
- Input validation for filenames
- Audit logging for deletions
