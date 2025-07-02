#!/bin/bash
"""
Entrypoint for Function Installer Container
==========================================
"""

set -e

echo "🚀 Starting Enhanced Memory Function Auto-Installer..."
echo "================================================"

# Run the Python installer
python3 /scripts/auto_install_function.py

echo "✅ Function installer completed"
exit 0
