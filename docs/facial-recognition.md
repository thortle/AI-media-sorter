# Facial Recognition Setup

Search for photos of yourself using the query **"me"**.

## Quick Start

```bash
# 1. Install dependencies
pip install deepface tf-keras tensorflow scipy

# 2. Create reference dataset (20-50 clear photos of yourself)
mkdir -p data/face_recognition_dataset
cp /path/to/your/photos/*.jpg data/face_recognition_dataset/

# 3. Run processor
cd scripts/facial_recognition
python3 main.py --max-photos 100  # Test first
python3 main.py                   # Full processing

# 4. Search
# Via web UI or API: search for "me"
```

## Reference Dataset Tips

- **Quality > Quantity**: 20-50 clear photos
- Include different angles, expressions, lighting
- Avoid blurry images, sunglasses, face coverings

## How It Works

1. DeepFace extracts face embeddings from your reference photos
2. Each photo in your library is scanned for faces
3. Faces are compared against your reference embeddings
4. Matches are stored in `descriptions.json` under `face_recognition`

## Output Format

```json
{
  "filename": "IMG_1234.HEIC",
  "face_recognition": {
    "has_known_faces": true,
    "face_count": 2,
    "known_faces": [
      {"name": "me", "confidence": 0.85}
    ]
  }
}
```
