# Files That Stay Local

These files should **NOT** be pushed to GitHub:

## Sensitive Information
- `photo-server/docker-compose.yml` - Contains username/password
- `HOMELAB_SETUP_PLAN.md` - Personal homelab setup with Tailscale IPs
- `manual-check.txt` - Personal review notes

## Large Data Files (already in .gitignore)
- `data/descriptions.json` (9MB) - Photo metadata
- `data/embeddings.npy` (12MB) - Sentence embeddings
- `data/embeddings_metadata.json` (4KB) - Embedding info
- `data/search_history.jsonl` (16KB) - Search logs
- `data/face_recognition_dataset/` - Personal photos
- `photo-server/thumbnails/` (259MB) - Generated thumbnails

## Action Needed Before Push

### 1. Create docker-compose.example.yml without credentials

### 2. Fix hardcoded paths in these files:
- `scripts/analyze_search_history.py`
- `scripts/generate/complete_descriptions.py` 
- `scripts/generate/test_incomplete.py`

### 3. Add .env.example file for environment variables
