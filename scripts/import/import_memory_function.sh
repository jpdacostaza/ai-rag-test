#!/bin/bash
# OpenWebUI Function Import Script
# This script imports our memory pipeline as a function into OpenWebUI's database

set -e

echo "🚀 OpenWebUI Memory Pipeline Function Import"
echo "=========================================="

# Configuration
OPENWEBUI_URL="http://localhost:3000"
ADMIN_EMAIL="admin@theroot.za.net"
ADMIN_PASSWORD="admin"
PIPELINE_FILE="./memory/simple_working_pipeline.py"
FUNCTION_ID="simple_memory_pipeline"
FUNCTION_NAME="Simple Memory Pipeline"
FUNCTION_DESCRIPTION="Memory pipeline that adds context from previous conversations using Redis and ChromaDB"

echo "⏳ Waiting for OpenWebUI to be ready..."
while ! curl -s "$OPENWEBUI_URL/health" > /dev/null 2>&1; do
    echo "   Waiting for OpenWebUI..."
    sleep 2
done
echo "✅ OpenWebUI is ready!"

echo "🔑 Getting API token..."

# Get API token by signing in
SIGNIN_RESPONSE=$(curl -s -X POST "$OPENWEBUI_URL/api/v1/auths/signin" \
  -H "Content-Type: application/json" \
  --data-raw "{\"email\":\"$ADMIN_EMAIL\", \"password\":\"$ADMIN_PASSWORD\"}")

API_KEY=$(echo "$SIGNIN_RESPONSE" | jq -r '.token')

if [ "$API_KEY" = "null" ] || [ -z "$API_KEY" ]; then
    echo "❌ Failed to get API token. Response: $SIGNIN_RESPONSE"
    exit 1
fi

echo "✅ Got API token: ${API_KEY:0:20}..."

echo "📄 Reading pipeline file..."
if [ ! -f "$PIPELINE_FILE" ]; then
    echo "❌ Pipeline file not found: $PIPELINE_FILE"
    exit 1
fi

# Read the Python file and escape for JSON
PYTHON_CODE=$(jq -Rs . < "$PIPELINE_FILE")

echo "📦 Creating function payload..."

# Create the function payload
FUNCTION_PAYLOAD=$(jq -n \
  --arg id "$FUNCTION_ID" \
  --arg name "$FUNCTION_NAME" \
  --arg desc "$FUNCTION_DESCRIPTION" \
  --argjson content "$PYTHON_CODE" \
  '{
    "id": $id,
    "name": $name,
    "type": "filter",
    "content": $content,
    "meta": {
      "description": $desc,
      "manifest": {
        "type": "filter",
        "requirements": ["httpx"]
      }
    },
    "is_active": true,
    "is_global": false
  }')

echo "🚀 Importing function into OpenWebUI..."

IMPORT_RESPONSE=$(curl -s -X POST "$OPENWEBUI_URL/api/v1/functions/create" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  --data-raw "$FUNCTION_PAYLOAD")

echo "📋 Import response: $IMPORT_RESPONSE"

# Check if import was successful
FUNCTION_ID_RESPONSE=$(echo "$IMPORT_RESPONSE" | jq -r '.id // empty')

if [ -n "$FUNCTION_ID_RESPONSE" ]; then
    echo "✅ Function imported successfully!"
    echo "   Function ID: $FUNCTION_ID_RESPONSE"
    echo ""
    echo "🎯 Next Steps:"
    echo "1. Go to OpenWebUI Admin → Functions"
    echo "2. Find 'Simple Memory Pipeline' and enable it"
    echo "3. Go to Models → llama3.2:3b → Filters"
    echo "4. Add the memory pipeline as a filter"
    echo "5. Chat using llama3.2:3b with memory!"
else
    echo "❌ Function import failed!"
    echo "Response: $IMPORT_RESPONSE"
    exit 1
fi

echo ""
echo "🎉 Memory Pipeline Function Import Complete!"
