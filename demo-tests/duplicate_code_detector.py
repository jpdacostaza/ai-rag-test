#!/usr/bin/env python3
"""
Duplicate Code Detection Tool
============================

This script detects duplicate code blocks within Python files using multiple approaches:
1. Exact text matching
2. AST-based structural similarity
3. Function/method similarity
4. Cross-file duplicate detection

Usage: python duplicate_code_detector.py [--min-lines N] [--similarity-threshold N]
"""

import argparse
import ast
import difflib
import hashlib
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict
from typing import List
from typing import NamedTuple
from typing import Set
from typing import Tuple


class CodeBlock(NamedTuple):
    """Represents a code block with metadata."""

    file_path: str
    start_line: int
    end_line: int
    content: str
    content_hash: str
    normalized_content: str


class DuplicateMatch(NamedTuple):
    """Represents a duplicate code match."""

    block1: CodeBlock
    block2: CodeBlock
    similarity: float
    match_type: str


class DuplicateCodeDetector:
    def __init__(self, project_root: str, min_lines: int = 5, similarity_threshold: float = 0.8):
        self.project_root = Path(project_root)
        self.min_lines = min_lines
        self.similarity_threshold = similarity_threshold
        self.duplicates = []
        self.code_blocks = []

    def find_python_files(self) -> List[Path]:
        """Find all Python files in the project."""
        python_files = []
        for root, dirs, files in os.walk(self.project_root):
            # Skip certain directories
            dirs[:] = [
                d for d in dirs if d not in [".git", "__pycache__", ".venv", "venv", "storage"]
            ]

            for file in files:
                if file.endswith(".py"):
                    python_files.append(Path(root) / file)

        return sorted(python_files)

    def normalize_code(self, code: str) -> str:
        """Normalize code by removing comments, extra whitespace, and variable names."""
        # Remove comments
        lines = []
        for line in code.split("\n"):
            # Remove inline comments but preserve strings
            in_string = False
            quote_char = None
            result = ""
            i = 0
            while i < len(line):
                char = line[i]
                if not in_string and char == "#":
                    break  # Rest of line is comment
                elif char in ['"', "'"]:
                    if not in_string:
                        in_string = True
                        quote_char = char
                    elif char == quote_char:
                        in_string = False
                        quote_char = None
                result += char
                i += 1
            lines.append(result.rstrip())

        normalized = "\n".join(lines)

        # Remove extra whitespace
        normalized = re.sub(r"\s+", " ", normalized)

        # Replace variable names with placeholders (simple approach)
        # This is a basic normalization - more sophisticated AST-based approaches exist
        normalized = re.sub(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", "VAR", normalized)

        return normalized.strip()

    def extract_code_blocks(self, file_path: Path) -> List[CodeBlock]:
        """Extract code blocks from a Python file."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return []

        blocks = []
        total_lines = len(lines)

        # Extract sliding windows of code
        for start in range(total_lines - self.min_lines + 1):
            for end in range(start + self.min_lines, min(start + 50, total_lines + 1)):
                block_lines = lines[start:end]
                content = "".join(block_lines).strip()

                # Skip blocks that are mostly empty or comments
                non_empty_lines = [
                    line.strip()
                    for line in block_lines
                    if line.strip() and not line.strip().startswith("#")
                ]
                if len(non_empty_lines) < self.min_lines:
                    continue

                normalized = self.normalize_code(content)
                content_hash = hashlib.md5(normalized.encode()).hexdigest()

                block = CodeBlock(
                    file_path=str(file_path.relative_to(self.project_root)),
                    start_line=start + 1,
                    end_line=end,
                    content=content,
                    content_hash=content_hash,
                    normalized_content=normalized,
                )
                blocks.append(block)

        return blocks

    def extract_functions_and_classes(self, file_path: Path) -> List[CodeBlock]:
        """Extract functions and classes as separate blocks for comparison."""

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
                lines = content.split("\n")
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return []

        blocks = []

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    start_line = node.lineno
                    end_line = getattr(node, "end_lineno", None)
                    if end_line is None:
                        # Estimate end line for older Python versions
                        end_line = start_line + 10

                    if end_line - start_line >= self.min_lines:
                        block_content = "\n".join(lines[start_line - 1 : end_line])
                        normalized = self.normalize_code(block_content)
                        content_hash = hashlib.md5(normalized.encode()).hexdigest()

                        block = CodeBlock(
                            file_path=str(file_path.relative_to(self.project_root)),
                            start_line=start_line,
                            end_line=end_line,
                            content=block_content,
                            content_hash=content_hash,
                            normalized_content=normalized,
                        )
                        blocks.append(block)

        except SyntaxError:
            # If file has syntax errors, skip AST-based extraction
            pass

        return blocks

    def calculate_similarity(self, block1: CodeBlock, block2: CodeBlock) -> float:
        """Calculate similarity between two code blocks."""
        # Use difflib for sequence-based similarity
        seq1 = block1.normalized_content.split()
        seq2 = block2.normalized_content.split()

        matcher = difflib.SequenceMatcher(None, seq1, seq2)
        return matcher.ratio()

    def find_exact_duplicates(self) -> List[DuplicateMatch]:
        """Find exact duplicates based on normalized content."""
        hash_groups = defaultdict(list)

        for block in self.code_blocks:
            hash_groups[block.content_hash].append(block)

        duplicates = []
        for content_hash, blocks in hash_groups.items():
            if len(blocks) > 1:
                # Found duplicates
                for i in range(len(blocks)):
                    for j in range(i + 1, len(blocks)):
                        duplicate = DuplicateMatch(
                            block1=blocks[i], block2=blocks[j], similarity=1.0, match_type="exact"
                        )
                        duplicates.append(duplicate)

        return duplicates

    def find_similar_duplicates(self) -> List[DuplicateMatch]:
        """Find similar duplicates based on similarity threshold."""
        duplicates = []

        for i in range(len(self.code_blocks)):
            for j in range(i + 1, len(self.code_blocks)):
                block1 = self.code_blocks[i]
                block2 = self.code_blocks[j]

                # Skip if blocks are from the same location
                if (
                    block1.file_path == block2.file_path
                    and abs(block1.start_line - block2.start_line) < self.min_lines
                ):
                    continue

                similarity = self.calculate_similarity(block1, block2)

                if similarity >= self.similarity_threshold:
                    duplicate = DuplicateMatch(
                        block1=block1, block2=block2, similarity=similarity, match_type="similar"
                    )
                    duplicates.append(duplicate)

        return duplicates

    def analyze_project(self):
        """Analyze the entire project for duplicates."""
        print(f"🔍 Analyzing project for duplicate code...")
        print(f"Minimum lines: {self.min_lines}")
        print(f"Similarity threshold: {self.similarity_threshold}")
        print("=" * 60)

        python_files = self.find_python_files()
        print(f"Found {len(python_files)} Python files to analyze")

        # Extract all code blocks
        total_blocks = 0
        for file_path in python_files:
            print(f"Extracting blocks from: {file_path.relative_to(self.project_root)}")

            # Extract sliding window blocks
            file_blocks = self.extract_code_blocks(file_path)
            self.code_blocks.extend(file_blocks)

            # Extract function/class blocks
            func_blocks = self.extract_functions_and_classes(file_path)
            self.code_blocks.extend(func_blocks)

            total_blocks += len(file_blocks) + len(func_blocks)

        print(f"Extracted {total_blocks} code blocks")

        # Find duplicates
        print("\n🔎 Finding exact duplicates...")
        exact_duplicates = self.find_exact_duplicates()

        print("🔎 Finding similar duplicates...")
        similar_duplicates = self.find_similar_duplicates()

        self.duplicates = exact_duplicates + similar_duplicates

        print(f"\n✅ Analysis complete!")
        print(f"Found {len(exact_duplicates)} exact duplicates")
        print(f"Found {len(similar_duplicates)} similar duplicates")
        print(f"Total duplicates: {len(self.duplicates)}")

    def generate_report(self) -> str:
        """Generate a comprehensive duplicate code report."""
        report = []
        report.append("DUPLICATE CODE DETECTION REPORT")
        report.append("=" * 50)
        report.append(f"Project: {self.project_root}")
        report.append(f"Minimum lines: {self.min_lines}")
        report.append(f"Similarity threshold: {self.similarity_threshold}")
        report.append(f"Total duplicates found: {len(self.duplicates)}")
        report.append("")

        if not self.duplicates:
            report.append("🎉 No significant duplicate code found!")
            report.append("Your codebase appears to have good code reuse practices.")
            return "\n".join(report)

        # Group by similarity
        exact_matches = [d for d in self.duplicates if d.match_type == "exact"]
        similar_matches = [d for d in self.duplicates if d.match_type == "similar"]

        report.append("SUMMARY")
        report.append("-" * 20)
        report.append(f"Exact duplicates: {len(exact_matches)}")
        report.append(f"Similar duplicates: {len(similar_matches)}")
        report.append("")

        # Exact duplicates
        if exact_matches:
            report.append("EXACT DUPLICATES")
            report.append("-" * 20)

            for i, duplicate in enumerate(exact_matches[:20], 1):  # Limit to first 20
                report.append(f"\nDuplicate #{i}:")
                report.append(
                    f"File 1: {duplicate.block1.file_path} (lines {duplicate.block1.start_line}-{duplicate.block1.end_line})"
                )
                report.append(
                    f"File 2: {duplicate.block2.file_path} (lines {duplicate.block2.start_line}-{duplicate.block2.end_line})"
                )
                report.append(f"Similarity: {duplicate.similarity:.2%}")

                # Show a snippet of the duplicate code
                lines = duplicate.block1.content.split("\n")[:5]
                report.append("Code snippet:")
                for line in lines:
                    report.append(f"  {line}")
                if len(duplicate.block1.content.split("\n")) > 5:
                    report.append("  ...")

            if len(exact_matches) > 20:
                report.append(f"\n... and {len(exact_matches) - 20} more exact duplicates")

        # Similar duplicates
        if similar_matches:
            report.append("\n\nSIMILAR DUPLICATES")
            report.append("-" * 20)

            # Sort by similarity (highest first)
            similar_matches.sort(key=lambda x: x.similarity, reverse=True)

            for i, duplicate in enumerate(similar_matches[:10], 1):  # Limit to first 10
                report.append(f"\nSimilar #{i}:")
                report.append(
                    f"File 1: {duplicate.block1.file_path} (lines {duplicate.block1.start_line}-{duplicate.block1.end_line})"
                )
                report.append(
                    f"File 2: {duplicate.block2.file_path} (lines {duplicate.block2.start_line}-{duplicate.block2.end_line})"
                )
                report.append(f"Similarity: {duplicate.similarity:.2%}")

                # Show a snippet
                lines = duplicate.block1.content.split("\n")[:3]
                report.append("Code snippet (first file):")
                for line in lines:
                    report.append(f"  {line}")

            if len(similar_matches) > 10:
                report.append(f"\n... and {len(similar_matches) - 10} more similar duplicates")

        # Recommendations
        report.append("\n\nRECOMMENDATIONS")
        report.append("-" * 20)
        report.append("1. Extract common code into shared functions or classes")
        report.append("2. Create utility modules for frequently duplicated patterns")
        report.append("3. Use inheritance or composition to reduce code duplication")
        report.append("4. Consider using design patterns like Factory or Strategy")
        report.append("5. Review and refactor the highest similarity duplicates first")

        # File statistics
        file_duplicate_counts = defaultdict(int)
        for duplicate in self.duplicates:
            file_duplicate_counts[duplicate.block1.file_path] += 1
            file_duplicate_counts[duplicate.block2.file_path] += 1

        if file_duplicate_counts:
            report.append("\n\nFILES WITH MOST DUPLICATES")
            report.append("-" * 30)
            sorted_files = sorted(file_duplicate_counts.items(), key=lambda x: x[1], reverse=True)
            for file_path, count in sorted_files[:10]:
                report.append(f"{file_path}: {count} duplicates")

        return "\n".join(report)

    def save_detailed_report(self, output_file: str):
        """Save a detailed report with code snippets."""
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(self.generate_report())

            # Add detailed code blocks for reference
            f.write("\n\n" + "=" * 80)
            f.write("\nDETAILED CODE BLOCKS")
            f.write("\n" + "=" * 80)

            for i, duplicate in enumerate(self.duplicates[:50], 1):  # First 50 for details
                f.write(f"\n\nDUPLICATE #{i}")
                f.write("\n" + "-" * 40)

                f.write(
                    f"\nBlock 1: {duplicate.block1.file_path} (lines {duplicate.block1.start_line}-{duplicate.block1.end_line})"
                )
                f.write("\n" + "~" * 40)
                f.write(f"\n{duplicate.block1.content}")

                f.write(
                    f"\n\nBlock 2: {duplicate.block2.file_path} (lines {duplicate.block2.start_line}-{duplicate.block2.end_line})"
                )
                f.write("\n" + "~" * 40)
                f.write(f"\n{duplicate.block2.content}")

                f.write(f"\n\nSimilarity: {duplicate.similarity:.2%} ({duplicate.match_type})")


def main():
    parser = argparse.ArgumentParser(description="Detect duplicate code in Python projects")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--min-lines", type=int, default=5, help="Minimum lines for a code block")
    parser.add_argument(
        "--similarity-threshold", type=float, default=0.8, help="Similarity threshold (0.0-1.0)"
    )
    parser.add_argument("--output", default="duplicate_code_report.md", help="Output report file")

    args = parser.parse_args()

    detector = DuplicateCodeDetector(
        project_root=args.project_root,
        min_lines=args.min_lines,
        similarity_threshold=args.similarity_threshold,
    )

    detector.analyze_project()

    # Generate and save report
    report = detector.generate_report()

    # Save to file
    output_path = Path(args.project_root) / "readme" / args.output
    detector.save_detailed_report(output_path)

    print(f"\n📄 Report saved to: {output_path}")
    print("\nSummary:")
    print("-" * 20)

    # Print summary
    lines = report.split("\n")
    summary_start = next(i for i, line in enumerate(lines) if line.startswith("SUMMARY"))
    summary_end = next(
        i
        for i, line in enumerate(lines[summary_start:], summary_start)
        if line.startswith("EXACT DUPLICATES") or line.startswith("RECOMMENDATIONS")
    )

    for line in lines[summary_start:summary_end]:
        print(line)


if __name__ == "__main__":
    main()
