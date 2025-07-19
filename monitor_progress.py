#!/usr/bin/env python3
"""
Progress Monitor for AI Media Description Generator
Shows current progress and estimated completion time
"""

import os
import time
from datetime import datetime, timedelta

def monitor_progress():
    descriptions_file = "complete_descriptions.txt"
    total_images = 8330  # As reported by the scanner
    
    print("🤖 AI Media Description Generator - Progress Monitor")
    print("=" * 60)
    print(f"📁 Total images to process: {total_images:,}")
    print("⏱️  Average processing time: ~8 seconds per image")
    print("🎯 Estimated total time: ~18.5 hours")
    print("=" * 60)
    
    start_time = datetime.now()
    
    while True:
        try:
            if os.path.exists(descriptions_file):
                with open(descriptions_file, 'r') as f:
                    lines = f.readlines()
                    processed = len(lines)
                
                if processed > 0:
                    elapsed = datetime.now() - start_time
                    progress_pct = (processed / total_images) * 100
                    
                    if processed > 1:
                        avg_time_per_image = elapsed.total_seconds() / processed
                        remaining_images = total_images - processed
                        eta_seconds = remaining_images * avg_time_per_image
                        eta = datetime.now() + timedelta(seconds=eta_seconds)
                    else:
                        eta = "Calculating..."
                    
                    print(f"\r🔄 Progress: {processed:,}/{total_images:,} ({progress_pct:.1f}%) | "
                          f"⏰ ETA: {eta if isinstance(eta, str) else eta.strftime('%H:%M %m/%d')} | "
                          f"🕐 Elapsed: {str(elapsed).split('.')[0]}", end="", flush=True)
                else:
                    print(f"\r📝 File created, waiting for first description...", end="", flush=True)
            else:
                print(f"\r⏳ Waiting for descriptions file to be created...", end="", flush=True)
            
            time.sleep(30)  # Update every 30 seconds
            
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped by user")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_progress()
