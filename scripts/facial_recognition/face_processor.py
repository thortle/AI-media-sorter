"""
Face Recognition Processor using DeepFace
Detects faces in photos and matches against a reference dataset
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# Register HEIC support
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    logger.info("HEIC support enabled")
except ImportError:
    logger.warning("pillow-heif not available, HEIC files won't be supported")


class FaceRecognitionProcessor:
    """
    Processes photos to detect and recognize faces using DeepFace
    """
    
    def __init__(self, reference_dataset_path: str, model_name: str = "Facenet512", 
                 detector_backend: str = "retinaface", distance_threshold: float = 0.4):
        """
        Initialize the face recognition processor
        
        Args:
            reference_dataset_path: Path to directory with reference face images
            model_name: DeepFace model to use (Facenet512, VGG-Face, ArcFace, etc.)
            detector_backend: Face detector backend (retinaface, mtcnn, opencv, etc.)
            distance_threshold: Maximum distance for face match (lower = stricter)
        """
        self.reference_dataset_path = Path(reference_dataset_path)
        self.model_name = model_name
        self.detector_backend = detector_backend
        self.distance_threshold = distance_threshold
        self.reference_embeddings = []
        
        # Configure TensorFlow for MPS (Apple Silicon) acceleration
        self._configure_tensorflow()
        
        # Load DeepFace after TF configuration
        self._load_deepface()
        
        # Build reference face database
        self._build_reference_database()
    
    def _configure_tensorflow(self):
        """Configure TensorFlow to use Apple Silicon MPS acceleration"""
        try:
            import tensorflow as tf
            
            # Check for MPS availability
            if tf.config.list_physical_devices('GPU'):
                logger.info("MPS (Metal Performance Shaders) GPU detected")
                # TensorFlow automatically uses MPS on Apple Silicon
                # Set memory growth to avoid allocation issues
                gpus = tf.config.list_physical_devices('GPU')
                if gpus:
                    for gpu in gpus:
                        tf.config.experimental.set_memory_growth(gpu, True)
                    logger.info(f"TensorFlow configured for MPS acceleration with {len(gpus)} GPU(s)")
            else:
                logger.info("No GPU detected, using CPU")
                
        except Exception as e:
            logger.warning(f"Could not configure TensorFlow for MPS: {e}")
            logger.info("Proceeding with default TensorFlow configuration")
    
    def _load_deepface(self):
        """Load DeepFace library"""
        try:
            global DeepFace
            from deepface import DeepFace as DF
            DeepFace = DF
            logger.info(f"DeepFace loaded successfully")
            logger.info(f"Using model: {self.model_name}")
            logger.info(f"Using detector: {self.detector_backend}")
        except ImportError:
            raise ImportError(
                "DeepFace not installed. Install with: pip install deepface tf-keras"
            )
    
    def _build_reference_database(self):
        """Build reference face embeddings from dataset"""
        if not self.reference_dataset_path.exists():
            raise ValueError(f"Reference dataset path does not exist: {self.reference_dataset_path}")
        
        # Get all image files in reference dataset
        image_extensions = {'.jpg', '.jpeg', '.png', '.heic', '.tiff'}
        reference_files = [
            f for f in self.reference_dataset_path.iterdir()
            if f.suffix.lower() in image_extensions and not f.name.startswith('.')
        ]
        
        if not reference_files:
            raise ValueError(f"No reference images found in {self.reference_dataset_path}")
        
        logger.info(f"Building reference database from {len(reference_files)} images...")
        
        for img_path in reference_files:
            try:
                # Extract face embedding from reference image
                embedding = self._get_face_embedding(str(img_path))
                if embedding is not None:
                    self.reference_embeddings.append({
                        'embedding': embedding,
                        'filename': img_path.name
                    })
                    logger.info(f"  ✓ Processed reference: {img_path.name}")
                else:
                    logger.warning(f"  ✗ No face detected in reference: {img_path.name}")
            except Exception as e:
                logger.error(f"  ✗ Error processing {img_path.name}: {e}")
        
        logger.info(f"Reference database built with {len(self.reference_embeddings)} face(s)")
        
        if len(self.reference_embeddings) == 0:
            raise ValueError("No faces detected in reference dataset")
    
    def _get_face_embedding(self, image_path: str) -> Optional[np.ndarray]:
        """
        Extract face embedding from an image
        
        Args:
            image_path: Path to image file
            
        Returns:
            Face embedding as numpy array, or None if no face detected
        """
        try:
            # DeepFace.represent returns a list of face embeddings (one per face)
            result = DeepFace.represent(
                img_path=image_path,
                model_name=self.model_name,
                detector_backend=self.detector_backend,
                enforce_detection=False  # Don't raise error if no face detected
            )
            
            # If faces detected, return the first face embedding
            if result and len(result) > 0:
                return np.array(result[0]['embedding'])
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting embedding: {e}")
            return None
    
    def _calculate_distance(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine distance between two face embeddings
        
        Args:
            embedding1: First face embedding
            embedding2: Second face embedding
            
        Returns:
            Cosine distance (0 = identical, 2 = completely different)
        """
        # Cosine distance = 1 - cosine similarity
        from scipy.spatial.distance import cosine
        return cosine(embedding1, embedding2)
    
    def analyze_photo(self, photo_path: str) -> Dict[str, Any]:
        """
        Analyze a photo for faces and match against reference dataset
        
        Args:
            photo_path: Path to photo to analyze
            
        Returns:
            Dictionary with face recognition results:
            {
                'has_faces': bool,
                'face_count': int,
                'has_known_faces': bool,
                'known_faces': [{'match_confidence': float, 'reference_image': str}, ...]
            }
        """
        result = {
            'has_faces': False,
            'face_count': 0,
            'has_known_faces': False,
            'known_faces': []
        }
        
        try:
            # Detect all faces in the photo
            faces = DeepFace.represent(
                img_path=photo_path,
                model_name=self.model_name,
                detector_backend=self.detector_backend,
                enforce_detection=False
            )
            
            if not faces or len(faces) == 0:
                return result
            
            result['has_faces'] = True
            result['face_count'] = len(faces)
            
            # Match each detected face against reference database
            for face in faces:
                face_embedding = np.array(face['embedding'])
                
                # Find best match in reference database
                best_match = None
                best_distance = float('inf')
                
                for ref in self.reference_embeddings:
                    distance = self._calculate_distance(face_embedding, ref['embedding'])
                    
                    if distance < best_distance:
                        best_distance = distance
                        best_match = ref
                
                # If best match is below threshold, it's a positive match
                if best_match and best_distance < self.distance_threshold:
                    result['has_known_faces'] = True
                    result['known_faces'].append({
                        'match_confidence': float(1.0 - (best_distance / 2.0)),  # Convert distance to 0-1 confidence
                        'reference_image': best_match['filename'],
                        'distance': float(best_distance)
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing photo {photo_path}: {e}")
            return result
    
    def process_photos_batch(self, photo_paths: List[str], 
                            progress_callback: Optional[callable] = None) -> Dict[str, Dict[str, Any]]:
        """
        Process multiple photos in batch
        
        Args:
            photo_paths: List of photo paths to process
            progress_callback: Optional callback function(current, total, filename)
            
        Returns:
            Dictionary mapping photo paths to face recognition results
        """
        results = {}
        total = len(photo_paths)
        
        for i, photo_path in enumerate(photo_paths, 1):
            if progress_callback:
                progress_callback(i, total, Path(photo_path).name)
            
            try:
                results[photo_path] = self.analyze_photo(photo_path)
            except Exception as e:
                logger.error(f"Failed to process {photo_path}: {e}")
                results[photo_path] = {
                    'has_faces': False,
                    'face_count': 0,
                    'has_known_faces': False,
                    'known_faces': [],
                    'error': str(e)
                }
        
        return results
