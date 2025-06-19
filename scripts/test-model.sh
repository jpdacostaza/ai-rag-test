#!/bin/bash
# test-model.sh - Test a specific model

set -euo pipefail

MODEL_NAME="${1:-mistral:7b-instruct-v0.3-q4_k_m}"

echo "🧪 Testing model: $MODEL_NAME"
echo "=============================="

# Test via backend API
echo "📡 Testing via backend API..."

curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer f2b985dd-219f-45b1-a90e-170962cc7082" \
  -d '{
    "model": "'"$MODEL_NAME"'",
    "messages": [
      {
        "role": "user", 
        "content": "Hello! Please introduce yourself and tell me what you can do. Keep it brief."
      }
    ],
    "max_tokens": 150,
    "temperature": 0.7
  }' | jq -r '.choices[0].message.content'

echo ""
echo "✅ Model test complete!"
echo ""
echo "📊 Model info:"
docker exec backend-ollama ollama show "$MODEL_NAME" | head -20
