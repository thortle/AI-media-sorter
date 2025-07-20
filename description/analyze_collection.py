#!/usr/bin/env python3
"""
File Analysis Utility - Analyze your G-photos collection
Shows file distribution and sampling methods
"""

import os
import sys
from pathlib import Path
from datetime import datetime

def analyze_files(base_path, sample_size=10):
    """Analyze file distribution and show samples"""
    
    supported_extensions = {'.jpg', '.jpeg', '.png', '.heic', '.heif', '.tiff', '.tif',
                           '.mp4', '.mov', '.avi', '.mkv', '.m4v', '.webm'}
    
    all_files = []
    
    print(f"🔍 Analyzing media files in: {base_path}")
    print("=" * 80)
    
    # Discover all files
    for root, dirs, files in os.walk(base_path):
        for file in files:
            # Skip hidden files
            if file.startswith('.') or file.startswith('_'):
                continue
                
            file_path = Path(root) / file
            if file_path.suffix.lower() in supported_extensions:
                try:
                    mod_time = file_path.stat().st_mtime
                    all_files.append((file, str(file_path), mod_time))
                except OSError:
                    continue
    
    print(f"📊 Total media files found: {len(all_files):,}")
    
    # Show file type distribution
    extensions = {}
    for file, _, _ in all_files:
        ext = file.lower().split('.')[-1]
        extensions[ext] = extensions.get(ext, 0) + 1
    
    print(f"\\n📁 File type distribution:")
    for ext, count in sorted(extensions.items()):
        percentage = (count / len(all_files)) * 100
        print(f"  .{ext}: {count:,} files ({percentage:.1f}%)")
    
    # Show different selection methods
    methods = {
        'filesystem': ('Natural filesystem order', lambda x: x),
        'newest': ('Newest files first', lambda x: sorted(x, key=lambda f: f[2], reverse=True)), 
        'oldest': ('Oldest files first', lambda x: sorted(x, key=lambda f: f[2])),
        'name_asc': ('Alphabetical A-Z', lambda x: sorted(x, key=lambda f: f[0].lower())),
        'name_desc': ('Alphabetical Z-A', lambda x: sorted(x, key=lambda f: f[0].lower(), reverse=True))
    }
    
    print(f"\\n🎯 Sample of first {sample_size} files with different selection methods:")
    print("=" * 80)
    
    for method, (description, sort_func) in methods.items():
        print(f"\\n{method.upper()} ({description}):")
        
        sorted_files = sort_func(all_files.copy())
        
        for i, (filename, _, mod_time) in enumerate(sorted_files[:sample_size]):
            date_str = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M')
            print(f"  {i+1:2d}. {filename} ({date_str})")
        
        if len(sorted_files) > sample_size:
            print(f"     ... and {len(sorted_files) - sample_size:,} more files")
    
    print(f"\\n🚀 Ready to sort! Example commands:")
    print(f"   # Random sample for testing:")
    print(f"   python3 main.py '{base_path}' 'dog photos' --selection-method random --max-files 50 --dry-run")
    print(f"   ")
    print(f"   # Most recent photos:")
    print(f"   python3 main.py '{base_path}' 'vacation photos' --selection-method newest --max-files 100")
    print(f"   ")
    print(f"   # Process all files alphabetically:")
    print(f"   python3 main.py '{base_path}' 'person photos' --selection-method name_asc --target-dir people")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = "/Volumes/T7_SSD/G-photos"
    
    if not os.path.exists(path):
        print(f"Error: Path does not exist: {path}")
        sys.exit(1)
    
    analyze_files(path)
