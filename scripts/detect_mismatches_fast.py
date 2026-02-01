#!/usr/bin/env python3
"""
Fast thumbnail mismatch detection using batched CLIP inference.
Shows clear progress and estimates completion time.
"""

import json
from pathlib import Path
from PIL import Image
import pillow_heif
import torch
from transformers import CLIPProcessor, CLIPModel
import numpy as np
from datetime import datetime
import time
import sys

# Register HEIF opener
pillow_heif.register_heif_opener()

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
THUMBNAIL_DIR = Path(__file__).parent.parent / "photo-server" / "thumbnails"
PHOTO_DIR = Path("/Volumes/T7_SSD/G-photos")
DESCRIPTIONS_PATH = DATA_DIR / "descriptions.json"
OUTPUT_PATH = Path(__file__).parent / "thumbnail_mismatches.json"

MISMATCH_THRESHOLD = 0.85
BATCH_SIZE = 16  # Process images in batches for speed


def load_image_safe(path: Path) -> Image.Image | None:
    """Load image, return None on error."""
    try:
        return Image.open(path).convert("RGB")
    except Exception as e:
        return None


def print_progress(current, total, start_time, mismatches_found, errors):
    """Print progress bar with ETA."""
    elapsed = time.time() - start_time
    if current > 0:
        per_item = elapsed / current
        remaining = (total - current) * per_item
        eta_mins = remaining / 60
    else:
        eta_mins = 0
    
    pct = current / total * 100
    bar_width = 40
    filled = int(bar_width * current / total)
    bar = "█" * filled + "░" * (bar_width - filled)
    
    sys.stdout.write(f"\r[{bar}] {pct:5.1f}% ({current}/{total}) | Mismatches: {mismatches_found} | Errors: {errors} | ETA: {eta_mins:.1f}m")
    sys.stdout.flush()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fast thumbnail mismatch detection")
    parser.add_argument("--limit", type=int, help="Limit photos to check")
    parser.add_argument("--threshold", type=float, default=0.85, help="Mismatch threshold")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size for inference")
    parser.add_argument("--start-from", type=int, default=0, help="Start from photo index (for resuming)")
    args = parser.parse_args()
    
    threshold = args.threshold
    batch_size = args.batch_size
    
    # Determine device
    if torch.backends.mps.is_available():
        device = "mps"
    elif torch.cuda.is_available():
        device = "cuda"
    else:
        device = "cpu"
    
    print(f"Fast Thumbnail Mismatch Detection")
    print(f"   Device: {device}")
    print(f"   Batch size: {batch_size}")
    print(f"   Threshold: {threshold}")
    print()
    
    # Load model
    print("Loading CLIP model...")
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    model.to(device)
    model.eval()
    print("Model loaded!")
    print()
    
    # Load photo list
    print("Loading photo list...")
    with open(DESCRIPTIONS_PATH, 'r') as f:
        data = json.load(f)
    photos = data['photos']
    
    # Apply start-from offset
    if args.start_from > 0:
        photos = photos[args.start_from:]
        print(f"   Starting from index {args.start_from}")
    
    if args.limit:
        photos = photos[:args.limit]
    
    total = len(photos)
    print(f"   Checking {total} photos")
    print()
    
    mismatches = []
    errors = []
    start_time = time.time()
    
    # Process in batches
    for batch_start in range(0, total, batch_size):
        batch_end = min(batch_start + batch_size, total)
        batch = photos[batch_start:batch_end]
        
        # Prepare batch data
        thumb_images = []
        photo_images = []
        valid_indices = []
        
        for i, photo in enumerate(batch):
            filename = photo['filename']
            thumb_name = Path(filename).stem + ".jpg"
            thumb_path = THUMBNAIL_DIR / thumb_name
            photo_path = PHOTO_DIR / filename
            
            # Check files exist
            if not thumb_path.exists():
                errors.append({"filename": filename, "error": "thumbnail missing"})
                continue
            if not photo_path.exists():
                errors.append({"filename": filename, "error": "original missing"})
                continue
            
            # Load images
            thumb_img = load_image_safe(thumb_path)
            photo_img = load_image_safe(photo_path)
            
            if thumb_img is None or photo_img is None:
                errors.append({"filename": filename, "error": "failed to load image"})
                continue
            
            thumb_images.append(thumb_img)
            photo_images.append(photo_img)
            valid_indices.append(batch_start + i)
        
        if not thumb_images:
            print_progress(batch_end, total, start_time, len(mismatches), len(errors))
            continue
        
        # Batch inference
        try:
            # Process thumbnails
            thumb_inputs = processor(images=thumb_images, return_tensors="pt", padding=True)
            thumb_inputs = {k: v.to(device) for k, v in thumb_inputs.items()}
            
            with torch.no_grad():
                thumb_embs = model.get_image_features(**thumb_inputs)
                thumb_embs = thumb_embs / thumb_embs.norm(dim=-1, keepdim=True)
            
            # Process originals
            photo_inputs = processor(images=photo_images, return_tensors="pt", padding=True)
            photo_inputs = {k: v.to(device) for k, v in photo_inputs.items()}
            
            with torch.no_grad():
                photo_embs = model.get_image_features(**photo_inputs)
                photo_embs = photo_embs / photo_embs.norm(dim=-1, keepdim=True)
            
            # Compute similarities
            similarities = (thumb_embs * photo_embs).sum(dim=-1).cpu().numpy()
            
            # Check for mismatches
            for idx, (valid_idx, sim) in enumerate(zip(valid_indices, similarities)):
                photo = photos[valid_idx - batch_start] if batch_start == 0 else photos[valid_idx]
                photo = photos[valid_idx]
                
                if sim < threshold:
                    mismatches.append({
                        "filename": photo['filename'],
                        "similarity": round(float(sim), 4),
                        "description": photo['description'][:150] + "..."
                    })
                    
        except Exception as e:
            print(f"\nBatch error: {e}")
            for i in valid_indices:
                errors.append({"filename": photos[i]['filename'], "error": str(e)})
        
        # Update progress
        print_progress(batch_end, total, start_time, len(mismatches), len(errors))
    
    print()  # New line after progress bar
    print()
    
    # Sort by similarity (worst first)
    mismatches.sort(key=lambda x: x['similarity'])
    
    # Calculate stats
    elapsed = time.time() - start_time
    
    # Save results
    results = {
        "threshold": threshold,
        "total_checked": total - len(errors),
        "mismatches_found": len(mismatches),
        "errors": len(errors),
        "scan_time_seconds": round(elapsed, 1),
        "scan_date": datetime.now().isoformat(),
        "mismatches": mismatches,
        "error_list": errors[:100]
    }
    
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Summary
    print("=" * 60)
    print("THUMBNAIL MISMATCH SCAN COMPLETE")
    print("=" * 60)
    print(f"  Photos checked:    {total - len(errors)}")
    print(f"  Mismatches found:  {len(mismatches)} ({len(mismatches)/(total-len(errors))*100:.1f}%)")
    print(f"  Errors:            {len(errors)}")
    print(f"  Time taken:        {elapsed/60:.1f} minutes")
    print(f"  Speed:             {(total-len(errors))/elapsed:.1f} photos/sec")
    print(f"  Results saved:     {OUTPUT_PATH}")
    
    if mismatches:
        print(f"\n  Top 10 worst mismatches:")
        for m in mismatches[:10]:
            print(f"    {m['filename']}: {m['similarity']:.4f}")


if __name__ == "__main__":
    main()
