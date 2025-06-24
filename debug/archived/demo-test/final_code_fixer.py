#!/usr/bin/env python3
"""
Final Comprehensive Code Fixer
Addresses the remaining specific issues identified in the code review.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Dict
from typing import List


class FinalCodeFixer:
    """Fixes the final remaining code quality issues."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)

    def fix_unused_variables(self, file_path: Path) -> int:
        """Fix unused variables by replacing with underscores."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Get F841 errors
            result = subprocess.run(
                ["flake8", "--select=F841", str(file_path)],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if result.returncode != 0:
                lines = content.split("\n")
                changes = 0

                for line in result.stdout.split("\n"):
                    if "F841" in line and "assigned to but never used" in line:
                        # Extract line number and variable name
                        line_match = re.search(r":(\d+):", line)
                        var_match = re.search(r"'([^']*)'", line)

                        if line_match and var_match:
                            line_num = int(line_match.group(1)) - 1
                            var_name = var_match.group(1)

                            if line_num < len(lines):
                                original_line = lines[line_num]

                                # Handle exception variables
                                if "except" in original_line and f" as {var_name}" in original_line:
                                    lines[line_num] = original_line.replace(f" as {var_name}", "")
                                    changes += 1
                                # Handle assignments
                                elif f"{var_name} =" in original_line:
                                    lines[line_num] = original_line.replace(
                                        f"{var_name} =", f"_{var_name} ="
                                    )
                                    changes += 1
                                # Handle tuple unpacking
                                elif ", " in original_line and var_name in original_line:
                                    lines[line_num] = original_line.replace(
                                        f"{var_name}", f"_{var_name}"
                                    )
                                    changes += 1

                if changes > 0:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write("\n".join(lines))
                    return changes

        except Exception as e:
            print(f"Error fixing unused variables in {file_path}: {e}")

        return 0

    def add_missing_imports(self, file_path: Path) -> int:
        """Add missing imports based on F821 errors."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Get F821 errors
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

                # Import mapping for common undefined names
                import_map = {
                    "hashlib": "import hashlib",
                    "json": "import json",
                    "datetime": "from datetime import datetime",
                    "logging": "import logging",
                    "os": "import os",
                    "sys": "import sys",
                    "re": "import re",
                    "time": "import time",
                    "asyncio": "import asyncio",
                    "threading": "import threading",
                    "argparse": "import argparse",
                    "uuid": "import uuid",
                    "Path": "from pathlib import Path",
                    "glob": "import glob",
                    "shutil": "import shutil",
                    "subprocess": "import subprocess",
                    "traceback": "import traceback",
                    "httpx": "import httpx",
                    "timedelta": "from datetime import timedelta",
                    "asdict": "from dataclasses import asdict",
                    "redis": "import redis",
                    "chromadb": "import chromadb",
                    # Project-specific imports (commented for manual fixing)
                    "log_service_status": "# TODO: from human_logging import log_service_status",
                    "get_embedding": "# TODO: from database import get_embedding",
                    "db_manager": "# TODO: from database import db_manager",
                    "retrieve_user_memory": "# TODO: from database import retrieve_user_memory",
                    "index_document_chunks": "# TODO: from database import index_document_chunks",
                }

                lines = content.split("\n")
                new_imports = []

                # Find where to insert imports (after existing imports)
                insert_pos = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith(("import ", "from ")) or line.strip().startswith(
                        "#"
                    ):
                        insert_pos = i + 1
                    elif line.strip() and not line.startswith('"""') and not line.startswith("'''"):
                        break

                # Add missing imports
                for name in undefined_names:
                    if name in import_map:
                        import_stmt = import_map[name]
                        if import_stmt not in content:
                            new_imports.append(import_stmt)

                if new_imports:
                    # Insert imports
                    for import_stmt in reversed(new_imports):
                        lines.insert(insert_pos, import_stmt)

                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write("\n".join(lines))

                    return len(new_imports)

        except Exception as e:
            print(f"Error adding imports to {file_path}: {e}")

        return 0

    def fix_all_remaining_issues(self):
        """Fix all remaining issues across the project."""
        print("Final Comprehensive Code Fixing")
        print("=" * 50)

        python_files = []
        for root, _, files in os.walk(self.project_root):
            for file in files:
                if (
                    file.endswith(".py")
                    and "venv" not in root
                    and "__pycache__" not in root
                    and "sentence-transformers" not in root
                ):
                    python_files.append(Path(root) / file)

        print(f"Processing {len(python_files)} Python files...")

        total_imports_added = 0
        total_variables_fixed = 0

        for file_path in python_files:
            rel_path = file_path.relative_to(self.project_root)

            # Fix unused variables
            vars_fixed = self.fix_unused_variables(file_path)
            if vars_fixed > 0:
                print(f"  {rel_path}: Fixed {vars_fixed} unused variables")
                total_variables_fixed += vars_fixed

            # Add missing imports
            imports_added = self.add_missing_imports(file_path)
            if imports_added > 0:
                print(f"  {rel_path}: Added {imports_added} imports")
                total_imports_added += imports_added

        print(f"\nSummary:")
        print(f"  Total imports added: {total_imports_added}")
        print(f"  Total unused variables fixed: {total_variables_fixed}")

        # Run final formatting
        print(f"\nRunning final formatting...")
        try:
            subprocess.run(
                ["black", ".", "--line-length=100"], cwd=self.project_root, capture_output=True
            )
            print("  ✓ Black formatting applied")
        except:
            print("  ⚠ Black formatting failed")

        print("\nFinal fixing completed!")


def main():
    """Main function."""
    project_root = r"e:\Projects\opt\backend"

    fixer = FinalCodeFixer(project_root)
    fixer.fix_all_remaining_issues()


if __name__ == "__main__":
    main()
