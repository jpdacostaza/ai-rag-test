#!/usr/bin/env python3
"""
Enhanced Automated Code Fixing Script
Systematically fixes common code quality issues across the codebase.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Dict
from typing import List


class EnhancedCodeFixer:
    """Enhanced code fixer that addresses common issues systematically."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.python_files = self._find_python_files()
        self.missing_imports = self._get_common_missing_imports()

    def _find_python_files(self) -> List[Path]:
        """Find all Python files in the project."""
        python_files = []
        for root, _, files in os.walk(self.project_root):
            for file in files:
                if file.endswith(".py"):
                    python_files.append(Path(root) / file)
        return python_files

    def _get_common_missing_imports(self) -> Dict[str, str]:
        """Map of common undefined names to their import statements."""
        return {
            "Enum": "from enum import Enum",
            "dataclass": "from dataclasses import dataclass",
            "datetime": "import datetime",
            "Optional": "from typing import Optional",
            "List": "from typing import List",
            "Dict": "from typing import Dict",
            "Any": "from typing import Any",
            "Union": "from typing import Union",
            "Tuple": "from typing import Tuple",
            "Callable": "from typing import Callable",
            "Type": "from typing import Type",
            "TypeVar": "from typing import TypeVar",
            "Generic": "from typing import Generic",
            "Protocol": "from typing import Protocol",
            "Literal": "from typing import Literal",
            "Final": "from typing import Final",
            "ClassVar": "from typing import ClassVar",
            "abstractmethod": "from abc import abstractmethod",
            "ABC": "from abc import ABC",
            "json": "import json",
            "os": "import os",
            "sys": "import sys",
            "re": "import re",
            "time": "import time",
            "logging": "import logging",
            "sqlite3": "import sqlite3",
            "asyncio": "import asyncio",
            "threading": "import threading",
            "uuid": "import uuid",
            "hashlib": "import hashlib",
            "base64": "import base64",
            "urllib": "import urllib",
            "requests": "import requests",
            "numpy": "import numpy as np",
            "pandas": "import pandas as pd",
        }

    def fix_missing_imports(self, file_path: Path) -> bool:
        """Fix missing imports in a file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Find undefined names using flake8 output
            result = subprocess.run(
                ["flake8", "--select=F821", str(file_path)],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if result.returncode != 0:
                undefined_names = set()
                for line in result.stdout.split("\n"):
                    if "F821" in line and "undefined name" in line:
                        match = re.search(r"undefined name '([^']*)'", line)
                        if match:
                            undefined_names.add(match.group(1))

                # Add necessary imports
                new_imports = []
                for name in undefined_names:
                    if name in self.missing_imports:
                        import_stmt = self.missing_imports[name]
                        if import_stmt not in content:
                            new_imports.append(import_stmt)

                if new_imports:
                    # Find the best place to insert imports
                    lines = content.split("\n")
                    insert_pos = 0

                    # Skip shebang and docstrings
                    for i, line in enumerate(lines):
                        if line.startswith("#") or line.startswith('"""') or line.startswith("'''"):
                            continue
                        if (
                            line.strip()
                            and not line.startswith("import")
                            and not line.startswith("from")
                        ):
                            insert_pos = i
                            break

                    # Insert imports
                    for import_stmt in new_imports:
                        lines.insert(insert_pos, import_stmt)
                        insert_pos += 1

                    # Write back
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write("\n".join(lines))

                    print(f"Added {len(new_imports)} imports to {file_path}")
                    return True

        except Exception as e:
            print(f"Error fixing imports in {file_path}: {e}")

        return False

    def fix_unused_variables(self, file_path: Path) -> bool:
        """Fix unused variables by either removing or using them."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Find unused variables using flake8
            result = subprocess.run(
                ["flake8", "--select=F841", str(file_path)],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if result.returncode != 0:
                lines = content.split("\n")

                for line in result.stdout.split("\n"):
                    if "F841" in line and "assigned to but never used" in line:
                        # Extract line number and variable name
                        match = re.search(r":(\d+):", line)
                        var_match = re.search(r"'([^']*)'", line)

                        if match and var_match:
                            line_num = int(match.group(1)) - 1
                            var_name = var_match.group(1)

                            if line_num < len(lines):
                                # Replace with underscore if it's an exception variable
                                if var_name == "e" and "except" in lines[line_num]:
                                    lines[line_num] = lines[line_num].replace(
                                        f"except Exception as {var_name}:", "except Exception:"
                                    )
                                elif var_name in lines[line_num] and "=" in lines[line_num]:
                                    # If it's a simple assignment, prefix with underscore
                                    lines[line_num] = lines[line_num].replace(
                                        f"{var_name} =", f"_{var_name} ="
                                    )

                # Write back
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines))

                return True

        except Exception as e:
            print(f"Error fixing unused variables in {file_path}: {e}")

        return False

    def run_black_formatting(self) -> bool:
        """Run black formatter on all Python files."""
        try:
            result = subprocess.run(
                ["black", ".", "--line-length=100"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )
            print("Black formatting completed")
            return result.returncode == 0
        except Exception as e:
            print(f"Error running black: {e}")
            return False

    def run_isort_imports(self) -> bool:
        """Run isort to organize imports."""
        try:
            result = subprocess.run(
                ["isort", ".", "--profile=black"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )
            print("Import sorting completed")
            return result.returncode == 0
        except Exception as e:
            print(f"Error running isort: {e}")
            return False

    def fix_all_files(self):
        """Fix all common issues across all Python files."""
        print("Starting Enhanced Automated Code Fixing...")
        print("=" * 50)

        # Phase 1: Fix missing imports
        print("\nPhase 1: Fixing missing imports...")
        for file_path in self.python_files:
            if "venv" not in str(file_path) and "__pycache__" not in str(file_path):
                self.fix_missing_imports(file_path)

        # Phase 2: Fix unused variables
        print("\nPhase 2: Fixing unused variables...")
        for file_path in self.python_files:
            if "venv" not in str(file_path) and "__pycache__" not in str(file_path):
                self.fix_unused_variables(file_path)

        # Phase 3: Run automated formatters
        print("\nPhase 3: Running automated formatters...")
        self.run_isort_imports()
        self.run_black_formatting()

        print("\nEnhanced automated fixing completed!")


def main():
    """Main function to run enhanced automated fixes."""
    project_root = r"e:\Projects\opt\backend"

    fixer = EnhancedCodeFixer(project_root)
    fixer.fix_all_files()


if __name__ == "__main__":
    main()
