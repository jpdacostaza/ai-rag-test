#!/bin/bash
# Quick Start Script for OpenWebUI Memory Pipeline
# Date: June 24, 2025

echo "🚀 Starting OpenWebUI Memory Pipeline System..."
echo "================================================"

# Start all Docker services
echo "📦 Starting Docker containers..."
docker-compose up -d

echo "⏳ Waiting for services to start (60 seconds)..."
sleep 60

# Check service health
echo "🏥 Checking service health..."
echo "Backend Health:"
curl -s http://localhost:8001/health | jq .

echo -e "\nPipeline Discovery:"
curl -s http://localhost:8001/pipelines | jq .

echo -e "\nDocker Services:"
docker-compose ps

echo -e "\n✅ System Status:"
echo "- Backend: http://localhost:8001"
echo "- OpenWebUI: http://localhost:3000"
echo "- Pipeline Endpoints: http://localhost:8001/pipelines"

echo -e "\n🎯 NEXT STEPS:"
echo "1. Open http://localhost:3000 in browser"
echo "2. Go to Settings → Admin → Pipelines"
echo "3. Enable 'Backend Memory Pipeline'"
echo "4. Test: Say 'My name is John' then ask 'What's my name?'"

echo -e "\n📋 STATUS: Ready for final activation!"
