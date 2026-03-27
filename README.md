
> This project is the result of a personal problem I was confronted with. I found myself with a photo library of thousands of images stripped of all metadata — no dates, no tags, nothing to sort by. Every cloud solution meant giving up my data. So I built this instead: a fully local photo library where you can search it all with plain language from your own machine.

# Local AI Photo Library

A self-hosted photo library with semantic search powered by AI-generated descriptions.

## Current Status

- More than **8,000 photos** indexed with AI descriptions (Moondream2 VLM)
- **Semantic search** using `all-MiniLM-L12-v2` embeddings (384 dimensions)
- **Hybrid search** with 25% minimum threshold and 500 max results
- **Query expansion** for compound concepts ("family dinner", "sad people")
- **Keyword boosting** (+15% per match, max 30%)
- **FastAPI server** in Docker with HEIC support
- **Browse All** feature with pagination (500 photos per page)
- **Filter options** for People, Dogs, and Cars
- **Remote access** support via Tailscale or VPN

## Access URLs

| Location | URL |
|----------|-----|
| Local | http://localhost:8000 |
| Remote (Tailscale) | http://YOUR_TAILSCALE_IP:8000 |

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

# Check photo directory is accessible
ls /path/to/your/photos
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
├── .env.example                    # Environment variable template
├── requirements.txt                # Python dependencies for scripts
├── photo-server/                   # FastAPI Docker server
│   ├── Dockerfile
│   ├── docker-compose.example.yml  # Copy to docker-compose.yml and configure
│   ├── generate_thumbnails.py      # Pre-generate thumbnails before first run
│   ├── thumbnails/                 # Generated thumbnails (gitignored)
│   └── app/
│       ├── main.py                 # API endpoints
│       ├── search.py               # Semantic search + query expansion
│       ├── search_logger.py
│       ├── requirements.txt
│       └── templates/
│           └── index.html          # Web UI
├── data/                           # Gitignored - generated locally
│   ├── descriptions.json           # Photo metadata
│   ├── embeddings.npy              # Sentence embeddings
│   └── search_history.jsonl        # Search logs
├── scripts/
│   ├── generate/                   # VLM description generation
│   │   ├── main.py
│   │   ├── complete_descriptions.py
│   │   ├── models/
│   │   └── utils/
│   ├── embeddings/                 # Embedding creation
│   │   ├── create_embeddings.py
│   │   └── semantic_search.py
│   ├── search/                     # Search utilities
│   │   ├── json_converter.py
│   │   ├── process_keywords.py
│   │   └── search_photos.py
    └── facial_recognition/         # Face recognition (not yet functional - WIP)
└── docs/
    └── facial-recognition.md       # WIP - see notice inside
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

### Upload Photos
Upload photos from any device via the web UI. Photos are automatically processed with AI descriptions and become immediately searchable. Requires Moondream service running on host:

```bash
# Start Moondream service (run once before uploading)
python services/moondream_service.py
```

### Recent Uploads
Click the Recent button to view recently uploaded photos, sorted by upload date.

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
| `/api/upload` | POST | Upload photo (multipart form) |
| `/api/uploads` | GET | List recent uploads |
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
| Photos | `/path/to/your/photos/` |
| Thumbnails | `photo-server/thumbnails/` |
| Descriptions | `data/descriptions.json` |
| Embeddings | `data/embeddings.npy` |
| Trash | `/path/to/your/photos/_trash/` |

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

For a full hardening checklist (credential rotation, branch protection, secret scanning, Docker
hardening, and a pre-publish audit) see [`SECURITY.md`](SECURITY.md).

If you are working across branches or evaluating a security PR while you have local changes,
see [`docs/safe-merge-workflow.md`](docs/safe-merge-workflow.md) for a step-by-step guide.
