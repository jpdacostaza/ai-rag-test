#!/usr/bin/env python3
"""
Python Cache Cleanup Script
===========================

Removes all __pycache__ directories and .pyc files recursively.
Safe to run anytime to clean up Python compilation cache.
"""

import os
import shutil
from pathlib import Path

def cleanup_python_cache():
    """Remove all __pycache__ directories and .pyc files"""
    backend_dir = Path(__file__).parent.parent
    
    removed_dirs = 0
    removed_files = 0
    
    print("🧹 Cleaning Python cache files...")
    print("=" * 40)
    
    # Remove __pycache__ directories
    for pycache_dir in backend_dir.rglob("__pycache__"):
        if pycache_dir.is_dir():
            print(f"Removing directory: {pycache_dir.relative_to(backend_dir)}")
            shutil.rmtree(pycache_dir)
            removed_dirs += 1
    
    # Remove .pyc files
    for pyc_file in backend_dir.rglob("*.pyc"):
        if pyc_file.is_file():
            print(f"Removing file: {pyc_file.relative_to(backend_dir)}")
            pyc_file.unlink()
            removed_files += 1
    
    # Remove .pyo files (optimized bytecode)
    for pyo_file in backend_dir.rglob("*.pyo"):
        if pyo_file.is_file():
            print(f"Removing file: {pyo_file.relative_to(backend_dir)}")
            pyo_file.unlink()
            removed_files += 1
    
    print("=" * 40)
    print(f"✅ Cleanup completed:")
    print(f"   📁 Removed {removed_dirs} __pycache__ directories")
    print(f"   📄 Removed {removed_files} .pyc/.pyo files")
    
    if removed_dirs == 0 and removed_files == 0:
        print("   ℹ️  No cache files found - already clean!")

if __name__ == "__main__":
    cleanup_python_cache()
