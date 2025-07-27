import json
import requests
import time
import argparse
from typing import Dict, List

class KeywordProcessor:
    def __init__(self, ollama_model="llama3.2:3b"):
        self.ollama_model = ollama_model
        self.ollama_url = "http://localhost:11434/api/generate"
        
    def get_llm_keywords(self, description: str) -> Dict:
        """Extract categorized keywords from description using LLM"""
        
        prompt = f"""Analyze this image description and detect if there are any human characters present.

Description: "{description}"

Return ONLY a valid JSON object with this structure:
{{
  "has_characters": true/false,
  "characters": [
    {{
      "type": "specific descriptor from description like 'man', 'woman', 'child', 'hiker', 'gentleman', 'tourist', 'couple', 'student', 'individuals', etc.",
      "count": 1
    }}
  ]
}}

INSTRUCTIONS:
1. Set "has_characters" to true if ANY human being is mentioned in the description (man/woman/child/kid/person/hiker/gentleman/lady/tourist/student/couple/etc.)
2. Set "has_characters" to false if NO human beings are mentioned
3. In "characters" array, list each type of human character mentioned with their count
4. Use the exact descriptive terms from the description (like 'young man', 'woman', 'couple', 'hiker', 'child')
5. Do NOT include animals, objects, or non-human subjects
6. Return only valid JSON with no markdown formatting or comments"""

        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.9
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '')
                
                # Try to extract JSON from response
                try:
                    # Find JSON in response (sometimes LLM adds extra text)
                    start_idx = response_text.find('{')
                    end_idx = response_text.rfind('}') + 1
                    
                    if start_idx != -1 and end_idx != 0:
                        json_str = response_text[start_idx:end_idx]
                        return json.loads(json_str)
                    else:
                        print(f"No JSON found in response: {response_text}")
                        return self._get_empty_keywords()
                        
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    print(f"Response was: {response_text}")
                    return self._get_empty_keywords()
            else:
                print(f"HTTP error: {response.status_code}")
                return self._get_empty_keywords()
                
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return self._get_empty_keywords()
    
    def _get_empty_keywords(self) -> Dict:
        """Return empty keyword structure"""
        return {
            "has_characters": False,
            "characters": []
        }
    
    def process_json_file(self, input_file: str, start_from: int = 0, batch_size: int = 50, max_photos: int = None):
        """Process the descriptions.json file and update keywords"""
        
        print(f"Loading {input_file}...")
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        photos = data.get('photos', [])
        total_photos = len(photos)
        
        print(f"Found {total_photos} photos to process")
        print(f"Starting from photo {start_from}")
        if max_photos:
            print(f"Will process maximum {max_photos} photos")
        
        processed_count = 0
        
        for i, photo in enumerate(photos):
            if i < start_from:
                continue
                
            # Stop if we've reached the maximum number of photos to process
            if max_photos and processed_count >= max_photos:
                break
                
            # Skip if no description
            if 'description' not in photo or not photo['description']:
                continue
            
            print(f"Processing photo {i+1}/{total_photos}: {photo.get('filename', 'Unknown')}")
            
            # Get new keywords from LLM
            new_keywords = self.get_llm_keywords(photo['description'])
            
            # Update the photo's keywords
            photo['keywords'] = new_keywords
            
            processed_count += 1
            
            # Save progress every batch_size photos
            if processed_count % batch_size == 0:
                print(f"Saving progress... ({processed_count} photos processed)")
                with open(input_file, 'w', encoding='utf-8') as f:  # Same file
                    json.dump(data, f, indent=2, ensure_ascii=False)
    
        # Final save
        print(f"Processing complete. Saving final results...")
        with open(input_file, 'w', encoding='utf-8') as f:  # Same file
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Finished processing {processed_count} photos")
        print(f"Results saved to {input_file}")

def main():
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Process photo descriptions to detect human characters')
    parser.add_argument('--test', type=int, metavar='N', 
                       help='Test mode: process only N photos (e.g., --test 5, --test 10, --test 15)')
    
    args = parser.parse_args()
    
    processor = KeywordProcessor()
    input_file = "/Users/thortle/Desktop/media_sorter/sorting/descriptions.json"
    
    if args.test:
        # Test mode: process only specified number of photos
        print(f"🧪 Test mode: Processing only {args.test} photos")
        processor.process_json_file(input_file, start_from=0, batch_size=args.test, max_photos=args.test)
    else:
        # Default mode: process all photos
        print("🚀 Processing all photos in the gallery")
        processor.process_json_file(input_file, start_from=0, batch_size=50)

if __name__ == "__main__":
    main()