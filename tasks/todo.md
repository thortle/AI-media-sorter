# Fix Semantic Search Ranking Issues - Investigation & Fix

## Current Status

**Branch:** `experimental/compound-phrase-search`
**Previous Work:** Implemented spaCy-based compound phrase search with weighted scoring
**Problem:** Search results still showing ranking inconsistencies

---

## Problem Statement

Query **"orange hair woman"** returns mismatched results in top rankings:

### Wrong Results (appearing in top 7):
1. **IMG_2373.JPG** - Score too high
   - Description: "dark brown hair... person wearing a pink shirt"
   - Issue: Has "dark brown hair" (not orange), no "woman" mentioned
   - Why it ranks high: Only matches "hair" keyword

2. **IMG_2202.JPG** - Score too high
   - Description: "woman with... blonde highlights"
   - Issue: Has "blonde hair" (not orange)
   - Why it ranks high: Matches "woman" and "hair" but misses "orange"

### Correct Result (appearing AFTER the wrong ones):
3. **IMG_5685.HEIC** - Should rank higher
   - Description: "young woman with vibrant reddish-pink curly hair"
   - Should rank #1: Matches "woman" + "orange/reddish-pink hair" semantically

---

## Investigation Tasks

### Phase 1: Reproduce and Analyze Issue
- [ ] Test query "orange hair woman" and capture top 50 results with descriptions
- [ ] Analyze phrase extraction for this query:
  - What phrases are extracted? (expected: ["orange hair", "woman"])
  - What are the phrase weights? (expected: 0.6 for "orange hair", 0.4 for "woman")
- [ ] Check semantic scores for the 3 problem photos:
  - What is the semantic score breakdown per phrase?
  - Are the embeddings for "orange hair" matching correctly?
  - Is "woman" matching too broadly?

### Phase 2: Root Cause Analysis
- [ ] Investigate phrase extraction logic for "orange hair woman"
  - Run `extract_noun_phrases("orange hair woman")` in container
  - Verify it returns [("orange hair", 2), ("woman", 1)]
  - Check if spaCy is parsing correctly (ADJ-NOUN vs NOUN-NOUN)

- [ ] Test individual phrase embeddings
  - Encode "orange hair" alone and check top matches
  - Encode "woman" alone and check top matches
  - Are individual phrases too generic or too specific?

- [ ] Check weight calculation
  - For "orange hair" (2 tokens) + "woman" (1 token)
  - Expected: "orange hair" = 0.6, "woman" = 0.4 (normalized to 1.0)
  - Is the normalization working correctly?

- [ ] Analyze semantic similarity scores
  - Why does "dark brown hair" score high for "orange hair"?
  - Is sentence-transformers model treating colors too generically?
  - Should we increase weight for longer/more specific phrases?

### Phase 3: Hypothesis Testing

Test these potential fixes:

- [ ] **Hypothesis 1: Phrase weights too balanced**
  - Current: 3+ tokens=0.6, 2 tokens=0.3, 1 token=0.2
  - Try: 3+ tokens=0.7, 2 tokens=0.25, 1 token=0.05
  - Test "orange hair woman" - does ranking improve?

- [ ] **Hypothesis 2: Color descriptors need special handling**
  - Colors might be too semantically similar in embedding space
  - Consider adding color-specific boosting in keyword tie-breaker
  - Test with "orange", "red", "blonde", "brown" hair queries

- [ ] **Hypothesis 3: Single nouns dilute compound importance**
  - "woman" alone may match too broadly
  - Could increase compound phrase weight relative to single words
  - Test: 3+ tokens=0.8, 2 tokens=0.15, 1 token=0.05

- [ ] **Hypothesis 4: Need minimum score threshold per phrase**
  - Photos should only rank high if ALL phrases score above threshold
  - Current: additive scoring allows one high phrase to compensate for low others
  - Consider multiplicative or min-threshold approach

### Phase 4: Implement Fix

Based on investigation findings:

- [ ] Update phrase weight calculation in `calculate_phrase_weights()`
- [ ] Update scoring logic if needed (additive vs multiplicative)
- [ ] Add special handling for color descriptors if needed
- [ ] Rebuild Docker: `docker compose build`
- [ ] Restart container: `docker compose up -d`

### Phase 5: Comprehensive Testing

Run these test queries and capture top 10 results:

- [ ] **"orange hair woman"** - Target: IMG_5685.HEIC should be #1 or #2
- [ ] **"vibrant orange hair bathroom"** - Previous test, ensure no regression
- [ ] **"blonde hair woman"** - Test color accuracy
- [ ] **"brown hair man"** - Test color + gender accuracy
- [ ] **"red car mountains"** - Ensure non-hair queries still work
- [ ] **"family dinner"** - Backward compatibility with 2-word compounds
- [ ] **"beach sunset"** - Backward compatibility
- [ ] **"woman"** (single word) - Should work as before

For each query, verify:
- Top 3 results are semantically accurate
- No mismatched color/gender/context in top 5
- Descriptions match the query intent

### Phase 6: Document and Commit

- [ ] Update done.md with:
  - Root cause found
  - Fix applied
  - Test results showing improvement
- [ ] Commit changes to experimental branch
- [ ] Push to origin

---

## Testing Script Template

Use this to test queries systematically:

```bash
# Test a query and show top 10 results
QUERY="orange hair woman"
curl -s -u thortle:pozeleNOASTRE "http://localhost:8000/api/search?q=${QUERY// /+}&limit=10" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'\n=== Query: {data[\"query\"]} ===\n')
for i, r in enumerate(data['results']):
    print(f'{i+1}. Score: {r[\"similarity\"]:.4f} | {r[\"filename\"]}')
    print(f'   {r[\"description\"][:150]}...\n')
"
```

---

## Investigation Checklist

Run these commands inside Docker container:

```bash
# 1. Check phrase extraction
docker exec photo-server python3 -c "
import spacy
nlp = spacy.load('en_core_web_sm', disable=['ner', 'lemmatizer', 'textcat'])
from search import extract_noun_phrases, calculate_phrase_weights

query = 'orange hair woman'
phrases = extract_noun_phrases(query)
weights = calculate_phrase_weights(phrases)
print(f'Query: {query}')
print(f'Phrases: {phrases}')
print(f'Weights: {weights}')
"

# 2. Test individual phrase embeddings
docker exec photo-server python3 -c "
from sentence_transformers import SentenceTransformer
import numpy as np
import json

model = SentenceTransformer('all-MiniLM-L12-v2')

# Load descriptions
with open('/app/data/descriptions.json') as f:
    data = json.load(f)
    photos = data['photos']

# Test 'orange hair' alone
emb = model.encode('orange hair', normalize_embeddings=True)
embeddings = np.load('/app/data/embeddings.npy')
scores = np.dot(embeddings, emb)
top5_idx = np.argsort(scores)[-5:][::-1]

print('Top 5 for \"orange hair\":')
for i in top5_idx:
    print(f'{scores[i]:.4f} - {photos[i][\"filename\"]}: {photos[i][\"description\"][:80]}...')
"
```

---

## Success Criteria

- [ ] Query "orange hair woman" returns IMG_5685.HEIC (reddish-pink hair woman) in top 3
- [ ] IMG_2373.JPG (dark brown hair) ranks lower than position 10
- [ ] IMG_2202.JPG (blonde highlights) ranks lower than position 10
- [ ] All backward compatibility tests pass (no regression)
- [ ] Color+attribute queries show consistent accuracy (blonde/brown/red hair)
- [ ] Documented root cause and fix in done.md

---

## Notes for Agent

1. **Start by investigating** - Don't jump to solutions
2. **Run the test queries** yourself using the curl commands
3. **Analyze the scores** - Look at semantic_score breakdown per phrase
4. **Test hypotheses** incrementally - Change one thing at a time
5. **Verify fix** with comprehensive test suite before committing
6. **Document findings** in done.md for future reference

The goal is to understand WHY the ranking is wrong, not just make it work for one query.
