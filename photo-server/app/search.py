"""
Search module for semantic photo search using pre-computed embeddings.
Includes query expansion and improved keyword matching.
"""

import json
import os
import re
from pathlib import Path
from typing import Optional, List, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer
from search_logger import SearchLogger

# Load spaCy for noun phrase extraction
try:
    import spacy
    nlp = spacy.load("en_core_web_sm", disable=["ner", "lemmatizer", "textcat"])
    SPACY_AVAILABLE = True
    print("spaCy model loaded successfully")
except Exception as e:
    nlp = None
    SPACY_AVAILABLE = False
    print(f"spaCy not available, using fallback: {e}")


# Query expansion rules - transforms simple queries into richer semantic descriptions
QUERY_EXPANSIONS = {
    # Compound concepts
    "family dinner": "group of people gathered around table eating food together meal dining family",
    "family photo": "group of relatives family members posing together portrait",
    "green mountains": "mountains covered with green trees vegetation forested hills lush greenery",
    "blue sky": "clear sky bright blue cloudless sunny day",
    "bright hat": "colorful hat vibrant headwear cap",
    "old building": "ancient historic aged architecture old structure weathered building",
    "young child": "kid baby toddler infant small child young boy girl",
    "adult person": "grown-up adult man woman mature person",
    
    # Emotions and expressions
    "sad people": "unhappy person crying melancholic distressed face sorrowful upset tears",
    "sad": "unhappy crying melancholic distressed sorrowful upset tears",
    "angry": "frustrated mad furious annoyed irritated scowling aggressive hostile",
    "happy": "joyful smiling cheerful delighted pleased excited laughing",
    "happy moment": "joyful celebration smiling cheerful happy people laughing",
    "peaceful": "calm serene tranquil quiet relaxed soothing",
    "peaceful scene": "calm serene tranquil quiet landscape relaxed soothing nature",
    
    # Activities and events
    "birthday party": "celebration cake candles birthday presents gifts gathering people",
    "wedding": "bride groom marriage ceremony wedding dress celebration",
    "vacation": "travel holiday trip beach tourist sightseeing relaxation getaway",
    "hiking": "trail walking mountains nature outdoors trekking adventure",
    "cooking": "kitchen food preparing meal chef cooking stove",
    
    # Places and scenes
    "beach": "ocean sea sand shore waves coast seaside water",
    "city": "urban buildings streets downtown metropolitan skyline",
    "forest": "trees woods nature woodland greenery leaves",
    "home": "house residence living room interior domestic",
    
    # Animals
    "puppy": "young dog small dog baby dog cute puppy",
    "kitten": "young cat small cat baby cat cute kitten",
    "pet": "dog cat animal companion domestic pet",
}


def expand_query(query: str) -> str:
    """
    Expand a query into a richer semantic description.
    
    For compound queries, this helps the embedding model understand
    the combined meaning rather than treating words separately.
    """
    query_lower = query.lower().strip()
    
    # Check for exact match first
    if query_lower in QUERY_EXPANSIONS:
        expanded = f"{query} {QUERY_EXPANSIONS[query_lower]}"
        return expanded
    
    # Check for partial matches (query contains an expansion key)
    for key, expansion in QUERY_EXPANSIONS.items():
        if key in query_lower:
            expanded = f"{query} {expansion}"
            return expanded
    
    # No expansion found, return original
    return query


def extract_noun_phrases(query: str) -> List[Tuple[str, int]]:
    """
    Extract noun phrases from a query using spaCy.

    Returns list of (phrase, token_count) tuples sorted by length (longest first).
    Falls back to simple word splitting if spaCy unavailable.

    For search queries like "vibrant orange hair bathroom", this splits at noun
    boundaries when adjectives precede, giving ["vibrant orange hair", "bathroom"].
    But "family dinner" (NOUN NOUN without adj) stays together.
    """
    if not SPACY_AVAILABLE or nlp is None:
        # Fallback: treat entire query as one phrase
        words = query.strip().split()
        return [(query.strip(), len(words))]

    doc = nlp(query)
    phrases = []

    for chunk in doc.noun_chunks:
        tokens = list(chunk)
        current_phrase = []
        has_adjective_before_noun = False

        for i, tok in enumerate(tokens):
            # Track if we've seen an adjective before nouns
            if tok.pos_ == "ADJ":
                has_adjective_before_noun = True

            current_phrase.append(tok.text)

            # Split at NOUN-NOUN boundary only if adjectives preceded
            # This keeps "family dinner" together but splits "orange hair bathroom"
            if (tok.pos_ == "NOUN" and
                i + 1 < len(tokens) and
                tokens[i + 1].pos_ == "NOUN" and
                has_adjective_before_noun):
                phrase_text = " ".join(current_phrase)
                if phrase_text.strip():
                    phrases.append((phrase_text.strip(), len(current_phrase)))
                current_phrase = []
                has_adjective_before_noun = False

        # Add remaining tokens as a phrase
        if current_phrase:
            phrase_text = " ".join(current_phrase)
            if phrase_text.strip():
                phrases.append((phrase_text.strip(), len(current_phrase)))

    # If no noun phrases found, use the full query
    if not phrases:
        words = query.strip().split()
        return [(query.strip(), len(words))]

    # Sort by token count descending (longer phrases first)
    phrases.sort(key=lambda x: x[1], reverse=True)
    return phrases


def calculate_phrase_weights(phrases: List[Tuple[str, int]]) -> List[Tuple[str, float]]:
    """
    Calculate weights for phrases based on their length/specificity.

    Longer phrases (compound descriptors) get higher weights.
    Returns list of (phrase, normalized_weight) tuples.
    """
    if not phrases:
        return []

    # Assign raw weights based on token count
    # 3+ tokens = 0.6, 2 tokens = 0.3, 1 token = 0.2
    weighted = []
    for phrase, token_count in phrases:
        if token_count >= 3:
            weight = 0.6
        elif token_count == 2:
            weight = 0.3
        else:
            weight = 0.2
        weighted.append((phrase, weight))

    # Normalize weights to sum to 1.0
    total_weight = sum(w for _, w in weighted)
    if total_weight > 0:
        weighted = [(phrase, weight / total_weight) for phrase, weight in weighted]

    return weighted


def extract_phrases(query: str) -> tuple[list[str], list[str]]:
    """
    Extract meaningful phrases from a query.
    Returns tuple of (full_phrases, individual_words) for proper scoring.
    """
    words = query.lower().split()
    full_phrases = []
    individual_words = []

    # Add the full query as a phrase if multi-word
    if len(words) > 1:
        full_phrases.append(query.lower())

    # Add individual words (3+ chars)
    individual_words = [w for w in words if len(w) >= 3]

    return full_phrases, individual_words


def extract_adjective_noun_pairs(text: str) -> list[tuple[str, str]]:
    """
    Extract (adjective, noun) pairs from text using spaCy dependency parsing.

    Returns list of (adjective, noun) tuples where the adjective modifies the noun.
    E.g., "vibrant pink hair" -> [("vibrant", "hair"), ("pink", "hair")]
    E.g., "pink shirt and brown hair" -> [("pink", "shirt"), ("brown", "hair")]
    """
    if not SPACY_AVAILABLE or nlp is None:
        return []

    doc = nlp(text.lower())
    pairs = []

    for token in doc:
        # Find adjectives that modify nouns (amod = adjectival modifier)
        if token.dep_ == "amod" and token.head.pos_ == "NOUN":
            pairs.append((token.text, token.head.text))

    return pairs


def check_adjective_noun_match(description: str, query_words: list[str]) -> bool:
    """
    Check if query words form a valid adjective-noun relationship in the description.

    For "pink hair" query:
    - "vibrant pink hair" -> True (pink modifies hair)
    - "dark brown hair...pink shirt" -> False (pink modifies shirt, not hair)

    For single-word queries, returns True (no relationship to check).
    """
    if len(query_words) < 2:
        return True  # Single word, no relationship to check

    # Extract adj-noun pairs from description
    pairs = extract_adjective_noun_pairs(description)

    if not pairs:
        # No adjective-noun pairs found in description
        # This means the description doesn't have the expected grammatical structure
        # Don't give it a boost - return False to apply penalty
        return False

    # For a query like "pink car", check if any adjective matching "pink"
    # modifies a noun matching "car"
    for adj, noun in pairs:
        # Check if adjective matches query word(s) and noun matches query noun
        # Use exact or prefix matching to avoid false positives like "car" in "scarf"
        adj_matches_query = any(
            adj == qw or adj.startswith(qw)  # "pink" or "pink-ish"
            for qw in query_words[:-1]  # All words except last (potential adjectives)
        )
        noun_matches_query = (
            noun == query_words[-1] or noun.startswith(query_words[-1])  # "car" or "cars"
        )

        if adj_matches_query and noun_matches_query:
            return True

    # Also check reverse: maybe user typed "car pink" instead of "pink car"
    for adj, noun in pairs:
        adj_matches_query = any(
            adj == qw or adj.startswith(qw)
            for qw in query_words[1:]  # All words except first
        )
        noun_matches_query = (
            noun == query_words[0] or noun.startswith(query_words[0])
        )

        if adj_matches_query and noun_matches_query:
            return True

    return False


def check_word_proximity(description: str, words: list[str], max_distance: int = 3) -> bool:
    """
    Check if all query words appear within max_distance words of each other.

    For "pink hair" query:
    - "vibrant pink hair" -> True (adjacent)
    - "dark brown hair...pink shirt" -> False (too far apart)
    """
    if len(words) <= 1:
        return True

    # Tokenize description into words
    desc_words = description.lower().split()

    # Find all positions of each query word
    positions = {}
    for word in words:
        positions[word] = []
        for i, desc_word in enumerate(desc_words):
            # Check if query word is contained in description word
            if word in desc_word:
                positions[word].append(i)

    # Check if any word is missing
    for word in words:
        if not positions[word]:
            return False

    # For two words, check if any pair is within max_distance
    if len(words) == 2:
        for pos1 in positions[words[0]]:
            for pos2 in positions[words[1]]:
                if abs(pos1 - pos2) <= max_distance:
                    return True
        return False

    # For 3+ words, check if all can be found within a window of max_distance
    # Use the first word as anchor and check if others are nearby
    for anchor_pos in positions[words[0]]:
        all_nearby = True
        for other_word in words[1:]:
            found_nearby = False
            for other_pos in positions[other_word]:
                if abs(anchor_pos - other_pos) <= max_distance:
                    found_nearby = True
                    break
            if not found_nearby:
                all_nearby = False
                break
        if all_nearby:
            return True

    return False


class PhotoSearchEngine:
    """Handles semantic search over photo descriptions using embeddings."""
    
    def __init__(self, data_path: str = "/app/data"):
        self.data_path = Path(data_path)
        self.model: Optional[SentenceTransformer] = None
        self.embeddings: Optional[np.ndarray] = None
        self.photos: list = []
        self.model_name = "all-MiniLM-L12-v2"  # Upgraded from L6 to L12
        self.logger = SearchLogger(str(self.data_path / "search_history.jsonl"))
        
    def load(self) -> None:
        """Load embeddings, metadata, and photos on startup."""
        print("Loading search engine...")
        
        # Load embeddings
        embeddings_path = self.data_path / "embeddings.npy"
        self.embeddings = np.load(embeddings_path)
        print(f"Loaded embeddings: {self.embeddings.shape}")
        
        # Load photo descriptions
        descriptions_path = self.data_path / "descriptions.json"
        with open(descriptions_path, "r") as f:
            data = json.load(f)
            self.photos = data.get("photos", [])
        print(f"Loaded {len(self.photos)} photos")
        
        # Load embedding model (for encoding search queries)
        print(f"Loading model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        print("Search engine ready!")
        
    def search(
        self,
        query: str,
        top_k: int = 50,
        has_characters: Optional[bool] = None,
        has_dogs: Optional[bool] = None,
        has_cars: Optional[bool] = None,
        min_score: float = 0.0,
    ) -> list[dict]:
        """
        Semantic search with keyword tie-breaking.
        
        The semantic score is the PRIMARY signal (captures meaning).
        Keyword matching only provides a small multiplicative boost
        to break ties between semantically similar results.
        
        Args:
            query: Natural language search query
            top_k: Number of results to return
            has_characters: Filter for photos with people
            has_dogs: Filter for photos with dogs
            has_cars: Filter for photos with cars
            min_score: Minimum similarity score (0.0-1.0) to include
            
        Returns:
            List of photo dicts with similarity scores
        """
        if self.model is None or self.embeddings is None:
            raise RuntimeError("Search engine not loaded. Call load() first.")

        # Extract noun phrases and calculate weights
        raw_phrases = extract_noun_phrases(query)
        weighted_phrases = calculate_phrase_weights(raw_phrases)

        # Build expanded query string for logging
        phrase_names = [p for p, _ in weighted_phrases]
        expanded_query = f"Multi-phrase: {phrase_names}"

        # Calculate weighted semantic scores across all phrases
        semantic_scores = np.zeros(len(self.embeddings))

        for phrase, weight in weighted_phrases:
            # Apply query expansion to each phrase
            expanded_phrase = expand_query(phrase)
            # Encode phrase
            phrase_embedding = self.model.encode(expanded_phrase, normalize_embeddings=True)
            # Calculate similarity for this phrase
            phrase_scores = np.dot(self.embeddings, phrase_embedding)
            # Add weighted contribution
            semantic_scores += weight * phrase_scores

        # Extract words for tie-breaking
        _, individual_words = extract_phrases(query)
        full_query_lower = query.lower().strip()
        is_multi_word = len(query.split()) > 1
        
        # Calculate scores
        candidates = []
        for idx, photo in enumerate(self.photos):
            semantic_score = float(semantic_scores[idx])
            
            # Skip low scores early
            if semantic_score < min_score:
                continue
            
            keywords = photo.get("keywords", {})
            
            # Apply filters
            if has_characters is not None:
                if keywords.get("has_characters", False) != has_characters:
                    continue
            if has_dogs is not None:
                if keywords.get("has_dogs", False) != has_dogs:
                    continue
            if has_cars is not None:
                if keywords.get("has_cars", False) != has_cars:
                    continue
            
            # Keyword tie-breaking (small multiplicative boost, max 5%)
            description_lower = photo["description"].lower()
            phrase_matched = False
            word_matches = 0

            # Check for full phrase match
            if is_multi_word and full_query_lower in description_lower:
                phrase_matched = True

            # Count individual word matches
            for word in individual_words:
                if word in description_lower:
                    word_matches += 1

            # Keyword boost/penalty logic with NLP adjective-noun matching
            # - Full phrase match: 10% boost
            # - All words match AND adjective modifies noun: 10% boost
            # - All words match but adjective does NOT modify noun: 40% penalty
            # - Partial match (some words missing): penalty proportional to missing words
            # - No match: no adjustment
            if phrase_matched:
                tie_breaker = 1.10  # 10% boost for exact phrase
            elif word_matches == len(individual_words) and len(individual_words) > 0:
                # All words present - check if adjective actually modifies the noun
                if check_adjective_noun_match(description_lower, individual_words):
                    tie_breaker = 1.10  # 10% boost if proper adj-noun relationship
                else:
                    tie_breaker = 0.60  # 40% penalty for misleading scattered matches
            elif word_matches > 0 and len(individual_words) > 1:
                # Partial match - penalize based on missing words
                # E.g., "curly hair" query but only "hair" in description
                # Strong penalty to ensure actual matches rank above partial matches
                missing_ratio = 1 - (word_matches / len(individual_words))
                tie_breaker = 1.0 - (0.50 * missing_ratio)  # Up to 50% penalty
            else:
                tie_breaker = 1.0
            
            final_score = semantic_score * tie_breaker
            
            candidates.append({
                "filename": photo["filename"],
                "description": photo["description"],
                "similarity": round(final_score, 4),
                "semantic_score": round(semantic_score, 4),
                "phrase_matched": phrase_matched,
                "word_matches": word_matches,
                "keywords": keywords,
            })
        
        # Sort by final score and return top_k
        candidates.sort(key=lambda x: x["similarity"], reverse=True)
        results = candidates[:top_k]
        
        # Log this search for analysis
        if results:
            top_score = results[0]["similarity"]
            top_3_avg = sum(r["similarity"] for r in results[:3]) / min(3, len(results))
            
            self.logger.log_search(
                query=query,
                results_count=len(results),
                top_score=top_score,
                top_3_avg=top_3_avg,
                expanded_query=expanded_query,
                filters={
                    "has_characters": has_characters,
                    "has_dogs": has_dogs,
                    "has_cars": has_cars,
                } if any([has_characters is not None, has_dogs is not None, has_cars is not None]) else None,
            )
        
        return results
    
    def get_all_photos(
        self,
        limit: int = 100,
        offset: int = 0,
        has_characters: Optional[bool] = None,
        has_dogs: Optional[bool] = None,
        has_cars: Optional[bool] = None,
    ) -> tuple[list[dict], int]:
        """
        Get all photos with optional filtering.
        
        Returns:
            Tuple of (photos list, total count matching filters)
        """
        filtered = []
        
        for photo in self.photos:
            keywords = photo.get("keywords", {})
            
            # Apply filters
            if has_characters is not None:
                if keywords.get("has_characters", False) != has_characters:
                    continue
            if has_dogs is not None:
                if keywords.get("has_dogs", False) != has_dogs:
                    continue
            if has_cars is not None:
                if keywords.get("has_cars", False) != has_cars:
                    continue
            
            filtered.append({
                "filename": photo["filename"],
                "description": photo["description"],
                "keywords": keywords,
            })
        
        total = len(filtered)
        return filtered[offset:offset + limit], total
    
    def get_photo_by_filename(self, filename: str) -> Optional[dict]:
        """Get a single photo's metadata by filename."""
        for photo in self.photos:
            if photo["filename"] == filename:
                return {
                    "filename": photo["filename"],
                    "description": photo["description"],
                    "keywords": photo.get("keywords", {}),
                }
        return None
    
    def remove_photo(self, filename: str) -> bool:
        """
        Remove a photo from the in-memory index.

        Args:
            filename: The filename to remove

        Returns:
            True if photo was found and removed, False otherwise
        """
        # Find the photo index
        photo_idx = None
        for idx, photo in enumerate(self.photos):
            if photo["filename"] == filename:
                photo_idx = idx
                break

        if photo_idx is None:
            return False

        # Remove from photos list
        self.photos.pop(photo_idx)

        # Remove from embeddings array
        if self.embeddings is not None:
            self.embeddings = np.delete(self.embeddings, photo_idx, axis=0)

        print(f"Removed photo from index: {filename} (now {len(self.photos)} photos)")
        return True

    def add_photo(self, photo: dict, embedding: np.ndarray) -> None:
        """
        Add a photo to the in-memory index (hot reload).

        Args:
            photo: Photo dict with filename, description, etc.
            embedding: Pre-computed embedding vector (384 dims for MiniLM-L12)
        """
        # Add to photos list
        self.photos.append(photo)

        # Add embedding to array
        if self.embeddings is not None:
            if len(embedding.shape) == 1:
                embedding = embedding.reshape(1, -1)
            self.embeddings = np.vstack([self.embeddings, embedding])

        print(f"Added photo to index: {photo['filename']} (now {len(self.photos)} photos)")


# Global search engine instance
search_engine = PhotoSearchEngine()
