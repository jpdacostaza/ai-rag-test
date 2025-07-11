#!/bin/bash

# Entrypoint for Function Installer Container
set -e

echo "🚀 Starting Enhanced Memory Function Auto-Installer..."
echo "================================================"

# Wait for OpenWebUI to be available
echo "Waiting for OpenWebUI to be available..."
while ! curl -s http://openwebui:8080/health > /dev/null; do
    echo "Waiting for OpenWebUI..."
    sleep 5
done

echo "OpenWebUI is available! Starting installation..."

# Run the Python installer
python3 /scripts/auto_install_function.py

echo "✅ Function installer completed"
exit 0
