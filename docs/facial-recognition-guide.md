# Facial Recognition Setup Guide

This guide will help you set up facial recognition in your media sorter project to enable searching for photos of yourself using the keyword "me".

## Overview

The facial recognition module uses DeepFace (a deep learning facial recognition library) to:
1. Build a reference database from your photos
2. Detect faces in your photo collection
3. Match detected faces against your reference photos
4. Add metadata to descriptions.json for easy searching

## Prerequisites

### System Requirements
- **Apple Silicon Mac**: M series chip (for MPS GPU acceleration)
- **Python**: 3.8 or higher
- **Storage**: ~2-3GB for DeepFace models
- **Memory**: 8GB+ RAM recommended

### Software Dependencies
```bash
# Install facial recognition dependencies
pip install deepface tf-keras tensorflow scipy
```

## Step 1: Prepare Reference Dataset

The quality of your reference dataset directly impacts recognition accuracy.

### Create Reference Directory
```bash
mkdir -p data/face_recognition_dataset
```

### Select Reference Photos

**Quantity**: 20-50 photos of yourself

**Quality Guidelines:**
-  Clear, well-lit face photos
-  Various angles (front, side, 3/4 view)
-  Different expressions (smiling, neutral, laughing)
-  Different lighting conditions (indoor, outdoor, natural, artificial)
-  Different time periods (if appearance changed)
-  Different hairstyles/facial hair (if applicable)
-  Various backgrounds
-  Avoid blurry or low-resolution images
-  Avoid sunglasses or face coverings
-  Avoid extreme angles or partial face coverage

**Example reference set:**
- 10 photos: Front-facing, various lighting
- 5 photos: Side profile (left and right)
- 5 photos: 3/4 view angles
- 10 photos: Different expressions and settings

### Add Photos to Dataset
```bash
# Copy photos to reference dataset
cp /path/to/your/reference/photos/*.jpg data/face_recognition_dataset/

# Check reference dataset
ls data/face_recognition_dataset/
```

**Note:** The directory already contains sample reference photos. You can add your own photos or replace them entirely.

## Step 2: Run Facial Recognition Processor

### Basic Usage
```bash
cd scripts/facial_recognition
python3 main.py
```

This will:
1. Load reference photos from `data/face_recognition_dataset/`
2. Build face embeddings for reference faces
3. Process all photos in `descriptions.json`
4. Detect faces and match against reference
5. Update `descriptions.json` with face recognition metadata
6. Create a backup before saving changes

### Test Mode
To test on a limited number of photos first:
```bash
python3 main.py --max-photos 100
```

### Configuration Options

**Model Selection** (--model):
- `Facenet512` (default, recommended): Best balance of speed and accuracy
- `Facenet`: Faster but less accurate
- `VGG-Face`: Good accuracy, slower
- `ArcFace`: High accuracy, slower
- `Dlib`: Fast, moderate accuracy
- `SFace`: Fast, good for Asian faces

```bash
python3 main.py --model Facenet512
```

**Detector Backend** (--detector):
- `retinaface` (default, recommended): Best accuracy
- `mtcnn`: Good accuracy, faster
- `opencv`: Fast, lower accuracy
- `ssd`: Fast, moderate accuracy
- `dlib`: Moderate speed and accuracy

```bash
python3 main.py --detector retinaface
```

**Match Threshold** (--threshold):
- Lower = stricter matching (fewer false positives)
- Higher = looser matching (more false positives)
- Default: 0.4 (recommended)
- Range: 0.0 - 1.0

```bash
# Stricter matching
python3 main.py --threshold 0.35

# Looser matching
python3 main.py --threshold 0.45
```

**Force Reprocessing** (--force):
Reprocess all photos, even if they already have face recognition data:
```bash
python3 main.py --force
```

### Advanced Usage
```bash
# Custom configuration
python3 main.py \
  --model Facenet512 \
  --detector retinaface \
  --threshold 0.38 \
  --max-photos 500

# Use different reference dataset
python3 main.py \
  --reference-dataset /path/to/other/dataset

# Process with custom descriptions file
python3 main.py \
  --descriptions-file /path/to/descriptions.json
```

## Step 3: Search for Yourself

Once facial recognition processing is complete, you can search for photos of yourself:

```bash
cd scripts/search
python3 search_photos.py
```

In the search prompt, type:
```
Search: me
```

This will return all photos where your face was detected and matched against the reference dataset.

### View Statistics
```
Search: stats
```

This shows:
- Total photos in collection
- Photos with face recognition data
- Photos with detected faces
- Photos with known faces (you)

## Understanding Results

### Face Recognition Metadata

Each photo with face recognition data will have a `face_recognition` field:

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

**Fields:**
- `has_faces`: Whether any faces were detected
- `face_count`: Total number of faces detected
- `has_known_faces`: Whether any faces matched your reference
- `known_faces`: Array of matched faces with confidence and reference info

**Confidence Score:**
- 0.90-1.00: Very high confidence
- 0.80-0.89: High confidence
- 0.70-0.79: Moderate confidence
- Below 0.70: May need verification

**Distance:**
- Cosine distance between face embeddings
- Lower is better (more similar)
- Threshold determines what counts as a match

## Performance

### Processing Speed
On Apple Silicon (M1/M2/M3):
- **Reference Database Building**: ~2-5 seconds per photo
- **Face Detection**: ~1-2 seconds per photo
- **Face Matching**: ~0.1 seconds per face
- **Total**: ~2-3 seconds per photo average

### MPS (Metal Performance Shaders) Acceleration
The facial recognition processor automatically uses Apple Silicon's GPU:
- TensorFlow detects MPS availability
- Models run on GPU automatically
- ~2-3x faster than CPU-only processing

## Troubleshooting

### No Faces Detected in Reference Dataset
```
ValueError: No faces detected in reference dataset
```

**Solutions:**
- Ensure reference photos have clear, visible faces
- Try different photos with better lighting
- Verify photos aren't corrupted
- Check file formats are supported (JPG, PNG, HEIC)

### Low Match Confidence

**Solutions:**
- Add more diverse reference photos
- Lower the threshold: `--threshold 0.45`
- Try different model: `--model ArcFace`
- Ensure reference photos cover various angles/lighting

### Too Many False Positives
Photos without you being marked as matches.

**Solutions:**
- Increase threshold: `--threshold 0.35`
- Use stricter model: `--model Facenet512`
- Improve reference dataset quality
- Remove poor quality reference photos

### Memory Errors
```
ResourceExhaustedError: OOM when allocating tensor
```

**Solutions:**
- Process in smaller batches: `--max-photos 1000`
- Close other applications
- Restart Python session between batches
- Ensure at least 8GB RAM available

### Slow Processing
Processing taking longer than expected.

**Solutions:**
- Verify MPS acceleration is working (check logs)
- Use faster model: `--model Facenet`
- Use faster detector: `--detector opencv`
- Close resource-intensive applications

### Import Errors
```
ImportError: cannot import name 'DeepFace'
```

**Solutions:**
- Install dependencies: `pip install deepface tf-keras tensorflow scipy`
- Verify installation: `python -c "from deepface import DeepFace; print('OK')"`
- Try reinstalling: `pip uninstall deepface tf-keras tensorflow && pip install deepface tf-keras tensorflow`

## Advanced Topics

### Multiple People
To recognize multiple people, you can:
1. Create separate reference datasets
2. Run processor multiple times with different datasets
3. Extend code to handle multiple reference datasets

### Batch Processing
Process photos in chunks to manage memory:

```bash
# Process first 1000 photos
python3 main.py --max-photos 1000

# Continue with next batch (use --force to reprocess)
python3 main.py --max-photos 2000 --force
```

### Backup and Recovery
The processor creates automatic backups:
- Backup file: `descriptions.json.backup`
- Created before any changes
- Restore: `mv descriptions.json.backup descriptions.json`

## Architecture

### Components

**face_processor.py**:
- FaceRecognitionProcessor class
- DeepFace integration
- MPS acceleration configuration
- Face embedding extraction
- Face matching logic

**main.py**:
- CLI interface with Click
- Progress tracking with tqdm
- Batch processing
- JSON update logic

### Data Flow
```
Reference Photos → Face Embeddings → Reference Database
                                    ↓
    Photo Collection → Face Detection → Face Matching → Metadata Update
                                                       ↓
                                              descriptions.json
```

### Models Used
- **Face Detection**: RetinaFace (default)
- **Face Recognition**: Facenet512 (default)
- **Distance Metric**: Cosine distance
- **Framework**: TensorFlow with MPS backend

## Integration with Existing Workflow

The facial recognition module integrates seamlessly:

```bash
# 1. Generate descriptions (existing)
cd scripts/generate && python3 main.py "/path/to/photos"

# 2. Convert to JSON (existing)
cd scripts/search && python3 json_converter.py

# 3. Add keywords (existing, optional)
cd scripts/search && python3 process_keywords.py

# 4. Add facial recognition (NEW, optional)
cd scripts/facial_recognition && python3 main.py

# 5. Search (existing, now with "me" support)
cd scripts/search && python3 search_photos.py
```

The module only adds data to descriptions.json - it never modifies existing descriptions or keywords.

## FAQ

**Q: Do I need to reprocess photos after updating reference dataset?**
A: Yes, use `--force` to reprocess all photos with new references.

**Q: Can I search for multiple people?**
A: Currently "me" searches for one person. Extending the code for multiple people.

**Q: Will this work on Intel Macs?**
A: Yes, but without MPS acceleration (CPU-only, slower).

**Q: Can I run this on Linux/Windows?**
A: Yes, but MPS acceleration is Mac-only. Use CUDA (NVIDIA) or CPU.

**Q: How accurate is it?**
A: With good reference photos: 90-95% accuracy typical.

**Q: Does it work with old photos?**
A: Yes, but accuracy may be lower if appearance changed significantly.

**Q: Can I exclude certain photos from processing?**
A: Currently no built-in support.

**Q: Is my data private?**
A: Yes, everything runs locally. No data sent to external servers.

## Resources

- [DeepFace Documentation](https://github.com/serengil/deepface)
- [TensorFlow Metal Plugin](https://developer.apple.com/metal/tensorflow-plugin/)
- [Face Recognition Models](https://github.com/serengil/deepface/tree/master/deepface/models)

## Support

For issues or questions:
1. Check this guide's troubleshooting section
2. Review logs for specific errors
3. Try adjusting parameters (threshold, model, detector)
4. Ensure reference dataset quality is high

---

**Next Steps:**
- Set up your reference dataset
- Run initial test with `--max-photos 100`
- Adjust threshold based on results
- Process full collection
- Search for "me" and enjoy!
