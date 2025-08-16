#!/usr/bin/env python3
"""
Test script to verify Unicode character removal was successful
"""

import sys
import re
from pathlib import Path

def check_file_for_unicode(file_path):
    """Check a file for problematic Unicode characters"""
    unicode_chars = ['🚨', '🔍', '🔥', '❌', '✅', '⚡', '🧠', '📊', '🌐', '⚠️', '🔄']
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        found_chars = []
        for char in unicode_chars:
            if char in content:
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if char in line:
                        found_chars.append(f"Line {i}: {char}")
        
        return found_chars
    except Exception as e:
        return [f"Error reading file: {e}"]

def main():
    """Main test function"""
    print("Testing Unicode character removal...")
    
    # Files that should be clean of Unicode characters
    test_files = [
        "functions/filters/auto_web_search_filter.py",
        "functions/filters/enhanced_memory_function_filter_v5_1_final.py", 
        "test_filter_activation.py"
    ]
    
    all_clean = True
    
    for file_path in test_files:
        if not Path(file_path).exists():
            print(f"[SKIP] {file_path} - File not found")
            continue
            
        unicode_issues = check_file_for_unicode(file_path)
        
        if unicode_issues:
            print(f"[FAIL] {file_path} - Found Unicode characters:")
            for issue in unicode_issues:
                print(f"  {issue}")
            all_clean = False
        else:
            print(f"[PASS] {file_path} - Clean of problematic Unicode")
    
    if all_clean:
        print("\n✓ All tested files are clean of problematic Unicode characters!")
        print("✓ System should now work without Unicode encoding issues")
        return 0
    else:
        print("\n✗ Some files still contain problematic Unicode characters")
        return 1

if __name__ == "__main__":
    sys.exit(main())
