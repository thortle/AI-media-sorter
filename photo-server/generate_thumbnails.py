#!/usr/bin/env python3
"""
Generate thumbnails for all photos in the source directory.
Run this script before starting the photo server.
"""

import argparse
import os
import sys
from pathlib import Path

from PIL import Image
from tqdm import tqdm

# Try to import pillow-heif for HEIC support
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIC_SUPPORT = True
except ImportError:
    HEIC_SUPPORT = False
    print("Warning: pillow-heif not installed. HEIC files will be skipped.")
    print("Install with: pip install pillow-heif")

# Configuration
# PHOTO_DIR is read from the PHOTO_DIR environment variable or --photos CLI argument.
# Set it in your .env file or pass it on the command line.
_photo_dir_env = os.getenv("PHOTO_DIR")
PHOTO_DIR = _photo_dir_env  # resolved below in __main__ if a CLI arg is given
THUMBNAIL_DIR = os.getenv("THUMBNAIL_DIR", "./thumbnails")
THUMBNAIL_SIZE = (400, 400)
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
if HEIC_SUPPORT:
    SUPPORTED_FORMATS.add('.heic')


def generate_thumbnails():
    """Generate thumbnails for all photos."""
    os.makedirs(THUMBNAIL_DIR, exist_ok=True)
    
    # Check if photo directory exists
    photo_path = Path(PHOTO_DIR)
    if not photo_path.exists():
        print(f"Error: Photo directory not found: {PHOTO_DIR}")
        print("Make sure the path is correct and accessible.")
        return
    
    # Find all photos (skip macOS metadata files)
    photos = [
        f for f in photo_path.iterdir()
        if f.suffix.lower() in SUPPORTED_FORMATS 
        and f.is_file()
        and not f.name.startswith('._')  # Skip macOS metadata files
    ]
    
    print(f"Found {len(photos)} photos in {PHOTO_DIR}")
    
    # Count existing thumbnails
    existing = sum(
        1 for f in Path(THUMBNAIL_DIR).glob("*.jpg")
    )
    print(f"Existing thumbnails: {existing}")
    
    created = 0
    skipped = 0
    errors = 0
    
    for photo_path in tqdm(photos, desc="Generating thumbnails"):
        try:
            # Thumbnail filename: stem_EXT.jpg (e.g. IMG_0216_HEIC.jpg)
            # Using the full extension avoids collisions when two files share
            # the same stem (e.g. IMG_0216.HEIC and IMG_0216.PNG).
            thumb_name = photo_path.stem + "_" + photo_path.suffix.lstrip(".") + ".jpg"
            thumb_path = Path(THUMBNAIL_DIR) / thumb_name
            
            # Skip if already exists
            if thumb_path.exists():
                skipped += 1
                continue
            
            # Open and create thumbnail
            with Image.open(photo_path) as img:
                # Handle EXIF orientation
                try:
                    from PIL import ImageOps
                    img = ImageOps.exif_transpose(img)
                except Exception:
                    pass
                
                # Convert to RGB (handles RGBA, HEIC, etc.)
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Create thumbnail
                img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                
                # Save as JPEG
                img.save(thumb_path, "JPEG", quality=85, optimize=True)
                created += 1
                
        except Exception as e:
            errors += 1
            tqdm.write(f"Error processing {photo_path.name}: {e}")
    
    print(f"\nComplete!")
    print(f"  Created: {created}")
    print(f"  Skipped (existing): {skipped}")
    print(f"  Errors: {errors}")
    print(f"  Total thumbnails: {len(list(Path(THUMBNAIL_DIR).glob('*.jpg')))}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate thumbnails for all photos.")
    parser.add_argument("--photos", default=None,
                        help="Path to photo directory (overrides PHOTO_DIR env var)")
    parser.add_argument("--thumbnails", default=None,
                        help="Path to thumbnail output directory (overrides THUMBNAIL_DIR env var)")
    args = parser.parse_args()

    if args.photos:
        PHOTO_DIR = args.photos
    if args.thumbnails:
        THUMBNAIL_DIR = args.thumbnails

    if not PHOTO_DIR:
        print("Error: Photo directory not set.")
        print("Set the PHOTO_DIR environment variable or use --photos /path/to/photos")
        sys.exit(1)

    generate_thumbnails()
