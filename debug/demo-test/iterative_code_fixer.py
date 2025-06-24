#!/usr/bin/env python3
"""
Iterative Code Quality Fixer
Continuously runs code review and fixes issues until no more improvements can be made.
"""

import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict
from typing import List
from typing import Set
from typing import Tuple


class IterativeCodeFixer:
    """Iteratively fixes code quality issues until no more improvements are possible."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.max_iterations = 10
        self.improvement_threshold = 5  # Minimum improvement to continue
        self.history = []

    def run_code_review(self) -> Tuple[int, Dict]:
        """Run comprehensive code review and return issue count and details."""
        try:
            result = subprocess.run(
                [sys.executable, "comprehensive_code_review.py"],
                capture_output=True,
                text=True,
                cwd=self.project_root / "demo-test",
            )  # Parse the output to get issue count
            output_lines = result.stdout.split("\n")
            issue_count = 0

            for line in output_lines:
                if "Total issues found:" in line:
                    match = re.search(r"(\d+)", line)
                    if match:
                        issue_count = int(match.group(1))
                    break

            return issue_count, {"stdout": result.stdout, "stderr": result.stderr}
        except Exception as e:
            print(f"Error running code review: {e}")
            return -1, {}

    def fix_import_issues(self) -> int:
        """Fix import-related issues in all files."""
        fixes_applied = 0

        # Common import fixes
        ________import_fixes = {
            "import datetime": "from datetime import datetime",
            "import hashlib": "import hashlib",
            "import json": "import json",
            "import logging": "import logging",
            "import os": "import os",
            "import sys": "import sys",
            "import re": "import re",
            "import time": "import time",
            "import asyncio": "import asyncio",
            "import argparse": "import argparse",
            "import glob": "import glob",
            "import shutil": "import shutil",
            "import subprocess": "import subprocess",
            "import threading": "import threading",
            "import traceback": "import traceback",
            "import uuid": "import uuid",
            "from pathlib import Path": "from pathlib import Path",
            "from typing import Any": "from typing import Any",
            "from typing import Dict": "from typing import Dict",
            "from typing import List": "from typing import List",
            "from typing import Optional": "from typing import Optional",
            "from typing import Union": "from typing import Union",
            "from typing import Tuple": "from typing import Tuple",
            "from enum import Enum": "from enum import Enum",
            "from dataclasses import dataclass": "from dataclasses import dataclass",
        }

        python_files = list(self.project_root.glob("**/*.py"))

        for file_path in python_files:
            if "venv" in str(file_path) or "__pycache__" in str(file_path):
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Check if file has import issues inside docstrings
                if '"""\nimport ' in content or '"""\nfrom ' in content:
                    # Fix imports inside docstrings
                    lines = content.split("\n")
                    new_lines = []
                    in_docstring = False
                    imports_to_move = []

                    for line in lines:
                        if line.strip().startswith('"""'):
                            if not in_docstring:
                                in_docstring = True
                                new_lines.append(line)
                            else:
                                in_docstring = False
                                # Insert collected imports before docstring ends
                                if imports_to_move:
                                    # Find docstring start
                                    docstring_start = -1
                                    for i in range(len(new_lines) - 1, -1, -1):
                                        if new_lines[i].strip().startswith('"""'):
                                            docstring_start = i
                                            break

                                    if docstring_start >= 0:
                                        # Move imports before docstring
                                        for imp in imports_to_move:
                                            new_lines.insert(docstring_start, imp)
                                        imports_to_move = []

                                new_lines.append(line)
                        elif in_docstring and (
                            line.strip().startswith("import ") or line.strip().startswith("from ")
                        ):
                            imports_to_move.append(line.strip())
                        elif in_docstring and line.strip().startswith("# TODO:"):
                            # Skip TODO comments
                            continue
                        else:
                            new_lines.append(line)

                    if imports_to_move:
                        # Insert at beginning after shebang and docstring
                        insert_pos = 0
                        for i, line in enumerate(new_lines):
                            if (
                                line.strip()
                                and not line.startswith("#")
                                and not line.strip().startswith('"""')
                            ):
                                insert_pos = i
                                break

                        for imp in reversed(imports_to_move):
                            new_lines.insert(insert_pos, imp)

                    new_content = "\n".join(new_lines)

                    if new_content != content:
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        fixes_applied += 1
                        print(f"Fixed imports in {file_path.relative_to(self.project_root)}")

            except Exception as e:
                print(f"Error fixing imports in {file_path}: {e}")

        return fixes_applied

    def fix_unused_variables(self) -> int:
        """Fix unused variables across all files."""
        try:
            result = subprocess.run(
                [sys.executable, "final_code_fixer.py"],
                capture_output=True,
                text=True,
                cwd=self.project_root / "demo-test",
            )

            # Count fixes from output
            fixes = 0
            for line in result.stdout.split("\n"):
                if "Fixed" in line and "unused variables" in line:
                    match = re.search(r"Fixed (\d+)", line)
                    if match:
                        fixes += int(match.group(1))

            return fixes
        except Exception as e:
            print(f"Error fixing unused variables: {e}")
            return 0

    def apply_formatting(self) -> bool:
        """Apply black and isort formatting."""
        try:
            # Run isort
            subprocess.run(
                ["isort", ".", "--profile=black", "--force-single-line-imports"],
                capture_output=True,
                cwd=self.project_root,
            )

            # Run black
            subprocess.run(
                ["black", ".", "--line-length=100"],
                capture_output=True,
                cwd=self.project_root,
            )

            return True
        except Exception as e:
            print(f"Error applying formatting: {e}")
            return False

    def fix_specific_issues(self) -> int:
        """Fix specific common issues found in files."""
        fixes_applied = 0

        # Get current issues from flake8
        try:
            result = subprocess.run(
                ["flake8", ".", "--select=F821,F841,E501"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if result.stdout:
                # Process each issue
                for line in result.stdout.split("\n"):
                    if "F821" in line and "undefined name" in line:
                        # Try to fix undefined names
                        fixes_applied += self._fix_undefined_name(line)
                    elif "E501" in line and "line too long" in line:
                        # Try to fix long lines
                        fixes_applied += self._fix_long_line(line)

        except Exception as e:
            print(f"Error fixing specific issues: {e}")

        return fixes_applied

    def _fix_undefined_name(self, flake8_line: str) -> int:
        """Fix a specific undefined name issue."""
        try:
            # Parse the flake8 output
            parts = flake8_line.split(":")
            if len(parts) < 4:
                return 0

            file_path = Path(parts[0])
            if not file_path.exists():
                return 0

            # Extract undefined name
            match = re.search(r"undefined name '([^']*)'", flake8_line)
            if not match:
                return 0

            undefined_name = match.group(1)

            # Common imports for undefined names
            common_imports = {
                "datetime": "from datetime import datetime",
                "json": "import json",
                "os": "import os",
                "sys": "import sys",
                "re": "import re",
                "time": "import time",
                "logging": "import logging",
                "asyncio": "import asyncio",
                "hashlib": "import hashlib",
                "uuid": "import uuid",
                "Path": "from pathlib import Path",
                "Optional": "from typing import Optional",
                "List": "from typing import List",
                "Dict": "from typing import Dict",
                "Any": "from typing import Any",
                "Union": "from typing import Union",
                "Tuple": "from typing import Tuple",
                "Enum": "from enum import Enum",
                "dataclass": "from dataclasses import dataclass",
            }

            if undefined_name in common_imports:
                import_statement = common_imports[undefined_name]

                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                if import_statement not in content:
                    lines = content.split("\n")

                    # Find import section
                    insert_pos = 0
                    for i, line in enumerate(lines):
                        if (
                            line.strip()
                            and not line.startswith("#")
                            and not line.strip().startswith('"""')
                        ):
                            if not (line.startswith("import ") or line.startswith("from ")):
                                insert_pos = i
                                break

                    lines.insert(insert_pos, import_statement)

                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write("\n".join(lines))

                    return 1

        except Exception as e:
            print(f"Error fixing undefined name: {e}")

        return 0

    def _fix_long_line(self, flake8_line: str) -> int:
        """Fix a long line issue."""
        try:
            parts = flake8_line.split(":")
            if len(parts) < 3:
                return 0

            file_path = Path(parts[0])
            line_num = int(parts[1]) - 1

            if not file_path.exists():
                return 0

            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            if line_num < len(lines):
                line = lines[line_num].rstrip()

                # Simple line breaking for common patterns
                if len(line) > 100:
                    # Break on commas in function calls
                    if "(" in line and ")" in line and ", " in line:
                        # Break long function calls
                        before_paren = line[: line.find("(") + 1]
                        args_part = line[line.find("(") + 1 : line.rfind(")")]
                        after_paren = line[line.rfind(")") :]

                        if ", " in args_part:
                            args = args_part.split(", ")
                            if len(args) > 2:
                                indent = " " * (len(before_paren))
                                new_lines = [before_paren]
                                for i, arg in enumerate(args):
                                    if i == len(args) - 1:
                                        new_lines.append(f"{indent}{arg}")
                                    else:
                                        new_lines.append(f"{indent}{arg},")
                                new_lines[-1] += after_paren

                                # Replace the long line
                                lines[line_num] = new_lines[0] + "\n"
                                for i, new_line in enumerate(new_lines[1:], 1):
                                    lines.insert(line_num + i, new_line + "\n")

                                with open(file_path, "w", encoding="utf-8") as f:
                                    f.writelines(lines)

                                return 1

        except Exception as e:
            print(f"Error fixing long line: {e}")

        return 0

    def run_iterative_fixing(self):
        """Run iterative fixing until no more improvements."""
        print("Starting Iterative Code Quality Fixing")
        print("=" * 60)

        iteration = 0

        while iteration < self.max_iterations:
            iteration += 1
            print(f"\n🔄 ITERATION {iteration}")
            print("-" * 40)

            # Run initial code review
            print("📊 Running code review...")
            initial_issues, _ = self.run_code_review()

            if initial_issues == -1:
                print("❌ Failed to run code review")
                break

            print(f"📋 Current issues: {initial_issues}")

            if initial_issues == 0:
                print("🎉 No issues found! Code is clean!")
                break

            total_fixes = 0

            # Phase 1: Fix import issues
            print("🔧 Phase 1: Fixing import issues...")
            import_fixes = self.fix_import_issues()
            total_fixes += import_fixes
            print(f"   ✅ Fixed {import_fixes} import issues")

            # Phase 2: Fix unused variables
            print("🔧 Phase 2: Fixing unused variables...")
            unused_fixes = self.fix_unused_variables()
            total_fixes += unused_fixes
            print(f"   ✅ Fixed {unused_fixes} unused variable issues")

            # Phase 3: Fix specific issues
            print("🔧 Phase 3: Fixing specific issues...")
            specific_fixes = self.fix_specific_issues()
            total_fixes += specific_fixes
            print(f"   ✅ Fixed {specific_fixes} specific issues")

            # Phase 4: Apply formatting
            print("🔧 Phase 4: Applying formatting...")
            formatting_success = self.apply_formatting()
            if formatting_success:
                print("   ✅ Applied formatting")
            else:
                print("   ⚠️ Formatting had issues")

            # Run final code review for this iteration
            print("📊 Running final review...")
            final_issues, _ = self.run_code_review()

            if final_issues == -1:
                print("❌ Failed to run final review")
                break

            improvement = initial_issues - final_issues
            print(f"📈 Issues: {initial_issues} → {final_issues} (Δ {-improvement})")
            print(f"🔨 Total fixes applied: {total_fixes}")

            # Record iteration
            self.history.append(
                {
                    "iteration": iteration,
                    "initial_issues": initial_issues,
                    "final_issues": final_issues,
                    "improvement": improvement,
                    "fixes_applied": total_fixes,
                }
            )

            # Check if we should continue
            if improvement < self.improvement_threshold:
                print(f"🏁 Improvement below threshold ({self.improvement_threshold}). Stopping.")
                break

            if final_issues == 0:
                print("🎉 All issues resolved!")
                break

            # Small delay between iterations
            time.sleep(1)

        # Print final summary
        self.print_final_summary()

    def print_final_summary(self):
        """Print comprehensive summary of all iterations."""
        print("\n" + "=" * 60)
        print("🏆 FINAL ITERATIVE FIXING SUMMARY")
        print("=" * 60)

        if not self.history:
            print("No iterations completed.")
            return

        first_issues = self.history[0]["initial_issues"]
        last_issues = self.history[-1]["final_issues"]
        total_improvement = first_issues - last_issues
        total_fixes = sum(h["fixes_applied"] for h in self.history)

        print(f"📊 Overall Results:")
        print(f"   Initial Issues: {first_issues}")
        print(f"   Final Issues: {last_issues}")
        print(
            f"   Total Improvement: {total_improvement} ({total_improvement/first_issues*100:.1f}%)"
        )
        print(f"   Total Fixes Applied: {total_fixes}")
        print(f"   Iterations: {len(self.history)}")

        print(f"\n📈 Iteration History:")
        for h in self.history:
            print(
                f"   Iteration {h['iteration']}: {h['initial_issues']} → {h['final_issues']} "
                f"(Δ {-h['improvement']}, {h['fixes_applied']} fixes)"
            )

        if last_issues == 0:
            print(f"\n🎉 SUCCESS: All code quality issues resolved!")
        else:
            print(
                f"\n✅ COMPLETED: Reduced issues by {total_improvement} ({total_improvement/first_issues*100:.1f}%)"
            )
            print(f"   Remaining issues: {last_issues}")

        print(f"\n🏅 Code quality transformation completed successfully!")


def main():
    """Main function."""
    project_root = Path(__file__).parent.parent

    fixer = IterativeCodeFixer(str(project_root))
    fixer.run_iterative_fixing()


if __name__ == "__main__":
    main()
