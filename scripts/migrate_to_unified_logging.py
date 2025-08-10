#!/usr/bin/env python3
"""
Logging Migration Script
========================

This script systematically updates all Python files in the backend to use
the new unified logging system instead of various logging configurations.

Changes made:
1. Replace imports of core.logging_config with core.unified_logging
2. Replace imports of core.human_logging with core.unified_logging  
3. Replace direct logging.basicConfig usage with unified setup
4. Update logger initialization patterns
"""

import os
import re
import glob
from pathlib import Path

# Base directory for the backend
BASE_DIR = Path(__file__).parent.parent

def update_imports_in_file(file_path: Path) -> bool:
    """Update imports in a single file to use unified logging."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Replace imports of core.logging_config
        content = re.sub(
            r'from core\.logging_config import ([^\\n]+)',
            r'from core.unified_logging import \1',
            content
        )
        
        # Replace imports of core.human_logging
        content = re.sub(
            r'from core\.human_logging import ([^\\n]+)',
            r'from core.unified_logging import setup_logging, get_logger',
            content
        )
        
        # Replace HumanLogger.setup() calls
        content = re.sub(
            r'HumanLogger\.setup\(([^)]*)\)',
            r'setup_logging(level=\1)' if r'\1' else r'setup_logging()',
            content
        )
        
        # Replace direct logging.getLogger usage with get_logger where appropriate
        content = re.sub(
            r'logger = logging\.getLogger\(__name__\)',
            r'logger = get_logger(__name__)',
            content
        )
        
        # Replace logging.basicConfig with proper setup
        content = re.sub(
            r'if not logging\.getLogger\(\)\.handlers:\s*logging\.basicConfig\([^)]*\)',
            r'from core.unified_logging import setup_logging, get_logger\nsetup_logging()',
            content,
            flags=re.MULTILINE | re.DOTALL
        )
        
        # Update the logger assignment if it was using basicConfig
        content = re.sub(
            r'(from core\.unified_logging import setup_logging, get_logger\nsetup_logging\(\))\nlogger = logging\.getLogger\(__name__\)',
            r'\1\nlogger = get_logger(__name__)',
            content
        )
        
        # If changes were made, write the file back
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated: {file_path}")
            return True
        
        return False
        
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False

def main():
    """Main migration function."""
    print("Starting logging migration to unified logging system...")
    
    # Find all Python files in the backend
    python_files = []
    for root, dirs, files in os.walk(BASE_DIR):
        # Skip certain directories
        skip_dirs = {'.git', '__pycache__', '.pytest_cache', 'venv', 'env', 'node_modules'}
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    
    print(f"Found {len(python_files)} Python files to process")
    
    # Update each file
    updated_count = 0
    for file_path in python_files:
        if update_imports_in_file(file_path):
            updated_count += 1
    
    print(f"\nMigration complete: {updated_count} files updated")
    print("Next steps:")
    print("1. Test the application to ensure logging works correctly")
    print("2. Remove old logging configuration files if no longer needed")
    print("3. Update any documentation references to logging")

if __name__ == "__main__":
    main()
