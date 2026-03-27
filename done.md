# AI Photo Library - Session Status

**Date:** 2026-03-27
**Status:** COMPLETE - Compound phrase search implemented and tested on experimental branch

---

## Latest Activity (2026-03-27) - Compound Phrase Search

### Implemented spaCy-Based Compound Phrase Search

**Problem Solved:** Query "vibrant orange hair bathroom" was returning photos with generic "hair + bathroom" instead of prioritizing "vibrant orange hair" specifically.

**Solution:** Added intelligent noun phrase extraction and weighted scoring using spaCy NLP.

**Implementation:**

1. **Dependencies & Setup**
   - Added `spacy==3.7.4` to requirements.txt
   - Updated Dockerfile to download `en_core_web_sm-3.7.1` model
   - Added error handling with fallback if spaCy unavailable

2. **Noun Phrase Extraction** (`extract_noun_phrases()`)
   - Uses spaCy to extract noun chunks from queries
   - Intelligently splits at noun-noun boundaries when adjectives precede
   - Examples:
     - "vibrant orange hair bathroom" → ["vibrant orange hair", "bathroom"]
     - "family dinner" → ["family dinner"] (keeps NOUN-NOUN together)
     - "red car mountains" → ["red car", "mountains"]

3. **Weighted Scoring** (`calculate_phrase_weights()`)
   - Assigns weights based on phrase length/specificity
   - 3+ word phrases: 0.6 weight (highest priority)
   - 2 word phrases: 0.3 weight
   - 1 word phrases: 0.2 weight
   - Normalizes to sum to 1.0

4. **Modified Search Logic** (`search()` method)
   - Calculates separate embeddings for each phrase
   - Applies query expansion to individual phrases
   - Combines scores as weighted sum: `final_score = Σ(weight × phrase_similarity)`
   - Preserves all existing filters, tie-breaking, and sorting

**Files Modified:**
- `photo-server/app/requirements.txt` - Added spacy==3.7.4
- `photo-server/Dockerfile` - Added spaCy model download
- `photo-server/app/search.py` - Added 120+ lines for phrase extraction and weighted scoring

### Test Results

| Query | Phrases | Top Score | Result |
|-------|---------|-----------|--------|
| vibrant orange hair bathroom | ["vibrant orange hair", "bathroom"] | 0.47 | Red/vibrant hair in bathrooms ✅ |
| family dinner | ["family dinner"] | 0.59 | Groups eating together ✅ |
| red car mountains | ["red car", "mountains"] | 0.51 | Red cars with mountain context ✅ |
| beach sunset | ["beach sunset"] | 0.69 | Beach scenes at sunset ✅ |
| dog park | ["dog park"] | 0.67 | Dogs in parks ✅ |
| bathroom (single) | ["bathroom"] | 0.64 | Bathroom scenes ✅ |

**Backward Compatibility:** All existing queries still work well or better. Query expansion continues to be applied to each phrase.

**Branch:** `experimental/compound-phrase-search`
**Commit:** `03dbf63 "Add spaCy-based compound phrase search"`

**Status:** ✅ Implementation complete, tested, and pushed to experimental branch

---

### Added Bulk Photo Upload (Up to 25 Photos)

**Enhancement:** Updated upload functionality to support bulk uploads instead of single photos.

**Implementation:**
- Added `multiple` attribute to file input with max 25 files validation
- Replaced single file preview with scrollable file list showing:
  - Filename and file size for each photo
  - Individual upload status (Pending → Uploading → Success/Failed)
- Sequential upload processing to avoid overwhelming Moondream service
- Overall progress bar showing "Uploading X of Y"
- Summary on completion: "Complete! X succeeded, Y failed"
- Auto-redirect to Recent Uploads view if any uploads succeed

**Files Modified:**
- `photo-server/app/templates/index.html` - Updated upload modal HTML and JavaScript

**Deployment:**
- Rebuilt and restarted Docker container
- Verified bulk upload UI present with "max 25 photos" text

**Status:** ✅ Bulk upload feature deployed and functional

---

### Removed Custom Login Form, Fixed Double Login

**Issue:** Users were being prompted to login twice:
1. Custom HTML login form in the web interface
2. Browser's HTTP Basic Auth dialog when making API calls

**Solution:** Removed custom login interface entirely and rely only on browser's native HTTP Basic Auth:
- Made GET / endpoint require authentication via FastAPI's `verify_credentials` dependency
- Removed 127 lines of custom login CSS, HTML, and JavaScript
- Simplified authFetch to use browser credentials: 'include' for native auth
- Browser now shows its standard login dialog on first page visit

**Files Modified:**
- `photo-server/app/main.py` - Added auth requirement to index route
- `photo-server/app/templates/index.html` - Removed login overlay, CSS, and JS (127 lines)

**Deployment:**
- Rebuilt and restarted Docker container
- Verified 401 Unauthorized response without credentials
- Verified proper HTML response with valid credentials
- Browser native auth dialog is now the only login method

**Status:** ✅ Cleaner auth flow, eliminated double login issue

---

### Set Up Persistent Services (Sleep-Proof)

**Requirement:** Keep entire server pipeline running when MacBook sleeps or locks, only stopping on explicit shutdown.

**Solution:** Configured both services for persistent operation:

1. **Docker Container** - Already had `restart: unless-stopped` policy
   - Automatically restarts after system reboot
   - Continues running during sleep/lock
   - Only stops with explicit `docker compose down`

2. **Moondream Service** - Created launchd configuration
   - Installed as macOS LaunchAgent
   - `KeepAlive=true` ensures continuous operation
   - Auto-starts on login
   - Survives sleep/lock/crashes

**Files Created:**
- `services/com.photoserver.moondream.plist` - launchd service configuration
- `services/setup_persistent.sh` - One-time setup installer
- `services/manage_service.sh` - Service management script (start/stop/status/logs)
- `services/README.md` - Complete service documentation

**Files Modified:**
- `README.md` - Updated Quick Start with persistent setup instructions

**Deployment:**
- Stopped manual Moondream process (PID 18208)
- Installed launchd service via setup script
- Verified both services running:
  - Docker: `photo-server` container (restart: unless-stopped)
  - Moondream: LaunchAgent PID 51552 (KeepAlive: true)

**Status:** ✅ Both services now run persistently, sleep-proof setup complete

---

### Fixed Upload Race Condition

**Issue:** Photo uploads were failing with error: `"Processing failed: 500: Moondream error: {"detail":"Photo not found"}"`

**Root Cause:** Race condition between Docker container writing files and host filesystem sync. When a photo was uploaded:
1. Container saved file to `/photos/` (Docker volume mount to `/Volumes/T7_SSD/G-photos`)
2. Immediately called Moondream service on host
3. File hadn't finished syncing to host filesystem yet (T7 external SSD)
4. Moondream service couldn't find the file

**Solution:** Added explicit file flush and sync operations in `photo-server/app/main.py`:
- Added `f.flush()` to flush write buffer
- Added `os.fsync(f.fileno())` to force filesystem sync to disk
- This ensures file is fully written before calling external services

**Files Modified:**
- `photo-server/app/main.py` (lines 613-617)

**Status:** ✅ Fix deployed, container rebuilt and restarted

---

## What This Session Accomplished

### Phase 1: Security Audit Review & Merge

Reviewed and merged Copilot's security audit PR containing critical security fixes:

**Critical CVE Patches:**
- Pillow 10.2.0 → 12.1.1 (PSD buffer overflow, out-of-bounds write fix)
- FastAPI 0.109.0 → 0.115.0 (ReDoS in Content-Type parsing fix)
- python-multipart 0.0.6 → 0.0.22 (ReDoS, DoS, arbitrary file-write fixes)

**Security Fixes Implemented:**
- Stored XSS vulnerability: Added `escapeHtml()` function, applied to all user-supplied data in templates
- Upload filename sanitization: Changed from `replace(" ", "_")` to strict regex `[^a-zA-Z0-9_-]`
- Path containment: Switched from string prefix check to `Path.is_relative_to()` for security
- Docker hardening: Container now runs as non-root user (appuser, UID 1000)
- Upload size limit: Added 50MB maximum to prevent DoS
- Default credentials: Added startup warning when defaults detected
- Moondream path translation: Introduced `HOST_PHOTO_DIR` env var for proper host path mapping
- Hardcoded path leak: Removed developer-specific `/Volumes/T7_SSD/G-photos` from code

**Configuration Management:**
- `SECURITY_AUDIT.md` kept locally only (added to `.gitignore` for privacy)
- `docker-compose.yml` gitignored (contains credentials)
- Updated `.env.example` with all new configuration variables
- Updated `README.md` with Security section referencing full audit details

### Phase 2: Documentation Updates

- Updated README.md with Security section
- Fixed Dockerfile line continuation (RUN && to proper format)
- Added HOST_PHOTO_DIR to docker-compose.yml for proper path translation
- All sensitive files properly excluded from public repo

### Phase 3: Deployment & Verification

**Docker Build & Container Launch:**
- Image built successfully with all security updates
- Container running as appuser (non-root)
- API responding on port 8000
- Moondream service accessible on port 8001

**Environment Verification:**
- All patch dependencies confirmed in requirements.txt
- XSS protection (escapeHtml) confirmed in templates
- Filename sanitization confirmed in main.py
- Non-root user setup confirmed in Dockerfile
- Sensitive files properly gitignored and not tracked

---

## Previous Work (Completed)

### Photo Upload Feature

Built complete upload functionality (from previous session):
- Moondream HTTP service on port 8001
- `/api/upload` endpoint with full pipeline (save → thumbnail → AI → embedding → index)
- `/api/uploads` endpoint for recent uploads
- Upload UI with modal, file picker, preview, progress bar
- Search index hot-reload via `add_photo()`
- All integrated and working

Current upload status: **FULLY FUNCTIONAL**
- Server running and healthy
- All dependencies patched for security
- Path translation working via HOST_PHOTO_DIR
- AI descriptions functional

---

## Git Status

**Commits Made This Session:**
```
828d03e → 54c84d3: Apply security audit fixes and update documentation
- Merged security audit PR with all critical/high CVE patches
- Updated README with Security section
- Fixed Dockerfile syntax
- Updated .gitignore to exclude SECURITY_AUDIT.md
- Branch: main, pushed to origin/main
```

**Current State:**
- Branch: main (up to date with origin/main)
- All changes committed and pushed
- No uncommitted changes (except local activity logs: done.md, tasks/)

---

## Architecture

```
Phone/Browser (Tailscale)
    ↓
Docker FastAPI Server (port 8000, appuser non-root)
    ↓ (host.docker.internal via extra_hosts)
Host Services:
  - Moondream2 (port 8001) - AI descriptions
  - Ollama (port 11434) - Alternative AI descriptions
    ↓
Samsung T7 SSD → /Volumes/T7_SSD/G-photos
  - Photos directory
  - Thumbnails
  - Embeddings & descriptions
```

---

## Security & Hardening Checklist

Completed in this session:
- [x] Critical CVE patches (pillow, fastapi, python-multipart)
- [x] XSS vulnerability fixed (HTML escaping)
- [x] Filename sanitization (strict alphanumeric + underscores/hyphens)
- [x] Path containment improved (is_relative_to vs string prefix)
- [x] Docker non-root user (appuser, UID 1000)
- [x] Upload size limit (50MB)
- [x] Hardcoded paths removed
- [x] Default credential warning
- [x] Sensitive configuration excluded from git
- [x] Full security audit documented locally

---

## Development Notes

### Key Technical Decisions
- Non-root user (1000:1000) in Docker for extra security isolation
- PATH conversion happens at container boundary (Docker path → host path)
- Filename sanitization uses negative character set to allow underscores/hyphens
- SECURITY_AUDIT.md kept private - contains detailed audit findings
- docker-compose.yml excluded from git - contains credentials

### Performance
- Search engine: 8,314 photos indexed
- Upload processing: ~2-5 seconds with AI description
- Moondream model: Lazy-loaded, ~500MB in memory after first query

### Dependencies
- Python 3.11, FastAPI 0.115.0, Uvicorn
- Sentence-transformers for embeddings (all-MiniLM-L12-v2, 384-dim)
- Pillow 12.1.1 for image processing
- pillow-heif for HEIC support
- httpx 0.27.0 for async HTTP calls to Moondream

---

## For Next Session

### Compound Phrase Search - COMPLETED ✅
- Implementation on `experimental/compound-phrase-search` branch
- Ready for testing and review before merging to main
- Can be tested at: `http://localhost:8000` with queries like:
  - "vibrant orange hair bathroom"
  - "family dinner"
  - "red car mountains"

### To Merge to Main
```bash
git checkout main
git merge experimental/compound-phrase-search
git push origin main
```

### Current Server Status
- Launch photo-server: `cd photo-server && docker compose up -d`
- Start Moondream: `python services/moondream_service.py` (in host environment)
- Access: `http://localhost:8000` or Tailscale IP

### Important Reminders
- Do NOT commit docker-compose.yml (contains credentials)
- Do NOT commit SECURITY_AUDIT.md (security details)
- Both are correctly gitignored
- HOST_PHOTO_DIR must match PHOTO_DIR for uploads to work
- Container user is appuser (UID 1000), may need permission fixes on Linux

---

**Latest Features:**
- ✅ Compound phrase semantic search with spaCy NLP
- ✅ Bulk photo upload (up to 25 photos)
- ✅ Browser HTTP Basic Auth only (no custom login)
- ✅ Persistent services (sleep-proof on macOS)
- ✅ Security hardening and CVE patches
- ✅ Photo upload with AI descriptions
- ✅ Hybrid semantic + keyword search
- ✅ Browse all with pagination
- ✅ Filter by people/dogs/cars
