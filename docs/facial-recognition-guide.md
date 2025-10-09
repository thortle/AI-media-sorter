# Facial Recognition Setup Guide

Enable searching for photos of yourself using the query **"me"** by setting up facial recognition with DeepFace.

## Quick Start

```bash
# 1. Install dependencies
pip install deepface tf-keras tensorflow scipy

# 2. Create reference dataset
mkdir -p data/face_recognition_dataset
cp /path/to/your/photos/*.jpg data/face_recognition_dataset/

# 3. Run processor
cd scripts/facial_recognition && python3 main.py --max-photos 100  # Test first
cd scripts/facial_recognition && python3 main.py                   # Full processing

# 4. Search for yourself
cd scripts/search && python3 search_photos.py
Search: me
```

## Prerequisites

- **System:** Apple Silicon Mac (M-series chip for MPS GPU acceleration)
- **Python:** 3.8+
- **Storage:** ~2-3GB for DeepFace models
- **Memory:** 8GB+ RAM recommended

## Reference Dataset Setup

**Quality > Quantity:** 20-50 clear photos of yourself

| Category | Examples |
|----------|----------|
| **Angles** | Front, side, 3/4 view |
| **Expressions** | Smiling, neutral, laughing |
| **Lighting** | Indoor, outdoor, natural, artificial |
| **Time Periods** | Different hairstyles, facial hair variations |

**Avoid:** Blurry images, sunglasses, face coverings, extreme angles

```bash
# Add photos to dataset
cp /path/to/your/reference/photos/*.jpg data/face_recognition_dataset/

# Verify setup before processing
cd scripts/facial_recognition && python3 setup_check.py
```

## Configuration Options

| Option | Default | Alternatives | Use Case |
|--------|---------|--------------|----------|
| `--model` | Facenet512 | Facenet, VGG-Face, ArcFace, Dlib | Balance speed vs accuracy |
| `--detector` | retinaface | mtcnn, opencv, ssd | Balance speed vs accuracy |
| `--threshold` | 0.4 | 0.3-0.5 | Lower = stricter, Higher = looser |
| `--max-photos` | All | Any number | Test mode or batch processing |
| `--force` | False | True | Reprocess photos with updated references |

**Examples:**
```bash
# Test with custom settings
python3 main.py --model Facenet512 --detector retinaface --threshold 0.38 --max-photos 500

# Stricter matching (fewer false positives)
python3 main.py --threshold 0.35

# Reprocess all with new references
python3 main.py --force
```

## Understanding Results

### Metadata Structure
```json
{
  "face_recognition": {
    "has_faces": true,
    "face_count": 2,
    "has_known_faces": true,
    "known_faces": [
      {
        "match_confidence": 0.92,
        "reference_image": "IMG_1052.JPG",
        "distance": 0.16
      }
    ]
  }
}
```

### Confidence Scores
- **0.90-1.00:** Very high confidence 
- **0.80-0.89:** High confidence 
- **0.70-0.79:** Moderate confidence 
- **< 0.70:** May need verification 

## Performance

| Task | Speed (Apple Silicon) |
|------|----------------------|
| Reference Building | ~2-5 sec/photo |
| Face Detection | ~1-2 sec/photo |
| Face Matching | ~0.1 sec/face |
| **Average** | **~2-3 sec/photo** |

**MPS Acceleration:** TensorFlow automatically uses Apple Silicon GPU (~2-3x faster than CPU)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **No faces detected in references** | Use clear photos with visible faces, check formats (JPG/PNG/HEIC) |
| **Low match confidence** | Add more diverse reference photos, lower threshold (`--threshold 0.45`) |
| **Too many false positives** | Increase threshold (`--threshold 0.35`), improve reference quality |
| **Memory errors** | Process in batches (`--max-photos 1000`), close other apps |
| **Slow processing** | Use faster model (`--model Facenet`) or detector (`--detector opencv`) |
| **Import errors** | `pip install deepface tf-keras tensorflow scipy` |

## Integration Workflow

```bash
# 1. Generate descriptions
cd scripts/generate && python3 main.py "/path/to/photos"

# 2. Convert to JSON
cd scripts/search && python3 json_converter.py

# 3. (Optional) Add keywords
cd scripts/search && python3 process_keywords.py

# 4. (Optional) Add facial recognition
cd scripts/facial_recognition && python3 main.py

# 5. Search with "me" support
cd scripts/search && python3 search_photos.py
Search: me
```

**Note:** Facial recognition only adds metadata - never modifies existing descriptions or keywords. Automatic backup created before changes.

## FAQ

| Question | Answer |
|----------|--------|
| Reprocess after updating references? | Yes, use `--force` |
| Works on Intel Macs? | Yes, but CPU-only (slower) |
| Works on Linux/Windows? | Yes, but no MPS acceleration |
| Typical accuracy? | 90-95% with good reference photos |
| Data privacy? | Fully local, no external servers |
| Multiple people support? | Currently single person ("me" query only) |

## Resources

- [DeepFace Documentation](https://github.com/serengil/deepface)
- [TensorFlow Metal Plugin](https://developer.apple.com/metal/tensorflow-plugin/)
- [Face Recognition Models](https://github.com/serengil/deepface/tree/master/deepface/models)
