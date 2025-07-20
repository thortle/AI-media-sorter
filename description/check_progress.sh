#!/bin/bash
cd ~/Desktop/media_sorter
source .venv/bin/activate

python -c "
import os
from datetime import datetime, timedelta

descriptions_file = 'complete_descriptions.txt'
total_images = 8330

if os.path.exists(descriptions_file):
    with open(descriptions_file, 'r') as f:
        processed = len(f.readlines())
    
    progress_pct = (processed / total_images) * 100
    remaining = total_images - processed
    
    # Estimate based on current rate
    remaining_hours = (remaining * 8) / 3600
    
    print(f'🤖 AI Media Description Generator - Progress Update')
    print(f'=' * 50)
    print(f'🔄 Progress: {processed:,}/{total_images:,} ({progress_pct:.1f}%)')
    print(f'⏱️  Estimated time remaining: {remaining_hours:.1f} hours')
    print(f'📊 Processing rate: ~8 seconds per image')
    print(f'🎯 Estimated completion: {(datetime.now() + timedelta(hours=remaining_hours)).strftime(\"%H:%M on %m/%d/%Y\")}')
    print(f'📁 Output file: complete_descriptions.txt')
    print(f'=' * 50)
    
    # Show last few processed files
    with open(descriptions_file, 'r') as f:
        lines = f.readlines()
        if len(lines) >= 3:
            print(f'📝 Latest processed files:')
            for line in lines[-3:]:
                filename = line.split(' - Description:')[0]
                print(f'   ✅ {filename}')
else:
    print('⏳ Descriptions file not found yet')
"
