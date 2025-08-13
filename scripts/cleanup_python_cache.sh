#!/bin/bash
# Python Cache Cleanup Script (Bash version)
# Removes all __pycache__ directories and .pyc files recursively

echo "🧹 Cleaning Python cache files..."
echo "========================================"

# Count files before cleanup
pycache_dirs=$(find . -type d -name "__pycache__" | wc -l)
pyc_files=$(find . -name "*.pyc" -o -name "*.pyo" | wc -l)

echo "Found:"
echo "  📁 $pycache_dirs __pycache__ directories"
echo "  📄 $pyc_files .pyc/.pyo files"

if [ $pycache_dirs -eq 0 ] && [ $pyc_files -eq 0 ]; then
    echo "✅ Already clean - no cache files found!"
    exit 0
fi

echo ""
echo "Removing..."

# Remove __pycache__ directories
find . -type d -name "__pycache__" -exec echo "Removing directory: {}" \; -exec rm -rf {} +

# Remove .pyc and .pyo files
find . -name "*.pyc" -exec echo "Removing file: {}" \; -delete
find . -name "*.pyo" -exec echo "Removing file: {}" \; -delete

echo ""
echo "✅ Python cache cleanup completed!"
echo "========================================"
