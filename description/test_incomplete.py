#!/usr/bin/env python3
"""
Test script to check how many incomplete descriptions exist
"""

import json
import sys
import os

def is_description_incomplete(description):
    """Check if a description is incomplete"""
    if not description or not description.strip():
        return True
    
    description = description.strip()
    return not description.endswith(('.', '!', '?'))

def main():
    descriptions_file = "/Users/thortle/Desktop/media_sorter/sorting/descriptions.json"
    
    try:
        with open(descriptions_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading file: {e}")
        return
    
    total_photos = len(data.get('photos', []))
    incomplete_count = 0
    
    print(f"Checking {total_photos} photos for incomplete descriptions...")
    
    incomplete_examples = []
    
    for i, photo in enumerate(data['photos']):
        if 'description' in photo:
            if is_description_incomplete(photo['description']):
                incomplete_count += 1
                if len(incomplete_examples) < 5:  # Show first 5 examples
                    incomplete_examples.append({
                        'filename': photo.get('filename', 'unknown'),
                        'description': photo['description'][-100:] if len(photo['description']) > 100 else photo['description']
                    })
    
    print(f"\nResults:")
    print(f"Total photos: {total_photos}")
    print(f"Incomplete descriptions: {incomplete_count}")
    print(f"Percentage incomplete: {(incomplete_count/total_photos)*100:.2f}%")
    
    print(f"\nFirst {len(incomplete_examples)} examples of incomplete descriptions:")
    for i, example in enumerate(incomplete_examples, 1):
        print(f"\n{i}. {example['filename']}")
        print(f"   Description ends with: \"...{example['description']}\"")

if __name__ == "__main__":
    main()
