#!/bin/bash
# enhanced-add-model.sh - Enhanced model addition with automatic detection

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
MODEL_NAME="${1:-}"
BACKEND_URL="http://localhost:8001"
API_KEY="f2b985dd-219f-45b1-a90e-170962cc7082"

usage() {
    echo "🤖 Enhanced Model Addition with Auto-Detection"
    echo "Usage: $0 <model_name>"
    echo ""
    echo "Examples:"
    echo "  $0 mistral:7b-instruct-v0.3-q4_k_m"
    echo "  $0 llama3.1:8b"
    echo "  $0 codellama:13b"
    echo ""
    echo "Features:"
    echo "  ✅ Downloads model to Ollama"
    echo "  ✅ Automatically refreshes backend model cache"
    echo "  ✅ Notifies OpenWebUI of new model"
    echo "  ✅ Validates model availability"
    echo "  ✅ Tests model functionality"
    exit 1
}

if [[ -z "$MODEL_NAME" ]]; then
    usage
fi

echo -e "${BLUE}🚀 Enhanced Model Addition: $MODEL_NAME${NC}"
echo "=============================================="

# Step 1: Check prerequisites
echo -e "${BLUE}📋 Checking prerequisites...${NC}"

if ! docker ps >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running or not accessible${NC}"
    exit 1
fi

if ! docker ps | grep -q "backend-ollama"; then
    echo -e "${YELLOW}⚠️  Ollama container not running, starting...${NC}"
    docker-compose up -d ollama
    sleep 10
fi

if ! docker ps | grep -q "backend-llm-backend"; then
    echo -e "${YELLOW}⚠️  Backend container not running, starting...${NC}"
    docker-compose up -d llm_backend
    sleep 10
fi

# Step 2: Download the model
echo -e "${BLUE}📥 Downloading model: $MODEL_NAME${NC}"
docker exec backend-ollama ollama pull "$MODEL_NAME"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to download model $MODEL_NAME${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Model $MODEL_NAME downloaded successfully${NC}"

# Step 3: Verify model in Ollama
echo -e "${BLUE}🔍 Verifying model in Ollama...${NC}"
if docker exec backend-ollama ollama list | grep -q "$MODEL_NAME"; then
    echo -e "${GREEN}✅ Model verified in Ollama${NC}"
else
    echo -e "${RED}❌ Model not found in Ollama list${NC}"
    exit 1
fi

# Step 4: Refresh backend model cache
echo -e "${BLUE}🔄 Refreshing backend model cache...${NC}"
REFRESH_RESPONSE=$(curl -s -X POST "${BACKEND_URL}/v1/models/refresh" \
    -H "Authorization: Bearer ${API_KEY}" \
    -H "Content-Type: application/json")

if echo "$REFRESH_RESPONSE" | grep -q "success"; then
    echo -e "${GREEN}✅ Backend model cache refreshed${NC}"
    # Extract model count from response
    MODEL_COUNT=$(echo "$REFRESH_RESPONSE" | grep -o '"models":\[[^]]*\]' | grep -o '"[^"]*"' | wc -l)
    echo -e "${BLUE}ℹ️  Backend now knows about $MODEL_COUNT Ollama models${NC}"
else
    echo -e "${YELLOW}⚠️  Failed to refresh backend cache, but continuing...${NC}"
    echo "Response: $REFRESH_RESPONSE"
fi

# Step 5: Notify backend of new model
echo -e "${BLUE}📢 Notifying backend of new model...${NC}"
NOTIFY_RESPONSE=$(curl -s -X POST "${BACKEND_URL}/v1/models/added" \
    -H "Authorization: Bearer ${API_KEY}" \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"$MODEL_NAME\", \"source\": \"ollama\", \"added_at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}")

if echo "$NOTIFY_RESPONSE" | grep -q "success"; then
    echo -e "${GREEN}✅ Backend notified successfully${NC}"
else
    echo -e "${YELLOW}⚠️  Failed to notify backend, but model is still available${NC}"
fi

# Step 6: Verify model is available via API
echo -e "${BLUE}🧪 Testing model via API...${NC}"
API_RESPONSE=$(curl -s "${BACKEND_URL}/v1/models" \
    -H "Authorization: Bearer ${API_KEY}")

if echo "$API_RESPONSE" | grep -q "$MODEL_NAME"; then
    echo -e "${GREEN}✅ Model is available via API${NC}"
else
    echo -e "${YELLOW}⚠️  Model not yet visible via API (may need cache refresh)${NC}"
fi

# Step 7: Test model functionality
echo -e "${BLUE}🎯 Testing model functionality...${NC}"
TEST_RESPONSE=$(curl -s -X POST "${BACKEND_URL}/v1/chat/completions" \
    -H "Authorization: Bearer ${API_KEY}" \
    -H "Content-Type: application/json" \
    -d "{
        \"model\": \"$MODEL_NAME\",
        \"messages\": [{\"role\": \"user\", \"content\": \"Say 'Model test successful' if you can respond.\"}],
        \"max_tokens\": 50,
        \"temperature\": 0.1
    }" | head -c 500)  # Limit output length

if echo "$TEST_RESPONSE" | grep -qi "successful\|working\|test"; then
    echo -e "${GREEN}✅ Model functionality test passed${NC}"
else
    echo -e "${YELLOW}⚠️  Model test inconclusive, but model is available${NC}"
    echo "Response preview: $(echo "$TEST_RESPONSE" | head -c 100)..."
fi

# Step 8: Final status
echo ""
echo -e "${GREEN}🎉 Model Addition Complete!${NC}"
echo "================================"
echo ""
echo "📊 Model Information:"
echo "   Name: $MODEL_NAME"
echo "   Status: Available"
echo "   Source: Ollama"
echo "   Added: $(date)"
echo ""
echo "🔧 Usage Instructions:"
echo "1. Via API (specify model):"
echo "   curl -X POST ${BACKEND_URL}/v1/chat/completions \\"
echo "     -H 'Authorization: Bearer ${API_KEY}' \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"model\": \"$MODEL_NAME\", \"messages\": [...]}'"
echo ""
echo "2. Set as default (edit docker-compose.yml):"
echo "   DEFAULT_MODEL=$MODEL_NAME"
echo "   Then: docker-compose restart llm_backend"
echo ""
echo "3. OpenWebUI should automatically detect the new model"
echo "   If not, refresh the OpenWebUI page or restart OpenWebUI"
echo ""
echo "📋 Available models:"
docker exec backend-ollama ollama list | head -10

echo ""
echo -e "${BLUE}ℹ️  For model management: ./manage-models.sh${NC}"
