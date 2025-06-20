#!/usr/bin/env python3
"""
Multi-Pass Code Quality Fixer
Runs multiple automated tools in sequence to fix code quality issues.
"""

import subprocess
import sys
from pathlib import Path


class MultiPassFixer:
    """Runs multiple passes of automated code fixing tools."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)

    def run_command(self, cmd: list, description: str) -> bool:
        """Run a command and return success status."""
        try:
            print(f"Running: {description}")
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            if result.returncode == 0:
                print(f"  ✓ {description} completed successfully")
                return True
            else:
                print(f"  ⚠ {description} completed with warnings")
                if result.stdout:
                    print(f"    stdout: {result.stdout[:200]}...")
                if result.stderr:
                    print(f"    stderr: {result.stderr[:200]}...")
                return False
        except Exception as e:
            print(f"  ✗ Error running {description}: {e}")
            return False

    def fix_specific_files(self):
        """Fix specific high-priority files manually."""
        high_priority_files = [
            "adaptive_learning.py",
            "cache_manager.py",
            "enhanced_document_processing.py",
            "enhanced_integration.py",
            "database_manager.py",
            "error_handler.py",
            "watchdog.py",
        ]

        for filename in high_priority_files:
            file_path = self.project_root / filename
            if file_path.exists():
                print(f"\nFixing high-priority file: {filename}")

                # Run autopep8 for basic fixes
                self.run_command(
                    ["autopep8", "--in-place", "--aggressive", "--aggressive", str(file_path)],
                    f"autopep8 on {filename}",
                )

                # Run autoflake to remove unused imports
                self.run_command(
                    [
                        "autoflake",
                        "--in-place",
                        "--remove-all-unused-imports",
                        "--remove-unused-variables",
                        str(file_path),
                    ],
                    f"autoflake on {filename}",
                )

    def run_all_fixes(self):
        """Run all automated fixes in sequence."""
        print("Multi-Pass Code Quality Fixing")
        print("=" * 50)

        # Phase 1: Install missing tools if needed
        print("\nPhase 1: Installing missing tools...")
        tools_to_install = ["autopep8", "autoflake", "isort", "black"]
        for tool in tools_to_install:
            self.run_command([sys.executable, "-m", "pip", "install", tool], f"Installing {tool}")

        # Phase 2: Fix specific high-priority files
        print("\nPhase 2: Fixing high-priority files...")
        self.fix_specific_files()

        # Phase 3: Run autoflake on all files
        print("\nPhase 3: Removing unused imports and variables...")
        self.run_command(
            [
                "autoflake",
                "--in-place",
                "--recursive",
                "--remove-all-unused-imports",
                "--remove-unused-variables",
                ".",
            ],
            "autoflake on all files",
        )

        # Phase 4: Run autopep8 on all files
        print("\nPhase 4: Applying PEP8 fixes...")
        self.run_command(
            ["autopep8", "--in-place", "--aggressive", "--aggressive", "--recursive", "."],
            "autopep8 on all files",
        )

        # Phase 5: Sort imports
        print("\nPhase 5: Sorting imports...")
        self.run_command(
            ["isort", ".", "--profile=black", "--force-single-line-imports"], "isort import sorting"
        )

        # Phase 6: Apply black formatting
        print("\nPhase 6: Applying black formatting...")
        self.run_command(["black", ".", "--line-length=100"], "black code formatting")

        print("\n" + "=" * 50)
        print("Multi-pass fixing completed!")
        print("Run the comprehensive code review again to see improvements.")


def main():
    """Main function."""
    project_root = r"e:\Projects\opt\backend"

    fixer = MultiPassFixer(project_root)
    fixer.run_all_fixes()


if __name__ == "__main__":
    main()
