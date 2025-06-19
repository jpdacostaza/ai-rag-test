#!/usr/bin/env python3
"""
Line Length Fix Script
Automatically fixes line length violations by breaking long lines.
"""

import os
import re
import subprocess
from pathlib import Path


def fix_line_length_violations():
    """Fix line length violations in Python files."""
    print("🔧 Fixing line length violations...")

    # Get files with E501 violations
    result = subprocess.run(
        [
            "python",
            "-m",
            "flake8",
            "--max-line-length=88",
            "--exclude=storage",
            "--select=E501",
            ".",
        ],
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
    )

    if result.returncode != 0:
        return

    # Parse flake8 output to get files and line numbers
    violations = {}
    for line in result.stdout.strip().split("\n"):
        if ":" in line and "E501" in line:
            parts = line.split(":")
            if len(parts) >= 3:
                file_path = parts[0].strip(".")
                line_num = int(parts[1])
                if file_path not in violations:
                    violations[file_path] = []
                violations[file_path].append(line_num)

    fixed_files = 0
    for file_path, line_numbers in violations.items():
        try:
            full_path = Path.cwd() / file_path.lstrip("\\").lstrip("/")
            if not full_path.exists():
                continue

            with open(full_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            modified = False

            # Fix lines in reverse order to maintain line numbers
            for line_num in sorted(line_numbers, reverse=True):
                if line_num <= len(lines):
                    line_idx = line_num - 1
                    line = lines[line_idx]

                    if len(line.rstrip("\n")) > 88:
                        fixed_line = fix_long_line(line)
                        if fixed_line != line:
                            lines[line_idx] = fixed_line
                            modified = True

            if modified:
                with open(full_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)
                fixed_files += 1
                print(f"   ✅ Fixed line lengths in {file_path}")

        except Exception as e:
            print(f"   ❌ Error processing {file_path}: {e}")

    print(f"✅ Fixed line length violations in {fixed_files} files")


def fix_long_line(line):
    """Fix a single long line by breaking it appropriately."""
    original_line = line
    line = line.rstrip("\n")

    # Don't modify lines that are already properly formatted
    if len(line) <= 88:
        return original_line

    # Get indentation
    indent = len(line) - len(line.lstrip())
    indent_str = line[:indent]

    # Common patterns to fix

    # 1. Long string literals
    if '"""' in line or "'''" in line:
        return original_line  # Skip docstrings

    # 2. Function calls with many arguments
    if "(" in line and ")" in line and "," in line:
        # Find the opening parenthesis
        paren_pos = line.find("(")
        if paren_pos > 0:
            before_paren = line[: paren_pos + 1]
            after_paren = line[paren_pos + 1 :]

            # Check if we can break after the opening parenthesis
            if len(before_paren) < 80:
                # Split arguments
                args_part = after_paren.rstrip(")")
                closing = ")" if after_paren.endswith(")") else ""

                if "," in args_part:
                    args = [arg.strip() for arg in args_part.split(",")]
                    if len(args) > 1:
                        new_indent = " " * (len(before_paren))
                        result = before_paren + "\n"
                        for i, arg in enumerate(args[:-1]):
                            result += new_indent + arg + ",\n"
                        result += new_indent + args[-1] + closing + "\n"
                        return result

    # 3. Long import statements
    if line.strip().startswith("from ") and " import " in line:
        parts = line.split(" import ")
        if len(parts) == 2:
            from_part = parts[0]
            import_part = parts[1]

            if "," in import_part:
                imports = [imp.strip() for imp in import_part.split(",")]
                if len(imports) > 1:
                    result = from_part + " import (\n"
                    for imp in imports:
                        result += indent_str + "    " + imp + ",\n"
                    result += indent_str + ")\n"
                    return result

    # 4. Long assignments or expressions
    if "=" in line and not line.strip().startswith("#"):
        eq_pos = line.find("=")
        if eq_pos > 0 and eq_pos < len(line) - 1:
            left_part = line[:eq_pos].rstrip()
            right_part = line[eq_pos + 1 :].lstrip()

            # If the right part is very long, try to break it
            if len(right_part) > 60:
                # Break long f-strings
                if right_part.startswith('f"') or right_part.startswith("f'"):
                    quote = right_part[1]
                    if quote in right_part[2:]:
                        # Can potentially break f-string
                        pass

                # Break long concatenations
                if " + " in right_part:
                    parts = right_part.split(" + ")
                    if len(parts) > 1:
                        result = left_part + " = (\n"
                        for i, part in enumerate(parts):
                            if i == 0:
                                result += indent_str + "    " + part.strip() + " +\n"
                            elif i == len(parts) - 1:
                                result += indent_str + "    " + part.strip() + "\n"
                            else:
                                result += indent_str + "    " + part.strip() + " +\n"
                        result += indent_str + ")\n"
                        return result

    # 5. Long string literals
    if (
        (line.count('"') >= 2 or line.count("'") >= 2)
        and 'f"' not in line
        and "f'" not in line
    ):
        # Find string literals and break them
        for quote in ['"', "'"]:
            if line.count(quote) >= 2:
                start = line.find(quote)
                end = line.rfind(quote)
                if start != end and end - start > 50:
                    before = line[:start]
                    string_content = line[start : end + 1]
                    after = line[end + 1 :]

                    if len(string_content) > 60:
                        # Break the string
                        mid_point = len(string_content) // 2
                        # Find a good break point (space)
                        for i in range(
                            mid_point, min(mid_point + 20, len(string_content))
                        ):
                            if string_content[i] == " ":
                                part1 = string_content[:i] + quote
                                part2 = quote + string_content[i + 1 :]
                                result = (
                                    before
                                    + part1
                                    + " \\\n"
                                    + indent_str
                                    + "    "
                                    + part2
                                    + after
                                    + "\n"
                                )
                                return result

    # If no specific pattern matched, try generic line breaking
    if len(line) > 88:
        # Look for natural break points
        break_chars = [", ", " and ", " or ", " + ", " - ", " * ", " / "]
        for char in break_chars:
            if char in line:
                parts = line.split(char)
                if len(parts) > 1:
                    # Try to break at a reasonable point
                    current_length = 0
                    result_parts = []
                    current_part = ""

                    for i, part in enumerate(parts):
                        test_length = (
                            len(current_part) + len(char) + len(part)
                            if current_part
                            else len(part)
                        )
                        if test_length <= 80 or not current_part:
                            current_part += char + part if current_part else part
                        else:
                            result_parts.append(current_part)
                            current_part = part

                    if current_part:
                        result_parts.append(current_part)

                    if len(result_parts) > 1:
                        result = result_parts[0] + " \\\n"
                        for part in result_parts[1:-1]:
                            result += indent_str + "    " + part + " \\\n"
                        result += indent_str + "    " + result_parts[-1] + "\n"
                        return result

    return original_line


def fix_unused_variables():
    """Fix unused variables by prefixing with underscore."""
    print("🔧 Fixing unused variables...")

    # Get files with F841 violations
    result = subprocess.run(
        [
            "python",
            "-m",
            "flake8",
            "--max-line-length=88",
            "--exclude=storage",
            "--select=F841",
            ".",
        ],
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
    )

    if result.returncode != 0:
        return

    fixed_files = set()
    for line in result.stdout.strip().split("\n"):
        if ":" in line and "F841" in line:
            parts = line.split(":")
            if len(parts) >= 4:
                file_path = parts[0].strip(".")
                line_num = int(parts[1])
                message = ":".join(parts[3:])

                # Extract variable name from message
                if (
                    "local variable '" in message
                    and "' is assigned to but never used" in message
                ):
                    var_name = message.split("local variable '")[1].split("'")[0]

                    try:
                        full_path = Path.cwd() / file_path.lstrip("\\").lstrip("/")
                        if not full_path.exists():
                            continue

                        with open(full_path, "r", encoding="utf-8") as f:
                            lines = f.readlines()

                        if line_num <= len(lines):
                            line_content = lines[line_num - 1]

                            # Replace variable assignment
                            if f"{var_name} =" in line_content:
                                new_line = line_content.replace(
                                    f"{var_name} =", f"_{var_name} ="
                                )
                                lines[line_num - 1] = new_line

                                with open(full_path, "w", encoding="utf-8") as f:
                                    f.writelines(lines)
                                fixed_files.add(file_path)

                    except Exception as e:
                        print(f"   ❌ Error processing {file_path}: {e}")

    print(f"✅ Fixed unused variables in {len(fixed_files)} files")


def main():
    """Main execution function."""
    print("🚀 Starting Targeted Code Quality Fixes")
    print("=" * 50)

    # Fix line length violations
    fix_line_length_violations()

    # Fix unused variables
    fix_unused_variables()

    # Apply black formatting again to clean up
    print("\n🖤 Applying final black formatting...")
    subprocess.run(["black", "--line-length", "88", "."], cwd=Path.cwd())

    print("\n✅ Targeted fixes completed!")


if __name__ == "__main__":
    main()
