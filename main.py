#!/usr/bin/env python3
"""
Media Sorter - AI-powered photo/video organization tool
Uses Moondream2 for content analysis and natural language sorting
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
@click.argument('prompt', type=str)
@click.option('--target-dir', type=str, help='Target directory name (will be created in source_dir)')
@click.option('--dry-run', is_flag=True, help='Preview operations without copying files')
@click.option('--max-files', type=int, default=None, help='Limit number of files to process (for testing)')
@click.option('--selection-method', 
              type=click.Choice(['filesystem', 'random', 'newest', 'oldest', 'name_asc', 'name_desc']), 
              default='filesystem', 
              help='Method for selecting files to process')
@click.option('--random-seed', type=int, help='Random seed for reproducible random selection')
def main(source_dir, prompt, target_dir, dry_run, max_files, selection_method, random_seed):
    """
    Sort media files using AI-powered content analysis.
    
    Examples:
    python main.py /path/to/G-photos "sort all dog photos" --target-dir oliver
    python main.py /path/to/G-photos "find vacation photos" --dry-run
    """
    
    # Setup logging
    logger = setup_logger()
    
    logger.info(f"Starting media sorting with prompt: '{prompt}'")
    logger.info(f"Source directory: {source_dir}")
    logger.info(f"Selection method: {selection_method}")
    
    if max_files:
        logger.info(f"Processing limit: {max_files} files")
    
    if dry_run:
        logger.info("DRY RUN mode - no files will be copied")
    
    try:
        # Initialize components
        logger.info("Loading Moondream2 vision model...")
        vision_model = MoondreamVisionModel()
        
        logger.info("Initializing file manager...")
        file_manager = MediaFileManager(source_dir)
        
        # Discover media files with specified selection method
        logger.info("Scanning for media files...")
        media_files = file_manager.discover_media_files(
            max_files=max_files, 
            selection_method=selection_method,
            random_seed=random_seed
        )
        logger.info(f"Found {len(media_files)} media files to analyze")
        
        if selection_method == 'random' and random_seed:
            logger.info(f"Random seed: {random_seed} (use same seed for reproducible results)")
        
        if len(media_files) == 0:
            logger.warning("No media files found!")
            return
        
        # Analyze files
        logger.info("Starting content analysis...")
        matching_files = []
        
        for i, file_path in enumerate(media_files, 1):
            logger.info(f"Analyzing file {i}/{len(media_files)}: {Path(file_path).name}")
            
            try:
                # Use enhanced analysis for better accuracy
                result = vision_model.enhanced_matches_prompt(file_path, prompt)
                
                description = result['description']
                confidence = result['final_confidence']
                
                logger.info(f"  Description: {description}")
                logger.info(f"  Basic confidence: {result['basic_confidence']:.2f}")
                logger.info(f"  Enhanced confidence: {result['enhanced_confidence']:.2f}")
                
                # Trust the model's analysis completely - no artificial threshold
                if confidence > 0:
                    matching_files.append((file_path, confidence, description))
                    logger.info(f"  ✓ Match found (final confidence: {confidence:.2f})")
                    
                    # Show validation details
                    if result.get('validation_results'):
                        for keyword, validation in result['validation_results'].items():
                            logger.info(f"    {keyword}: detected={validation['detected']}, confidence={validation['confidence']:.2f}")
                else:
                    logger.info(f"  ✗ No match (final confidence: {confidence:.2f})")
                    
            except Exception as e:
                logger.error(f"  Error analyzing {file_path}: {e}")
                continue
        
        logger.info(f"Found {len(matching_files)} matching files")
        
        if len(matching_files) == 0:
            logger.info("No files matched the criteria")
            return
        
        # Show preview
        logger.info("\\nMatching files:")
        for file_path, confidence, description in matching_files:
            logger.info(f"  {Path(file_path).name} (confidence: {confidence:.2f})")
            logger.debug(f"    Description: {description}")
        
        if dry_run:
            logger.info("\\nDry run complete - no files were copied")
            return
        
        # Confirm operation
        if not click.confirm(f"\\nCopy {len(matching_files)} files to '{target_dir}'?"):
            logger.info("Operation cancelled")
            return
        
        # Copy files
        if target_dir:
            target_path = file_manager.create_target_directory(target_dir)
            logger.info(f"Copying files to {target_path}")
            
            success_count = 0
            for file_path, confidence, _ in matching_files:
                try:
                    file_manager.copy_file(file_path, target_path)
                    success_count += 1
                    logger.info(f"  ✓ Copied {Path(file_path).name}")
                except Exception as e:
                    logger.error(f"  ✗ Failed to copy {Path(file_path).name}: {e}")
            
            logger.info(f"\\nOperation complete: {success_count}/{len(matching_files)} files copied")
        else:
            logger.error("Target directory not specified")
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    main()
