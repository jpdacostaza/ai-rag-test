#!/bin/bash
# debug-openwebui-models.sh - Debug OpenWebUI model detection

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

BACKEND_URL="http://localhost:8001"
OPENWEBUI_URL="http://localhost:3000"
API_KEY="f2b985dd-219f-45b1-a90e-170962cc7082"

echo -e "${BLUE}🔍 OpenWebUI Model Detection Debug${NC}"
echo "====================================="

# Check 1: Backend /v1/models endpoint
echo -e "\n${BLUE}1. Checking Backend /v1/models endpoint...${NC}"
BACKEND_MODELS=$(curl -s "${BACKEND_URL}/v1/models" \
    -H "Authorization: Bearer ${API_KEY}" 2>/dev/null)

if [ $? -eq 0 ] && [ -n "$BACKEND_MODELS" ]; then
    echo -e "${GREEN}✅ Backend models endpoint accessible${NC}"
    echo "Models found:"
    echo "$BACKEND_MODELS" | jq -r '.data[].id' 2>/dev/null | while read -r model; do
        echo "  • $model"
    done
else
    echo -e "${RED}❌ Backend models endpoint not accessible${NC}"
    echo "Response: $BACKEND_MODELS"
fi

# Check 2: Ollama direct endpoint
echo -e "\n${BLUE}2. Checking Ollama direct endpoint...${NC}"
OLLAMA_MODELS=$(curl -s "http://localhost:11434/api/tags" 2>/dev/null)

if [ $? -eq 0 ] && [ -n "$OLLAMA_MODELS" ]; then
    echo -e "${GREEN}✅ Ollama endpoint accessible${NC}"
    echo "Ollama models:"
    echo "$OLLAMA_MODELS" | jq -r '.models[].name' 2>/dev/null | while read -r model; do
        echo "  • $model"
    done
else
    echo -e "${RED}❌ Ollama endpoint not accessible${NC}"
fi

# Check 3: Container status
echo -e "\n${BLUE}3. Checking container status...${NC}"
if docker ps | grep -q "backend-llm-backend"; then
    echo -e "${GREEN}✅ Backend container running${NC}"
else
    echo -e "${RED}❌ Backend container not running${NC}"
fi

if docker ps | grep -q "backend-ollama"; then
    echo -e "${GREEN}✅ Ollama container running${NC}"
else
    echo -e "${RED}❌ Ollama container not running${NC}"
fi

if docker ps | grep -q "open-webui"; then
    echo -e "${GREEN}✅ OpenWebUI container running${NC}"
else
    echo -e "${YELLOW}⚠️  OpenWebUI container not found (may be external)${NC}"
fi

# Check 4: Network connectivity
echo -e "\n${BLUE}4. Checking network connectivity...${NC}"
if curl -s "${BACKEND_URL}/health" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend health endpoint accessible${NC}"
else
    echo -e "${RED}❌ Backend health endpoint not accessible${NC}"
fi

if curl -s "http://localhost:11434/api/version" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Ollama API accessible${NC}"
else
    echo -e "${RED}❌ Ollama API not accessible${NC}"
fi

# Check 5: Backend logs for model-related messages
echo -e "\n${BLUE}5. Checking backend logs (last 20 model-related lines)...${NC}"
docker logs backend-llm-backend 2>&1 | grep -i "model\|ollama" | tail -20 | while read -r line; do
    echo "  $line"
done

# Check 6: Force model cache refresh
echo -e "\n${BLUE}6. Force refreshing model cache...${NC}"
REFRESH_RESPONSE=$(curl -s -X POST "${BACKEND_URL}/v1/models/refresh" \
    -H "Authorization: Bearer ${API_KEY}" \
    -H "Content-Type: application/json" 2>/dev/null)

if echo "$REFRESH_RESPONSE" | grep -q "success"; then
    echo -e "${GREEN}✅ Model cache refreshed successfully${NC}"
    echo "$REFRESH_RESPONSE" | jq . 2>/dev/null || echo "$REFRESH_RESPONSE"
else
    echo -e "${RED}❌ Failed to refresh model cache${NC}"
    echo "Response: $REFRESH_RESPONSE"
fi

# Check 7: Test specific model
echo -e "\n${BLUE}7. Testing specific model availability...${NC}"
read -p "Enter model name to test (or press Enter to skip): " TEST_MODEL

if [ -n "$TEST_MODEL" ]; then
    echo "Testing model: $TEST_MODEL"
    
    # Check if model exists in Ollama
    if echo "$OLLAMA_MODELS" | grep -q "$TEST_MODEL"; then
        echo -e "${GREEN}✅ Model exists in Ollama${NC}"
    else
        echo -e "${RED}❌ Model not found in Ollama${NC}"
    fi
    
    # Check if model is available via backend
    if echo "$BACKEND_MODELS" | grep -q "$TEST_MODEL"; then
        echo -e "${GREEN}✅ Model available via backend API${NC}"
    else
        echo -e "${RED}❌ Model not available via backend API${NC}"
    fi
    
    # Test model functionality
    echo "Testing model chat completion..."
    TEST_RESPONSE=$(curl -s -X POST "${BACKEND_URL}/v1/chat/completions" \
        -H "Authorization: Bearer ${API_KEY}" \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"$TEST_MODEL\",
            \"messages\": [{\"role\": \"user\", \"content\": \"Test message\"}],
            \"max_tokens\": 50
        }" 2>/dev/null)
    
    if echo "$TEST_RESPONSE" | grep -q "choices"; then
        echo -e "${GREEN}✅ Model responds to chat completions${NC}"
    else
        echo -e "${RED}❌ Model does not respond properly${NC}"
        echo "Response: $(echo "$TEST_RESPONSE" | head -c 200)..."
    fi
fi

# Recommendations
echo -e "\n${BLUE}💡 Troubleshooting Recommendations:${NC}"
echo "======================================"

if ! echo "$BACKEND_MODELS" | grep -q "mistral\|llama"; then
    echo "• No Ollama models detected via backend - try:"
    echo "  docker-compose restart llm_backend"
    echo "  curl -X POST ${BACKEND_URL}/v1/models/refresh"
fi

if ! docker ps | grep -q "backend-ollama"; then
    echo "• Ollama container not running - try:"
    echo "  docker-compose up -d ollama"
fi

echo "• If OpenWebUI doesn't show new models:"
echo "  1. Refresh the OpenWebUI page (Ctrl+F5)"
echo "  2. Restart OpenWebUI container"
echo "  3. Check OpenWebUI logs for errors"
echo "  4. Verify OpenWebUI is pointing to correct backend URL"

echo "• If models exist but don't work:"
echo "  1. Check model compatibility with your system"
echo "  2. Verify sufficient RAM/storage"
echo "  3. Check Ollama logs: docker logs backend-ollama"

echo ""
echo -e "${GREEN}🎯 Quick Fixes:${NC}"
echo "• Restart backend: docker-compose restart llm_backend"
echo "• Refresh models: curl -X POST ${BACKEND_URL}/v1/models/refresh"
echo "• Add model: ./enhanced-add-model.sh <model_name>"
