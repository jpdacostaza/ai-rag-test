#!/bin/bash

# ARM64 System Health Check and Fix Script
# Run this on your Orange Pi 5 Plus to fix missing file issues

echo "🔧 ARM64 System Health Check & Fix"
echo "=================================="

# Check current directory
echo "📁 Current directory: $(pwd)"

# Check if required files exist
echo ""
echo "📋 Checking required files:"

files_to_check=(
    "config/config_unified.py"
    "pipelines/requirements.txt"
    "utilities/web_search_tool.py"
)

missing_files=()

for file in "${files_to_check[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file - EXISTS"
    else
        echo "❌ $file - MISSING"
        missing_files+=("$file")
    fi
done

# Check Docker container mounts
echo ""
echo "🐳 Checking Docker container mounts:"
docker exec backend-main ls -la /app/config/config_unified.py 2>/dev/null && echo "✅ Config mounted correctly" || echo "❌ Config mount issue"
docker exec backend-main ls -la /app/pipelines/requirements.txt 2>/dev/null && echo "✅ Pipelines mounted correctly" || echo "❌ Pipelines mount issue"
docker exec backend-main ls -la /app/utilities/ 2>/dev/null && echo "✅ Utilities mounted correctly" || echo "❌ Utilities mount issue"

# Fix missing files if any
if [ ${#missing_files[@]} -eq 0 ]; then
    echo ""
    echo "✅ All required files present"
else
    echo ""
    echo "🔧 Creating missing files:"
    
    # Create missing pipelines requirements if needed
    if [[ ! -f "pipelines/requirements.txt" ]]; then
        echo "📝 Creating pipelines/requirements.txt"
        cat > pipelines/requirements.txt << 'EOF'
# Pipeline dependencies
requests>=2.31.0
pydantic>=2.0.0
fastapi>=0.100.0
uvicorn>=0.23.0
httpx>=0.24.0
python-multipart>=0.0.6
aiofiles>=23.0.0
EOF
    fi
    
    # Create missing web search tool if needed
    if [[ ! -f "utilities/web_search_tool.py" ]]; then
        echo "📝 Creating utilities/web_search_tool.py"
        mkdir -p utilities
        cat > utilities/web_search_tool.py << 'EOF'
"""
Legacy Web Search Tool - Compatibility Module
"""

def should_trigger_web_search(query: str) -> bool:
    """Legacy function - deprecated"""
    return False

def search_web(query: str) -> dict:
    """Legacy function - deprecated"""
    return {"error": "Use Enhanced Web Search Pipeline instead"}
EOF
    fi
fi

# Check ARM64 optimization status
echo ""
echo "🚀 ARM64 Optimization Status:"
docker exec backend-main env | grep ARM64_OPTIMIZED || echo "⚠️  ARM64_OPTIMIZED not set"
docker exec backend-main env | grep LLM_TIMEOUT || echo "⚠️  LLM_TIMEOUT not set"

# Restart containers if fixes were applied
if [ ${#missing_files[@]} -gt 0 ]; then
    echo ""
    echo "🔄 Restarting containers to apply fixes..."
    docker-compose -f docker-compose.yml -f docker-compose.arm64.yml restart backend-main
    echo "✅ Restart completed"
fi

echo ""
echo "🎯 Health Check Complete!"
echo "📊 System should now run without missing file errors."
