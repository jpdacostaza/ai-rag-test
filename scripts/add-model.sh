#!/bin/bash
# add-model.sh - Add and manage Ollama models

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Model to add
MODEL_NAME="${1:-}"

usage() {
    echo "🤖 Add Model to Ollama System"
    echo "Usage: $0 <model_name>"
    echo ""
    echo "Examples:"
    echo "  $0 mistral:7b-instruct-v0.3-q4_k_m"
    echo "  $0 llama3.1:8b"
    echo "  $0 codellama:13b"
    echo ""
    echo "Available model formats:"
    echo "  • mistral:7b-instruct-v0.3-q4_k_m"
    echo "  • llama3.1:8b"
    echo "  • llama3.2:3b (current default)"
    echo "  • codellama:13b"
    echo "  • phi3:3.8b"
    echo "  • qwen2.5:7b"
    exit 1
}

if [[ -z "$MODEL_NAME" ]]; then
    usage
fi

echo -e "${BLUE}🤖 Adding Model: $MODEL_NAME${NC}"
echo "================================"

# Check if Docker is running
if ! docker ps >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running or not accessible${NC}"
    exit 1
fi

# Check if Ollama container is running
if ! docker ps | grep -q "backend-ollama"; then
    echo -e "${YELLOW}⚠️  Ollama container not running, starting services...${NC}"
    docker-compose up -d ollama
    sleep 10
fi

echo -e "${BLUE}📥 Downloading model: $MODEL_NAME${NC}"

# Download the model using Ollama API
docker exec backend-ollama ollama pull "$MODEL_NAME"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Model $MODEL_NAME downloaded successfully${NC}"
else
    echo -e "${RED}❌ Failed to download model $MODEL_NAME${NC}"
    exit 1
fi

echo -e "${BLUE}📋 Verifying model availability...${NC}"

# List all models to verify
echo "Available models:"
docker exec backend-ollama ollama list

echo ""
echo -e "${GREEN}🎉 Model $MODEL_NAME is now available!${NC}"
echo ""
echo "🔧 To use this model:"
echo "1. Set as default in docker-compose.yml:"
echo "   DEFAULT_MODEL=$MODEL_NAME"
echo ""
echo "2. Or use via API with model parameter:"
echo "   curl -X POST http://localhost:8001/v1/chat/completions \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"model\": \"$MODEL_NAME\", \"messages\": [...]}'"
echo ""
echo "3. Test the model:"
echo "   ./test-model.sh $MODEL_NAME"
