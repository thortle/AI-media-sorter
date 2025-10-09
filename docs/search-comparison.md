# Search Methods Comparison

## Quick Overview

| Feature | Keyword Search | Semantic Search |
|---------|---------------|-----------------|
| **Algorithm** | Direct string matching with proximity | Vector embeddings + cosine similarity |
| **Speed** | Instant (0.01s) | Fast (0.05s + 1-2s initial load) |
| **Setup** | None | Requires running `create_embeddings.py` |
| **Memory** | ~5MB | ~50MB (model + embeddings) |
| **Precision** | Exact matches only | Conceptual matches + synonyms |
| **Boolean Logic** |  AND/OR supported |  Natural language only |
| **Synonyms** |  Must use exact words |  Automatic synonym detection |

---

## How Each Method Works

### Keyword Search
1. Parse query for AND/OR logic
2. Split description into words
3. Check for partial matches (fuzzy matching)
4. Measure proximity between keywords (≤3 words apart)
5. Return photos where all conditions met

### Semantic Search
1. Convert query to 384-dimensional vector
2. Calculate cosine similarity with all photo embeddings
3. Rank by similarity score (0.0 to 1.0)
4. Return matches above threshold (default: 0.3)

---

## Strengths & Limitations

| Aspect | Keyword | Semantic |
|--------|---------|----------|
| **Best For** | Exact terms, Boolean queries, predictable results | Natural language, concepts, synonym variations |
| **Strengths** | Fast, precise, no AI needed, complex logic | Understands meaning, finds synonyms, conceptual matching |
| **Limitations** | Misses synonyms/concepts, requires exact wording | Slower initial load, less precise, no boolean logic |

---

## Query Examples

| Query | Keyword Finds | Semantic Also Finds |
|-------|--------------|---------------------|
| `dog` | dog, dogs, doggy | puppy, canine, retriever, pet |
| `red hair` | "red" near "hair" | ginger, auburn, copper-colored hair |
| `happy person` | exact "happy" + "person" | joyful, smiling, cheerful, grinning face |
| `mountain sunset` | "mountain" + "sunset" | peak at dusk, alpine golden hour, twilight |

---

## Use Case Recommendations

| Scenario | Recommended Method | Reason |
|----------|-------------------|---------|
| Exact name search | **Keyword** | Precise match needed |
| Concept search (e.g., "happy people") | **Semantic** | Many synonym variations |
| Boolean queries (AND/OR) | **Keyword** | Only method supporting logic |
| Broad exploration | **Semantic** | Better discovery |
| Filename lookup | **Keyword** | Exact match required |
| Natural language queries | **Semantic** | Understands intent |

---

## Real-World Comparison

### Query: "red hair and dog"

| Method | Results |
|--------|---------|
| **Keyword** | ✓ "woman with **red** curly **hair** and golden retriever **dog**"<br>✓ "person with **red** **hair** walking **dog**"<br>✗ "ginger-haired person with puppy" |
| **Semantic** | 0.890 - "woman with red curly hair and golden retriever dog"<br>0.850 - "ginger-haired person with puppy" ✓<br>0.820 - "auburn-haired lady and canine companion" ✓<br>0.780 - "copper-colored hair petting pet" ✓ |

### Query: "happy person"

| Method | Results |
|--------|---------|
| **Keyword** | ✓ "**happy** **person** smiling at camera"<br>✗ "person with joyful expression"<br>✗ "smiling individual looking cheerful" |
| **Semantic** | 0.910 - "person with joyful expression" ✓<br>0.895 - "happy person smiling at camera" ✓<br>0.870 - "smiling individual looking cheerful" ✓<br>0.850 - "grinning face showing teeth" ✓ |

---

## Special Feature: Face Recognition ("me" query)

Both methods support searching for photos of yourself using the query **"me"**.

**Setup Required:**
1. Add reference photos → `data/face_recognition_dataset/`
2. Run: `cd scripts/facial_recognition && python3 main.py`

**How It Works:**
- Filters photos with `has_known_faces = true` in metadata
- Returns matches with confidence scores
- Works identically in both keyword and semantic search

**Example Output:**
```
 Found 15 photos with recognized faces (you):

1. 📊 Similarity: 1.000
   📸 IMG_1234.jpg
   👤 Face Recognition: 94.5% confidence (ref: reference_01.jpg)
```

---

## Quick Decision Guide

**Use Keyword Search when:**
-  You know exact words in descriptions
-  You need complex AND/OR logic
-  You want instant, predictable results
-  You need precise filtering

**Use Semantic Search when:**
-  You want natural language queries
-  You need to find concepts/synonyms
-  You're exploring or browsing
-  Descriptions vary in wording