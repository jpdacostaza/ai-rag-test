#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict
from typing import List
from typing import Optional

"""

Automated Code Fixing Tool
==========================

This script automatically fixes common code quality issues found by the comprehensive_code_review.py script.
It handles:
1. Removing unused imports
2. Fixing whitespace and trailing spaces
3. Applying Black formatting
4. Basic PEP8 compliance fixes

Usage: python auto_code_fix.py [--dry-run] [--specific-file FILE]
"""


class AutoCodeFixer:
    def __init__(self, project_root: str, dry_run: bool = False):
        self.project_root = Path(project_root)
        self.dry_run = dry_run
        self.fixes_applied = {}

    def find_python_files(self) -> List[Path]:
        """Find all Python files in the project."""
        python_files = []
        for root, dirs, files in os.walk(self.project_root):
            # Skip certain directories
            if any(
                skip in root for skip in [".git", "__pycache__", ".venv", "node_modules", "storage"]
            ):
                continue
            for file in files:
                if file.endswith(".py"):
                    python_files.append(Path(root) / file)
        return python_files

    def run_command(self, command: List[str], cwd: Optional[str] = None) -> tuple:
        """Run a command and return stdout, stderr, return_code."""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=cwd or self.project_root,
                encoding="utf-8",
                errors="replace",
            )
            return result.stdout, result.stderr, result.returncode
        except Exception as e:
            return "", str(e), 1

    def remove_unused_imports(self, file_path: Path) -> int:
        """Remove unused imports from a Python file."""
        print("Checking unused imports in {file_path.name}...")

        # Use autoflake to remove unused imports
        cmd = ["autoflake", "--remove-all-unused-imports", "--in-place", str(file_path)]
        if self.dry_run:
            cmd.insert(-1, "--check")

        stdout, stderr, returncode = self.run_command(cmd)

        if returncode == 0:
            if not self.dry_run:
                print("  ✓ Removed unused imports from {file_path.name}")
                return 1
            else:
                if "would be modified" in stdout:
                    print("  → Would remove unused imports from {file_path.name}")
                    return 1
        else:
            if "No such file" not in stderr:
                print("  ⚠ Could not process {file_path.name}: {stderr.strip()}")

        return 0

    def fix_whitespace_issues(self, file_path: Path) -> int:
        """Fix whitespace and trailing space issues."""
        if self.dry_run:
            print("Would fix whitespace in {file_path.name}")
            return 0

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            original_content = content

            # Fix trailing whitespace
            lines = content.split("\n")
            fixed_lines = [line.rstrip() for line in lines]

            # Remove multiple consecutive blank lines (keep max 2)
            final_lines = []
            blank_count = 0
            for line in fixed_lines:
                if line.strip() == "":
                    blank_count += 1
                    if blank_count <= 2:
                        final_lines.append(line)
                else:
                    blank_count = 0
                    final_lines.append(line)

            # Ensure file ends with exactly one newline
            while final_lines and final_lines[-1] == "":
                final_lines.pop()
            final_lines.append("")

            new_content = "\n".join(final_lines)

            if new_content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print("  ✓ Fixed whitespace issues in {file_path.name}")
                return 1

        except Exception:
            print("  ⚠ Error fixing whitespace in {file_path.name}: {e}")

        return 0

    def apply_black_formatting(self, file_path: Path) -> int:
        """Apply Black code formatting."""
        print("Applying Black formatting to {file_path.name}...")

        cmd = ["black", "--line-length", "120", str(file_path)]
        if self.dry_run:
            cmd.insert(-1, "--check")

        stdout, stderr, returncode = self.run_command(cmd)

        if returncode == 0:
            if not self.dry_run:
                print("  ✓ Applied Black formatting to {file_path.name}")
                return 1
            else:
                print("  → {file_path.name} is already formatted")
        elif returncode == 1 and self.dry_run:
            print("  → Would reformat {file_path.name}")
            return 1
        else:
            print("  ⚠ Black formatting failed for {file_path.name}: {stderr.strip()}")

        return 0

    def sort_imports(self, file_path: Path) -> int:
        """Sort imports using isort."""
        print("Sorting imports in {file_path.name}...")

        cmd = ["isort", "--profile", "black", "--line-length", "120", str(file_path)]
        if self.dry_run:
            cmd.append("--check-only")

        stdout, stderr, returncode = self.run_command(cmd)

        if returncode == 0:
            if not self.dry_run:
                print("  ✓ Sorted imports in {file_path.name}")
                return 1
            else:
                print("  → {file_path.name} imports are already sorted")
        elif returncode == 1 and self.dry_run:
            print("  → Would sort imports in {file_path.name}")
            return 1
        else:
            if "No such file" not in stderr:
                print("  ⚠ Import sorting failed for {file_path.name}: {stderr.strip()}")

        return 0

    def fix_file(self, file_path: Path) -> Dict[str, int]:
        """Apply all fixes to a single file."""
        fixes = {"unused_imports": 0, "whitespace": 0, "formatting": 0, "import_sorting": 0}

        print("\n🔧 Processing {file_path.relative_to(self.project_root)}")

        # 1. Remove unused imports first
        try:
            fixes["unused_imports"] = self.remove_unused_imports(file_path)
        except Exception:
            print("  ⚠ Error removing unused imports: {e}")

        # 2. Fix whitespace issues
        try:
            fixes["whitespace"] = self.fix_whitespace_issues(file_path)
        except Exception:
            print("  ⚠ Error fixing whitespace: {e}")

        # 3. Sort imports
        try:
            fixes["import_sorting"] = self.sort_imports(file_path)
        except Exception:
            print("  ⚠ Error sorting imports: {e}")

        # 4. Apply Black formatting last
        try:
            fixes["formatting"] = self.apply_black_formatting(file_path)
        except Exception:
            print("  ⚠ Error applying Black formatting: {e}")

        return fixes

    def install_required_tools(self):
        """Install required code formatting tools."""
        tools = ["autoflake", "black", "isort"]

        for tool in tools:
            # Check if tool is installed
            stdout, stderr, returncode = self.run_command([tool, "--version"])
            if returncode != 0:
                print("Installing {tool}...")
                stdout, stderr, returncode = self.run_command(
                    [sys.executable, "-m", "pip", "install", tool]
                )
                if returncode == 0:
                    print("  ✓ Installed {tool}")
                else:
                    print("  ⚠ Failed to install {tool}: {stderr}")
                    return False
            else:
                print("  ✓ {tool} is available")

        return True

    def fix_all_files(self, specific_file: Optional[str] = None):
        """Fix all Python files in the project."""
        print("🚀 Starting Automated Code Fixing")
        print("=" * 50)

        if self.dry_run:
            print("🔍 DRY RUN MODE - No changes will be made")
            print("-" * 50)

        # Install required tools
        print("\n📦 Checking required tools...")
        if not self.install_required_tools():
            print("❌ Failed to install required tools. Exiting.")
            return

        # Get files to process
        if specific_file:
            files_to_process = [Path(specific_file)]
            if not files_to_process[0].exists():
                print("❌ File not found: {specific_file}")
                return
        else:
            files_to_process = self.find_python_files()

        print(f"\n📁 Found {len(files_to_process)} Python files to process")

        total_fixes = {"unused_imports": 0, "whitespace": 0, "formatting": 0, "import_sorting": 0}

        files_processed = 0

        for file_path in files_to_process:
            try:
                file_fixes = self.fix_file(file_path)
                for fix_type, count in file_fixes.items():
                    total_fixes[fix_type] += count
                files_processed += 1

                # Store fixes for this file
                if any(file_fixes.values()):
                    self.fixes_applied[str(file_path)] = file_fixes

            except Exception:
                print("❌ Error processing {file_path}: {e}")

        # Print summary
        print("\n" + "=" * 50)
        print("📊 SUMMARY")
        print("=" * 50)
        print("Files processed: {files_processed}")
        print("Files with fixes: {len(self.fixes_applied)}")

        if self.dry_run:
            print("\n🔍 CHANGES THAT WOULD BE MADE:")
        else:
            print("\n✅ FIXES APPLIED:")

        for fix_type, count in total_fixes.items():
            if count > 0:
                print("  {fix_type.replace('_', ' ').title()}: {count} files")

        if not any(total_fixes.values()):
            print("  No fixes needed - code is already clean! ✨")

        print("\nMode: {'DRY RUN' if self.dry_run else 'LIVE CHANGES'}")


def main():
    parser = argparse.ArgumentParser(description="Automatically fix common code quality issues")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be changed without making changes"
    )
    parser.add_argument("--specific-file", help="Fix only a specific file")
    parser.add_argument("--project-root", default=".", help="Project root directory")

    args = parser.parse_args()
    # Determine project root
    if args.specific_file:
        specific_file_path = Path(args.specific_file).resolve()
        if not specific_file_path.exists():
            print("❌ File not found: {args.specific_file}")
            sys.exit(1)
        project_root = specific_file_path.parent
        args.specific_file = str(specific_file_path)
    else:
        project_root = Path(args.project_root).resolve()
        if not project_root.exists():
            print("❌ Project root does not exist: {project_root}")
            sys.exit(1)

    # Create fixer and run
    fixer = AutoCodeFixer(str(project_root), dry_run=args.dry_run)
    fixer.fix_all_files(specific_file=args.specific_file)


if __name__ == "__main__":
    main()
