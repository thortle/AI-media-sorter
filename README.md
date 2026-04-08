
> This project is the result of a personal problem I was confronted with. I found myself with a photo library of thousands of images stripped of all metadata — no dates, no tags, nothing to sort by. Every cloud solution meant giving up my data. So I built this instead: a fully local photo library where you can search it all with plain language from your own machine.

# Local AI Photo Library

A self-hosted photo library with semantic search powered by AI-generated descriptions.

## Current Status

- **Semantic search** using `all-MiniLM-L12-v2` embeddings (384 dimensions)
- **NLP-based ranking** with spaCy adjective-noun matching for accurate results
- **Compound phrase search** with weighted scoring for multi-word queries
- **Query expansion** for compound concepts ("family dinner", "pink hair")
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

### First-Time Setup (Persistent Services)

```bash
# 1. Set up Moondream service (runs persistently, even when Mac sleeps)
cd services
./setup_persistent.sh

# 2. Start Docker container
cd ../photo-server
docker compose up -d

# 3. Verify everything is running
cd ../services && ./manage_service.sh status
docker ps
```

Both services will now:
- Keep running when your Mac sleeps or locks
- Restart automatically if they crash
- Start automatically on login/reboot

### Daily Usage

Services are already running! Just access: http://localhost:8000

### Managing Services

```bash
# Moondream service
cd services
./manage_service.sh status    # Check status
./manage_service.sh logs       # View logs
./manage_service.sh restart    # Restart
./manage_service.sh stop       # Stop service

# Docker container
cd photo-server
docker compose logs -f         # View logs
docker compose restart         # Restart
docker compose down            # Stop (won't auto-restart)
docker compose up -d           # Start
```

**Note:** Moondream logs are saved to `services/moondream.log` and `services/moondream.error.log`. Docker Desktop must be set to start on login for the container to auto-start.

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

### NLP-Based Ranking

Uses spaCy dependency parsing to ensure adjectives modify the correct nouns:
- "pink hair" only matches photos where "pink" describes the hair (not "pink shirt" near "hair")
- "red car" only matches photos where "red" describes the car (not "red jacket" near "car")

**Scoring:**
- Exact phrase match or correct adjective-noun relationship: 10% boost
- Scattered word matches (wrong grammar): 40% penalty
- Partial matches: up to 50% penalty

### Browse All
Click the Browse All button to paginate through all photos (500 per page) with Next/Previous navigation.

### Upload Photos
Upload photos from any device via the web UI. Photos are automatically processed with AI descriptions and become immediately searchable. The Moondream service is configured to run persistently via the setup instructions above.

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
- **NLP**: spaCy en_core_web_sm (adjective-noun relationship parsing)
- **Server**: FastAPI + Uvicorn
- **HEIC Support**: pillow-heif
- **Tag Validation**: CLIP (openai/clip-vit-base-patch32)
- **Container**: Docker
- **Remote Access**: Tailscale

## Security

Current setup has basic authentication. For production use on untrusted networks, consider:
- Rate limiting
- Input validation for filenames
- Audit logging for deletions

For a full hardening checklist (credential rotation, branch protection, secret scanning, Docker
hardening, and a pre-publish audit) see [`SECURITY.md`](SECURITY.md).

If you are working across branches or evaluating a security PR while you have local changes,
see [`docs/safe-merge-workflow.md`](docs/safe-merge-workflow.md) for a step-by-step guide.
