#!/usr/bin/env python3
"""
Complete Descriptions Script

This script finds incomplete descriptions in descriptions.json and regenerates them
using the vision model. Incomplete descriptions are those that don't end with
proper punctuation (., !, ?).
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add the parent directory to the path to import vision model
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.vision_model import MoondreamVisionModel
from utils.logger import setup_logger

# Setup logging
logger = setup_logger(log_file="complete_descriptions.log")

class DescriptionCompleter:
    """
    Handles finding and completing incomplete descriptions
    """
    
    def __init__(self, descriptions_json_path: str):
        self.descriptions_json_path = descriptions_json_path
        self.vision_model = None
        self.data = None
        
    def load_descriptions(self) -> bool:
        """
        Load the descriptions.json file
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(self.descriptions_json_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            logger.info(f"Loaded descriptions from {self.descriptions_json_path}")
            return True
        except FileNotFoundError:
            logger.error(f"Descriptions file not found: {self.descriptions_json_path}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON file: {e}")
            return False
        except Exception as e:
            logger.error(f"Error loading descriptions file: {e}")
            return False
    
    def save_descriptions(self) -> bool:
        """
        Save the updated descriptions back to the JSON file
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create backup of original file
            backup_path = f"{self.descriptions_json_path}.backup"
            if os.path.exists(self.descriptions_json_path):
                os.rename(self.descriptions_json_path, backup_path)
                logger.info(f"Created backup: {backup_path}")
            
            # Save updated data
            with open(self.descriptions_json_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved updated descriptions to {self.descriptions_json_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving descriptions file: {e}")
            return False
    
    def is_description_incomplete(self, description: str) -> bool:
        """
        Check if a description is incomplete
        
        Args:
            description: The description text to check
            
        Returns:
            bool: True if incomplete, False if complete
        """
        if not description or not description.strip():
            return True
        
        description = description.strip()
        
        # Check if description ends with proper punctuation
        return not description.endswith(('.', '!', '?'))
    
    def find_incomplete_descriptions(self) -> List[Tuple[int, Dict]]:
        """
        Find all photos with incomplete descriptions
        
        Returns:
            List of tuples containing (index, photo_data) for incomplete descriptions
        """
        incomplete = []
        
        if not self.data or 'photos' not in self.data:
            logger.error("No photos data found in descriptions file")
            return incomplete
        
        for i, photo in enumerate(self.data['photos']):
            if 'description' in photo:
                if self.is_description_incomplete(photo['description']):
                    incomplete.append((i, photo))
        
        logger.info(f"Found {len(incomplete)} incomplete descriptions")
        return incomplete
    
    def initialize_vision_model(self) -> bool:
        """
        Initialize the vision model
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("Initializing vision model...")
            self.vision_model = MoondreamVisionModel()
            logger.info("Vision model initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing vision model: {e}")
            return False
    
    def complete_description(self, photo_data: Dict) -> str:
        """
        Generate a new complete description for a photo
        
        Args:
            photo_data: Photo data dictionary containing file path info
            
        Returns:
            str: New complete description, or empty string if failed
        """
        try:
            # Try to get image path from full_path first, then construct it
            image_path = photo_data.get('full_path')
            
            if not image_path or not os.path.exists(image_path):
                logger.warning(f"Image not found at {image_path}, skipping {photo_data.get('filename', 'unknown')}")
                return ""
            
            logger.info(f"Regenerating description for {photo_data['filename']}")
            new_description = self.vision_model.analyze_image(image_path)
            
            if new_description and not self.is_description_incomplete(new_description):
                logger.info(f"Successfully generated complete description for {photo_data['filename']}")
                return new_description
            else:
                logger.warning(f"Generated description is still incomplete for {photo_data['filename']}")
                return new_description  # Return even if incomplete, it might be better than original
                
        except Exception as e:
            logger.error(f"Error generating description for {photo_data.get('filename', 'unknown')}: {e}")
            return ""
    
    def process_incomplete_descriptions(self) -> bool:
        """
        Process all incomplete descriptions and update them
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.load_descriptions():
            return False
        
        incomplete_descriptions = self.find_incomplete_descriptions()
        
        if not incomplete_descriptions:
            logger.info("No incomplete descriptions found!")
            return True
        
        if not self.initialize_vision_model():
            return False
        
        updated_count = 0
        total_count = len(incomplete_descriptions)
        
        logger.info(f"Starting to process {total_count} incomplete descriptions...")
        
        for i, (index, photo_data) in enumerate(incomplete_descriptions, 1):
            logger.info(f"Processing {i}/{total_count}: {photo_data.get('filename', 'unknown')}")
            
            try:
                new_description = self.complete_description(photo_data)
                
                if new_description:
                    # Update the description in the data
                    self.data['photos'][index]['description'] = new_description
                    
                    # Update metadata if it exists
                    if 'metadata' in self.data['photos'][index]:
                        self.data['photos'][index]['metadata']['description_length'] = len(new_description)
                        self.data['photos'][index]['metadata']['word_count'] = len(new_description.split())
                    
                    updated_count += 1
                    logger.info(f"Updated description for {photo_data['filename']}")
                else:
                    logger.warning(f"Failed to generate new description for {photo_data['filename']}")
                    
            except Exception as e:
                logger.error(f"Error processing {photo_data.get('filename', 'unknown')}: {e}")
                continue
        
        logger.info(f"Completed processing. Updated {updated_count}/{total_count} descriptions.")
        
        if updated_count > 0:
            return self.save_descriptions()
        else:
            logger.info("No descriptions were updated, skipping save.")
            return True


def main():
    """Main function"""
    # Path to descriptions.json file
    descriptions_file = "/Users/thortle/Desktop/media_sorter/sorting/descriptions.json"
    
    if not os.path.exists(descriptions_file):
        logger.error(f"Descriptions file not found: {descriptions_file}")
        return False
    
    completer = DescriptionCompleter(descriptions_file)
    
    try:
        success = completer.process_incomplete_descriptions()
        if success:
            logger.info("Description completion process finished successfully!")
        else:
            logger.error("Description completion process failed!")
        return success
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
