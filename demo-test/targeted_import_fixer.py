#!/usr/bin/env python3
"""
Targeted Import Fixer
Fixes remaining F821 undefined name errors by adding proper imports.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import List


class TargetedImportFixer:
    """Fixes missing imports that weren't caught by the previous script."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)

    def get_f821_errors(self, file_path: Path) -> List[str]:
        """Get all F821 undefined name errors for a file."""
        try:
            result = subprocess.run(
                ["flake8", "--select=F821", str(file_path)],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            undefined_names = []
            for line in result.stdout.split("\n"):
                if "F821" in line and "undefined name" in line:
                    match = re.search(r"undefined name '([^']*)'", line)
                    if match:
                        undefined_names.append(match.group(1))

            return list(set(undefined_names))  # Remove duplicates
        except Exception as e:
            print(f"Error getting F821 errors for {file_path}: {e}")
            return []

    def fix_specific_imports(self, file_path: Path) -> bool:
        """Fix specific missing imports for a file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            undefined_names = self.get_f821_errors(file_path)
            if not undefined_names:
                return False

            print(
                f"Fixing {len(undefined_names)} undefined names in {file_path.name}: {undefined_names}"
            )

            # Mapping of undefined names to import statements
            import_map = {
                "Enum": "from enum import Enum",
                "dataclass": "from dataclasses import dataclass",
                "datetime": "from datetime import datetime",
                "Optional": "from typing import Optional",
                "List": "from typing import List",
                "Dict": "from typing import Dict",
                "Any": "from typing import Any",
                "Union": "from typing import Union",
                "Tuple": "from typing import Tuple",
                "Callable": "from typing import Callable",
                "asyncio": "import asyncio",
                "json": "import json",
                "os": "import os",
                "sys": "import sys",
                "re": "import re",
                "time": "import time",
                "logging": "import logging",
                "sqlite3": "import sqlite3",
                "threading": "import threading",
                "uuid": "import uuid",
                "Path": "from pathlib import Path",
                "defaultdict": "from collections import defaultdict",
                "deque": "from collections import deque",
                # Project-specific imports - these will need manual fixing
                "log_service_status": "# from human_logging import log_service_status",
                "get_embedding": "# from database import get_embedding",
                "db_manager": "# from database import db_manager",
                "retrieve_user_memory": "# from database import retrieve_user_memory",
                "index_document_chunks": "# from database import index_document_chunks",
                "MemoryErrorHandler": "# from error_handler import MemoryErrorHandler",
            }

            lines = content.split("\n")
            new_imports = []

            # Find import section
            import_end = 0
            for i, line in enumerate(lines):
                if line.strip().startswith(("import ", "from ")) or line.strip().startswith("#"):
                    import_end = i + 1
                elif line.strip() and not line.startswith('"""') and not line.startswith("'''"):
                    break

            # Add missing imports
            for name in undefined_names:
                if name in import_map:
                    import_stmt = import_map[name]
                    if import_stmt not in content and not any(
                        name in line for line in lines[:import_end]
                    ):
                        new_imports.append(import_stmt)

            if new_imports:
                # Insert at the end of import section
                for import_stmt in reversed(new_imports):
                    lines.insert(import_end, import_stmt)

                # Write back
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines))

                print(f"  Added {len(new_imports)} imports")
                return True

        except Exception as e:
            print(f"Error fixing imports in {file_path}: {e}")

        return False

    def fix_all_f821_errors(self):
        """Fix all F821 errors across the project."""
        print("Fixing F821 (undefined name) errors...")
        print("=" * 50)

        python_files = []
        for root, _, files in os.walk(self.project_root):
            for file in files:
                if file.endswith(".py") and "venv" not in root and "__pycache__" not in root:
                    # Skip the problematic file with long path
                    if "sentence-transformers" not in root:
                        python_files.append(Path(root) / file)

        fixed_count = 0
        for file_path in python_files:
            if self.fix_specific_imports(file_path):
                fixed_count += 1

        print(f"\nFixed imports in {fixed_count} files")


def main():
    """Main function."""
    project_root = r"e:\Projects\opt\backend"

    fixer = TargetedImportFixer(project_root)
    fixer.fix_all_f821_errors()


if __name__ == "__main__":
    main()
