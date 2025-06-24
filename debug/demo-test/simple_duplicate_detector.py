#!/usr/bin/env python3
"""
Simple Duplicate Code Detection Tool
===================================

This script detects duplicate code blocks within Python files using:
1. Exact text matching (after normalization)
2. Line-by-line similarity analysis
3. Function/method duplicate detection

Usage: python simple_duplicate_detector.py [--min-lines N] [--threshold N]
"""

import argparse
import hashlib
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict
from typing import List
from typing import Tuple


class SimpleDuplicateDetector:
    def __init__(self, project_root: str, min_lines: int = 5, similarity_threshold: float = 0.85):
        self.project_root = Path(project_root)
        self.min_lines = min_lines
        self.similarity_threshold = similarity_threshold
        self.duplicates = []

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

    def normalize_code_line(self, line: str) -> str:
        """Normalize a single line of code for comparison."""
        # Remove leading/trailing whitespace
        line = line.strip()

        # Skip empty lines and comments
        if not line or line.startswith("#"):
            return ""

        # Remove inline comments
        if "#" in line:
            # Simple approach - doesn't handle strings with # properly
            parts = line.split("#")
            line = parts[0].strip()

        # Normalize whitespace
        line = re.sub(r"\s+", " ", line)

        # Remove string literals (replace with placeholder)
        line = re.sub(r'"[^"]*"', '"STRING"', line)
        line = re.sub(r"'[^']*'", "'STRING'", line)

        # Normalize variable names (simple approach)
        # This is very basic - a more sophisticated approach would use AST
        line = re.sub(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b(?=\s*=)", "VAR", line)

        return line

    def extract_code_blocks(self, file_path: Path) -> List[Tuple[int, int, str, str]]:
        """Extract code blocks from a file. Returns (start_line, end_line, content, normalized)."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return []

        blocks = []
        total_lines = len(lines)

        # Extract overlapping windows of code
        for start in range(total_lines - self.min_lines + 1):
            for window_size in [self.min_lines, self.min_lines + 5, self.min_lines + 10]:
                end = min(start + window_size, total_lines)
                if end - start < self.min_lines:
                    continue

                # Get the code block
                block_lines = lines[start:end]
                raw_content = "".join(block_lines)

                # Normalize lines
                normalized_lines = []
                significant_lines = 0

                for line in block_lines:
                    normalized = self.normalize_code_line(line)
                    if normalized:
                        normalized_lines.append(normalized)
                        significant_lines += 1

                # Only consider blocks with enough significant lines
                if significant_lines >= self.min_lines:
                    normalized_content = "\n".join(normalized_lines)
                    blocks.append((start + 1, end, raw_content.strip(), normalized_content))

        return blocks

    def calculate_line_similarity(self, content1: str, content2: str) -> float:
        """Calculate similarity between two code blocks."""
        lines1 = [line for line in content1.split("\n") if line.strip()]
        lines2 = [line for line in content2.split("\n") if line.strip()]

        if not lines1 or not lines2:
            return 0.0

        # Simple line-by-line comparison
        matching_lines = 0
        total_lines = max(len(lines1), len(lines2))

        for i in range(min(len(lines1), len(lines2))):
            if lines1[i] == lines2[i]:
                matching_lines += 1

        return matching_lines / total_lines

    def find_exact_duplicates(self, all_blocks: Dict[str, List]) -> List[Dict]:
        """Find exact duplicates based on normalized content."""
        hash_groups = defaultdict(list)
        duplicates = []

        # Group blocks by their normalized content hash
        for file_path, blocks in all_blocks.items():
            for start_line, end_line, raw_content, normalized_content in blocks:
                if normalized_content.strip():
                    content_hash = hashlib.md5(normalized_content.encode()).hexdigest()
                    hash_groups[content_hash].append(
                        {
                            "file": file_path,
                            "start_line": start_line,
                            "end_line": end_line,
                            "content": raw_content,
                            "normalized": normalized_content,
                        }
                    )

        # Find groups with multiple entries (duplicates)
        for content_hash, blocks in hash_groups.items():
            if len(blocks) > 1:
                # Check if they're actually from different locations
                unique_blocks = []
                for block in blocks:
                    is_unique = True
                    for existing in unique_blocks:
                        # Skip if from same file and overlapping lines
                        if (
                            block["file"] == existing["file"]
                            and abs(block["start_line"] - existing["start_line"]) < self.min_lines
                        ):
                            is_unique = False
                            break
                    if is_unique:
                        unique_blocks.append(block)

                if len(unique_blocks) > 1:
                    # Add all combinations as duplicates
                    for i in range(len(unique_blocks)):
                        for j in range(i + 1, len(unique_blocks)):
                            duplicates.append(
                                {
                                    "type": "exact",
                                    "similarity": 1.0,
                                    "block1": unique_blocks[i],
                                    "block2": unique_blocks[j],
                                    "lines": unique_blocks[i]["end_line"]
                                    - unique_blocks[i]["start_line"],
                                }
                            )

        return duplicates

    def find_similar_duplicates(self, all_blocks: Dict[str, List]) -> List[Dict]:
        """Find similar duplicates using similarity threshold."""
        duplicates = []
        all_block_list = []

        # Flatten all blocks into a single list
        for file_path, blocks in all_blocks.items():
            for start_line, end_line, raw_content, normalized_content in blocks:
                if normalized_content.strip():
                    all_block_list.append(
                        {
                            "file": file_path,
                            "start_line": start_line,
                            "end_line": end_line,
                            "content": raw_content,
                            "normalized": normalized_content,
                        }
                    )

        # Compare all pairs
        for i in range(len(all_block_list)):
            for j in range(i + 1, len(all_block_list)):
                block1 = all_block_list[i]
                block2 = all_block_list[j]

                # Skip if from same file and overlapping
                if (
                    block1["file"] == block2["file"]
                    and abs(block1["start_line"] - block2["start_line"]) < self.min_lines
                ):
                    continue

                # Calculate similarity
                similarity = self.calculate_line_similarity(
                    block1["normalized"], block2["normalized"]
                )

                if similarity >= self.similarity_threshold:
                    duplicates.append(
                        {
                            "type": "similar",
                            "similarity": similarity,
                            "block1": block1,
                            "block2": block2,
                            "lines": block1["end_line"] - block1["start_line"],
                        }
                    )

        return duplicates

    def analyze_project(self):
        """Analyze the entire project for duplicates."""
        print(f"🔍 Analyzing project for duplicate code...")
        print(f"Project: {self.project_root}")
        print(f"Minimum lines: {self.min_lines}")
        print(f"Similarity threshold: {self.similarity_threshold}")
        print("=" * 60)

        python_files = self.find_python_files()
        print(f"Found {len(python_files)} Python files")

        # Extract code blocks from all files
        all_blocks = {}
        total_blocks = 0

        for file_path in python_files:
            rel_path = str(file_path.relative_to(self.project_root))
            print(f"Analyzing: {rel_path}")

            blocks = self.extract_code_blocks(file_path)
            all_blocks[rel_path] = blocks
            total_blocks += len(blocks)

        print(f"Extracted {total_blocks} code blocks")

        # Find duplicates
        print("\n🔎 Finding exact duplicates...")
        exact_duplicates = self.find_exact_duplicates(all_blocks)

        print("🔎 Finding similar duplicates...")
        similar_duplicates = self.find_similar_duplicates(all_blocks)

        self.duplicates = exact_duplicates + similar_duplicates

        # Sort by line count (larger duplicates first)
        self.duplicates.sort(key=lambda x: x["lines"], reverse=True)

        print(f"\n✅ Analysis complete!")
        print(f"Exact duplicates: {len(exact_duplicates)}")
        print(f"Similar duplicates: {len(similar_duplicates)}")
        print(f"Total duplicates: {len(self.duplicates)}")

    def generate_report(self) -> str:
        """Generate a comprehensive duplicate code report."""
        report = []
        report.append("DUPLICATE CODE DETECTION REPORT")
        report.append("=" * 50)
        report.append(f"Project: {self.project_root}")
        report.append(f"Minimum lines: {self.min_lines}")
        report.append(f"Similarity threshold: {self.similarity_threshold}")
        report.append("")

        if not self.duplicates:
            report.append("🎉 No significant duplicate code found!")
            report.append("Your codebase appears to have good code reuse practices.")
            return "\n".join(report)

        # Summary
        exact_count = len([d for d in self.duplicates if d["type"] == "exact"])
        similar_count = len([d for d in self.duplicates if d["type"] == "similar"])

        report.append("SUMMARY")
        report.append("-" * 20)
        report.append(f"Total duplicates found: {len(self.duplicates)}")
        report.append(f"Exact duplicates: {exact_count}")
        report.append(f"Similar duplicates: {similar_count}")
        report.append("")

        # Top duplicates
        report.append("TOP DUPLICATES (by size)")
        report.append("-" * 30)

        for i, duplicate in enumerate(self.duplicates[:15], 1):  # Top 15
            report.append(f"\n#{i} - {duplicate['type'].upper()} DUPLICATE")
            report.append(f"Similarity: {duplicate['similarity']:.1%}")
            report.append(f"Size: {duplicate['lines']} lines")

            block1 = duplicate["block1"]
            block2 = duplicate["block2"]

            report.append(
                f"Location 1: {block1['file']} (lines {block1['start_line']}-{block1['end_line']})"
            )
            report.append(
                f"Location 2: {block2['file']} (lines {block2['start_line']}-{block2['end_line']})"
            )

            # Show first few lines
            content_lines = block1["content"].split("\n")[:4]
            report.append("Code preview:")
            for line in content_lines:
                if line.strip():
                    report.append(f"  {line}")
            if len(block1["content"].split("\n")) > 4:
                report.append("  ...")

        if len(self.duplicates) > 15:
            report.append(f"\n... and {len(self.duplicates) - 15} more duplicates")

        # File statistics
        file_counts = defaultdict(int)
        for duplicate in self.duplicates:
            file_counts[duplicate["block1"]["file"]] += 1
            file_counts[duplicate["block2"]["file"]] += 1

        if file_counts:
            report.append("\n\nFILES WITH MOST DUPLICATES")
            report.append("-" * 30)
            sorted_files = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)
            for file_path, count in sorted_files[:10]:
                report.append(f"{file_path}: {count} duplicates")

        # Recommendations
        report.append("\n\nRECOMMENDATIONS")
        report.append("-" * 20)
        report.append("1. Extract common patterns into utility functions")
        report.append("2. Create base classes for similar functionality")
        report.append("3. Use configuration or data-driven approaches")
        report.append("4. Consider design patterns (Factory, Strategy, etc.)")
        report.append("5. Focus on the largest duplicates first for maximum impact")

        return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description="Simple duplicate code detection for Python")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument(
        "--min-lines", type=int, default=5, help="Minimum lines for duplicate detection"
    )
    parser.add_argument(
        "--threshold", type=float, default=0.85, help="Similarity threshold (0.0-1.0)"
    )

    args = parser.parse_args()

    detector = SimpleDuplicateDetector(
        project_root=args.project_root,
        min_lines=args.min_lines,
        similarity_threshold=args.threshold,
    )

    detector.analyze_project()

    # Generate and display report
    report = detector.generate_report()
    print("\n" + "=" * 60)
    print("DUPLICATE CODE REPORT")
    print("=" * 60)

    # Save detailed report
    output_path = Path(args.project_root) / "readme" / "DUPLICATE_CODE_REPORT.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

        # Add detailed information
        f.write("\n\n" + "=" * 80)
        f.write("\nDETAILED DUPLICATE ANALYSIS")
        f.write("\n" + "=" * 80)

        for i, duplicate in enumerate(detector.duplicates, 1):
            f.write(f"\n\n--- DUPLICATE #{i} ---")
            f.write(f"\nType: {duplicate['type']}")
            f.write(f"\nSimilarity: {duplicate['similarity']:.1%}")
            f.write(f"\nLines: {duplicate['lines']}")

            block1 = duplicate["block1"]
            block2 = duplicate["block2"]

            f.write(
                f"\n\nFILE 1: {block1['file']} (lines {block1['start_line']}-{block1['end_line']})"
            )
            f.write("\n" + "-" * 40)
            f.write(f"\n{block1['content']}")

            f.write(
                f"\n\nFILE 2: {block2['file']} (lines {block2['start_line']}-{block2['end_line']})"
            )
            f.write("\n" + "-" * 40)
            f.write(f"\n{block2['content']}")

    print(f"\n📄 Detailed report saved to: {output_path}")

    # Print summary
    lines = report.split("\n")
    summary_start = next(i for i, line in enumerate(lines) if line.startswith("SUMMARY"))
    summary_end = next(
        i
        for i, line in enumerate(lines[summary_start:], summary_start)
        if line.startswith("TOP DUPLICATES")
    )

    for line in lines[summary_start:summary_end]:
        print(line)


if __name__ == "__main__":
    main()
