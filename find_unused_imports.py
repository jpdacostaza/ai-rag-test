#!/usr/bin/env python3
"""
Script to remove unused imports from Python files
"""
import ast
import re
from pathlib import Path


def find_unused_imports(file_path):
    """Find unused imports in a Python file"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse the AST
        tree = ast.parse(content)

        # Find all imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        imports.append(alias.name)

        # Find which imports are actually used
        used_imports = set()
        for imp in imports:
            if re.search(rf"\b{re.escape(imp)}\b", content):
                used_imports.add(imp)

        # Return unused imports
        return [imp for imp in imports if imp not in used_imports]

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return []


def main():
    """Process files to find unused imports"""
    py_files = list(Path(".").glob("**/*.py"))
    py_files = [f for f in py_files if "__pycache__" not in str(f)]

    total_unused = 0
    for py_file in py_files:
        unused = find_unused_imports(py_file)
        if unused:
            print(f"{py_file}: {unused}")
            total_unused += len(unused)

    print(f"\nTotal unused imports found: {total_unused}")


if __name__ == "__main__":
    main()
