#!/bin/bash

echo "🚀 Starting Complete Memory System with Functions + Pipelines"
echo "============================================================="

# Create necessary directories
echo "📁 Creating required directories..."
mkdir -p storage/pipelines storage/openwebui storage/backend storage/memory storage/redis storage/chroma storage/ollama storage/models

# Copy memory pipeline to pipelines directory
echo "📁 Setting up memory pipeline..."
cp memory_pipeline.py storage/pipelines/

# Start the main services first
echo "🔄 Starting main Docker services..."
docker-compose up -d --remove-orphans

echo "⏳ Waiting for services to be ready..."
sleep 45

echo "🔍 Checking service health..."
docker-compose ps

echo ""
echo "🛠️ Installing Memory Function..."
docker-compose --profile installer run --rm function_installer

echo ""
echo "🛠️ Installing Memory Pipeline..."
docker-compose --profile installer run --rm pipeline_installer

echo ""
echo "🎯 Complete Setup Instructions:"
echo "==============================="
echo ""
echo "1. Wait for all services to be healthy (check: docker-compose ps)"
echo ""
echo "2. Access OpenWebUI at: http://localhost:8080"
echo "   - Create an account if you haven't already"
echo ""
echo "3. For PIPELINE-based memory (recommended for user isolation):"
echo "   a. Go to Admin Panel > Settings > Connections"
echo "   b. Click '+' to add a new connection"
echo "   c. Set API URL to: http://localhost:9099"
echo "   d. Set API Key to: 0p3n-w3bu!"
echo "   e. Save and verify the connection"
echo "   f. Go to Admin Panel > Settings > Pipelines"
echo "   g. Verify 'Enhanced Memory Pipeline' is listed"
echo "   h. In chat, select models with the Pipelines icon"
echo ""
echo "4. For FUNCTION-based memory (fallback):"
echo "   a. Go to Admin Panel > Settings > Functions"
echo "   b. Verify 'Enhanced Memory Function' is enabled"
echo "   c. Use any model normally"
echo ""
echo "📊 Service URLs:"
echo "- OpenWebUI: http://localhost:8080"
echo "- Pipelines: http://localhost:9099 (for user-specific memory)"
echo "- Backend API: http://localhost:3000"
echo "- Memory API: http://localhost:8001"
echo ""
echo "🔧 Debugging:"
echo "- Pipeline logs: docker logs backend-pipelines"
echo "- Function logs: docker logs backend-openwebui"
echo "- Memory API logs: docker logs backend-memory-api"
echo "- Backend logs: docker logs backend-main"
echo ""
echo "💡 Memory System Features:"
echo "- Functions: DISABLED (Enhanced Memory Pipeline provides proper user isolation)"
echo "- Pipelines: Advanced memory (proper user isolation by email/ID)"
echo ""
echo "✅ Complete memory system setup finished!"
echo "   Both Functions and Pipelines are now available for testing."
