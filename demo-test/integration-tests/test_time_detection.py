#!/usr/bin/env python3
"""
Test to confirm that 'What is my name?' is being detected as a time query.
"""

import re

def test_time_detection():
    user_message = "What is my name?"
    
    time_patterns = [
        r"time(?:\s*(?:in|for|at))?\s+([a-zA-Z ]+)",
        r"current time in ([a-zA-Z ]+)",
        r"what(?:'s| is) the time in ([a-zA-Z ]+)",
        r"timeanddate\\.com.*([a-zA-Z ]+)",
    ]
    
    print(f"Testing message: '{user_message}'")
    
    for i, pat in enumerate(time_patterns):
        m = re.search(pat, user_message, re.IGNORECASE)
        if m:
            print(f"Pattern {i} matched: {pat}")
            print(f"Match groups: {m.groups()}")
            print(f"Full match: '{m.group(0)}'")
            if m.groups():
                print(f"Captured country: '{m.group(1)}'")
        else:
            print(f"Pattern {i} no match: {pat}")

if __name__ == "__main__":
    test_time_detection()
