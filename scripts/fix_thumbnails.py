#!/usr/bin/env python3
"""
Fix mismatched thumbnails by regenerating them from the original photos.
Reads the mismatch list and regenerates each thumbnail.
"""

import json
from pathlib import Path
from PIL import Image
import pillow_heif
import sys
import time

# Register HEIF opener
pillow_heif.register_heif_opener()

# Paths
SCRIPT_DIR = Path(__file__).parent
THUMBNAIL_DIR = SCRIPT_DIR.parent / "photo-server" / "thumbnails"
PHOTO_DIR = Path("/Volumes/T7_SSD/G-photos")
MISMATCHES_PATH = SCRIPT_DIR / "thumbnail_mismatches.json"

THUMBNAIL_SIZE = (400, 400)


def regenerate_thumbnail(photo_path: Path, thumb_path: Path) -> bool:
    """Regenerate a single thumbnail."""
    try:
        with Image.open(photo_path) as img:
            img = img.convert("RGB")
            img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
            img.save(thumb_path, "JPEG", quality=85)
        return True
    except Exception as e:
        print(f"\nError: {photo_path.name}: {e}")
        return False


def print_progress(current, total, start_time, fixed, errors):
    """Print progress bar."""
    elapsed = time.time() - start_time
    if current > 0:
        per_item = elapsed / current
        remaining = (total - current) * per_item
        eta_secs = remaining
    else:
        eta_secs = 0
    
    pct = current / total * 100
    bar_width = 40
    filled = int(bar_width * current / total)
    bar = "█" * filled + "░" * (bar_width - filled)
    
    sys.stdout.write(f"\r[{bar}] {pct:5.1f}% ({current}/{total}) | Fixed: {fixed} | Errors: {errors} | ETA: {eta_secs:.0f}s")
    sys.stdout.flush()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fix mismatched thumbnails")
    parser.add_argument("--dry-run", action="store_true", help="Just show what would be fixed")
    parser.add_argument("--limit", type=int, help="Limit number of fixes")
    args = parser.parse_args()
    
    # Load mismatches
    print("Loading mismatch list...")
    with open(MISMATCHES_PATH, 'r') as f:
        data = json.load(f)
    
    mismatches = data['mismatches']
    print(f"Found {len(mismatches)} mismatched thumbnails")
    
    if args.limit:
        mismatches = mismatches[:args.limit]
        print(f"Limiting to {args.limit} fixes")
    
    if args.dry_run:
        print("\nDRY RUN - No changes will be made\n")
        for m in mismatches[:20]:
            print(f"  Would fix: {m['filename']} (similarity: {m['similarity']:.4f})")
        if len(mismatches) > 20:
            print(f"  ... and {len(mismatches) - 20} more")
        return
    
    print(f"\nRegenerating {len(mismatches)} thumbnails...\n")
    
    fixed = 0
    errors = 0
    start_time = time.time()
    
    for i, mismatch in enumerate(mismatches):
        filename = mismatch['filename']
        photo_path = PHOTO_DIR / filename
        thumb_name = Path(filename).stem + ".jpg"
        thumb_path = THUMBNAIL_DIR / thumb_name
        
        if not photo_path.exists():
            errors += 1
            continue
        
        if regenerate_thumbnail(photo_path, thumb_path):
            fixed += 1
        else:
            errors += 1
        
        print_progress(i + 1, len(mismatches), start_time, fixed, errors)
    
    elapsed = time.time() - start_time
    
    print("\n")
    print("=" * 60)
    print("THUMBNAIL FIX COMPLETE")
    print("=" * 60)
    print(f"  Fixed:    {fixed}")
    print(f"  Errors:   {errors}")
    print(f"  Time:     {elapsed:.1f} seconds")
    print(f"  Speed:    {fixed/elapsed:.1f} thumbnails/sec")


if __name__ == "__main__":
    main()
