#!/usr/bin/env python3
"""
Cleanup script to remove Python cache files and directories.
"""

import os
import shutil
import sys
from pathlib import Path

def cleanup_pycache(root_dir="."):
    """Remove all __pycache__ directories and .pyc files."""
    root_path = Path(root_dir)
    removed_dirs = 0
    removed_files = 0
    
    print(f"🧹 Cleaning Python cache files in: {root_path.absolute()}")
    
    # Remove __pycache__ directories
    for pycache_dir in root_path.rglob("__pycache__"):
        if pycache_dir.is_dir():
            print(f"  🗑️  Removing: {pycache_dir}")
            shutil.rmtree(pycache_dir)
            removed_dirs += 1
    
    # Remove .pyc files
    for pyc_file in root_path.rglob("*.pyc"):
        if pyc_file.is_file():
            print(f"  🗑️  Removing: {pyc_file}")
            pyc_file.unlink()
            removed_files += 1
    
    # Remove .pyo files (optimized bytecode)
    for pyo_file in root_path.rglob("*.pyo"):
        if pyo_file.is_file():
            print(f"  🗑️  Removing: {pyo_file}")
            pyo_file.unlink()
            removed_files += 1
    
    print(f"✅ Cleanup complete!")
    print(f"   📁 Directories removed: {removed_dirs}")
    print(f"   📄 Files removed: {removed_files}")

if __name__ == "__main__":
    # Allow specifying directory as command line argument
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    cleanup_pycache(target_dir)
