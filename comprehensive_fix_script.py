#!/usr/bin/env python3
"""
Comprehensive Code Quality Fix Script
Automatically fixes remaining flake8 issues in the codebase.
"""

import re
import subprocess
from pathlib import Path


def run_command(command, description):
    """Run a shell command and return its output."""
    print(f"\n🔧 {description}")
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, cwd=Path.cwd()
        )
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return result.stdout
        else:
            print(f"❌ {description} failed: {result.stderr}")
            return None
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return None


def fix_unused_imports():
    """Remove unused imports using autoflake."""
    print("\n📦 Installing autoflake...")
    install_result = run_command(
        "pip install autoflake", "Installing autoflake for unused import removal"
    )

    if install_result is not None:
        print("\n🧹 Removing unused imports...")
        run_command(
            "autoflake --remove-all-unused-imports --in-place --recursive .",
            "Removing unused imports with autoflake",
        )


def fix_f_string_issues():
    """Fix f-string issues by converting f-strings without placeholders to regular strings."""
    print("\n🔤 Fixing f-string issues...")

    python_files = list(Path(".").rglob("*.py"))
    fixed_count = 0

    for file_path in python_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content

            # Pattern to match f-strings without placeholders
            # Look for "text" or 'text' where text doesn't contain {}
            f_string_pattern = r'f(["\'])((?:(?!\1)[^{}\\]|\\.)*)(\1)'

            def replace_f_string(match):
                quote = match.group(1)
                text = match.group(2)
                # Only replace if there are no {} placeholders
                if "{" not in text and "}" not in text:
                    return f"{quote}{text}{quote}"
                return match.group(0)

            content = re.sub(f_string_pattern, replace_f_string, content)

            if content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                fixed_count += 1
                print(f"   ✅ Fixed f-strings in {file_path}")

        except Exception as e:
            print(f"   ❌ Error processing {file_path}: {e}")

    print(f"\n✅ Fixed f-string issues in {fixed_count} files")


def fix_whitespace_issues():
    """Fix trailing whitespace and blank line issues."""
    print("\n🔲 Fixing whitespace issues...")

    python_files = list(Path(".").rglob("*.py"))
    fixed_count = 0

    for file_path in python_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            original_lines = lines[:]
            modified = False

            # Fix trailing whitespace (W291)
            for i, line in enumerate(lines):
                if line.rstrip() != line.rstrip("\n"):
                    lines[i] = (
                        line.rstrip() + "\n" if line.endswith("\n") else line.rstrip()
                    )
                    modified = True

            # Fix blank lines with whitespace (W293)
            for i, line in enumerate(lines):
                if line.strip() == "" and line != "\n":
                    lines[i] = "\n"
                    modified = True

            if modified:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)
                fixed_count += 1
                print(f"   ✅ Fixed whitespace in {file_path}")

        except Exception as e:
            print(f"   ❌ Error processing {file_path}: {e}")

    print(f"\n✅ Fixed whitespace issues in {fixed_count} files")


def fix_import_spacing():
    """Fix missing whitespace after commas in imports."""
    print("\n📥 Fixing import spacing...")

    python_files = list(Path(".").rglob("*.py"))
    fixed_count = 0

    for file_path in python_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content

            # Fix missing whitespace after commas in imports
            # Pattern: comma not followed by space
            content = re.sub(r", (?!\s)", ", ", content)

            if content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                fixed_count += 1
                print(f"   ✅ Fixed import spacing in {file_path}")

        except Exception as e:
            print(f"   ❌ Error processing {file_path}: {e}")

    print(f"\n✅ Fixed import spacing in {fixed_count} files")


def fix_comparison_issues():
    """Fix comparison to False issues."""
    print("\n🔍 Fixing comparison issues...")

    python_files = list(Path(".").rglob("*.py"))
    fixed_count = 0

    for file_path in python_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content

            # Fix comparison to False
            content = re.sub(r"==\s*False\b", "is False", content)
            content = re.sub(r"!=\s*False\b", "is not False", content)

            if content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                fixed_count += 1
                print(f"   ✅ Fixed comparisons in {file_path}")

        except Exception as e:
            print(f"   ❌ Error processing {file_path}: {e}")

    print(f"\n✅ Fixed comparison issues in {fixed_count} files")


def apply_black_and_isort():
    """Apply black and isort formatting."""
    print("\n🖤 Applying black formatting...")
    run_command("black --line-length 88 .", "Black formatting")

    print("\n📋 Applying isort...")
    run_command("isort --profile black .", "Import sorting with isort")


def get_flake8_statistics():
    """Get current flake8 statistics."""
    print("\n📊 Getting flake8 statistics...")
    result = run_command(
        "python -m flake8 --max-line-length=88 --statistics .",
        "Running flake8 analysis",
    )
    return result


def main():
    """Main execution function."""
    print("🚀 Starting Comprehensive Code Quality Fixes")
    print("=" * 50)

    # Get initial statistics
    print("\n📊 Initial flake8 statistics:")
    initial_stats = get_flake8_statistics()

    # Step 1: Remove unused imports
    fix_unused_imports()

    # Step 2: Fix f-string issues
    fix_f_string_issues()

    # Step 3: Fix whitespace issues
    fix_whitespace_issues()

    # Step 4: Fix import spacing
    fix_import_spacing()

    # Step 5: Fix comparison issues
    fix_comparison_issues()

    # Step 6: Apply formatting tools
    apply_black_and_isort()

    # Get final statistics
    print("\n📊 Final flake8 statistics:")
    final_stats = get_flake8_statistics()

    print("\n🎉 Comprehensive fixes completed!")
    print("=" * 50)

    # Summary
    print("\n📋 SUMMARY:")
    print("✅ Removed unused imports")
    print("✅ Fixed f-string issues")
    print("✅ Fixed whitespace issues")
    print("✅ Fixed import spacing")
    print("✅ Fixed comparison issues")
    print("✅ Applied black and isort formatting")

    print("\n🔍 NEXT STEPS:")
    print("1. Review remaining line length violations (E501)")
    print("2. Fix import placement issues (E402) manually")
    print("3. Replace bare except clauses (E722)")
    print("4. Remove unused variables (F841)")
    print("5. Fix any remaining issues manually")


if __name__ == "__main__":
    main()
