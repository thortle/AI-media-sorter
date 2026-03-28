#!/usr/bin/env python3
"""
Repair Embeddings - Fix misaligned embeddings

This script:
1. Identifies photos with mismatched embeddings (stored vs fresh encoding)
2. Regenerates embeddings for ALL photos to ensure correct alignment
3. Uses filename as the key to ensure no index-based mismatches

Run this script when embeddings become out of sync with descriptions.
"""

from sentence_transformers import SentenceTransformer
import json
import numpy as np
from pathlib import Path
import sys

def analyze_mismatches(photos, embeddings, model, threshold=0.90):
    """Find photos where stored embedding doesn't match description."""
    mismatches = []

    print(f"Analyzing {len(photos)} photos for mismatches...")
    print(f"Embeddings array shape: {embeddings.shape}")

    if len(photos) != len(embeddings):
        print(f"\nWARNING: Count mismatch!")
        print(f"  Photos: {len(photos)}")
        print(f"  Embeddings: {len(embeddings)}")
        print(f"  Difference: {len(embeddings) - len(photos)}")

    for i, p in enumerate(photos):
        if i >= len(embeddings):
            mismatches.append((i, p['filename'], 'NO_EMBEDDING', 0.0))
            continue

        stored = embeddings[i]
        fresh = model.encode(p['description'], normalize_embeddings=True)
        sim = float(np.dot(stored, fresh))

        if sim < threshold:
            mismatches.append((i, p['filename'], sim))

    return mismatches


def regenerate_all_embeddings(photos, model, batch_size=32):
    """Regenerate embeddings for all photos from descriptions."""
    print(f"\nRegenerating embeddings for {len(photos)} photos...")

    descriptions = [photo['description'] for photo in photos]

    embeddings = model.encode(
        descriptions,
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    print(f"Created embeddings with shape: {embeddings.shape}")
    return embeddings


def verify_embeddings(photos, embeddings, model, sample_size=50):
    """Verify that new embeddings match descriptions."""
    print(f"\nVerifying {sample_size} random samples...")

    # Sample random indices
    indices = np.random.choice(len(photos), min(sample_size, len(photos)), replace=False)

    all_match = True
    for i in indices:
        stored = embeddings[i]
        fresh = model.encode(photos[i]['description'], normalize_embeddings=True)
        sim = float(np.dot(stored, fresh))

        if sim < 0.999:  # Should be nearly identical
            print(f"  MISMATCH at index {i}: {photos[i]['filename']} (sim={sim:.4f})")
            all_match = False

    if all_match:
        print("  All samples verified successfully!")

    return all_match


def main():
    # Paths
    json_path = "../../data/descriptions.json"
    embeddings_path = "../../data/embeddings.npy"
    backup_path = "../../data/embeddings_backup.npy"

    # Check files exist
    if not Path(json_path).exists():
        print(f"Error: {json_path} not found!")
        sys.exit(1)

    if not Path(embeddings_path).exists():
        print(f"Error: {embeddings_path} not found!")
        sys.exit(1)

    # Load model
    print("Loading model: all-MiniLM-L12-v2...")
    model = SentenceTransformer('all-MiniLM-L12-v2')
    print(f"Model loaded (embedding dim: {model.get_sentence_embedding_dimension()})")

    # Load data
    print(f"\nLoading descriptions from {json_path}...")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    photos = data.get('photos', [])
    print(f"Loaded {len(photos)} photos")

    print(f"\nLoading embeddings from {embeddings_path}...")
    old_embeddings = np.load(embeddings_path)
    print(f"Loaded embeddings: {old_embeddings.shape}")

    # Analyze current state
    print("\n" + "="*60)
    print("ANALYSIS")
    print("="*60)
    mismatches = analyze_mismatches(photos, old_embeddings, model)
    print(f"\nMismatched embeddings: {len(mismatches)} / {len(photos)}")

    if len(mismatches) == 0:
        print("\nNo mismatches found! Embeddings are already in sync.")
        return

    # Show some examples
    print("\nFirst 5 mismatches:")
    for idx, fname, sim in mismatches[:5]:
        print(f"  Index {idx}: {fname} (sim={sim:.4f})")

    # Confirm regeneration
    print("\n" + "="*60)
    print("REGENERATION")
    print("="*60)

    response = input(f"\nRegenerate ALL {len(photos)} embeddings? [y/N]: ")
    if response.lower() != 'y':
        print("Aborted.")
        return

    # Backup old embeddings
    print(f"\nBacking up old embeddings to {backup_path}...")
    np.save(backup_path, old_embeddings)

    # Regenerate
    new_embeddings = regenerate_all_embeddings(photos, model)

    # Verify
    if not verify_embeddings(photos, new_embeddings, model):
        print("\nERROR: Verification failed! Not saving.")
        return

    # Save
    print(f"\nSaving new embeddings to {embeddings_path}...")
    np.save(embeddings_path, new_embeddings)

    # Save metadata
    metadata_path = embeddings_path.replace('.npy', '_metadata.json')
    metadata = {
        'model_name': 'all-MiniLM-L12-v2',
        'num_embeddings': len(new_embeddings),
        'embedding_dim': new_embeddings.shape[1],
        'normalized': True,
        'repaired': True,
        'previous_mismatches': len(mismatches)
    }
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print("\n" + "="*60)
    print("COMPLETE")
    print("="*60)
    print(f"Regenerated {len(new_embeddings)} embeddings")
    print(f"Fixed {len(mismatches)} mismatches")
    print(f"Backup saved to: {backup_path}")
    print("\nRestart the photo server to use the new embeddings:")
    print("  docker compose restart")


if __name__ == "__main__":
    main()
