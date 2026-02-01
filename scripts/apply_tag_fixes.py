#!/usr/bin/env python3
"""
Apply tag-only fixes from page 1 manual review.
This modifies has_characters, has_dogs, has_cars boolean values only.
"""

import json
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent / "data" / "descriptions.json"

# Tag fixes parsed from manual-check.txt
# Format: filename -> {remove: [], add: []}
TAG_FIXES = {
    # Remove tags (redundant)
    "20200818_215408.jpg": {"remove": ["people", "cars"], "add": []},
    "2016-05-10-14-13-49-7146.jpg": {"remove": ["cars"], "add": []},
    "IMG_2580.HEIC": {"remove": ["people", "dogs", "cars"], "add": []},
    "IMG_7628.HEIC": {"remove": ["people"], "add": []},
    "IMG_0799.JPG": {"remove": ["cars"], "add": []},
    "IMG_3509.JPG": {"remove": ["cars"], "add": []},
    "IMG_4287.HEIC": {"remove": ["people"], "add": []},
    "IMG_8312.JPG": {"remove": ["cars"], "add": []},
    "IMG_5150.JPG": {"remove": ["cars"], "add": []},
    "IMG_3407.HEIC": {"remove": ["people"], "add": []},
    "IMG_4638.HEIC": {"remove": ["people"], "add": []},
    "IMG_9018.JPG": {"remove": ["cars"], "add": []},
    "IMG_2538.HEIC": {"remove": ["people"], "add": []},
    "IMG_5357.HEIC": {"remove": ["cars"], "add": []},
    "IMG_8565.HEIC": {"remove": ["people", "cars"], "add": []},
    "IMG_8836.HEIC": {"remove": ["people"], "add": []},
    "IMG_1744.HEIC": {"remove": ["people"], "add": []},
    "IMG_6081.HEIC": {"remove": ["people"], "add": []},
    "IMG_1251.HEIC": {"remove": ["cars"], "add": []},
    "IMG_4931.JPG": {"remove": ["cars"], "add": []},
    "IMG_7805.HEIC": {"remove": ["cars"], "add": []},
    "IMG_9548.HEIC": {"remove": ["people", "cars"], "add": []},
    "IMG_2304.HEIC": {"remove": ["cars"], "add": []},
    "IMG_7106.HEIC": {"remove": ["cars", "dogs"], "add": []},
    "IMG_3846.HEIC": {"remove": ["people"], "add": []},
    "20210128_165403.jpg": {"remove": ["people"], "add": []},
    "IMG_6652.HEIC": {"remove": ["people"], "add": []},
    "IMG_5341.HEIC": {"remove": ["people", "cars"], "add": []},
    "IMG_0513.HEIC": {"remove": ["cars"], "add": []},
    "2016212184558.jpg": {"remove": ["cars"], "add": []},
    "IMG_2191.HEIC": {"remove": ["people"], "add": []},
    "IMG_3433(1).HEIC": {"remove": ["cars"], "add": []},
    "IMG_1617.HEIC": {"remove": ["people"], "add": []},
    "IMG_4045.HEIC": {"remove": ["people"], "add": []},
    "IMG_1247.HEIC": {"remove": ["cars"], "add": []},
    "IMG_4104.JPG": {"remove": ["cars"], "add": []},
    "IMG_6351.HEIC": {"remove": ["people", "cars"], "add": []},
    "IMG_7431.JPG": {"remove": ["cars"], "add": []},
    "IMG_4229.HEIC": {"remove": ["people"], "add": []},
    "IMG_6644.HEIC": {"remove": ["people"], "add": []},
    "P6161629.JPG": {"remove": ["cars"], "add": []},
    "IMG_5316.HEIC": {"remove": ["people", "dogs"], "add": []},
    "IMG_2980.HEIC": {"remove": ["people"], "add": []},
    "IMG_0809.JPG": {"remove": ["cars"], "add": []},
    "IMG_0952.HEIC": {"remove": ["cars"], "add": []},
    "IMG_3554.HEIC": {"remove": ["people"], "add": []},
    "IMG_6306.HEIC": {"remove": ["people"], "add": []},
    "IMG_5480.HEIC": {"remove": ["cars"], "add": []},
    "IMG_2715.HEIC": {"remove": ["people"], "add": []},
    "IMG_2200.HEIC": {"remove": ["people"], "add": []},
    "received_557747194394022.jpeg": {"remove": ["cars"], "add": []},
    "IMG_2180(1).HEIC": {"remove": ["people"], "add": []},
    "IMG_3256.HEIC": {"remove": ["people"], "add": []},
    "IMG_0149.JPG": {"remove": ["cars"], "add": []},
    "IMG_4069.HEIC": {"remove": ["cars"], "add": []},
    "20200520_205152.jpg": {"remove": ["people", "dogs"], "add": []},
    "IMG_1531.JPG": {"remove": ["cars"], "add": []},
    "IMG_2017.HEIC": {"remove": ["people", "cars"], "add": []},
    "IMG_5697.HEIC": {"remove": ["people"], "add": []},
    "IMG_4461.JPG": {"remove": ["cars"], "add": []},
    "IMG_5947.HEIC": {"remove": ["cars"], "add": []},
    "IMG_7829.JPG": {"remove": ["cars"], "add": []},
    "IMG_0808.JPG": {"remove": ["cars"], "add": []},
    "IMG_1142.HEIC": {"remove": ["cars"], "add": []},
    "20210625_165904.jpg": {"remove": ["cars"], "add": []},
    "IMG_8699.HEIC": {"remove": ["people", "cars"], "add": []},
    "IMG_8071.JPG": {"remove": ["cars"], "add": []},
    "P6161628.JPG": {"remove": ["cars"], "add": []},
    "IMG_7612.HEIC": {"remove": ["people", "cars"], "add": []},
    "IMG_2410.HEIC": {"remove": ["people"], "add": []},
    "PXL_20210403_132605592.jpg": {"remove": ["dogs", "cars"], "add": []},
    "IMG_0138.HEIC": {"remove": ["people"], "add": []},
    "IMG_5013.HEIC": {"remove": ["cars"], "add": []},
    "IMG_9390.JPG": {"remove": ["cars"], "add": []},
    "IMG_5156.HEIC": {"remove": ["people"], "add": []},
    "P6030498.JPG": {"remove": ["cars"], "add": []},
    "DSCF3261.JPG": {"remove": ["cars"], "add": []},
    "IMG_3578.HEIC": {"remove": ["people"], "add": []},
    "20210625_164327.jpg": {"remove": ["cars"], "add": []},
    "IMG_4028.HEIC": {"remove": ["people"], "add": []},
    "IMG_6015.HEIC": {"remove": ["cars"], "add": []},
    "IMG_4478.HEIC": {"remove": ["people", "cars"], "add": []},
    "camphoto_1254324197(4).jpg": {"remove": ["people", "cars"], "add": []},
    "IMG_8111.JPG": {"remove": ["cars"], "add": []},
    "IMG_2414.JPG": {"remove": ["people"], "add": []},
    "IMG_2113.HEIC": {"remove": ["people"], "add": []},
    "IMG_4497.HEIC": {"remove": ["people"], "add": []},
    "IMG_2390.HEIC": {"remove": ["people"], "add": []},
    "IMG_7192.HEIC": {"remove": ["people", "dogs", "cars"], "add": []},
    "IMG_6296.HEIC": {"remove": ["people"], "add": []},
    "IMG_0384(1).HEIC": {"remove": ["cars"], "add": []},
    "IMG_3911.JPG": {"remove": ["people"], "add": []},
    "IMG_8772.HEIC": {"remove": ["people"], "add": []},
    "IMG_8688.JPG": {"remove": ["people", "cars"], "add": []},
    "IMG_5140.HEIC": {"remove": ["people"], "add": []},
    "IMG_1874.JPG": {"remove": ["cars"], "add": []},
    
    # Add tags (missing)
    "IMG_2818.JPG": {"remove": [], "add": ["people"]},
    "IMG_7960.JPG": {"remove": [], "add": ["people"]},
    "IMG_0047.HEIC": {"remove": [], "add": ["dogs"]},
    "20210627_153113.jpg": {"remove": [], "add": ["people"]},
    "IMG_5778.JPG": {"remove": [], "add": ["people"]},
    "IMG_4792.HEIC": {"remove": [], "add": ["people"]},
    "IMG_2168.HEIC": {"remove": [], "add": ["dogs"]},
    "IMG_7690.HEIC": {"remove": [], "add": ["people", "dogs"]},
    "IMG_1314.HEIC": {"remove": [], "add": ["people"]},
    "IMG_2884.HEIC": {"remove": [], "add": ["people"]},
    "IMG_1178.HEIC": {"remove": [], "add": ["people"]},
    "IMG_1894.HEIC": {"remove": [], "add": ["cars"]},
    "IMG_4100.HEIC": {"remove": [], "add": ["people"]},
    "IMG_7686.HEIC": {"remove": [], "add": ["people", "dogs"]},
    "20191215_114857_Original(1).jpg": {"remove": [], "add": ["people"]},
    "20200830_181209.jpg": {"remove": [], "add": ["people"]},
    "IMG_9677.HEIC": {"remove": [], "add": ["dogs"]},
    "2595A57B-4E01-446E-90C9-8279D38206ED.jpg": {"remove": [], "add": ["people"]},
    "Screenshot_2015-11-13-21-21-16.png": {"remove": [], "add": ["people"]},
    "IMG_5226.JPG": {"remove": [], "add": ["people"]},
    "F2C468E1-218A-40C5-86F9-BD9150DB503B.jpg": {"remove": [], "add": ["people"]},
    "IMG_8898.HEIC": {"remove": [], "add": ["dogs"]},
    "IMG_8461.HEIC": {"remove": [], "add": ["people"]},
    "IMG_1139.HEIC": {"remove": [], "add": ["people"]},
    "IMG_9509.HEIC": {"remove": [], "add": ["dogs"]},
    "IMG_1586.HEIC": {"remove": [], "add": ["people"]},
    "IMG_5896.HEIC": {"remove": [], "add": ["dogs"]},
    "IMG_5031.JPG": {"remove": [], "add": ["cars"]},
    "IMG_1791.HEIC": {"remove": [], "add": ["people"]},
    "IMG_0180.HEIC": {"remove": [], "add": ["people"]},
    "IMG_7645.HEIC": {"remove": [], "add": ["dogs"]},
    "IMG_7700.HEIC": {"remove": [], "add": ["people", "dogs"]},
    "IMG_2851.HEIC": {"remove": [], "add": ["dogs"]},
    "IMG_6668.HEIC": {"remove": [], "add": ["dogs"]},
    "IMG_1007.HEIC": {"remove": [], "add": ["people"]},
    "IMG_6687.HEIC": {"remove": [], "add": ["dogs"]},
    "IMG_9030.HEIC": {"remove": [], "add": ["people", "dogs"]},
    "IMG_8271.HEIC": {"remove": [], "add": ["dogs"]},
    "IMG_8334.HEIC": {"remove": [], "add": ["dogs"]},
    "IMG_1816.HEIC": {"remove": [], "add": ["people"]},
    "P6222024.JPG": {"remove": [], "add": ["people"]},
    "IMG_0354.HEIC": {"remove": [], "add": ["people"]},
    "IMG_9225.HEIC": {"remove": [], "add": ["dogs"]},
    "IMG_2406.HEIC": {"remove": [], "add": ["people"]},
    "20151223123607.jpg": {"remove": [], "add": ["people"]},
    "IMG_5286.HEIC": {"remove": [], "add": ["dogs"]},
    "IMG_8267.HEIC": {"remove": [], "add": ["dogs"]},
    "IMG_9026.HEIC": {"remove": [], "add": ["dogs"]},
    "IMG_9533.HEIC": {"remove": [], "add": ["people", "dogs"]},
    "IMG_7487.HEIC": {"remove": [], "add": ["dogs"]},
    "IMG_8322.HEIC": {"remove": [], "add": ["dogs"]},
    "IMG_7653.HEIC": {"remove": [], "add": ["dogs"]},
    "IMG_2902.HEIC": {"remove": [], "add": ["dogs"]},
}

# Map tag names to keyword fields
TAG_MAP = {
    "people": "has_characters",
    "dogs": "has_dogs", 
    "cars": "has_cars"
}

def load_data():
    with open(DATA_PATH, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_PATH, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    print("Loading descriptions.json...")
    data = load_data()
    photos = data['photos']
    
    # Build lookup dict
    photo_lookup = {p['filename']: p for p in photos}
    
    stats = {"found": 0, "not_found": 0, "tags_removed": 0, "tags_added": 0}
    not_found_files = []
    
    print(f"\nApplying {len(TAG_FIXES)} tag fixes...\n")
    
    for filename, fixes in TAG_FIXES.items():
        if filename not in photo_lookup:
            stats["not_found"] += 1
            not_found_files.append(filename)
            continue
        
        stats["found"] += 1
        photo = photo_lookup[filename]
        keywords = photo['keywords']
        
        # Remove tags
        for tag in fixes["remove"]:
            field = TAG_MAP[tag]
            if keywords.get(field, False):
                keywords[field] = False
                # Also clear the array if it exists
                array_field = "characters" if tag == "people" else tag
                if array_field in keywords:
                    keywords[array_field] = []
                stats["tags_removed"] += 1
        
        # Add tags
        for tag in fixes["add"]:
            field = TAG_MAP[tag]
            if not keywords.get(field, False):
                keywords[field] = True
                # Also set a default array entry
                if tag == "people":
                    keywords["characters"] = [{"type": "person", "count": 1}]
                elif tag == "dogs":
                    keywords["dogs"] = [{"type": "dog", "count": 1}]
                elif tag == "cars":
                    keywords["cars"] = [{"type": "car", "count": 1}]
                stats["tags_added"] += 1
    
    # Save
    print("Saving changes...")
    save_data(data)
    
    print("\n" + "="*50)
    print("TAG FIXES SUMMARY:")
    print("="*50)
    print(f"  Files found:     {stats['found']}")
    print(f"  Files not found: {stats['not_found']}")
    print(f"  Tags removed:    {stats['tags_removed']}")
    print(f"  Tags added:      {stats['tags_added']}")
    
    if not_found_files:
        print(f"\nFiles not found in descriptions.json:")
        for f in not_found_files:
            print(f"     - {f}")
    
    print("\nDone!")

if __name__ == "__main__":
    main()
