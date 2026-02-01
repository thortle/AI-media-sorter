#!/usr/bin/env python3
"""
Create Semantic Embeddings - One-time setup script
Converts all photo descriptions to embedding vectors for semantic search
"""

from sentence_transformers import SentenceTransformer
import json
import numpy as np
from pathlib import Path
import sys

class EmbeddingCreator:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        """
        Initialize embedding creator
        
        Args:
            model_name: Sentence Transformer model to use
                       'all-MiniLM-L6-v2' (default): Fast, 80MB, 384 dims
                       'all-mpnet-base-v2': Better quality, 420MB, 768 dims
        """
        self.model_name = model_name
        self.model = None
        
    def load_model(self):
        """Load the sentence transformer model"""
        print(f"Loading model: {self.model_name}...")
        self.model = SentenceTransformer(self.model_name)
        print(f"Model loaded successfully")
        print(f"   Embedding dimensions: {self.model.get_sentence_embedding_dimension()}")
        
    def load_descriptions(self, json_path):
        """Load photo descriptions from JSON"""
        print(f"Loading descriptions from {json_path}...")
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        photos = data.get('photos', [])
        print(f"Loaded {len(photos)} photo descriptions")
        return photos
    
    def create_embeddings(self, photos, batch_size=32):
        """
        Create embeddings for all photo descriptions
        
        Args:
            photos: List of photo dictionaries from descriptions.json
            batch_size: Number of photos to process at once (higher=faster)
            
        Returns:
            numpy array of embeddings (shape: [num_photos, embedding_dim])
        """
        print(f"\nCreating embeddings for {len(photos)} photos...")
        print(f"Batch size: {batch_size}")
        
        # Extract descriptions
        descriptions = [photo['description'] for photo in photos]
        
        # Create embeddings (with progress bar)
        embeddings = self.model.encode(
            descriptions,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True  # Normalize for cosine similarity
        )
        
        print(f"Created embeddings with shape: {embeddings.shape}")
        return embeddings
    
    def save_embeddings(self, embeddings, output_path):
        """Save embeddings to disk"""
        print(f"\nSaving embeddings to {output_path}...")
        np.save(output_path, embeddings)
        
        # Save metadata
        metadata_path = output_path.replace('.npy', '_metadata.json')
        metadata = {
            'model_name': self.model_name,
            'num_embeddings': len(embeddings),
            'embedding_dim': embeddings.shape[1],
            'normalized': True
        }
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Embeddings saved successfully")
        print(f"   Size: {embeddings.nbytes / 1024 / 1024:.2f} MB")

def main():
    # Paths (relative to scripts/embeddings/)
    json_path = "../../data/descriptions.json"
    embeddings_path = "../../data/embeddings.npy"
    
    # Check if descriptions.json exists
    if not Path(json_path).exists():
        print(f"Error: {json_path} not found!")
        print("Please run the description generator first.")
        sys.exit(1)
    
    # Create embeddings
    creator = EmbeddingCreator(model_name='all-MiniLM-L12-v2')
    creator.load_model()
    
    photos = creator.load_descriptions(json_path)
    embeddings = creator.create_embeddings(photos, batch_size=32)
    creator.save_embeddings(embeddings, embeddings_path)
    
    print("\n" + "="*60)
    print("Embedding creation complete!")
    print("="*60)

if __name__ == "__main__":
    main()
