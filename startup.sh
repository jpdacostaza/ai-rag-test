#!/bin/bash
# startup.sh - Ensure all dependencies and services are ready

set -e

echo "=== LLM Backend Startup Script ==="

# Check if requirements are installed
echo "Checking Python dependencies..."
pip install -r requirements.txt --no-cache-dir

# Create complete storage directory structure
echo "Ensuring storage directory structure exists..."
mkdir -p ./storage/redis
mkdir -p ./storage/chroma/onnx_cache
mkdir -p ./storage/ollama
mkdir -p ./storage/backend
mkdir -p ./storage/models
mkdir -p ./storage/openwebui

# Set proper permissions for storage directories
echo "Setting storage directory permissions for Linux user 'llama'..."
chmod -R 755 ./storage
chmod -R 777 ./storage/redis      # Redis needs write access
chmod -R 777 ./storage/chroma     # ChromaDB needs write access
chmod -R 777 ./storage/ollama     # Ollama needs write access
chmod -R 777 ./storage/backend    # Backend data needs write access
chmod -R 777 ./storage/models     # Model cache needs write access
chmod -R 777 ./storage/openwebui  # OpenWebUI data needs write access

echo "Storage structure initialized successfully with proper permissions."

# Start the FastAPI application
echo "Starting FastAPI backend..."
exec uvicorn app:app --host 0.0.0.0 --port 8001 --log-level debug --reload
