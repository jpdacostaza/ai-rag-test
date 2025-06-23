#!/bin/bash
# fix-permissions.sh - Set proper permissions for Docker volumes on Linux host

echo "=== Setting up permissions for user 'llama' on Linux host ==="

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "This script should be run as root or with sudo"
    echo "Usage: sudo ./fix-permissions.sh"
    exit 1
fi

# Create storage directories if they don't exist
echo "Creating storage directories..."
mkdir -p ./storage/redis
mkdir -p ./storage/chroma/onnx_cache
mkdir -p ./storage/ollama
mkdir -p ./storage/backend
mkdir -p ./storage/models
mkdir -p ./storage/openwebui

# Check if llama user exists, create if not
if ! id "llama" &>/dev/null; then
    echo "Creating llama user (UID 1000)..."
    useradd -r -u 1000 -g users llama || groupadd llama && useradd -r -u 1000 -g llama llama
fi

# Set ownership to llama user
echo "Setting ownership to llama user (UID 1000)..."
chown -R 1000:1000 ./storage

# Set proper permissions
echo "Setting directory permissions..."
chmod -R 755 ./storage
chmod -R 777 ./storage/redis      # Redis needs write access
chmod -R 777 ./storage/chroma     # ChromaDB needs write access  
chmod -R 777 ./storage/ollama     # Ollama needs write access
chmod -R 777 ./storage/backend    # Backend data needs write access
chmod -R 777 ./storage/models     # Model cache needs write access
chmod -R 777 ./storage/openwebui  # OpenWebUI data needs write access

echo "=== Permissions set successfully ==="
echo "All storage directories are now owned by llama user (UID 1000)"
echo "You can now run: docker-compose up -d"
