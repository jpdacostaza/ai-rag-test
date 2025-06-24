#!/usr/bin/env python3
"""
Python Syntax Checker for Debug Tools
Identifies syntax and indentation errors in debug tool files.
"""

import ast
import os
import sys
from pathlib import Path

class PythonSyntaxChecker:
    def __init__(self):
        self.debug_tools = [
            "debug/utilities/endpoint_validator.py",
            "debug/utilities/debug_endpoints.py", 
            "debug/utilities/verify_memory_pipeline.py",
            "debug/memory-tests/comprehensive_memory_test.py",
            "debug/memory-tests/test_openwebui_memory.py",
            "debug/memory-tests/test_openwebui_memory_fixed.py",
            "debug/archived/demo-test/debug-tools/openwebui_memory_diagnostic.py",
            "debug/archived/demo-test/debug-tools/test_memory_cross_chat.py"
        ]
        
    def check_python_syntax(self, file_path):
        """Check if a Python file has valid syntax"""
        print(f"Checking: {file_path}")
        
        if not os.path.exists(file_path):
            print(f"  [FAIL] File not found")
            return False
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try to parse the file
            ast.parse(content)
            print(f"  [OK] Syntax is valid")
            return True
            
        except SyntaxError as e:
            print(f"  [FAIL] Syntax error: {e}")
            print(f"         Line {e.lineno}: {e.text.strip() if e.text else 'Unknown'}")
            return False
            
        except Exception as e:
            print(f"  [ERROR] Could not check file: {e}")
            return False
    
    def check_all_tools(self):
        """Check syntax for all debug tools"""
        print("[START] Python Syntax Checker for Debug Tools")
        print("="*60)
        
        valid_count = 0
        total_count = len(self.debug_tools)
        invalid_files = []
        
        for tool_path in self.debug_tools:
            if self.check_python_syntax(tool_path):
                valid_count += 1
            else:
                invalid_files.append(tool_path)
        
        print("\n" + "="*60)
        print("[TARGET] SYNTAX CHECK SUMMARY")
        print("="*60)
        print(f"[OK] Valid files: {valid_count}/{total_count}")
        print(f"[FAIL] Invalid files: {len(invalid_files)}")
        
        if invalid_files:
            print("\n[FAIL] Files needing syntax fixes:")
            for file_path in invalid_files:
                print(f"  - {file_path}")
        
        print("="*60)
        return valid_count == total_count

    def fix_common_indentation_issues(self, file_path):
        """Attempt to fix common indentation issues"""
        print(f"Attempting to fix: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            fixed_lines = []
            in_function = False
            expected_indent = 0
            
            for i, line in enumerate(lines):
                # Skip empty lines
                if line.strip() == '':
                    fixed_lines.append(line)
                    continue
                
                # Calculate current indentation
                current_indent = len(line) - len(line.lstrip())
                
                # Basic indentation fixes
                if line.strip().startswith('def ') or line.strip().startswith('class '):
                    expected_indent = 0
                    in_function = True
                elif in_function and line.strip() and not line.startswith(' '):
                    # This line should be indented if we're in a function
                    if not line.strip().startswith('def ') and not line.strip().startswith('class '):
                        line = '    ' + line.lstrip()
                
                fixed_lines.append(line)
            
            # Write the fixed content back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(fixed_lines)
            
            print(f"  [OK] Applied basic indentation fixes")
            return True
            
        except Exception as e:
            print(f"  [ERROR] Could not fix file: {e}")
            return False

if __name__ == "__main__":
    checker = PythonSyntaxChecker()
    
    print("Phase 1: Checking syntax of all debug tools...")
    all_valid = checker.check_all_tools()
    
    if not all_valid:
        print("\n[TOOL] Attempting to fix common indentation issues...")
        print("="*60)
        
        for tool_path in checker.debug_tools:
            if os.path.exists(tool_path):
                # First check if it needs fixing
                try:
                    with open(tool_path, 'r', encoding='utf-8') as f:
                        ast.parse(f.read())
                except SyntaxError:
                    # Try to fix it
                    checker.fix_common_indentation_issues(tool_path)
        
        print("\n[SEARCH] Re-checking syntax after fixes...")
        print("="*60)
        checker.check_all_tools()
    
    print("\n[FINISH] Syntax check complete!")
