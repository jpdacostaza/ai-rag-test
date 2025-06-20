#!/usr/bin/env python3
import os
import re
import sys
from pathlib import Path
from typing import List

"""

Final Code Cleanup Tool
======================

Fixes the remaining issues from the comprehensive code review:
- Line length issues (split long lines)
- Import order (move imports to top)
- Unused variables (add underscore prefix or remove)
- F-strings without placeholders (convert to regular strings)
- Bare except clauses
"""


class FinalCodeCleaner:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)

    def fix_long_lines(self, content: str) -> str:
        """Fix lines that are too long by adding appropriate line breaks."""
        lines = content.split("\n")
        fixed_lines = []

        for line in lines:
            if len(line) <= 120:
                fixed_lines.append(line)
                continue

            # Handle function calls with many parameters
            if "(" in line and ")" in line and "=" in line:
                # Split at commas in function parameters
                indent = len(line) - len(line.lstrip())
                if "(" in line:
                    before_paren = line[: line.find("(") + 1]
                    after_paren = line[line.find("(") + 1 :]
                    if ")" in after_paren:
                        params = after_paren[: after_paren.rfind(")")]
                        closing = after_paren[after_paren.rfind(")") :]

                        if "," in params:
                            param_list = [p.strip() for p in params.split(",")]
                            if len(param_list) > 1:
                                fixed_lines.append(before_paren)
                                for i, param in enumerate(param_list):
                                    if i == len(param_list) - 1:
                                        fixed_lines.append(" " * (indent + 4) + param)
                                    else:
                                        fixed_lines.append(" " * (indent + 4) + param + ",")
                                fixed_lines.append(" " * indent + closing)
                                continue

            # Handle string concatenation
            if " + " in line and '"' in line:
                parts = line.split(" + ")
                if len(parts) > 1:
                    indent = len(line) - len(line.lstrip())
                    fixed_lines.append(parts[0] + " + \\")
                    for part in parts[1:]:
                        fixed_lines.append(" " * (indent + 4) + part.strip())
                    continue

            # Simple fallback: break at 120 chars with backslash
            if len(line) > 120:
                indent = len(line) - len(line.lstrip())
                # Find a good place to break (space, comma, etc.)
                break_points = [i for i, c in enumerate(line[:120]) if c in " ,=+"]
                if break_points:
                    break_point = max(break_points)
                    fixed_lines.append(line[:break_point] + " \\")
                    fixed_lines.append(" " * (indent + 4) + line[break_point:].lstrip())
                else:
                    fixed_lines.append(line)  # Can't break it nicely
            else:
                fixed_lines.append(line)

        return "\n".join(fixed_lines)

    def fix_import_order(self, content: str) -> str:
        """Move imports to the top of the file."""
        lines = content.split("\n")
        imports = []
        other_lines = []
        docstring_ended = False
        in_docstring = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Handle docstrings at the start
            if i == 0 and stripped.startswith('"""'):
                if stripped.count('"""') == 2:  # Single line docstring
                    docstring_ended = True
                else:
                    in_docstring = True
                other_lines.append(line)
            elif in_docstring:
                other_lines.append(line)
                if '"""' in line:
                    in_docstring = False
                    docstring_ended = True
            elif not docstring_ended and (stripped.startswith("#") or stripped == ""):
                other_lines.append(line)
            elif stripped.startswith(("import ", "from ")) and "sys.path" not in line:
                imports.append(line)
            else:
                if not docstring_ended and stripped:
                    docstring_ended = True
                other_lines.append(line)

        if imports:
            # Find where to insert imports (after docstring/comments)
            insert_pos = 0
            for i, line in enumerate(other_lines):
                if line.strip() and not line.strip().startswith("#") and '"""' not in line:
                    insert_pos = i
                    break

            # Insert imports
            result = other_lines[:insert_pos] + imports + [""] + other_lines[insert_pos:]
        else:
            result = other_lines

        return "\n".join(result)

    def fix_unused_variables(self, content: str) -> str:
        """Prefix unused variables with underscore."""
        # This is a simple fix - more complex analysis would be needed for thorough cleanup
        lines = content.split("\n")
        fixed_lines = []

        for line in lines:
            # Fix common unused variable patterns
            if "local variable" in line and "assigned to but never used" in line:
                continue  # Skip comment lines

            # Fix unused variables in assignments
            line = re.sub(r"(\s+)([a-zA-Z_][a-zA-Z0-9_]*)\s*=", r"\1_\2 =", line)

            fixed_lines.append(line)

        return "\n".join(fixed_lines)

    def fix_f_strings(self, content: str) -> str:
        """Convert f-strings without placeholders to regular strings."""
        # Simple regex to find f-strings without {} placeholders
        content = re.sub(r'"([^"]*)"(?![^"]*\{)', r'"\1"', content)
        content = re.sub(r"'([^']*)'(?![^']*\{)", r"'\1'", content)
        return content

    def fix_bare_except(self, content: str) -> str:
        """Fix bare except clauses."""
        lines = content.split("\n")
        fixed_lines = []

        for line in lines:
            if "except:" in line and "except Exception:" not in line:
                line = line.replace("except:", "except Exception:")
            fixed_lines.append(line)

        return "\n".join(fixed_lines)

    def fix_file(self, file_path: Path) -> bool:
        """Apply all fixes to a single file."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            original_content = content

            # Apply fixes in order
            content = self.fix_f_strings(content)
            content = self.fix_bare_except(content)
            content = self.fix_import_order(content)
            content = self.fix_long_lines(content)

            # Only write if content changed
            if content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print("✓ Fixed {file_path.name}")
                return True
            else:
                print("→ {file_path.name} (no changes needed)")
                return False

        except Exception:
            print("✗ Error processing {file_path.name}: {e}")
            return False

    def fix_specific_issues(self):
        """Fix known specific issues from the report."""

        # Files with specific issues to fix
        specific_fixes = {
            "adaptive_learning.py": self.fix_adaptive_learning,
            "ai_tools.py": self.fix_ai_tools,
            "main.py": self.fix_main_py,
            "human_logging.py": self.fix_human_logging,
        }

        for filename, fix_func in specific_fixes.items():
            file_path = self.project_root / filename
            if file_path.exists():
                print("\n🔧 Applying specific fixes to {filename}")
                fix_func(file_path)

    def fix_adaptive_learning(self, file_path: Path):
        """Fix specific issues in adaptive_learning.py."""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Fix the long line at 297
        content = content.replace(
            'learning_data["questions_attempted"], learning_data["questions_correct"]',
            'learning_data["questions_attempted"],\n                learning_data["questions_correct"]',
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("  ✓ Fixed long line")

    def fix_ai_tools(self, file_path: Path):
        """Fix specific issues in ai_tools.py."""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Fix spacing issues
        content = re.sub(r",([^\s])", r", \1", content)

        # Fix bare except
        content = content.replace("except:", "except Exception:")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("  ✓ Fixed spacing and except clause")

    def fix_main_py(self, file_path: Path):
        """Fix specific issues in main.py."""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Remove unused global declarations
        lines = content.split("\n")
        fixed_lines = []

        for line in lines:
            if "global _model_cache" in line and line.strip().startswith("global"):
                # Skip unused global declarations
                continue
            fixed_lines.append(line)

        content = "\n".join(fixed_lines)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("  ✓ Removed unused global declarations")

    def fix_human_logging(self, file_path: Path):
        """Fix specific issues in human_logging.py."""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Break long lines in human_logging.py
        lines = content.split("\n")
        fixed_lines = []

        for line in lines:
            if len(line) > 120 and "logging.info" in line:
                # Split logging statements
                indent = len(line) - len(line.lstrip())
                if '("' in line:
                    before_msg = line[: line.find('(f"') + 3]
                    message = line[line.find('("') + 3 : line.rfind('"')]
                    ____________after_msg = line[line.rfind('"') :]

                    # Split message at logical points
                    if len(message) > 80:
                        words = message.split()
                        chunks = []
                        current_chunk = []
                        current_length = 0

                        for word in words:
                            if current_length + len(word) + 1 > 60:
                                chunks.append(" ".join(current_chunk))
                                current_chunk = [word]
                                current_length = len(word)
                            else:
                                current_chunk.append(word)
                                current_length += len(word) + 1

                        if current_chunk:
                            chunks.append(" ".join(current_chunk))

                        if len(chunks) > 1:
                            fixed_lines.append(before_msg + chunks[0] + ' " + \\')
                            for i, chunk in enumerate(chunks[1:], 1):
                                if i == len(chunks) - 1:
                                    fixed_lines.append(" " * (indent + 4) + '"{chunk}"{after_msg}')
                                else:
                                    fixed_lines.append(" " * (indent + 4) + '"{chunk} " + \\')
                        else:
                            fixed_lines.append(line)
                    else:
                        fixed_lines.append(line)
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)

        content = "\n".join(fixed_lines)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("  ✓ Fixed long logging lines")

    def run_cleanup(self):
        """Run the complete cleanup process."""
        print("🚀 Starting Final Code Cleanup")
        print("=" * 50)

        # Find all Python files
        python_files = []
        for root, dirs, files in os.walk(self.project_root):
            if any(skip in root for skip in [".git", "__pycache__", ".venv", "storage"]):
                continue
            for file in files:
                if file.endswith(".py"):
                    python_files.append(Path(root) / file)

        print("Found {len(python_files)} Python files to clean up")

        # Apply general fixes
        print("\n📝 Applying general fixes...")
        fixed_count = 0
        for file_path in python_files:
            if self.fix_file(file_path):
                fixed_count += 1

        # Apply specific fixes
        self.fix_specific_issues()

        print("\n✅ Cleanup complete!")
        print("Files processed: {len(python_files)}")
        print("Files modified: {fixed_count}")


def main():
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = "."

    cleaner = FinalCodeCleaner(project_root)
    cleaner.run_cleanup()


if __name__ == "__main__":
    main()
