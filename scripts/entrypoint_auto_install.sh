#!/bin/bash
"""
Auto-installer entrypoint for Memory Function
===========================================

This script runs as a sidecar container to automatically install
the memory function into OpenWebUI when the system starts up.
"""

set -e

echo "🚀 Memory Function Auto-Installer Starting..."

# Install required dependencies
pip install httpx

# Wait a bit for services to stabilize
echo "⏳ Waiting for services to stabilize..."
sleep 30

# Run the auto-installer
echo "🔧 Running automatic function installation..."
python /scripts/auto_install_function.py

# Keep container running for a bit in case of retries needed
echo "✅ Auto-installer completed, keeping container alive for 60 seconds..."
sleep 60

echo "🎉 Auto-installer finished successfully!"
