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
            
            # Try multiple prompts to get complete descriptions
            prompts = [
                "Describe this image in complete sentences.",
                "What do you see in this image? Provide a detailed description.",
                "Describe this image in detail.",
            ]
            
            best_description = ""
            
            for prompt in prompts:
                try:
                    description = self.model.answer_question(enc_image, prompt, self.tokenizer)
                    description = description.strip()
                    
                    # Check if description seems complete (ends with proper punctuation)
                    if description and (description.endswith('.') or description.endswith('!') or description.endswith('?')):
                        return description
                    
                    # Keep the longest description as backup
                    if len(description) > len(best_description):
                        best_description = description
                        
                except Exception as e:
                    logger.debug(f"Prompt '{prompt}' failed: {e}")
                    continue
            
            # If no complete description found, try to complete the best one
            if best_description:
                # If description doesn't end properly, try to get a continuation
                if not best_description.endswith(('.', '!', '?')):
                    try:
                        continuation_prompt = f"Complete this description: {best_description}"
                        continuation = self.model.answer_question(enc_image, continuation_prompt, self.tokenizer)
                        if continuation and len(continuation.strip()) > len(best_description):
                            best_description = continuation.strip()
                    except Exception:
                        pass
                        
                return best_description
            
            return ""
            
        except Exception as e:
            logger.error(f"Error analyzing image {image_path}: {e}")
            return ""
    
    def simple_matches_prompt(self, image_path, user_prompt):
        """
        Simple matching without confidence scoring - matches ANY detection
        
        Args:
            image_path: Path to the image file
            user_prompt: User's sorting criteria
            
        Returns:
            dict: Simple results with basic matching
        """
        try:
            # Get basic description
            description = self.analyze_image(image_path)
            
            # Extract keywords from prompt
            keywords = self._extract_keywords(user_prompt)
            
            # Simple keyword matching - ANY match counts
            description_lower = description.lower()
            matches_found = []
            
            for keyword in keywords:
                if keyword in description_lower:
                    matches_found.append(keyword)
            
            # Return True if ANY keyword matches
            is_match = len(matches_found) > 0
            
            return {
                'description': description,
                'is_match': is_match,
                'matched_keywords': matches_found,
                'all_keywords': keywords
            }
            
        except Exception as e:
            logger.error(f"Error analyzing {image_path}: {e}")
            return {
                'description': f"Error: {e}",
                'is_match': False,
                'matched_keywords': [],
                'all_keywords': []
            }
    
    def matches_prompt(self, description, user_prompt):
        """
        Determine if an image description matches the user's sorting prompt
        
        Args:
            description: Image description from analyze_image
            user_prompt: User's sorting criteria (e.g., "sort all dog photos")
            
        Returns:
            bool: True if ANY keyword matches, False otherwise
        """
        # Extract key terms from user prompt
        prompt_keywords = self._extract_keywords(user_prompt)
        
        if not prompt_keywords:
            return False
        
        # Simple keyword matching - ANY match counts
        description_lower = description.lower()
        
        for keyword in prompt_keywords:
            if keyword in description_lower:
                logger.debug(f"Match found: '{keyword}' in description")
                return True
        
        logger.debug(f"No matches found for keywords: {prompt_keywords}")
        return False
    
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
