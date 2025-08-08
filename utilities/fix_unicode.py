#!/usr/bin/env python3
"""
Unicode Character Cleanup Script
Removes Unicode emoji characters from Python files that cause Docker loading issues
"""

import os
import re
import glob

# Unicode character mappings - replace with ASCII equivalents
UNICODE_REPLACEMENTS = {
    '***': '***',  # Alert/warning
    '[OK]': '[OK]',  # Check mark
    '[FAIL]': '[FAIL]',  # Cross mark
    '[WARN]': '[WARN]',  # Warning
    '[SEARCH]': '[SEARCH]',  # Magnifying glass
    '[FOLDER]': '[FOLDER]',  # Folder
    '[FIRE]': '[FIRE]',  # Fire
    '[CHART]': '[CHART]',  # Chart
    '[MSG]': '[MSG]',  # Message
    '[MASK]': '[MASK]',  # Theater mask
    '[INFO]': '[INFO]',  # Information
    '[SYNC]': '[SYNC]',  # Sync/repeat
    '-': '-',  # Bullet point
    '->': '->'  # Arrow
}

def clean_unicode_from_file(file_path):
    """Remove Unicode characters from a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply replacements
        for unicode_char, replacement in UNICODE_REPLACEMENTS.items():
            content = content.replace(unicode_char, replacement)
        
        # Remove any remaining non-ASCII characters (except common ones)
        # Keep newlines, tabs, and basic punctuation
        content = re.sub(r'[^\x00-\x7F]', '', content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Cleaned: {file_path}")
            return True
        else:
            print(f"No changes: {file_path}")
            return False
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Clean Unicode characters from all Python files"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Find all Python files
    python_files = []
    for pattern in ['**/*.py', 'pipelines/*.py', 'core/*.py', 'utilities/*.py']:
        python_files.extend(glob.glob(os.path.join(base_dir, pattern), recursive=True))
    
    print(f"Found {len(python_files)} Python files to check...")
    
    cleaned_files = 0
    for file_path in python_files:
        if clean_unicode_from_file(file_path):
            cleaned_files += 1
    
    print(f"\nCompleted: {cleaned_files} files cleaned")
    
    # Also check JSON files for Unicode issues
    json_files = glob.glob(os.path.join(base_dir, 'config/*.json'))
    print(f"\nChecking {len(json_files)} JSON configuration files...")
    
    for file_path in json_files:
        if clean_unicode_from_file(file_path):
            cleaned_files += 1
    
    print(f"Total files cleaned: {cleaned_files}")

if __name__ == "__main__":
    main()
