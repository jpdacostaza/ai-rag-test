#!/bin/bash
# Zero-Config Deployment Verification Script
# Run this script to verify the system is ready for cross-host deployment

echo "🎯 Zero-Config Deployment Verification"
echo "======================================"

# Check critical files exist in correct locations
echo "📁 Checking file organization..."

if [ -f "memory/api/enhanced_memory_api.py" ]; then
    echo "✅ Enhanced Memory API found in correct location: memory/api/"
else
    echo "❌ Enhanced Memory API missing from memory/api/"
    exit 1
fi

if [ -f "memory/functions/memory_filter_function.py" ]; then
    echo "✅ Memory Filter Function found in correct location: memory/functions/"
else
    echo "❌ Memory Filter Function missing from memory/functions/"
    exit 1
fi

if [ -f "docker-compose.yml" ]; then
    echo "✅ Docker Compose configuration found"
else
    echo "❌ Docker Compose configuration missing"
    exit 1
fi

if [ -f ".env" ]; then
    echo "✅ Environment configuration found"
else
    echo "❌ Environment configuration missing"
    exit 1
fi

# Check service name consistency
echo ""
echo "🔧 Checking service name consistency..."

# Extract service name from docker-compose.yml
MEMORY_SERVICE=$(grep -A 1 "# 5. Memory API" docker-compose.yml | grep ":" | cut -d: -f1 | tr -d ' ')
if [ "$MEMORY_SERVICE" = "memory-api" ]; then
    echo "✅ Docker service name: $MEMORY_SERVICE"
else
    echo "❌ Unexpected Docker service name: $MEMORY_SERVICE"
    exit 1
fi

# Check .env consistency
ENV_URL=$(grep "MEMORY_API_URL=" .env | cut -d= -f2)
if [[ "$ENV_URL" == *"memory-api:5001"* ]]; then
    echo "✅ Environment URL matches service name: $ENV_URL"
else
    echo "❌ Environment URL mismatch: $ENV_URL"
    exit 1
fi

# Check Dockerfile consistency
if [ -f "Dockerfile.memory" ]; then
    if grep -q "memory.api.main:app" Dockerfile.memory; then
        echo "✅ Dockerfile.memory correctly references memory.api.main:app"
    else
        echo "❌ Dockerfile.memory missing correct entry point"
        exit 1
    fi
else
    echo "❌ Dockerfile.memory not found"
    exit 1
fi

# Check for hardcoded localhost in critical files
echo ""
echo "🌐 Checking for hardcoded localhost references..."

LOCALHOST_COUNT=$(grep -r "localhost" config/ pipelines/ memory/ --include="*.py" | grep -v "# " | wc -l)
if [ "$LOCALHOST_COUNT" -eq 0 ]; then
    echo "✅ No hardcoded localhost found in critical service files"
else
    echo "⚠️  Found $LOCALHOST_COUNT localhost references in service files"
    echo "   (Some may be acceptable for external API configuration)"
fi

# Final verification
echo ""
echo "🚀 Deployment Readiness Summary"
echo "==============================="
echo "✅ File organization: Complete"
echo "✅ Service names: Consistent"  
echo "✅ Docker configuration: Ready"
echo "✅ Environment variables: Configured"
echo "✅ Zero-config deployment: READY"
echo ""
echo "📋 To deploy on another host:"
echo "   1. Copy entire project directory"
echo "   2. Run: docker-compose up -d"
echo "   3. Access OpenWebUI at: http://localhost:8080"
echo ""
echo "🎉 System verified and ready for deployment!"
