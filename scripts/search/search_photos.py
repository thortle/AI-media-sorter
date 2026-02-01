#!/usr/bin/env python3

import json
import re
import sys
from pathlib import Path

class PhotoSearchEngine:
    def __init__(self, descriptions_file):
        self.descriptions_file = descriptions_file
        self.photos = []
        self.proximity_distance = 3  # Max words between keywords for proximity search
        self.load_data()
    
    def load_data(self):
        """Load photo descriptions from JSON file"""
        try:
            with open(self.descriptions_file, 'r') as f:
                data = json.load(f)
                self.photos = data['photos']
                total_photos = data.get('metadata', {}).get('total_photos', len(self.photos))
                print(f"Loaded {len(self.photos)} photos from {total_photos} total")
        except FileNotFoundError:
            print(f"Error: Could not find {self.descriptions_file}")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in {self.descriptions_file}")
            sys.exit(1)
    
    def set_proximity(self, distance):
        """Set proximity distance for keyword matching"""
        try:
            self.proximity_distance = int(distance)
            print(f"Proximity distance set to: {self.proximity_distance} words")
        except ValueError:
            print(f"Invalid proximity distance: {distance}. Use a number")
    
    def parse_query(self, query):
        """Parse query to extract AND/OR groups and logic"""
        # Split by 'or' first (case insensitive)
        or_groups = re.split(r'\s+or\s+', query.lower(), flags=re.IGNORECASE)
        
        parsed_groups = []
        
        for group in or_groups:
            # Split by 'and' within each OR group
            and_parts = re.split(r'\s+and\s+', group.strip(), flags=re.IGNORECASE)
            
            group_items = []
            for part in and_parts:
                # Check if this part has multiple words (proximity group)
                words = [w.strip() for w in part.split() if w.strip()]
                if len(words) > 1:
                    # Multiple words = proximity group
                    group_items.append({
                        'type': 'proximity',
                        'keywords': words
                    })
                elif len(words) == 1:
                    # Single word = standalone keyword
                    group_items.append({
                        'type': 'standalone',
                        'keywords': words
                    })
            
            if group_items:
                parsed_groups.append({
                    'type': 'and_group',
                    'items': group_items
                })
        
        return {
            'type': 'or_groups' if len(parsed_groups) > 1 else 'single_group',
            'groups': parsed_groups
        }
    
    def partial_match(self, keyword, word):
        """Check if keyword partially matches word (case insensitive) with improved logic"""
        keyword = keyword.lower()
        word = word.lower()
        
        # Exact match first (highest priority)
        if keyword == word:
            return True
        
        # If keyword is very short (1-2 chars), require exact match to avoid false positives
        if len(keyword) <= 2:
            return keyword == word
        
        # For longer keywords, check different matching strategies
        
        # 1. Word starts with keyword (e.g., "dog" matches "dogs", "doggy")
        if word.startswith(keyword):
            return True
        
        # 2. Word ends with keyword (e.g., "hair" matches "redhair" but not "chair")
        if word.endswith(keyword) and len(word) - len(keyword) <= 3:
            return True
        
        # 3. Keyword contains word (e.g., "mountain" contains "mount")
        if keyword in word and len(keyword) - len(word) <= 3:
            return True
        
        # 4. More restrictive substring matching - only if:
        #    - The keyword is reasonably long (4+ chars)
        #    - The substring appears at word boundaries or with limited context
        if len(keyword) >= 4:
            if keyword in word:
                # Check if it's likely a meaningful match
                # Avoid matches where keyword is buried in the middle of a much longer word
                if len(word) - len(keyword) <= 4:  # Allow some prefix/suffix
                    return True
                
                # Check if keyword appears at the start or end of the word
                keyword_pos = word.find(keyword)
                if keyword_pos == 0 or keyword_pos + len(keyword) == len(word):
                    return True
    
        return False
    
    def extract_context(self, words, match_index, window=3):
        """Extract context around matched word with smart padding"""
        total_words = len(words)
        
        # Calculate available words before and after
        words_before = min(match_index, window)
        words_after = min(total_words - match_index - 1, window)
        
        # If we can't get enough words on one side, take more from the other
        if words_before < window:
            words_after = min(total_words - match_index - 1, 2 * window - words_before)
        elif words_after < window:
            words_before = min(match_index, 2 * window - words_after)
        
        start_idx = max(0, match_index - words_before)
        end_idx = min(total_words, match_index + words_after + 1)
        
        context_words = words[start_idx:end_idx]
        
        # Highlight the matching word with **bold**
        highlighted_context = []
        for i, word in enumerate(context_words):
            actual_index = start_idx + i
            if actual_index == match_index:
                highlighted_context.append(f"**{word}**")
            else:
                highlighted_context.append(word)
        
        return " ".join(highlighted_context)
    
    def find_keyword_positions(self, description, keyword):
        """Find all positions where a keyword matches in the description"""
        words = re.findall(r'\b\w+\b', description)
        positions = []
        
        for i, word in enumerate(words):
            if self.partial_match(keyword, word):
                positions.append(i)
        
        return positions, words
    
    def find_proximity_matches(self, description, keywords):
        """Find contexts where keywords appear close to each other"""
        words = re.findall(r'\b\w+\b', description)
        
        # Find positions for all keywords
        keyword_positions = {}
        for keyword in keywords:
            positions = []
            for i, word in enumerate(words):
                if self.partial_match(keyword, word):
                    positions.append(i)
            if not positions:  # If any keyword is not found, no match
                return []
            keyword_positions[keyword] = positions
        
        # Find groups where all keywords appear close together
        contexts = []
        
        if len(keywords) == 1:
            # Single keyword
            for pos in keyword_positions[keywords[0]]:
                context = self.extract_context(words, pos)
                contexts.append(context)
        
        elif len(keywords) == 2:
            # Two keywords - check proximity
            kw1, kw2 = keywords
            pos1_list, pos2_list = keyword_positions[kw1], keyword_positions[kw2]
            
            for pos1 in pos1_list:
                for pos2 in pos2_list:
                    if abs(pos1 - pos2) <= self.proximity_distance:
                        # Create context that includes both keywords
                        min_pos = min(pos1, pos2)
                        max_pos = max(pos1, pos2)
                        
                        window = 3
                        start_idx = max(0, min_pos - window)
                        end_idx = min(len(words), max_pos + window + 1)
                        
                        context_words = words[start_idx:end_idx]
                        
                        # Highlight both matching keywords
                        highlighted_context = []
                        for i, word in enumerate(context_words):
                            actual_index = start_idx + i
                            if actual_index == pos1 or actual_index == pos2:
                                highlighted_context.append(f"**{word}**")
                            else:
                                highlighted_context.append(word)
                        
                        context_text = " ".join(highlighted_context)
                        if context_text not in contexts:  # Avoid duplicates
                            contexts.append(context_text)
        
        else:
            # More than 2 keywords - check if all appear in a reasonable window
            all_positions = []
            for positions in keyword_positions.values():
                all_positions.extend(positions)
            
            if all_positions:
                # Group positions that are close together
                all_positions.sort()
                
                # Find groups where all keywords appear within range
                for i in range(len(all_positions)):
                    group_positions = [all_positions[i]]
                    for j in range(i + 1, len(all_positions)):
                        if all_positions[j] - all_positions[i] <= self.proximity_distance * (len(keywords) - 1):
                            group_positions.append(all_positions[j])
                    
                    # Check if this group contains all keywords
                    keywords_found = set()
                    for pos in group_positions:
                        for keyword in keywords:
                            if pos in keyword_positions[keyword]:
                                keywords_found.add(keyword)
                    
                    if len(keywords_found) == len(keywords):
                        # All keywords found in this group
                        min_pos = min(group_positions)
                        max_pos = max(group_positions)
                        
                        window = 3
                        start_idx = max(0, min_pos - window)
                        end_idx = min(len(words), max_pos + window + 1)
                        
                        context_words = words[start_idx:end_idx]
                        
                        # Highlight all matching keywords
                        highlighted_context = []
                        for i, word in enumerate(context_words):
                            actual_index = start_idx + i
                            is_match = False
                            for keyword in keywords:
                                if actual_index in keyword_positions[keyword]:
                                    highlighted_context.append(f"**{word}**")
                                    is_match = True
                                    break
                            if not is_match:
                                highlighted_context.append(word)
                        
                        context_text = " ".join(highlighted_context)
                        if context_text not in contexts:
                            contexts.append(context_text)
                        break  # Found one valid group, that's enough
        
        return contexts
    
    def find_standalone_matches(self, description, keyword):
        """Find all matches of a standalone keyword"""
        words = re.findall(r'\b\w+\b', description)
        contexts = []
        
        for i, word in enumerate(words):
            if self.partial_match(keyword, word):
                context = self.extract_context(words, i)
                contexts.append(context)
        
        return contexts
    
    def search_photo(self, photo, parsed_query):
        """Search a single photo based on parsed query"""
        description = photo['description']
        
        if parsed_query['type'] == 'single_group':
            # Single AND group
            return self.search_and_group(description, parsed_query['groups'][0])
        
        else:  # or_groups
            # Multiple OR groups - any group can match
            for group in parsed_query['groups']:
                result = self.search_and_group(description, group)
                if result:
                    return result  # Return first matching group
            return None
    
    def search_and_group(self, description, and_group):
        """Search for an AND group (all items must be present)"""
        all_matches = {}
        
        for item in and_group['items']:
            if item['type'] == 'proximity':
                # Proximity group - keywords must be close
                contexts = self.find_proximity_matches(description, item['keywords'])
                if not contexts:  # If proximity group fails, whole AND group fails
                    return None
                label = " ".join(item['keywords'])
                all_matches[label] = contexts
            
            elif item['type'] == 'standalone':
                # Standalone keyword - can be anywhere in description
                keyword = item['keywords'][0]
                contexts = self.find_standalone_matches(description, keyword)
                if not contexts:  # If standalone keyword not found, whole AND group fails
                    return None
                all_matches[keyword] = contexts
        
        return all_matches if all_matches else None
    
    def search(self, query):
        """Main search function with smart query parsing"""
        if not query.strip():
            return []
        
        # Special case: search for "me" using face recognition
        if query.strip().lower() == 'me':
            return self.search_by_face_recognition()
        
        # Parse the query
        parsed_query = self.parse_query(query)
        
        # Generate search description
        search_desc = self.generate_search_description(parsed_query)
        print(f"{search_desc}")
        print("─" * 60)
        
        results = []
        
        for photo in self.photos:
            matches = self.search_photo(photo, parsed_query)
            
            if matches:
                results.append({
                    'filename': photo['filename'],
                    'matches': matches,
                    'full_path': photo['full_path'],
                    'description_length': len(photo['description']),
                    'word_count': photo.get('metadata', {}).get('word_count', 0)
                })
        
        return results
    
    def search_by_face_recognition(self):
        """Search for photos containing known faces (me)"""
        print(f"Searching for: Photos with recognized faces (you)")
        print("─" * 60)
        
        results = []
        
        for photo in self.photos:
            # Check if photo has face recognition data
            face_data = photo.get('face_recognition')
            
            if not face_data:
                continue  # No face recognition data yet
            
            # Check if known faces detected
            if face_data.get('has_known_faces', False):
                known_faces = face_data.get('known_faces', [])
                
                # Create a special match result for face recognition
                matches = {}
                face_info = []
                
                for face in known_faces:
                    confidence = face.get('match_confidence', 0)
                    ref_image = face.get('reference_image', 'unknown')
                    face_info.append(f"Match: {confidence:.1%} confidence (ref: {ref_image})")
                
                matches['Face Recognition'] = face_info
                
                results.append({
                    'filename': photo['filename'],
                    'matches': matches,
                    'full_path': photo['full_path'],
                    'description_length': len(photo['description']),
                    'word_count': photo.get('metadata', {}).get('word_count', 0),
                    'face_count': face_data.get('face_count', 0),
                    'known_faces_count': len(known_faces)
                })
        
        return results
    
    def generate_search_description(self, parsed_query):
        """Generate human-readable search description"""
        if parsed_query['type'] == 'single_group':
            group = parsed_query['groups'][0]
            parts = []
            for item in group['items']:
                if item['type'] == 'proximity':
                    keywords_str = " + ".join(item['keywords'])
                    parts.append(f"'{keywords_str}' (≤{self.proximity_distance} apart)")
                else:
                    parts.append(f"'{item['keywords'][0]}' (anywhere)")
            
            if len(parts) == 1:
                return f"Searching for: {parts[0]}"
            else:
                return f"Searching for: {' AND '.join(parts)}"
        
        else:  # or_groups
            group_descriptions = []
            for group in parsed_query['groups']:
                parts = []
                for item in group['items']:
                    if item['type'] == 'proximity':
                        keywords_str = " + ".join(item['keywords'])
                        parts.append(f"'{keywords_str}'")
                    else:
                        parts.append(f"'{item['keywords'][0]}'")
                
                if len(parts) == 1:
                    group_descriptions.append(parts[0])
                else:
                    group_descriptions.append(f"({' AND '.join(parts)})")
            
            return f"Searching for: {' OR '.join(group_descriptions)}"
    
    def display_results(self, results, show_stats=True):
        """Display search results in a formatted way"""
        if not results:
            print("No results found.")
            print("\nTips:")
            print("   • Use 'or' for broader results: 'dog or cat'")
            print("   • Use 'and' for additional requirements: 'red hair and woman'")
            print(f"   • Adjacent words are automatically grouped (≤{self.proximity_distance} apart)")
            print("   • Check spelling and try partial words")
            return
        
        print(f"Found {len(results)} result(s):")
        print()
        
        for i, result in enumerate(results, 1):
            # Header with filename
            print(f"{i:2d}. {result['filename']}")
            
            # Show context for each match group
            for match_label, contexts in result['matches'].items():
                print(f"     '{match_label}':")
                for context in contexts:
                    print(f"        ...{context}...")
            
            # File info
            if show_stats:
                word_count = result.get('word_count', 0)
                desc_length = result.get('description_length', 0)
                print(f"     {word_count} words, {desc_length} chars")
            
            # Full path
            print(f"     {result['full_path']}")
            print()

def main():
    # Path to the descriptions JSON file (relative to scripts/search/)
    descriptions_file = Path(__file__).parent.parent.parent / "data" / "descriptions.json"
    
    # Check if file exists
    if not descriptions_file.exists():
        print(f"Error: descriptions.json not found at {descriptions_file}")
        print("Make sure you're running this script from the scripts/search directory")
        sys.exit(1)
    
    # Initialize search engine
    search_engine = PhotoSearchEngine(descriptions_file)
    
    print("Smart Photo Search Tool")
    print("=" * 60)
    print("Smart Query Parser:")
    print("  - 'red hair' -> red AND hair close together")
    print("  - 'red or hair' -> red OR hair (either one)")
    print("  - 'red hair and dog' -> (red + hair close) AND dog anywhere")
    print("  - 'red hair or blue eyes' -> (red + hair) OR (blue + eyes)")
    print("  - 'me' -> photos with your face (requires face recognition)")
    print()
    print("Commands:")
    print("  - Set proximity: 'proximity 5' (max words between keywords)")
    print("  - Statistics: 'stats'")
    print("  - Quit: 'quit', 'exit', or 'q'")
    print()
    print(f"Current proximity: {search_engine.proximity_distance} words apart")
    print()
    
    while True:
        try:
            query = input(f"Search (≤{search_engine.proximity_distance}): ").strip()
            
            # Handle special commands
            if query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            # Handle proximity setting
            if query.lower().startswith('proximity '):
                distance = query[10:].strip()
                search_engine.set_proximity(distance)
                continue
            
            if query.lower() == 'stats':
                print(f"Collection Statistics:")
                print(f"   Total photos: {len(search_engine.photos)}")
                print(f"   Proximity distance: {search_engine.proximity_distance} words")
                
                # Count photos with dogs, cars, people
                has_dogs = sum(1 for p in search_engine.photos if p.get('keywords', {}).get('has_dogs', False))
                has_cars = sum(1 for p in search_engine.photos if p.get('keywords', {}).get('has_cars', False))
                has_people = sum(1 for p in search_engine.photos if p.get('keywords', {}).get('has_characters', False))
                
                print(f"   Photos with dogs: {has_dogs}")
                print(f"   Photos with cars: {has_cars}")
                print(f"   Photos with people: {has_people}")
                
                # Face recognition statistics
                has_face_data = sum(1 for p in search_engine.photos if 'face_recognition' in p)
                has_faces = sum(1 for p in search_engine.photos 
                               if p.get('face_recognition', {}).get('has_faces', False))
                has_known_faces = sum(1 for p in search_engine.photos 
                                     if p.get('face_recognition', {}).get('has_known_faces', False))
                
                print(f"   Photos with face recognition data: {has_face_data}")
                if has_face_data > 0:
                    print(f"   Photos with detected faces: {has_faces}")
                    print(f"   Photos with known faces (you): {has_known_faces}")
                
                print()
                continue
            
            if not query:
                continue
            
            # Perform search
            results = search_engine.search(query)
            
            # Display results
            search_engine.display_results(results)
            
            print("─" * 60)
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            print("Please try again or type 'quit' to exit")

if __name__ == "__main__":
    main()