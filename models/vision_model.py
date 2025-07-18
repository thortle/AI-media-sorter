import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from PIL import Image
import logging
import re

logger = logging.getLogger(__name__)

# Register HEIC support
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    logger.info("HEIC support enabled")
except ImportError:
    logger.warning("pillow-heif not available, HEIC files won't be supported")

logger = logging.getLogger(__name__)

class MoondreamVisionModel:
    """
    Simplified Moondream2 vision model for media sorting
    """
    
    def __init__(self, model_id="vikhyatk/moondream2"):
        self.model_id = model_id
        self.device = self._get_device()
        self.model = None
        self.tokenizer = None
        self._load_model()
    
    def _get_device(self):
        """Determine the best device for inference"""
        if torch.backends.mps.is_available():
            return "mps"
        elif torch.cuda.is_available():
            return "cuda"
        else:
            return "cpu"
    
    def _load_model(self):
        """Load the Moondream2 model and tokenizer"""
        try:
            logger.info(f"Using device: {self.device}")
            logger.info(f"Loading {self.model_id}...")
            
            # Load model and tokenizer
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id, 
                trust_remote_code=True,
                torch_dtype=torch.float16 if self.device != "cpu" else torch.float32
            ).to(self.device)
            
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            
            logger.info("Moondream2 model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def analyze_image(self, image_path):
        """
        Analyze an image and return a description
        
        Args:
            image_path: Path to the image file
            
        Returns:
            str: Description of the image content
        """
        try:
            # Load and process image
            image = Image.open(image_path).convert('RGB')
            
            # Generate description using Moondream2
            enc_image = self.model.encode_image(image)
            description = self.model.answer_question(enc_image, "Describe this image in detail.", self.tokenizer)
            
            return description.strip()
            
        except Exception as e:
            logger.error(f"Error analyzing image {image_path}: {e}")
            return ""
    
    def validate_detection(self, image_path, object_query):
        """
        Validate a specific object detection with multiple questions
        
        Args:
            image_path: Path to the image file
            object_query: Object to validate (e.g., "dog", "person", "car")
            
        Returns:
            dict: Validation results with confidence scores
        """
        try:
            image = Image.open(image_path).convert('RGB')
            enc_image = self.model.encode_image(image)
            
            # Ask multiple neutral validation questions
            questions = [
                f"What animals do you see in this image?",
                f"List all the objects you can identify in this photo.",
                f"Describe what is in the foreground of this image.",
                f"What living things are present in this image?"
            ]
            
            responses = {}
            for question in questions:
                response = self.model.answer_question(enc_image, question, self.tokenizer)
                responses[question] = response.strip().lower()
            
            # Check if the object is mentioned in neutral responses
            object_mentions = 0
            total_responses = len(responses)
            
            for response in responses.values():
                # Look for the object or its synonyms in the response
                if object_query.lower() in response:
                    object_mentions += 1
                # Check for related terms
                elif object_query == 'dog' and any(term in response for term in ['puppy', 'canine']):
                    object_mentions += 1
                elif object_query == 'cat' and any(term in response for term in ['kitten', 'feline']):
                    object_mentions += 1
            
            # Calculate validation confidence based on mentions
            confidence = object_mentions / total_responses
            detected = confidence > 0.5
            
            return {
                'detected': detected,
                'confidence': confidence,
                'responses': responses,
                'mentions': object_mentions,
                'total_responses': total_responses
            }
            
        except Exception as e:
            logger.error(f"Error validating detection in {image_path}: {e}")
            return {'detected': False, 'confidence': 0.0, 'error': str(e)}
    
    def matches_prompt(self, description, user_prompt):
        """
        Determine if an image description matches the user's sorting prompt
        
        Args:
            description: Image description from analyze_image
            user_prompt: User's sorting criteria (e.g., "sort all dog photos")
            
        Returns:
            float: Confidence score (0.0 to 1.0)
        """
        # Extract key terms from user prompt
        prompt_keywords = self._extract_keywords(user_prompt)
        
        if not prompt_keywords:
            return 0.0
        
        # Simple keyword matching with confidence scoring
        description_lower = description.lower()
        matches = 0
        total_keywords = len(prompt_keywords)
        
        for keyword in prompt_keywords:
            if keyword in description_lower:
                matches += 1
                # Bonus for exact matches
                if f" {keyword} " in f" {description_lower} ":
                    matches += 0.5
        
        confidence = min(matches / total_keywords, 1.0)
        
        logger.debug(f"Prompt keywords: {prompt_keywords}")
        logger.debug(f"Description: {description}")
        logger.debug(f"Confidence: {confidence:.2f}")
        
        return confidence
    
    def enhanced_matches_prompt(self, image_path, user_prompt):
        """
        Enhanced matching with validation for higher accuracy
        
        Args:
            image_path: Path to the image file
            user_prompt: User's sorting criteria
            
        Returns:
            dict: Enhanced results with validation
        """
        # First get basic description
        description = self.analyze_image(image_path)
        basic_confidence = self.matches_prompt(description, user_prompt)
        
        # If basic confidence is high, validate with targeted questions
        if basic_confidence >= 0.5:
            keywords = self._extract_keywords(user_prompt)
            
            validation_results = {}
            for keyword in keywords:
                validation = self.validate_detection(image_path, keyword)
                validation_results[keyword] = validation
            
            # Calculate enhanced confidence based on validation
            validated_keywords = 0
            total_keywords = len(keywords)
            
            for keyword, validation in validation_results.items():
                if validation['detected'] and validation['confidence'] >= 0.5:
                    validated_keywords += 1
            
            enhanced_confidence = validated_keywords / total_keywords if total_keywords > 0 else 0.0
            
            return {
                'description': description,
                'basic_confidence': basic_confidence,
                'enhanced_confidence': enhanced_confidence,
                'validation_results': validation_results,
                'final_confidence': enhanced_confidence
            }
        else:
            enhanced_confidence = basic_confidence
            return {
                'description': description,
                'basic_confidence': basic_confidence,
                'enhanced_confidence': enhanced_confidence,
                'validation_results': {},
                'final_confidence': enhanced_confidence
            }
    
    def _extract_keywords(self, prompt):
        """
        Extract relevant keywords from user prompt
        
        Args:
            prompt: User's natural language prompt
            
        Returns:
            list: List of keywords to search for
        """
        # Remove common words and extract meaningful terms
        stop_words = {
            'sort', 'all', 'the', 'find', 'get', 'photos', 'images', 'pictures', 
            'videos', 'files', 'in', 'to', 'from', 'with', 'and', 'or', 'of', 'a', 'an'
        }
        
        # Synonym mappings for better matching
        synonym_expansions = {
            'person': ['person', 'man', 'woman', 'people', 'human', 'individual', 'guy', 'girl', 'boy'],
            'people': ['person', 'man', 'woman', 'people', 'human', 'individual', 'guy', 'girl', 'boy', 'couple'],
            'dog': ['dog', 'puppy', 'canine'],
            'cat': ['cat', 'kitten', 'feline'],
            'water': ['water', 'river', 'lake', 'ocean', 'sea', 'stream'],
            'outdoor': ['outdoor', 'outside', 'nature', 'landscape'],
            'food': ['food', 'meal', 'eating', 'dinner', 'lunch', 'breakfast']
        }
        
        # Clean and split prompt
        cleaned_prompt = re.sub(r'[^a-zA-Z\s]', ' ', prompt.lower())
        words = cleaned_prompt.split()
        
        # Filter out stop words and short words
        base_keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Expand with synonyms
        expanded_keywords = []
        for keyword in base_keywords:
            if keyword in synonym_expansions:
                expanded_keywords.extend(synonym_expansions[keyword])
            else:
                expanded_keywords.append(keyword)
        
        # Remove duplicates while preserving order
        final_keywords = []
        seen = set()
        for keyword in expanded_keywords:
            if keyword not in seen:
                final_keywords.append(keyword)
                seen.add(keyword)
        
        return final_keywords
    
    def get_model_info(self):
        """Return model information"""
        return {
            "model_id": self.model_id,
            "device": self.device,
            "parameters": sum(p.numel() for p in self.model.parameters()),
            "dtype": str(next(self.model.parameters()).dtype)
        }
