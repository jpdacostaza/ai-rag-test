#!/usr/bin/env python3
"""
Test memory function extraction logic directly
"""

import sys
import os
import re
sys.path.insert(0, os.path.dirname(__file__))

def test_extraction():
    """Test the extraction logic directly"""
    
    # Test message with personal info + question
    test_message = "Hello, my name is J.P. and I live in Netherlands. I work as a systems and application engineer. Can you remember that?"
    
    print(f"🧪 TESTING EXTRACTION LOGIC")
    print(f"Test message: {test_message}")
    print(f"=" * 60)
    
    # Test question detection patterns
    question_start_patterns = [
        r'^\s*\?',  # Starts with question mark
        r'^\s*(?:what|who|where|when|why|how)\b',  # Starts with question words
        r'^\s*(?:do you|can you|are you|would you|could you)\b',  # Starts with question phrases
    ]
    
    print(f"1. Question Detection Test:")
    is_question = any(re.search(pattern, test_message.lower()) for pattern in question_start_patterns)
    print(f"   Is question (should be False): {is_question}")
    
    # Test text splitting
    print(f"\n2. Text Splitting Test:")
    declarative_parts = []
    if '?' in test_message:
        parts = test_message.split('?')
        for part in parts:
            if any(keyword in part.lower() for keyword in ['my name is', 'i am', 'i live', 'i work']):
                declarative_parts.append(part.strip())
    else:
        declarative_parts = [test_message]
    
    print(f"   Declarative parts found: {len(declarative_parts)}")
    for i, part in enumerate(declarative_parts):
        print(f"   Part {i+1}: {part}")
    
    # Test name extraction
    print(f"\n3. Name Extraction Test:")
    name_patterns = [
        r"(?:my name is|i am|i'm|call me|name's)\s+([A-Z][A-Za-z\.]*(?:\s+[A-Z][A-Za-z\.]*)*)",
        r"(?:i am|i'm)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        r"name(?:\s+is)?\s*:?\s*([A-Z][A-Za-z\.]+)",
    ]
    
    for part in declarative_parts:
        for pattern in name_patterns:
            matches = re.finditer(pattern, part, re.IGNORECASE)
            for match in matches:
                name = match.group(1).strip()
                name = re.sub(r'\s+', ' ', name)
                if 2 <= len(name) <= 30 and 'and' not in name.lower():
                    print(f"   ✅ Extracted name: '{name}'")
                else:
                    print(f"   ❌ Rejected name: '{name}' (validation failed)")
    
    # Test work extraction
    print(f"\n4. Work Extraction Test:")
    work_patterns = [
        r"(?:i work at|i work for|i'm at|i'm with|work at|work for|employed at|employed by)\s+([A-Za-z][A-Za-z0-9\s&\.,-]*)",
        r"(?:i work as)\s+([A-Za-z\s]+)",
    ]
    
    for part in declarative_parts:
        for pattern in work_patterns:
            matches = re.finditer(pattern, part, re.IGNORECASE)
            for match in matches:
                work_info = match.group(1).strip()
                work_info = re.sub(r'\s+', ' ', work_info)
                if len(work_info) > 1:
                    print(f"   ✅ Extracted work info: '{work_info}'")
    
    # Test location extraction
    print(f"\n5. Location Extraction Test:")
    location_patterns = [
        r"(?:i live in|i'm from|from|live in)\s+([A-Z][A-Za-z\s,.-]+)",
    ]
    
    for part in declarative_parts:
        for pattern in location_patterns:
            matches = re.finditer(pattern, part, re.IGNORECASE)
            for match in matches:
                location = match.group(1).strip()
                location = re.sub(r'\s+', ' ', location)
                if len(location) > 1:
                    print(f"   ✅ Extracted location: '{location}'")

if __name__ == "__main__":
    test_extraction()
