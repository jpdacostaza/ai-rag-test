#!/usr/bin/env python3
"""
Comprehensive Code Review Script
===============================

This script performs a systematic code quality review of the entire codebase:
- Runs flake8, black, pylint on all Python files
- Generates a comprehensive report of all issues
- Categorizes issues by severity and type
- Provides recommendations for fixes
"""

import datetime
import os
import subprocess
from pathlib import Path
from typing import Dict
from typing import List


class CodeReviewAnalyzer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.issues = {
            "flake8": {},
            "black": {},
            "pylint": {},
        }
        self.python_files = []

    def find_python_files(self) -> List[Path]:
        """Find all Python files in the project."""
        python_files = []
        for root, dirs, files in os.walk(self.project_root):
            # Skip certain directories
            dirs[:] = [
                d for d in dirs if d not in [".git", "__pycache__", ".venv", "venv", "node_modules"]
            ]

            for file in files:
                if file.endswith(".py"):
                    file_path = Path(root) / file
                    python_files.append(file_path)

        return sorted(python_files)

    def run_flake8(self, file_path: Path) -> List[str]:
        """Run flake8 on a file and return issues."""
        try:
            cmd = [
                "C:/Users/jdaco/AppData/Local/Programs/Python/Python312/python.exe",
                "-m",
                "flake8",
                str(file_path),
                "--max-line-length=120",
                "--extend-ignore=E203,W503",  # Ignore some common issues
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            if result.stdout:
                return result.stdout.strip().split("\n")
            return []
        except Exception:
            return ["Error running flake8: {e}"]

    def run_black_check(self, file_path: Path) -> List[str]:
        """Run black check on a file and return issues."""
        try:
            cmd = [
                "C:/Users/jdaco/AppData/Local/Programs/Python/Python312/python.exe",
                "-m",
                "black",
                "--check",
                "--dif",
                str(file_path),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            if result.returncode != 0:
                return [f"Black formatting issues found"]
            return []
        except Exception:
            return ["Error running black: {e}"]

    def run_pylint(self, file_path: Path) -> List[str]:
        """Run pylint on a file and return issues."""
        try:
            cmd = [
                "C:/Users/jdaco/AppData/Local/Programs/Python/Python312/python.exe",
                "-m",
                "pylint",
                str(file_path),
                "--disable=C0111,C0103,R0903,R0913,W0613,C0301",  # Disable some verbose warnings
                "--output-format=text",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            if result.stdout:
                lines = result.stdout.strip().split("\n")
                # Filter out just the issue lines
                issues = [
                    line
                    for line in lines
                    if ":" in line and ("error" in line.lower() or "warning" in line.lower())
                ]
                return issues
            return []
        except Exception:
            return ["Error running pylint: {e}"]

    def analyze_file(self, file_path: Path) -> Dict[str, List[str]]:
        """Analyze a single file with all tools."""
        print(f"Analyzing: {file_path.relative_to(self.project_root)}")

        file_issues = {
            "flake8": self.run_flake8(file_path),
            "black": self.run_black_check(file_path),
            "pylint": self.run_pylint(file_path),
        }

        return file_issues

    def analyze_all_files(self):
        """Analyze all Python files in the project."""
        self.python_files = self.find_python_files()

        print(f"Found {len(self.python_files)} Python files to analyze")
        print("=" * 60)

        for file_path in self.python_files:
            file_issues = self.analyze_file(file_path)
            rel_path = str(file_path.relative_to(self.project_root))

            for tool, issues in file_issues.items():
                if issues:
                    self.issues[tool][rel_path] = issues

    def categorize_issues(self) -> Dict[str, Dict[str, int]]:
        """Categorize issues by type and severity."""
        categories = {
            "critical": {"count": 0, "types": {}},
            "error": {"count": 0, "types": {}},
            "warning": {"count": 0, "types": {}},
            "style": {"count": 0, "types": {}},
        }

        # Flake8 error code mappings
        flake8_severity = {
            "E": "error",  # Error codes
            "W": "warning",  # Warning codes
            "F": "error",  # Pyflakes codes
            "C": "style",  # McCabe complexity
            "N": "style",  # pep8-naming
        }

        for tool, file_issues in self.issues.items():
            for file_path, issues in file_issues.items():
                for issue in issues:
                    if tool == "flake8" and ":" in issue:
                        # Extract error code (e.g., E501, W293)
                        parts = issue.split(":")
                        if len(parts) >= 4:
                            error_code = parts[3].strip().split()[0]
                            if error_code:
                                severity = flake8_severity.get(error_code[0], "style")
                                categories[severity]["count"] += 1
                                categories[severity]["types"][error_code] = (
                                    categories[severity]["types"].get(error_code, 0) + 1
                                )
                    elif tool == "pylint":
                        if "error" in issue.lower():
                            categories["error"]["count"] += 1
                        elif "warning" in issue.lower():
                            categories["warning"]["count"] += 1
                        else:
                            categories["style"]["count"] += 1
                    elif tool == "black":
                        categories["style"]["count"] += 1

        return categories

    def generate_report(self) -> str:
        """Generate a comprehensive report."""
        report = []
        report.append("COMPREHENSIVE CODE REVIEW REPORT")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Project: {self.project_root}")
        report.append(f"Files analyzed: {len(self.python_files)}")
        report.append("")

        # Summary statistics
        total_issues = sum(
            len(issues) for tool_issues in self.issues.values() for issues in tool_issues.values()
        )
        affected_files = set()
        for tool_issues in self.issues.values():
            affected_files.update(tool_issues.keys())

        report.append("SUMMARY")
        report.append("-" * 20)
        report.append(f"Total issues found: {total_issues}")
        report.append(f"Files with issues: {len(affected_files)} of {len(self.python_files)}")
        report.append("")

        # Issue categorization
        categories = self.categorize_issues()
        report.append("ISSUE BREAKDOWN BY SEVERITY")
        report.append("-" * 30)
        for severity, data in categories.items():
            if data["count"] > 0:
                report.append(f"{severity.upper()}: {data['count']} issues")
                if isinstance(data["types"], dict):
                    top_types = sorted(data["types"].items(), key=lambda x: x[1], reverse=True)[:5]
                    for issue_type, count in top_types:
                        report.append(f"  - {issue_type}: {count}")
        report.append("")

        # Detailed issues by tool
        for tool, tool_issues in self.issues.items():
            if tool_issues:
                report.append(f"{tool.upper()} ISSUES")
                report.append("-" * 20)

                for file_path, issues in sorted(tool_issues.items()):
                    report.append(f"\n{file_path}:")
                    for issue in issues:
                        report.append(f"  - {issue}")

                report.append("")

        # Recommendations
        report.append("RECOMMENDATIONS")
        report.append("-" * 20)
        report.append("1. Fix critical errors first (F-codes, syntax errors)")
        report.append("2. Address style issues with automated tools (black, isort)")
        report.append("3. Fix line length and whitespace issues")
        report.append("4. Remove unused imports and variables")
        report.append("5. Add proper type hints where missing")
        report.append("6. Consider adding docstrings for public functions")
        report.append("")

        # Priority files (most issues)
        file_issue_counts = {}
        for tool_issues in self.issues.values():
            for file_path, issues in tool_issues.items():
                file_issue_counts[file_path] = file_issue_counts.get(file_path, 0) + len(issues)

        if file_issue_counts:
            report.append("PRIORITY FILES (most issues)")
            report.append("-" * 30)
            priority_files = sorted(file_issue_counts.items(), key=lambda x: x[1], reverse=True)[
                :10
            ]
            for file_path, count in priority_files:
                report.append(f"{file_path}: {count} issues")

        return "\n".join(report)


def main():
    """Main function to run the comprehensive code review."""
    project_root = r"e:\Projects\opt\backend"

    print("Starting Comprehensive Code Review...")
    print("=" * 50)

    analyzer = CodeReviewAnalyzer(project_root)
    analyzer.analyze_all_files()

    # Generate and save report
    report = analyzer.generate_report()

    # Save to file
    report_path = Path(project_root) / "readme" / "COMPREHENSIVE_CODE_REVIEW_REPORT.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nReport saved to: {report_path}")
    print("\nReport Summary:")
    print("-" * 20)

    # Print just the summary part
    lines = report.split("\n")
    summary_start = lines.index("SUMMARY")
    summary_end = next(
        i
        for i, line in enumerate(lines[summary_start:], summary_start)
        if line.startswith("ISSUE BREAKDOWN")
    )

    for line in lines[summary_start:summary_end]:
        print(line)


if __name__ == "__main__":
    main()
