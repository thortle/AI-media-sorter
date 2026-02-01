#!/usr/bin/env python3
"""
JSON Converter - Convert descriptions.txt to structured JSON format
Transforms the text-based descriptions file into a searchable JSON database
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Any

class DescriptionConverter:
    """
    Converts text-based descriptions to structured JSON format
    """
    
    def __init__(self, source_dir: str = "/Volumes/T7_SSD/G-photos"):
        self.source_dir = Path(source_dir)
        
    def parse_descriptions_file(self, descriptions_file: str) -> List[Dict[str, Any]]:
        """
        Parse the descriptions.txt file into structured data
        
        Args:
            descriptions_file: Path to the descriptions text file
            
        Returns:
            List of dictionaries containing structured photo data
        """
        descriptions = []
        
        try:
            with open(descriptions_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Regex pattern to match filename followed by description until next filename
            # Matches: FILENAME - Description: [multi-paragraph description]
            # Until next filename pattern (something.extension)
            pattern = r'([^/\n]+?\.[a-zA-Z]{2,5})\s*-\s*Description:\s*(.*?)(?=\n[^/\n]+?\.[a-zA-Z]{2,5}\s*-\s*Description:|$)'
            
            matches = re.findall(pattern, content, re.DOTALL)
            
            for i, (filename, description) in enumerate(matches, 1):
                filename = filename.strip()
                description = description.strip()
                
                if filename and description:
                    # Create structured entry
                    entry = self._create_photo_entry(filename, description, i)
                    descriptions.append(entry)
                else:
                    print(f"Warning: Empty filename or description in entry {i}")
                        
        except Exception as e:
            print(f"Error reading descriptions file: {e}")
            return []
            
        return descriptions
    
    def _create_photo_entry(self, filename: str, description: str, line_num: int) -> Dict[str, Any]:
        """
        Create a structured photo entry with metadata
        
        Args:
            filename: Name of the photo file
            description: AI-generated description
            line_num: Line number in source file
            
        Returns:
            Structured dictionary with photo information
        """
        # Extract file extension and create potential full path
        file_path = self.source_dir / filename
        
        # Extract keywords from description for search optimization
        keywords = self._extract_keywords(description)
        
        return {
            "filename": filename,
            "description": description,
            "full_path": str(file_path),
            "keywords": keywords,
            "metadata": {
                "line_number": line_num,
                "file_extension": Path(filename).suffix.lower(),
                "description_length": len(description),
                "word_count": len(description.split())
            }
        }
    
    def _extract_keywords(self, description: str) -> List[str]:
        """
        Extract searchable keywords from description
        
        Args:
            description: The image description text
            
        Returns:
            List of relevant keywords for searching
        """
        # Convert to lowercase for consistent searching
        desc_lower = description.lower()
        
        # Common objects, people, and scene elements
        keywords = []
        
        # People-related keywords
        people_terms = ['man', 'woman', 'person', 'people', 'child', 'baby', 'couple', 'group', 'individual']
        for term in people_terms:
            if term in desc_lower:
                keywords.append(term)
        
        # Common objects and elements
        object_terms = ['dog', 'cat', 'animal', 'car', 'building', 'tree', 'mountain', 'water', 'snow', 
                       'beach', 'forest', 'city', 'house', 'bridge', 'flower', 'food', 'table']
        for term in object_terms:
            if term in desc_lower:
                keywords.append(term)
        
        # Weather and environment
        environment_terms = ['sunny', 'cloudy', 'sky', 'outdoor', 'indoor', 'landscape', 'portrait']
        for term in environment_terms:
            if term in desc_lower:
                keywords.append(term)
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(keywords))
    
    def convert_to_json(self, descriptions_file: str, output_file: str = "descriptions.json") -> bool:
        """
        Convert descriptions text file to JSON format
        
        Args:
            descriptions_file: Input text file path
            output_file: Output JSON file path
            
        Returns:
            True if successful, False otherwise
        """
        print(f"Converting {descriptions_file} to {output_file}...")
        
        # Parse the descriptions file
        descriptions = self.parse_descriptions_file(descriptions_file)
        
        if not descriptions:
            print("No descriptions found to convert!")
            return False
        
        # Create the JSON structure
        json_data = {
            "metadata": {
                "total_photos": len(descriptions),
                "source_file": descriptions_file,
                "source_directory": str(self.source_dir),
                "conversion_info": "Generated by AI Media Description Generator"
            },
            "photos": descriptions
        }
        
        # Write to JSON file
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            print(f"Successfully converted {len(descriptions)} descriptions to {output_file}")
            print(f"Total photos: {len(descriptions)}")
            
            # Show some statistics
            self._show_conversion_stats(descriptions)
            
            return True
            
        except Exception as e:
            print(f"Error writing JSON file: {e}")
            return False
    
    def _show_conversion_stats(self, descriptions: List[Dict[str, Any]]) -> None:
        """Show statistics about the conversion"""
        if not descriptions:
            return
            
        # File type statistics
        extensions = {}
        total_keywords = 0
        
        for desc in descriptions:
            ext = desc['metadata']['file_extension']
            extensions[ext] = extensions.get(ext, 0) + 1
            total_keywords += len(desc['keywords'])
        
        print(f"\nConversion Statistics:")
        print(f"   File types: {dict(sorted(extensions.items()))}")
        print(f"   Average keywords per photo: {total_keywords / len(descriptions):.1f}")
        print(f"   Average description length: {sum(d['metadata']['description_length'] for d in descriptions) / len(descriptions):.0f} chars")

def main():
    """Main function for command-line usage"""
    # If no arguments provided, use default values for easy execution
    if len(sys.argv) < 2:
        print("No arguments provided - using default settings")
        print("Converting descriptions file to ../../data/descriptions.json...")
        # Look for descriptions file in common locations
        possible_paths = [
            "../../data/complete_descriptions.txt",
            "../generate/complete_descriptions.txt"
        ]
        descriptions_file = None
        for path in possible_paths:
            if Path(path).exists():
                descriptions_file = path
                break
        
        if not descriptions_file:
            print("Error: Could not find descriptions file!")
            print("Please provide path: python3 json_converter.py <descriptions_file>")
            sys.exit(1)
            
        output_file = "../../data/descriptions.json"
    else:
        descriptions_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else "../../data/descriptions.json"
    
    # Check if input file exists
    if not Path(descriptions_file).exists():
        print(f"Error: Input file '{descriptions_file}' not found!")
        print("\nUsage: python3 json_converter.py <descriptions_file> [output_file]")
        print("Example: python3 json_converter.py /path/to/descriptions.txt ../../data/descriptions.json")
        sys.exit(1)
    
    # Initialize converter
    converter = DescriptionConverter()
    
    # Convert to JSON
    success = converter.convert_to_json(descriptions_file, output_file)
    
    if success:
        print(f"\nJSON conversion complete! You can now use {output_file} for searching.")
    else:
        print("Conversion failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
