"""
Photo Server - FastAPI application for semantic photo search.
"""

import base64
import io
import json
import logging
import os
import re
import secrets
import shutil
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx
import numpy as np
from fastapi import FastAPI, HTTPException, Query, Depends, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from PIL import Image, ImageOps
import pillow_heif

# Register HEIF opener with Pillow
pillow_heif.register_heif_opener()

from search import search_engine

log = logging.getLogger(__name__)

# Configuration from environment
PHOTO_BASE_PATH = Path(os.getenv("PHOTO_BASE_PATH", "/photos"))
THUMBNAIL_PATH = Path(os.getenv("THUMBNAIL_PATH", "/app/thumbnails"))
DATA_PATH = os.getenv("DATA_PATH", "/app/data")
TRASH_PATH = PHOTO_BASE_PATH / "_trash"
ALBUM_THUMBNAIL_PATH = THUMBNAIL_PATH / "albums"
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
MOONDREAM_HOST = os.getenv("MOONDREAM_HOST", "http://host.docker.internal:8001")

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp", ".gif"}

# Maximum allowed upload size (20 MB)
MAX_UPLOAD_BYTES = 20 * 1024 * 1024

# Authentication credentials (set via environment variables)
AUTH_USERNAME = os.getenv("AUTH_USERNAME", "admin")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "changeme")

_DEFAULT_CREDENTIALS = {"admin", "changeme"}
if AUTH_USERNAME in _DEFAULT_CREDENTIALS or AUTH_PASSWORD in _DEFAULT_CREDENTIALS:
    log.warning(
        "⚠  Default AUTH_USERNAME/AUTH_PASSWORD detected. "
        "Set AUTH_USERNAME and AUTH_PASSWORD environment variables before "
        "exposing this server to any network."
    )

# Security setup
security = HTTPBasic()


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify HTTP Basic Auth credentials."""
    correct_username = secrets.compare_digest(credentials.username, AUTH_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, AUTH_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal attacks."""
    # Block any path traversal attempts
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    # Only allow safe characters
    safe_name = Path(filename).name  # Extracts just the filename
    if safe_name != filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    return filename


def sanitize_album_path(album_name: str) -> Path:
    """Validate album name and return its absolute path inside PHOTO_BASE_PATH."""
    if ".." in album_name:
        raise HTTPException(status_code=400, detail="Invalid album name")
    album_path = (PHOTO_BASE_PATH / album_name).resolve()
    if not album_path.is_relative_to(PHOTO_BASE_PATH.resolve()):
        raise HTTPException(status_code=400, detail="Invalid album name")
    return album_path


def sanitize_rel_path(album_path: Path, rel_path: str) -> Path:
    """Validate a relative path within an album directory."""
    if ".." in rel_path:
        raise HTTPException(status_code=400, detail="Invalid path")
    full_path = (album_path / rel_path).resolve()
    if not full_path.is_relative_to(album_path.resolve()):
        raise HTTPException(status_code=400, detail="Invalid path")
    return full_path


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load search engine on startup."""
    search_engine.data_path = Path(DATA_PATH)
    search_engine.load()
    yield


app = FastAPI(
    title="Photo Server",
    description="Semantic search for your photo collection",
    version="1.0.0",
    lifespan=lifespan,
)

# Templates
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main web UI (auth handled client-side via login form)."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/search")
async def search_photos(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(500, ge=1, le=1000, description="Number of results"),
    has_characters: Optional[bool] = Query(None, description="Filter: has people"),
    has_dogs: Optional[bool] = Query(None, description="Filter: has dogs"),
    has_cars: Optional[bool] = Query(None, description="Filter: has cars"),
    min_score: float = Query(0.0, ge=0.0, le=1.0, description="Minimum similarity score"),
    username: str = Depends(verify_credentials),
):
    """
    Hybrid semantic search for photos.
    
    Example: /api/search?q=beach sunset&limit=20&min_score=0.2
    """
    results = search_engine.search(
        query=q,
        top_k=limit,
        has_characters=has_characters,
        has_dogs=has_dogs,
        has_cars=has_cars,
        min_score=min_score,
    )
    return {
        "query": q,
        "count": len(results),
        "results": results,
    }


@app.get("/api/photos")
async def list_photos(
    limit: int = Query(500, ge=1, le=1000, description="Number of results per page"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    has_characters: Optional[bool] = Query(None, description="Filter: has people"),
    has_dogs: Optional[bool] = Query(None, description="Filter: has dogs"),
    has_cars: Optional[bool] = Query(None, description="Filter: has cars"),
    username: str = Depends(verify_credentials),
):
    """
    List all photos with optional filtering and pagination.
    
    Example: /api/photos?limit=50&offset=0&has_dogs=true
    """
    photos, total = search_engine.get_all_photos(
        limit=limit,
        offset=offset,
        has_characters=has_characters,
        has_dogs=has_dogs,
        has_cars=has_cars,
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "count": len(photos),
        "photos": photos,
    }


@app.get("/api/photo/{filename}")
async def get_photo_info(filename: str, username: str = Depends(verify_credentials)):
    """Get metadata for a specific photo."""
    filename = sanitize_filename(filename)
    photo = search_engine.get_photo_by_filename(filename)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    return photo


@app.get("/thumbnail/{filename}")
async def get_thumbnail(filename: str, username: str = Depends(verify_credentials)):
    """Serve a thumbnail image."""
    filename = sanitize_filename(filename)
    # Thumbnails named as stem_EXT.jpg (e.g. IMG_0216_HEIC.jpg) to avoid
    # collisions when two files share the same stem (IMG_0216.HEIC vs IMG_0216.PNG)
    thumb_name = Path(filename).stem + "_" + Path(filename).suffix.lstrip(".") + ".jpg"
    thumb_path = THUMBNAIL_PATH / thumb_name
    
    if not thumb_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    
    return FileResponse(
        thumb_path,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@app.get("/photo/{filename}")
async def get_photo(filename: str, username: str = Depends(verify_credentials)):
    """Serve the original photo, converting HEIC to JPEG for browser compatibility."""
    filename = sanitize_filename(filename)
    photo_path = PHOTO_BASE_PATH / filename
    
    if not photo_path.exists():
        raise HTTPException(status_code=404, detail="Photo not found")
    
    ext = photo_path.suffix.lower()
    
    # Convert HEIC/HEIF to JPEG on-the-fly for browser compatibility
    if ext in [".heic", ".heif"]:
        try:
            img = Image.open(photo_path)
            # Convert to RGB if necessary (HEIC can have alpha channel)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # Save to buffer as JPEG
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=90)
            buffer.seek(0)
            
            return StreamingResponse(
                buffer,
                media_type="image/jpeg",
                headers={"Cache-Control": "public, max-age=3600"},
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to convert image: {str(e)}")
    
    # Serve other formats directly
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }
    media_type = media_types.get(ext, "application/octet-stream")
    
    return FileResponse(
        photo_path,
        media_type=media_type,
        headers={"Cache-Control": "public, max-age=3600"},
    )


@app.get("/download/{filename}")
async def download_photo(filename: str, username: str = Depends(verify_credentials)):
    """Download the original photo."""
    filename = sanitize_filename(filename)
    photo_path = PHOTO_BASE_PATH / filename
    
    if not photo_path.exists():
        raise HTTPException(status_code=404, detail="Photo not found")
    
    return FileResponse(
        photo_path,
        filename=filename,
        media_type="application/octet-stream",
    )


@app.get("/api/stats")
async def get_stats(username: str = Depends(verify_credentials)):
    """Get collection statistics."""
    photos, total = search_engine.get_all_photos(limit=1, offset=0)
    
    # Count filters
    _, with_characters = search_engine.get_all_photos(limit=1, has_characters=True)
    _, with_dogs = search_engine.get_all_photos(limit=1, has_dogs=True)
    _, with_cars = search_engine.get_all_photos(limit=1, has_cars=True)
    
    return {
        "total_photos": total,
        "with_characters": with_characters,
        "with_dogs": with_dogs,
        "with_cars": with_cars,
    }


# ── Album endpoints ──────────────────────────────────────────────────────────

@app.get("/api/albums")
async def list_albums(username: str = Depends(verify_credentials)):
    """
    List all photo albums (subdirectories of PHOTO_BASE_PATH that contain images).
    Directories starting with '_', '.' or '._' are excluded.
    """
    albums = []
    try:
        for item in sorted(PHOTO_BASE_PATH.iterdir()):
            if item.name.startswith("_") or item.name.startswith("."):
                continue
            try:
                if not item.is_dir():
                    continue
                count = sum(
                    1 for f in item.rglob("*")
                    if not f.name.startswith(".") and f.suffix.lower() in IMAGE_EXTENSIONS
                )
                if count > 0:
                    albums.append({"name": item.name, "photo_count": count})
            except (PermissionError, OSError):
                continue
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"albums": albums}


@app.get("/api/album/{album_name}/photos")
async def list_album_photos(
    album_name: str,
    limit: int = Query(500, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    username: str = Depends(verify_credentials),
):
    """List photos inside an album with pagination, sorted by filename."""
    album_path = sanitize_album_path(album_name)
    if not album_path.is_dir():
        raise HTTPException(status_code=404, detail="Album not found")

    files = sorted(
        [
            f for f in album_path.rglob("*")
            if not f.name.startswith(".") and f.suffix.lower() in IMAGE_EXTENSIONS
        ],
        key=lambda f: f.name,
    )
    total = len(files)
    page_files = files[offset : offset + limit]

    photos = [
        {
            "filename": f.name,
            "album": album_name,
            "rel_path": str(f.relative_to(album_path)),
        }
        for f in page_files
    ]
    return {"total": total, "offset": offset, "limit": limit, "count": len(photos), "photos": photos}


@app.get("/album-thumbnail/{album_name}/{rel_path:path}")
async def get_album_thumbnail(
    album_name: str, rel_path: str, username: str = Depends(verify_credentials)
):
    """Serve a thumbnail for an album photo, generating and caching it on first request."""
    album_path = sanitize_album_path(album_name)
    file_path = sanitize_rel_path(album_path, rel_path)

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Photo not found")

    # Build a flat cache key: replace path separators to avoid nested dirs
    flat_stem = rel_path.replace("/", "_").replace("\\", "_")
    thumb_dir = ALBUM_THUMBNAIL_PATH / album_name
    thumb_dir.mkdir(parents=True, exist_ok=True)
    thumb_path = thumb_dir / (Path(flat_stem).stem + ".jpg")

    if not thumb_path.exists():
        try:
            img = Image.open(file_path)
            if img.mode in ("RGBA", "P", "CMYK"):
                img = img.convert("RGB")
            img.thumbnail((400, 400))
            img.save(thumb_path, format="JPEG", quality=85)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate thumbnail: {e}")

    return FileResponse(
        thumb_path,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@app.get("/album-photo/{album_name}/{rel_path:path}")
async def get_album_photo(
    album_name: str, rel_path: str, username: str = Depends(verify_credentials)
):
    """Serve an album photo, converting HEIC to JPEG on-the-fly."""
    album_path = sanitize_album_path(album_name)
    file_path = sanitize_rel_path(album_path, rel_path)

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Photo not found")

    ext = file_path.suffix.lower()
    if ext in (".heic", ".heif"):
        try:
            img = Image.open(file_path)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=90)
            buffer.seek(0)
            return StreamingResponse(
                buffer,
                media_type="image/jpeg",
                headers={"Cache-Control": "public, max-age=3600"},
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to convert image: {e}")

    media_types = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
        ".webp": "image/webp", ".gif": "image/gif",
    }
    return FileResponse(
        file_path,
        media_type=media_types.get(ext, "application/octet-stream"),
        headers={"Cache-Control": "public, max-age=3600"},
    )


@app.get("/album-download/{album_name}/{rel_path:path}")
async def download_album_photo(
    album_name: str, rel_path: str, username: str = Depends(verify_credentials)
):
    """Download an original album photo."""
    album_path = sanitize_album_path(album_name)
    file_path = sanitize_rel_path(album_path, rel_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Photo not found")
    return FileResponse(file_path, filename=file_path.name, media_type="application/octet-stream")


# ─────────────────────────────────────────────────────────────────────────────

@app.delete("/api/photo/{filename}")
async def delete_photo(filename: str, username: str = Depends(verify_credentials)):
    """
    Move a photo to trash folder.
    
    - Moves original photo to _trash/ folder
    - Moves thumbnail to _trash/thumbnails/
    - Removes from descriptions.json
    - Updates in-memory search index
    """
    filename = sanitize_filename(filename)
    photo_path = PHOTO_BASE_PATH / filename
    
    if not photo_path.exists():
        raise HTTPException(status_code=404, detail="Photo not found")
    
    # Create trash directories if needed
    TRASH_PATH.mkdir(exist_ok=True)
    trash_thumbs = TRASH_PATH / "thumbnails"
    trash_thumbs.mkdir(exist_ok=True)
    
    # Generate unique trash filename (add timestamp to avoid conflicts)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    trash_filename = f"{Path(filename).stem}_{timestamp}{Path(filename).suffix}"
    
    try:
        # Move original photo to trash
        trash_photo_path = TRASH_PATH / trash_filename
        shutil.move(str(photo_path), str(trash_photo_path))
        
        # Move thumbnail to trash (if exists)
        thumb_name = Path(filename).stem + "_" + Path(filename).suffix.lstrip(".") + ".jpg"
        thumb_path = THUMBNAIL_PATH / thumb_name
        if thumb_path.exists():
            trash_thumb_name = f"{Path(filename).stem}_{Path(filename).suffix.lstrip('.')}_{timestamp}.jpg"
            shutil.move(str(thumb_path), str(trash_thumbs / trash_thumb_name))
        
        # Remove from search engine (in-memory)
        removed = search_engine.remove_photo(filename)
        
        if removed:
            # Update descriptions.json on disk
            descriptions_path = Path(DATA_PATH) / "descriptions.json"
            with open(descriptions_path, "r") as f:
                data = json.load(f)
            
            # Filter out the deleted photo
            data["photos"] = [p for p in data["photos"] if p["filename"] != filename]
            
            with open(descriptions_path, "w") as f:
                json.dump(data, f, indent=2)
        
        return {
            "status": "success",
            "message": f"Photo moved to trash: {filename}",
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete photo: {str(e)}")


# ── Upload endpoints ─────────────────────────────────────────────────────────

def generate_single_thumbnail(photo_path: Path, thumb_dir: Path) -> Path:
    """Generate thumbnail for a single photo."""
    thumb_name = photo_path.stem + "_" + photo_path.suffix.lstrip(".").upper() + ".jpg"
    thumb_path = thumb_dir / thumb_name

    if thumb_path.exists():
        return thumb_path

    img = Image.open(photo_path)
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass

    if img.mode in ('RGBA', 'P', 'CMYK'):
        img = img.convert('RGB')

    img.thumbnail((400, 400), Image.Resampling.LANCZOS)
    img.save(thumb_path, "JPEG", quality=85, optimize=True)
    return thumb_path


async def get_ai_description(photo_path: Path) -> str:
    """Get AI description from Moondream2 service running on host."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{MOONDREAM_HOST}/describe",
            json={"photo_path": str(photo_path)},
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail=f"Moondream error: {response.text}"
            )

        result = response.json()
        return result.get("description", "").strip()


@app.post("/api/upload")
async def upload_photo(
    file: UploadFile = File(...),
    username: str = Depends(verify_credentials),
):
    """
    Upload a photo and process it for semantic search.

    1. Saves the file with timestamp prefix
    2. Generates thumbnail
    3. Gets AI description from Ollama llava
    4. Creates embedding
    5. Adds to search index
    """
    # Validate file type
    ext = Path(file.filename).suffix.lower()
    if ext not in IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    # Read file and enforce size limit before writing to disk
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed size is {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
        )

    # Generate unique filename using only alphanumeric characters
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    original_stem = re.sub(r"[^a-zA-Z0-9_\-]", "_", Path(file.filename).stem)
    safe_name = f"upload_{timestamp}_{original_stem}{ext}"

    photo_path = PHOTO_BASE_PATH / safe_name

    # Save the file
    with open(photo_path, "wb") as f:
        f.write(content)

    try:
        # Generate thumbnail
        generate_single_thumbnail(photo_path, THUMBNAIL_PATH)

        # Get AI description from Ollama
        description = await get_ai_description(photo_path)

        # Create embedding
        embedding = search_engine.model.encode(description, normalize_embeddings=True)

        # Create photo entry
        new_photo = {
            "filename": safe_name,
            "description": description,
            "full_path": str(photo_path),
            "uploaded_at": datetime.now().isoformat(),
            "keywords": {},
            "metadata": {
                "file_extension": ext,
                "description_length": len(description),
            }
        }

        # Update descriptions.json
        descriptions_path = Path(DATA_PATH) / "descriptions.json"
        with open(descriptions_path, "r") as f:
            data = json.load(f)

        data["photos"].append(new_photo)
        data["metadata"]["total_photos"] = len(data["photos"])

        with open(descriptions_path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Update embeddings.npy
        embeddings_path = Path(DATA_PATH) / "embeddings.npy"
        existing_embeddings = np.load(embeddings_path)
        new_embeddings = np.vstack([existing_embeddings, embedding.reshape(1, -1)])
        np.save(embeddings_path, new_embeddings)

        # Add to in-memory search index
        search_engine.add_photo(new_photo, embedding)

        return {
            "status": "success",
            "filename": safe_name,
            "description": description[:200] + "..." if len(description) > 200 else description,
            "message": "Photo uploaded and processed successfully",
        }

    except Exception as e:
        # Log the full error for debugging
        import traceback
        print(f"Upload error for {safe_name}:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print(f"Traceback:")
        traceback.print_exc()

        # Clean up on failure
        if photo_path.exists():
            photo_path.unlink()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.get("/api/uploads")
async def list_recent_uploads(
    limit: int = Query(50, ge=1, le=200),
    username: str = Depends(verify_credentials),
):
    """
    List recently uploaded photos (those with uploaded_at timestamp).
    Sorted by upload time, newest first.
    """
    uploads = []
    for photo in search_engine.photos:
        if "uploaded_at" in photo:
            uploads.append({
                "filename": photo["filename"],
                "description": photo.get("description", ""),
                "uploaded_at": photo["uploaded_at"],
            })

    # Sort by upload time, newest first
    uploads.sort(key=lambda x: x["uploaded_at"], reverse=True)

    return {
        "total": len(uploads),
        "count": min(limit, len(uploads)),
        "uploads": uploads[:limit],
    }
