#!/usr/bin/env python3
"""Utility to move all test-related files under tests/ into tests/deleted/ archive.

Preserves relative subdirectory structure. Skips:
  * tests/deleted itself
  * __pycache__ directories
  * The archive script itself (not located in tests/)

After running, only tests/deleted (and optionally README files) should remain.

Safe to run multiple times (idempotent) – already moved files are ignored.
"""
from __future__ import annotations
import shutil
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "tests"
ARCHIVE = BASE / "deleted"

SKIP_DIR_NAMES = {"__pycache__", "deleted"}


def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    if parts & SKIP_DIR_NAMES:
        return True
    return False

def move_tests() -> None:
    if not BASE.exists():
        print(f"Tests directory not found: {BASE}")
        return
    ARCHIVE.mkdir(parents=True, exist_ok=True)

    moved = 0
    skipped = 0

    for path in list(BASE.rglob('*')):
        if path.is_dir():
            continue
        if should_skip(path):
            skipped += 1
            continue
        # If file already under archive, skip
        try:
            path.relative_to(ARCHIVE)
            skipped += 1
            continue
        except ValueError:
            pass
        rel = path.relative_to(BASE)
        target = ARCHIVE / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        # If target already exists (rerun), skip
        if target.exists():
            skipped += 1
            continue
        shutil.move(str(path), str(target))
        moved += 1
    print(f"Moved {moved} files. Skipped {skipped} (already archived or excluded).")

if __name__ == "__main__":
    move_tests()
