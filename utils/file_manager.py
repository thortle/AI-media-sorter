"""
File Manager for Media Sorting
Handles file discovery, copying, and directory management
"""

import os
import shutil
from pathlib import Path
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class MediaFileManager:
    """Manages media file operations for sorting"""
    
    # Supported media file extensions
    SUPPORTED_EXTENSIONS = {
        '.jpg', '.jpeg', '.png', '.heic', '.heif', '.tiff', '.tif',
        '.mp4', '.mov', '.avi', '.mkv', '.m4v', '.webm'
    }
    
    def __init__(self, source_directory: str):
        """
        Initialize file manager
        
        Args:
            source_directory: Path to directory containing media files
        """
        self.source_dir = Path(source_directory)
        if not self.source_dir.exists():
            raise FileNotFoundError(f"Source directory not found: {source_directory}")
        
        logger.info(f"Initialized file manager for: {self.source_dir}")
    
    def discover_media_files(self, max_files: Optional[int] = None, selection_method: str = 'filesystem', random_seed: Optional[int] = None) -> List[str]:
        """
        Discover media files with different selection methods
        
        Args:
            max_files: Maximum number of files to return (for testing)
            selection_method: 'filesystem', 'random', 'newest', 'oldest', 'name_asc', 'name_desc'
            random_seed: Random seed for reproducible random selection
            
        Returns:
            List of file paths
        """
        import random
        from datetime import datetime
        
        all_files = []
        
        logger.info(f"Scanning directory: {self.source_dir}")
        
        # Discover all media files
        for file_path in self.source_dir.rglob('*'):
            # Skip hidden files and system files
            if file_path.name.startswith('.') or file_path.name.startswith('_'):
                continue
            
            # Check if it's a supported media file
            if file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                try:
                    # Get file modification time for sorting
                    mod_time = file_path.stat().st_mtime
                    all_files.append((str(file_path), file_path.name, mod_time))
                except OSError:
                    # Skip files we can't access
                    continue
        
        # Apply selection method
        if selection_method == 'random':
            if random_seed is not None:
                random.seed(random_seed)
                logger.info(f"Using random seed: {random_seed}")
            random.shuffle(all_files)
        elif selection_method == 'newest':
            all_files.sort(key=lambda x: x[2], reverse=True)  # Sort by mod_time descending
        elif selection_method == 'oldest':
            all_files.sort(key=lambda x: x[2])  # Sort by mod_time ascending
        elif selection_method == 'name_asc':
            all_files.sort(key=lambda x: x[1].lower())  # Sort by filename A-Z
        elif selection_method == 'name_desc':
            all_files.sort(key=lambda x: x[1].lower(), reverse=True)  # Sort by filename Z-A
        # 'filesystem' uses natural discovery order (default)
        
        # Extract just the file paths
        media_files = [file_info[0] for file_info in all_files]
        
        if max_files:
            media_files = media_files[:max_files]
            logger.info(f"Reached max files limit: {max_files}")
        
        logger.info(f"Found {len(media_files)} media files using '{selection_method}' selection")
        return media_files
    
    def create_target_directory(self, target_name: str) -> Path:
        """
        Create target directory for sorted files
        
        Args:
            target_name: Name of the target directory
            
        Returns:
            Path to created directory
        """
        # Create target directory inside source directory
        target_path = self.source_dir / target_name
        
        # Handle existing directory
        if target_path.exists():
            counter = 1
            while (self.source_dir / f"{target_name}_{counter}").exists():
                counter += 1
            target_path = self.source_dir / f"{target_name}_{counter}"
            logger.warning(f"Target directory exists, using: {target_path.name}")
        
        target_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created target directory: {target_path}")
        
        return target_path
    
    def copy_file(self, source_file: str, target_directory: Path) -> bool:
        """
        Copy a file to the target directory
        
        Args:
            source_file: Path to source file
            target_directory: Target directory path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            source_path = Path(source_file)
            target_path = target_directory / source_path.name
            
            # Handle duplicate filenames
            if target_path.exists():
                stem = source_path.stem
                suffix = source_path.suffix
                counter = 1
                
                while target_path.exists():
                    target_path = target_directory / f"{stem}_{counter}{suffix}"
                    counter += 1
                
                logger.info(f"Renamed to avoid conflict: {target_path.name}")
            
            # Copy the file
            shutil.copy2(source_file, target_path)
            logger.debug(f"Copied: {source_path.name} -> {target_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to copy {source_file}: {e}")
            return False
    
    def get_file_info(self, file_path: str) -> dict:
        """
        Get information about a media file
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        path = Path(file_path)
        
        try:
            stat = path.stat()
            return {
                'name': path.name,
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'extension': path.suffix.lower(),
                'is_image': path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.tiff', '.tif'},
                'is_video': path.suffix.lower() in {'.mp4', '.mov', '.avi', '.mkv', '.m4v', '.webm'}
            }
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return {'name': path.name, 'error': str(e)}
    
    def cleanup_empty_dirs(self):
        """Remove empty directories in source"""
        for dirpath, dirnames, filenames in os.walk(self.source_dir, topdown=False):
            # Skip the root directory
            if dirpath == str(self.source_dir):
                continue
                
            try:
                if not dirnames and not filenames:
                    os.rmdir(dirpath)
                    logger.info(f"Removed empty directory: {dirpath}")
            except OSError:
                pass  # Directory not empty or permission error
