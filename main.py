#!/usr/bin/env python3
"""
Media Description Generator - AI-powered photo description tool
Uses Moondream2 for detailed image content analysis and description generation
"""

import click
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from models.vision_model import MoondreamVisionModel
from utils.file_manager import MediaFileManager
from utils.logger import setup_logger

@click.command()
@click.argument('source_dir', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--max-files', type=int, default=None, help='Limit number of files to process (for testing)')
@click.option('--selection-method', 
              type=click.Choice(['filesystem', 'random', 'newest', 'oldest', 'name_asc', 'name_desc']), 
              default='filesystem', 
              help='Method for selecting files to process')
@click.option('--random-seed', type=int, help='Random seed for reproducible random selection')
@click.option('--descriptions-file', type=str, default='descriptions.txt', help='File to save descriptions to')
def main(source_dir, max_files, selection_method, random_seed, descriptions_file):
    """
    Generate AI-powered descriptions for all images in a directory.
    
    Examples:
    python main.py /path/to/G-photos
    python main.py /path/to/G-photos --max-files 100 --descriptions-file my_descriptions.txt
    python main.py /path/to/G-photos --selection-method random --random-seed 12345
    """
    
    # Setup logging
    logger = setup_logger()
    
    logger.info(f"Starting description generation for images")
    logger.info(f"Descriptions will be saved to: {descriptions_file}")
    logger.info(f"Source directory: {source_dir}")
    logger.info(f"Selection method: {selection_method}")
    
    if max_files:
        logger.info(f"Processing limit: {max_files} files")
    
    try:
        # Initialize components
        logger.info("Loading Moondream2 vision model...")
        vision_model = MoondreamVisionModel()
        
        logger.info("Initializing file manager...")
        file_manager = MediaFileManager(source_dir)
        
        # Discover media files with specified selection method (images only)
        logger.info("Scanning for image files...")
        media_files = file_manager.discover_media_files(
            max_files=max_files, 
            selection_method=selection_method,
            random_seed=random_seed,
            images_only=True  # Always process only images
        )
        logger.info(f"Found {len(media_files)} image files to analyze")
        
        if selection_method == 'random' and random_seed:
            logger.info(f"Random seed: {random_seed} (use same seed for reproducible results)")
        
        if len(media_files) == 0:
            logger.warning("No image files found!")
            return
        
        # Create/clear the descriptions file
        descriptions_path = Path(descriptions_file)
        if descriptions_path.exists():
            logger.info(f"Appending to existing descriptions file: {descriptions_file}")
        else:
            logger.info(f"Creating new descriptions file: {descriptions_file}")
            # Create empty file
            descriptions_path.touch()
        
        # Generate descriptions
        logger.info("Starting description generation...")
        
        for i, file_path in enumerate(media_files, 1):
            logger.info(f"Analyzing file {i}/{len(media_files)}: {Path(file_path).name}")
            
            try:
                # Generate description only
                description = vision_model.analyze_image(file_path)
                
                # Write to descriptions file
                file_manager.write_description(descriptions_file, Path(file_path).name, description)
                logger.info(f"  Description: {description}")
                
            except Exception as e:
                logger.error(f"  Error analyzing {file_path}: {e}")
                continue
        
        # Completion message
        logger.info(f"\nDescription generation complete!")
        logger.info(f"Descriptions saved to: {descriptions_file}")
        logger.info(f"Total files processed: {len(media_files)}")
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    main()
