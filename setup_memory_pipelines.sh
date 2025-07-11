#!/bin/bash

echo "🚀 Starting Enhanced Memory System with Pipelines"
echo "=================================================="

# Create necessary directories
mkdir -p storage/pipelines
mkdir -p storage/openwebui
mkdir -p storage/backend
mkdir -p storage/memory
mkdir -p storage/redis
mkdir -p storage/chroma
mkdir -p storage/ollama
mkdir -p storage/models

# Copy memory pipeline to pipelines directory
echo "📁 Setting up memory pipeline..."
cp memory_pipeline.py storage/pipelines/

# Start the services
echo "🔄 Starting Docker services..."
docker-compose up -d

echo "⏳ Waiting for services to be ready..."
sleep 30

echo "🔍 Checking service health..."
docker-compose ps

echo ""
echo "🎯 Setup Instructions:"
echo "====================="
echo ""
echo "1. Wait for all services to start (check with: docker-compose ps)"
echo ""
echo "2. Access OpenWebUI at: http://localhost:8080"
echo "   - Create an account if you haven't already"
echo ""
echo "3. Go to Admin Panel > Settings > Connections"
echo "   - Click the '+' button to add a new connection"
echo "   - Set API URL to: http://localhost:9099"
echo "   - Set API Key to: 0p3n-w3bu!"
echo "   - Save and verify the connection"
echo ""
echo "4. Go to Admin Panel > Settings > Pipelines"
echo "   - You should see 'Enhanced Memory Pipeline'"
echo "   - Configure the valves if needed:"
echo "     * backend_url: http://backend:3000 (internal container URL)"
echo "     * debug: true (for testing)"
echo ""
echo "5. In a chat, select a model that routes through Pipelines"
echo "   - Look for the Pipelines icon next to model names"
echo ""
echo "📊 Service URLs:"
echo "- OpenWebUI: http://localhost:8080"
echo "- Pipelines: http://localhost:9099"
echo "- Backend API: http://localhost:3000"
echo "- Memory API: http://localhost:8001"
echo ""
echo "🔧 Debugging:"
echo "- Pipeline logs: docker logs backend-pipelines"
echo "- Memory API logs: docker logs backend-memory-api"
echo "- Backend logs: docker logs backend-main"
echo ""
echo "✅ Setup complete! Your memory system now has proper user identification."
