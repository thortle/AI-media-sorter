"""
Logging utilities for media sorter
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

def setup_logger(log_level=logging.INFO, log_file=None):
    """
    Set up logging configuration
    
    Args:
        log_level: Logging level (default: INFO)
        log_file: Optional log file path
        
    Returns:
        Configured logger
    """
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Create main logger
    logger = logging.getLogger('media_sorter')
    
    return logger

def log_operation_summary(operation_type, files_processed, files_successful, duration):
    """
    Log a summary of completed operation
    
    Args:
        operation_type: Type of operation (e.g., "sorting", "analysis")
        files_processed: Number of files processed
        files_successful: Number of successful operations
        duration: Operation duration in seconds
    """
    logger = logging.getLogger('media_sorter')
    
    logger.info(f"\\n=== Operation Summary ===")
    logger.info(f"Operation: {operation_type}")
    logger.info(f"Files processed: {files_processed}")
    logger.info(f"Successful: {files_successful}")
    logger.info(f"Failed: {files_processed - files_successful}")
    logger.info(f"Duration: {duration:.2f} seconds")
    logger.info(f"Average time per file: {duration/files_processed:.2f}s")
    logger.info(f"========================\\n")
