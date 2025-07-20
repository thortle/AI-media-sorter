import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from PIL import Image
import logging

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
    Moondream2 vision model for generating detailed image descriptions
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
    
    def get_model_info(self):
        """Return model information"""
        return {
            "model_id": self.model_id,
            "device": self.device,
            "parameters": sum(p.numel() for p in self.model.parameters()),
            "dtype": str(next(self.model.parameters()).dtype)
        }
