#!/bin/bash
# initialize-models.sh - Pull required models for the system

set -e

echo "🤖 Initializing required models..."

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to be ready..."
until curl -f http://backend-ollama:11434/api/tags > /dev/null 2>&1; do
    echo "⏳ Ollama not ready yet, waiting 5 seconds..."
    sleep 5
done

echo "✅ Ollama is ready!"

# Pull required models
echo "📥 Pulling required models..."

# Check if llama3.2:4b or qwen3:4b is already available
if docker exec backend-ollama ollama list | grep -q -E "(llama3\.2:.*4b|qwen.*4b)"; then
    echo "✅ 4B model is already available"
else
    echo "📥 Pulling 4B model (trying llama3.2:4b first, then qwen3:4b)..."
    if docker exec backend-ollama ollama pull llama3.2:4b 2>/dev/null; then
        echo "✅ llama3.2:4b pulled successfully"
    elif docker exec backend-ollama ollama pull qwen3:4b 2>/dev/null; then
        echo "✅ qwen3:4b pulled successfully"
    else
        echo "⚠️  Could not pull 4B model, falling back to available model"
        docker exec backend-ollama ollama pull llama3.2:3b
        echo "✅ Fallback model pulled successfully"
    fi
fi

# Check if nomic-embed-text is already available
if docker exec backend-ollama ollama list | grep -q "nomic-embed-text"; then
    echo "✅ nomic-embed-text is already available"
else
    echo "📥 Pulling nomic-embed-text..."
    docker exec backend-ollama ollama pull nomic-embed-text
    echo "✅ nomic-embed-text pulled successfully"
fi

echo "🎉 All required models are ready!"
