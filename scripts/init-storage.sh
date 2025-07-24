#!/bin/bash
# Storage Initialization Script
# Creates all required storage directories with proper permissions

set -e

echo "🏗️  Initializing storage directories..."

# Get current user info
CURRENT_USER=$(whoami)
CURRENT_UID=$(id -u)
CURRENT_GID=$(id -g)

echo "📋 Current user: $CURRENT_USER (UID: $CURRENT_UID, GID: $CURRENT_GID)"

# Create storage directories if they don't exist
STORAGE_DIRS=(
    "storage"
    "storage/.cache"
    "storage/chroma"
    "storage/ollama"
    "storage/redis"
    "storage/openwebui"
    "storage/pipelines"
    "storage/models"
    "storage/gateway"
    "storage/installer"
)

for dir in "${STORAGE_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "📁 Creating directory: $dir"
        mkdir -p "$dir"
    else
        echo "✅ Directory exists: $dir"
    fi
done

# Set proper ownership and permissions
echo "🔧 Setting proper ownership and permissions..."

# Option 1: If running as root, set ownership to current user
if [ "$CURRENT_UID" = "0" ]; then
    echo "⚠️  Running as root - setting ownership to user 1000:1000 (typical Docker user)"
    chown -R 1000:1000 storage/
else
    echo "👤 Setting ownership to current user: $CURRENT_USER"
    sudo chown -R $CURRENT_UID:$CURRENT_GID storage/
fi

# Set proper permissions (read/write for owner, read for group)
chmod -R 755 storage/

# Special permissions for cache directories (need write access)
chmod -R 777 storage/.cache
chmod -R 777 storage/models

echo "✅ Storage initialization complete!"
echo ""
echo "📋 Storage directory structure:"
ls -la storage/
