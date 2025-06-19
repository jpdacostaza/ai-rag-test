#!/usr/bin/env python3
"""
Final Code Quality Assessment and Roadmap
Provides actionable next steps for completing code quality improvements.
"""

import subprocess
from collections import defaultdict
from pathlib import Path


def analyze_remaining_issues():
    """Analyze and categorize remaining flake8 issues."""
    print("🔍 Analyzing remaining code quality issues...")

    result = subprocess.run(
        ["python", "-m", "flake8", "--max-line-length=88", "--exclude=storage", "."],
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
    )

    if result.returncode != 0:
        issues_by_type = defaultdict(list)
        files_with_issues = defaultdict(list)

        for line in result.stdout.strip().split("\n"):
            if ":" in line and any(code in line for code in ["E", "F", "W"]):
                parts = line.split(":")
                if len(parts) >= 4:
                    file_path = parts[0].strip(".")
                    line_num = parts[1]
                    error_code = parts[3].split()[0]
                    message = ":".join(parts[3:])

                    issues_by_type[error_code].append(
                        {"file": file_path, "line": line_num, "message": message}
                    )
                    files_with_issues[file_path].append(error_code)

        return issues_by_type, files_with_issues

    return {}, {}


def generate_priority_roadmap(issues_by_type, files_with_issues):
    """Generate a prioritized roadmap for fixing remaining issues."""
    print("\n📋 COMPREHENSIVE CODE QUALITY ROADMAP")
    print("=" * 60)

    # Sort issues by frequency
    sorted_issues = sorted(
        issues_by_type.items(), key=lambda x: len(x[1]), reverse=True
    )

    print(f"\n📊 CURRENT STATUS:")
    print(
        f"   Total remaining issues: {sum(len(issues) for issues in issues_by_type.values())}"
    )
    print(f"   Files affected: {len(files_with_issues)}")
    print(f"   Issue types: {len(issues_by_type)}")

    print(f"\n🎯 PRIORITY 1: AUTOMATED FIXES (High Impact, Low Effort)")
    print("-" * 50)

    # E501 - Line too long
    if "E501" in issues_by_type:
        count = len(issues_by_type["E501"])
        print(f"1. 📏 Line Length Violations (E501): {count} instances")
        print("   Action: Break long lines manually")
        print("   Tools: Use autopep8 --max-line-length=88")
        print("   Effort: 2-4 hours")

        # Show top files with most E501 violations
        e501_files = defaultdict(int)
        for issue in issues_by_type["E501"]:
            e501_files[issue["file"]] += 1

        print("   Priority Files:")
        for file_path, count in sorted(
            e501_files.items(), key=lambda x: x[1], reverse=True
        )[:5]:
            print(f"     - {file_path}: {count} violations")

    print(f"\n🎯 PRIORITY 2: MANUAL CODE REVIEW (Medium Impact, Medium Effort)")
    print("-" * 50)

    # E402 - Module level import not at top
    if "E402" in issues_by_type:
        count = len(issues_by_type["E402"])
        print(f"2. 📥 Import Organization (E402): {count} instances")
        print("   Action: Move imports to top of files")
        print("   Focus: main.py and other complex files")
        print("   Effort: 1-2 hours")

    # E722 - Bare except
    if "E722" in issues_by_type:
        count = len(issues_by_type["E722"])
        print(f"3. 🛡️  Exception Handling (E722): {count} instances")
        print("   Action: Replace bare except with specific exceptions")
        print("   Review: Each case needs business logic consideration")
        print("   Effort: 1-2 hours")

    # F841 - Local variable assigned but never used
    if "F841" in issues_by_type:
        count = len(issues_by_type["F841"])
        print(f"4. 🗑️  Unused Variables (F841): {count} instances")
        print("   Action: Remove or prefix with underscore")
        print("   Review: Check if variables are needed for business logic")
        print("   Effort: 30 minutes")

    print(f"\n🎯 PRIORITY 3: ARCHITECTURAL REVIEW (Low Impact, High Effort)")
    print("-" * 50)

    # F824 - Global variable assignment
    if "F824" in issues_by_type:
        count = len(issues_by_type["F824"])
        print(f"5. 🌐 Global Variables (F824): {count} instances")
        print("   Action: Review global state management")
        print("   Consideration: May be intentional architecture choice")
        print("   Effort: 15 minutes (review only)")

    print(f"\n🔧 IMMEDIATE ACTION PLAN (Next 4-6 Hours)")
    print("-" * 50)

    print("Hour 1-2: Line Length Fixes")
    print("  □ Focus on files with most E501 violations")
    print("  □ Use automated tools where possible")
    print("  □ Break complex expressions and long strings")

    print("\nHour 3: Import Organization")
    print("  □ Fix E402 violations in main.py")
    print("  □ Move conditional imports where appropriate")
    print("  □ Organize import sections")

    print("\nHour 4: Exception Handling")
    print("  □ Replace bare except clauses")
    print("  □ Add specific exception types")
    print("  □ Improve error handling logic")

    print("\nHour 5: Variable Cleanup")
    print("  □ Remove truly unused variables")
    print("  □ Prefix intentionally unused with underscore")
    print("  □ Review business logic implications")

    print("\nHour 6: Final Validation")
    print("  □ Run complete flake8 check")
    print("  □ Apply black and isort one final time")
    print("  □ Update documentation")

    print(f"\n🛠️  AUTOMATION COMMANDS")
    print("-" * 50)

    print("# Line length fixes (semi-automated):")
    print("autopep8 --max-line-length=88 --in-place --recursive .")

    print("\n# Final formatting:")
    print("black --line-length 88 .")
    print("isort --profile black .")

    print("\n# Validation:")
    print("python -m flake8 --max-line-length=88 --exclude=storage .")

    print(f"\n📈 EXPECTED OUTCOME")
    print("-" * 50)
    current_issues = sum(len(issues) for issues in issues_by_type.values())
    estimated_remaining = max(20, current_issues // 10)  # Estimate ~90% reduction

    print(f"Current issues: {current_issues}")
    print(f"Estimated after fixes: {estimated_remaining}")
    print(
        f"Expected improvement: {((current_issues - estimated_remaining) / current_issues * 100):.1f}%"
    )
    print(f"Code quality score: 95%+")

    print(f"\n🎉 SUCCESS CRITERIA")
    print("-" * 50)
    print("✅ <50 total flake8 violations")
    print("✅ <10 E501 line length violations")
    print("✅ 0 E402 import organization issues")
    print("✅ 0 E722 bare except clauses")
    print("✅ <5 F841 unused variables")
    print("✅ All critical files fully compliant")


def show_file_priorities(files_with_issues):
    """Show which files need the most attention."""
    print(f"\n📁 FILES REQUIRING ATTENTION")
    print("-" * 50)

    # Sort files by number of issues
    file_priorities = [
        (file_path, len(issues)) for file_path, issues in files_with_issues.items()
    ]
    file_priorities.sort(key=lambda x: x[1], reverse=True)

    print("Top 10 files with most issues:")
    for i, (file_path, issue_count) in enumerate(file_priorities[:10], 1):
        print(f"{i:2d}. {file_path}: {issue_count} issues")


def main():
    """Main execution function."""
    print("🚀 FINAL CODE QUALITY ASSESSMENT")
    print("=" * 60)

    issues_by_type, files_with_issues = analyze_remaining_issues()

    if not issues_by_type:
        print("🎉 CONGRATULATIONS! No flake8 issues found!")
        print("✅ Code quality review completed successfully!")
        return

    generate_priority_roadmap(issues_by_type, files_with_issues)
    show_file_priorities(files_with_issues)

    print(f"\n💡 NEXT STEPS")
    print("-" * 50)
    print("1. Follow the immediate action plan above")
    print("2. Use the automation commands provided")
    print("3. Validate fixes with flake8 after each step")
    print("4. Update the code quality report")
    print("5. Set up pre-commit hooks for future maintenance")


if __name__ == "__main__":
    main()
