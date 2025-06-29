#!/bin/bash
# start-memory-system.sh - Start the complete memory pipeline system

echo "🚀 Starting Complete Memory Pipeline System"
echo "=========================================="

# Create necessary directories
echo "📁 Creating storage directories..."
mkdir -p storage/memory
mkdir -p storage/pipelines
mkdir -p storage/openwebui
mkdir -p storage/backend
mkdir -p storage/redis
mkdir -p storage/chroma
mkdir -p storage/ollama

# Start the services
echo "🐳 Starting Docker services..."
docker-compose up -d memory_api
echo "⏳ Waiting for Memory API to start..."
sleep 10

docker-compose up -d pipelines
echo "⏳ Waiting for Pipelines server to start..."
sleep 15

docker-compose up -d openwebui
echo "⏳ Waiting for OpenWebUI to start..."
sleep 20

echo "✅ System Status Check:"
echo "========================"

# Check Memory API
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Memory API: Running on http://localhost:8000"
else
    echo "❌ Memory API: Failed to start"
fi

# Check Pipelines Server
if curl -s -H "Authorization: Bearer 0p3n-w3bu!" http://localhost:9098/ > /dev/null; then
    echo "✅ Pipelines Server: Running on http://localhost:9098"
else
    echo "❌ Pipelines Server: Failed to start"
fi

# Check OpenWebUI
if curl -s http://localhost:3000/health > /dev/null; then
    echo "✅ OpenWebUI: Running on http://localhost:3000"
else
    echo "❌ OpenWebUI: Failed to start"
fi

echo ""
echo "🎯 Next Steps:"
echo "1. Open http://localhost:3000 in your browser"
echo "2. Create an admin account (first time only)"
echo "3. Start a conversation and test memory functionality"
echo ""
echo "📋 Test Conversation:"
echo "Say: 'Hi! My name is [Your Name] and I work as [Your Job] at [Company].'"
echo "Then: 'What do you remember about me?'"
echo ""
echo "🔧 To stop the system: docker-compose down"
