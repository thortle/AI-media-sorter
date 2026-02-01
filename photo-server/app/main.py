"""
Photo Server - FastAPI application for semantic photo search.
"""

import io
import json
import os
import secrets
import shutil
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from PIL import Image
import pillow_heif

# Register HEIF opener with Pillow
pillow_heif.register_heif_opener()

from search import search_engine

# Configuration from environment
PHOTO_BASE_PATH = Path(os.getenv("PHOTO_BASE_PATH", "/photos"))
THUMBNAIL_PATH = Path(os.getenv("THUMBNAIL_PATH", "/app/thumbnails"))
DATA_PATH = os.getenv("DATA_PATH", "/app/data")
TRASH_PATH = PHOTO_BASE_PATH / "_trash"

# Authentication credentials (set via environment variables)
AUTH_USERNAME = os.getenv("AUTH_USERNAME", "admin")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "changeme")  # CHANGE THIS!

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
async def index(request: Request, username: str = Depends(verify_credentials)):
    """Serve the main web UI."""
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
    # Thumbnails are stored as .jpg regardless of original format
    thumb_name = Path(filename).stem + ".jpg"
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
        thumb_name = Path(filename).stem + ".jpg"
        thumb_path = THUMBNAIL_PATH / thumb_name
        if thumb_path.exists():
            trash_thumb_name = f"{Path(filename).stem}_{timestamp}.jpg"
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
            "trash_path": str(trash_photo_path),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete photo: {str(e)}")
