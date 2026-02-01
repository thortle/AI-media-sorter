#!/usr/bin/env python3
"""
Quick setup script for facial recognition module
Validates dependencies and reference dataset
"""

import sys
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    print("Checking dependencies...")
    
    missing = []
    
    try:
        import tensorflow
        print("  tensorflow installed")
    except ImportError:
        missing.append("tensorflow")
        print("  tensorflow not found")
    
    try:
        import deepface
        print("  deepface installed")
    except ImportError:
        missing.append("deepface")
        print("  deepface not found")
    
    try:
        from PIL import Image
        print("  pillow installed")
    except ImportError:
        missing.append("pillow")
        print("  pillow not found")
    
    try:
        import scipy
        print("  scipy installed")
    except ImportError:
        missing.append("scipy")
        print("  scipy not found")
    
    if missing:
        print(f"\nMissing dependencies: {', '.join(missing)}")
        print("\nInstall with:")
        print("   pip install deepface tf-keras tensorflow scipy")
        return False
    
    print("\nAll dependencies installed!")
    return True


def check_reference_dataset():
    """Check if reference dataset exists and has photos"""
    print("\nChecking reference dataset...")
    
    dataset_path = Path(__file__).parent.parent.parent / "data" / "face_recognition_dataset"
    
    if not dataset_path.exists():
        print(f"  Reference dataset directory not found: {dataset_path}")
        print("\nCreate with:")
        print(f"   mkdir -p {dataset_path}")
        print(f"   cp /path/to/your/photos/*.jpg {dataset_path}/")
        return False
    
    # Count image files
    image_extensions = {'.jpg', '.jpeg', '.png', '.heic', '.tiff'}
    image_files = [
        f for f in dataset_path.iterdir()
        if f.suffix.lower() in image_extensions and not f.name.startswith('.')
    ]
    
    if len(image_files) == 0:
        print(f"  No reference photos found in {dataset_path}")
        print("\nAdd reference photos:")
        print(f"   cp /path/to/your/photos/*.jpg {dataset_path}/")
        print("   Recommended: 20-50 clear photos of yourself")
        return False
    
    print(f"  Found {len(image_files)} reference photo(s)")
    
    if len(image_files) < 10:
        print("  Warning: Less than 10 reference photos")
        print("     Recommended: 20-50 photos for better accuracy")
    
    print("\nReference photos:")
    for i, photo in enumerate(sorted(image_files)[:10], 1):
        print(f"     {i}. {photo.name}")
    
    if len(image_files) > 10:
        print(f"     ... and {len(image_files) - 10} more")
    
    return True


def check_descriptions_file():
    """Check if descriptions.json exists"""
    print("\nChecking descriptions.json...")
    
    descriptions_path = Path(__file__).parent.parent.parent / "data" / "descriptions.json"
    
    if not descriptions_path.exists():
        print(f"  descriptions.json not found: {descriptions_path}")
        print("\nGenerate with:")
        print("   cd scripts/generate && python3 main.py '/path/to/photos'")
        print("   cd scripts/search && python3 json_converter.py")
        return False
    
    print(f"  descriptions.json found")
    
    # Try to load and check
    try:
        import json
        with open(descriptions_path) as f:
            data = json.load(f)
        
        photo_count = len(data.get('photos', []))
        print(f"  Contains {photo_count} photo(s)")
        
        if photo_count == 0:
            print("  Warning: No photos in descriptions.json")
            return False
        
    except Exception as e:
        print(f"  Warning: Could not validate file: {e}")
    
    return True


def main():
    """Main setup validation"""
    print("=" * 70)
    print("Facial Recognition Setup Validator")
    print("=" * 70)
    print()
    
    checks = [
        ("Dependencies", check_dependencies()),
        ("Reference Dataset", check_reference_dataset()),
        ("Descriptions File", check_descriptions_file())
    ]
    
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    
    all_passed = True
    for check_name, passed in checks:
        status = "PASS" if passed else "FAIL"
        print(f"{status} {check_name}")
        if not passed:
            all_passed = False
    
    print()
    
    if all_passed:
        print("All checks passed! You're ready to run facial recognition.")
        print("\nNext steps:")
        print("   cd scripts/facial_recognition")
        print("   python3 main.py --max-photos 100  # Test with 100 photos")
        print("   python3 main.py                   # Process all photos")
    else:
        print("Some checks failed. Please fix the issues above.")
        print("\nFor detailed setup instructions, see:")
        print("   docs/facial-recognition-guide.md")
    
    print()


if __name__ == "__main__":
    main()
