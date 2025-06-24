#!/usr/bin/env python3
"""Debug script to test time parsing logic."""

import re

def test_time_parsing():
    """Test the time parsing logic."""
    
    # Test messages
    test_messages = [
        "What is the time in Tokyo?",
        "time in tokyo",
        "current time in Tokyo",
        "What's the time in Amsterdam?",
        "time in amsterdam"
    ]
    
    # Patterns from main.py
    time_patterns = [
        r"time(?:\s*(?:in|for|at))?\s+([a-zA-Z ]+)",
        r"current time in ([a-zA-Z ]+)",
        r"what(?:'s| is) the time in ([a-zA-Z ]+)",
        r"timeanddate\\.com.*([a-zA-Z ]+)",
    ]
    
    for message in test_messages:
        print(f"\nTesting: '{message}'")
        
        for i, pattern in enumerate(time_patterns):
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                country = match.group(1).strip()
                print(f"  Pattern {i+1} matched: '{country}'")
                
                # Apply cleaning logic from main.py
                print(f"  Before cleaning: '{country}'")
                country_cleaned = re.sub(
                    r"^(is|what|'s|the|current|now|please|tell|me|show|give|provide|can|you|do|does|in|for|at|on|of|about|time|current time|the time)\s+",
                    "",
                    country,
                    flags=re.IGNORECASE,
                )
                country_cleaned = country_cleaned.strip()
                print(f"  After cleaning: '{country_cleaned}'")
                
                if country_cleaned:
                    print(f"  ✅ Final result: '{country_cleaned}'")
                else:
                    print("  ❌ Empty after cleaning!")
                break
        else:
            print("  ❌ No pattern matched")

if __name__ == "__main__":
    test_time_parsing()
