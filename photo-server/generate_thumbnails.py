#!/usr/bin/env python3
"""
Generate thumbnails for all photos in the source directory.
Run this script before starting the photo server.
"""

import os
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
PHOTO_DIR = "/Volumes/T7_SSD/G-photos"
THUMBNAIL_DIR = "./thumbnails"
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
        print("Make sure the Samsung T7 SSD is connected and mounted.")
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
            # Thumbnail filename (always .jpg)
            thumb_name = photo_path.stem + ".jpg"
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
    generate_thumbnails()
