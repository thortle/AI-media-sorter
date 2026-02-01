#!/usr/bin/env python3
"""
Semantic Photo Search - Search using meaning, not just keywords
Finds photos based on semantic similarity using pre-computed embeddings
"""

from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import json
from pathlib import Path
import sys

class SemanticPhotoSearch:
    def __init__(self, descriptions_path, embeddings_path, model_name='all-MiniLM-L6-v2'):
        """
        Initialize semantic search engine
        
        Args:
            descriptions_path: Path to descriptions.json
            embeddings_path: Path to embeddings.npy
            model_name: Must match the model used to create embeddings
        """
        self.descriptions_path = descriptions_path
        self.embeddings_path = embeddings_path
        self.model_name = model_name
        
        self.model = None
        self.photos = []
        self.embeddings = None
        
    def load(self):
        """Load model, descriptions, and embeddings"""
        print("Loading semantic search engine...")
        
        # Load model
        print(f"  Loading model: {self.model_name}...")
        self.model = SentenceTransformer(self.model_name)
        
        # Load descriptions
        print(f"  Loading descriptions from {self.descriptions_path}...")
        with open(self.descriptions_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.photos = data.get('photos', [])
        
        # Load embeddings
        print(f"  Loading embeddings from {self.embeddings_path}...")
        self.embeddings = np.load(self.embeddings_path)
        
        print(f"Loaded {len(self.photos)} photos with embeddings")
        
        # Verify consistency
        if len(self.photos) != len(self.embeddings):
            raise ValueError(
                f"Mismatch: {len(self.photos)} photos but {len(self.embeddings)} embeddings. "
                "Please regenerate embeddings."
            )
    
    def search(self, query, top_k=20, threshold=0.3):
        """
        Search for photos semantically similar to query
        
        Args:
            query: Search query (e.g., "red hair and dog")
            top_k: Maximum number of results to return
            threshold: Minimum similarity score (0.0-1.0)
            
        Returns:
            List of results with photo data and similarity scores
        """
        # Encode query
        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        
        # Calculate similarities
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # Get top matches above threshold
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score >= threshold:
                results.append({
                    'photo': self.photos[idx],
                    'similarity': score,
                    'rank': len(results) + 1
                })
        
        return results
    
    def search_by_face_recognition(self):
        """Search for photos containing known faces (me)"""
        print(f"Searching for: Photos with recognized faces (you)")
        print("─" * 60)
        
        results = []
        
        for idx, photo in enumerate(self.photos):
            # Check if photo has face recognition data
            face_data = photo.get('face_recognition')
            
            if not face_data:
                continue  # No face recognition data yet
            
            # Check if known faces detected
            if face_data.get('has_known_faces', False):
                known_faces = face_data.get('known_faces', [])
                
                results.append({
                    'photo': photo,
                    'similarity': 1.0,  # Perfect match for face recognition
                    'rank': len(results) + 1,
                    'face_count': face_data.get('face_count', 0),
                    'known_faces': known_faces
                })
        
        return results
    
    def display_results(self, results, query):
        """Display search results in a formatted way"""
        print("\n" + "="*60)
        print(f"Semantic Search: \"{query}\"")
        print("="*60)
        
        if not results:
            print("No results found above similarity threshold.")
            return
        
        print(f"Found {len(results)} semantically similar photos:\n")
        
        for result in results:
            photo = result['photo']
            similarity = result['similarity']
            rank = result['rank']
            
            # Display rank and similarity
            print(f"{rank}. Similarity: {similarity:.3f}")
            
            # Display filename
            print(f"   {photo['filename']}")
            
            # If this is a face recognition result, show face info
            if 'known_faces' in result:
                print(f"   Face Recognition:")
                for face in result['known_faces']:
                    confidence = face.get('match_confidence', 0)
                    ref_image = face.get('reference_image', 'unknown')
                    print(f"      • Match: {confidence:.1%} confidence (ref: {ref_image})")
            else:
                # Display description (truncated)
                description = photo['description']
                if len(description) > 200:
                    description = description[:197] + "..."
                print(f"   {description}")
            
            # Display full path
            print(f"   {photo['full_path']}")
            print()

def main():
    # Paths (relative to scripts/embeddings/)
    descriptions_path = "../../data/descriptions.json"
    embeddings_path = "../../data/embeddings.npy"
    
    # Check if files exist
    if not Path(descriptions_path).exists():
        print(f"Error: {descriptions_path} not found!")
        sys.exit(1)
    
    if not Path(embeddings_path).exists():
        print(f"Error: {embeddings_path} not found!")
        print("Please run create_embeddings.py first.")
        sys.exit(1)
    
    # Initialize search engine
    search_engine = SemanticPhotoSearch(descriptions_path, embeddings_path)
    search_engine.load()
    
    # Interactive search loop
    print("\n" + "="*60)
    print("Semantic Photo Search")
    print("="*60)
    print("\nExamples:")
    print("  • 'red hair and dog' - finds ginger-haired people with puppies")
    print("  • 'happy person' - finds smiling, joyful, cheerful people")
    print("  • 'mountain sunset' - finds peaks at dusk, golden hour scenes")
    print("  • 'car in city' - finds vehicles, sedans, SUVs in urban areas")
    print("  • 'me' - finds photos with your face (requires face recognition)")
    print("\nCommands:")
    print("  • 'quit' or 'exit' - Exit search")
    print("  • 'threshold N' - Set minimum similarity (0.0-1.0)")
    print("  • 'top N' - Set number of results (default: 20)")
    print()
    
    threshold = 0.3
    top_k = 20
    
    while True:
        try:
            query = input("Search: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            # Special case: search for "me" using face recognition
            if query.lower() == 'me':
                results = search_engine.search_by_face_recognition()
                search_engine.display_results(results, query)
                continue
            
            # Handle commands
            if query.lower().startswith('threshold '):
                try:
                    threshold = float(query.split()[1])
                    print(f"Threshold set to {threshold}")
                    continue
                except:
                    print("Invalid threshold. Use: threshold 0.3")
                    continue
            
            if query.lower().startswith('top '):
                try:
                    top_k = int(query.split()[1])
                    print(f"Top results set to {top_k}")
                    continue
                except:
                    print("Invalid number. Use: top 20")
                    continue
            
            # Perform search
            results = search_engine.search(query, top_k=top_k, threshold=threshold)
            search_engine.display_results(results, query)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
