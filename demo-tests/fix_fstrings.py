#!/usr/bin/env python3
"""
Fix f-string template issues automatically
"""

import os
import re
import sys

def fix_fstring_issues(file_path):
    """Fix f-string template issues in a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Find and fix print statements with template literals
        # Pattern: print(f"text {variable} more text")
        def fix_print_statement(match):
            quote = match.group(1)  # " or '
            text = match.group(2)
            return f'print(f{quote}{text}{quote})'
        
        # Pattern for print statements with string literals containing {}
        pattern = r'print\((["\'])([^"\']*\{[^}]+\}[^"\']*)\1\)'
        content = re.sub(pattern, fix_print_statement, content)
        
        # Pattern for other string assignments with {}
        # variable = f"text {variable} more text" -> variable = f"text {variable} more text"
        def fix_assignment(match):
            quote = match.group(1)
            text = match.group(2)
            return f'f{quote}{text}{quote}'
        
        # Find string literals that contain {} but don't start with f
        pattern2 = r'(?<!f)(["\'])([^"\']*\{[^}]+\}[^"\']*)\1'
        content = re.sub(pattern2, fix_assignment, content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed f-string issues in {file_path}")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Main function to fix f-string issues in Python files."""
    fixed_files = []
    
    # Process current directory and subdirectories
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if fix_fstring_issues(file_path):
                    fixed_files.append(file_path)
    
    print(f"\n🎉 Fixed f-string issues in {len(fixed_files)} files:")
    for file_path in fixed_files:
        print(f"   - {file_path}")

if __name__ == "__main__":
    main()
