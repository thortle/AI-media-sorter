#!/usr/bin/env python3
"""
Facial Recognition CLI - Add face recognition metadata to descriptions.json
"""

import click
import json
import logging
import sys
from pathlib import Path
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from face_processor import FaceRecognitionProcessor

def setup_logger():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)


@click.command()
@click.option('--descriptions-file', 
              type=click.Path(exists=True), 
              default='../../data/descriptions.json',
              help='Path to descriptions.json file')
@click.option('--reference-dataset', 
              type=click.Path(exists=True, file_okay=False, dir_okay=True),
              default='../../data/face_recognition_dataset',
              help='Path to reference face dataset directory')
@click.option('--model', 
              type=click.Choice(['Facenet512', 'Facenet', 'VGG-Face', 'ArcFace', 'Dlib', 'SFace']),
              default='Facenet512',
              help='DeepFace model to use (Facenet512 recommended)')
@click.option('--detector', 
              type=click.Choice(['retinaface', 'mtcnn', 'opencv', 'ssd', 'dlib']),
              default='retinaface',
              help='Face detector backend (retinaface recommended)')
@click.option('--threshold', 
              type=float, 
              default=0.4,
              help='Face match distance threshold (lower = stricter, 0.4 recommended)')
@click.option('--max-photos', 
              type=int, 
              default=None,
              help='Limit number of photos to process (for testing)')
@click.option('--force', 
              is_flag=True,
              help='Reprocess all photos, even if already processed')
def main(descriptions_file, reference_dataset, model, detector, threshold, max_photos, force):
    """
    Add facial recognition metadata to descriptions.json
    
    This script:
    1. Loads reference faces from the face_recognition_dataset
    2. Processes each photo in descriptions.json
    3. Detects faces and matches against reference dataset
    4. Adds face_recognition metadata to each photo entry
    
    Examples:
        python main.py
        python main.py --max-photos 100 --threshold 0.35
        python main.py --model Facenet512 --detector retinaface --force
    """
    logger = setup_logger()
    
    logger.info("=" * 70)
    logger.info("Facial Recognition Processor")
    logger.info("=" * 70)
    logger.info(f"Descriptions file: {descriptions_file}")
    logger.info(f"Reference dataset: {reference_dataset}")
    logger.info(f"Model: {model}")
    logger.info(f"Detector: {detector}")
    logger.info(f"Distance threshold: {threshold}")
    
    # Load descriptions.json
    try:
        with open(descriptions_file, 'r') as f:
            data = json.load(f)
        logger.info(f"✓ Loaded {len(data['photos'])} photos from descriptions.json")
    except Exception as e:
        logger.error(f"Failed to load descriptions file: {e}")
        sys.exit(1)
    
    # Initialize face recognition processor
    try:
        logger.info("\nInitializing face recognition processor...")
        processor = FaceRecognitionProcessor(
            reference_dataset_path=reference_dataset,
            model_name=model,
            detector_backend=detector,
            distance_threshold=threshold
        )
        logger.info("✓ Face recognition processor ready")
    except Exception as e:
        logger.error(f"Failed to initialize processor: {e}")
        sys.exit(1)
    
    # Filter photos to process
    photos_to_process = []
    
    for photo in data['photos']:
        # Skip if already processed (unless --force)
        if not force and 'face_recognition' in photo:
            continue
        
        photos_to_process.append(photo)
        
        # Apply max_photos limit
        if max_photos and len(photos_to_process) >= max_photos:
            break
    
    if len(photos_to_process) == 0:
        logger.info("\n✓ All photos already processed!")
        logger.info("  Use --force to reprocess all photos")
        return
    
    logger.info(f"\nProcessing {len(photos_to_process)} photos...")
    if not force:
        logger.info(f"(Skipping {len(data['photos']) - len(photos_to_process)} already processed)")
    
    # Process photos with progress bar
    processed_count = 0
    face_found_count = 0
    known_face_count = 0
    
    with tqdm(total=len(photos_to_process), desc="Analyzing faces") as pbar:
        for photo in photos_to_process:
            try:
                # Get full path to photo
                photo_path = photo.get('full_path')
                if not photo_path or not Path(photo_path).exists():
                    logger.warning(f"Photo not found: {photo.get('filename', 'unknown')}")
                    pbar.update(1)
                    continue
                
                # Analyze photo
                result = processor.analyze_photo(photo_path)
                
                # Add result to photo metadata
                photo['face_recognition'] = {
                    'has_faces': result['has_faces'],
                    'face_count': result['face_count'],
                    'has_known_faces': result['has_known_faces'],
                    'known_faces': result['known_faces']
                }
                
                # Update counters
                processed_count += 1
                if result['has_faces']:
                    face_found_count += 1
                if result['has_known_faces']:
                    known_face_count += 1
                
                pbar.update(1)
                
            except Exception as e:
                logger.error(f"Error processing {photo.get('filename')}: {e}")
                pbar.update(1)
                continue
    
    # Save updated descriptions.json
    try:
        # Create backup
        backup_path = Path(descriptions_file).with_suffix('.json.backup')
        with open(backup_path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"\n✓ Backup created: {backup_path}")
        
        # Save updated file
        with open(descriptions_file, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"✓ Updated descriptions saved to: {descriptions_file}")
        
    except Exception as e:
        logger.error(f"Failed to save updated descriptions: {e}")
        sys.exit(1)
    
    # Print summary
    logger.info("\n" + "=" * 70)
    logger.info("Processing Complete!")
    logger.info("=" * 70)
    logger.info(f"Photos processed: {processed_count}")
    logger.info(f"Photos with faces detected: {face_found_count}")
    logger.info(f"Photos with known faces (you): {known_face_count}")
    
    if known_face_count > 0:
        logger.info(f"\n✓ You can now search for 'me' to find photos of yourself!")


if __name__ == '__main__':
    main()
