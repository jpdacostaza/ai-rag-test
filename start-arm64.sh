#!/bin/bash
# ARM64-optimized startup script for Orange Pi 5 Plus and similar devices
# Enhanced startup script with ARM64-specific optimizations

set -e

echo "🚀 Starting AI RAG Backend on ARM64 architecture..."
echo "📊 System Info: $(uname -m) - $(nproc) CPU cores - $(free -h | grep Mem | awk '{print $2}') RAM"

# ARM64-specific environment variables
export ARM64_OPTIMIZED=true
export LLM_TIMEOUT=180
export EMBEDDING_BATCH_SIZE=8
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_NUMA=false

# Check available memory and adjust accordingly
TOTAL_MEM=$(free -m | grep Mem | awk '{print $2}')
echo "📈 Available Memory: ${TOTAL_MEM}MB"

if [ "$TOTAL_MEM" -lt 16000 ]; then
    echo "⚠️  Low memory detected (< 16GB). Applying aggressive optimizations..."
    export OLLAMA_MAX_VRAM=2048
    export REDIS_MAX_MEMORY=256mb
    export CHROMA_MAX_MEMORY=1G
else
    echo "✅ Sufficient memory detected. Using standard ARM64 optimizations..."
    export OLLAMA_MAX_VRAM=4096
    export REDIS_MAX_MEMORY=512mb
    export CHROMA_MAX_MEMORY=2G
fi

# Check if models need to be downloaded
echo "🤖 Checking Ollama models..."
if [ ! -d "./storage/ollama" ] || [ -z "$(ls -A ./storage/ollama 2>/dev/null)" ]; then
    echo "📥 No models found. Models will be downloaded on first use."
    echo "⚠️  Note: Initial model download may take longer on ARM64 devices."
fi

# Start services with ARM64 optimizations
echo "🐳 Starting Docker containers with ARM64 optimizations..."

# Use ARM64-optimized compose file
if [ -f "docker-compose.arm64.yml" ]; then
    echo "✅ Using ARM64-optimized configuration"
    docker-compose -f docker-compose.yml -f docker-compose.arm64.yml up -d
else
    echo "⚠️  ARM64 optimizations not found, using standard configuration"
    docker-compose up -d
fi

# Wait for services to start
echo "⏳ Waiting for services to initialize (this may take longer on ARM64)..."
sleep 30

# Health check loop with ARM64-appropriate timeouts
echo "🏥 Performing health checks..."
services=("redis" "chroma" "ollama" "backend" "memory-api" "pipelines" "openwebui")
max_attempts=20  # Longer wait for ARM64
attempt=0

for service in "${services[@]}"; do
    attempt=0
    echo -n "Checking backend-${service}... "
    
    while [ $attempt -lt $max_attempts ]; do
        if docker ps --filter "name=backend-${service}" --filter "health=healthy" | grep -q "backend-${service}"; then
            echo "✅ Healthy"
            break
        elif docker ps --filter "name=backend-${service}" --filter "health=unhealthy" | grep -q "backend-${service}"; then
            echo "❌ Unhealthy"
            docker logs "backend-${service}" --tail 10
            break
        else
            echo -n "."
            sleep 5
            ((attempt++))
        fi
    done
    
    if [ $attempt -eq $max_attempts ]; then
        echo "⏰ Timeout waiting for backend-${service}"
    fi
done

echo ""
echo "🎉 ARM64 Startup Complete!"
echo ""
echo "📍 Service URLs:"
echo "   🌐 OpenWebUI:     http://localhost:8080"
echo "   🚀 Backend API:   http://localhost:3000"
echo "   🧠 Memory API:    http://localhost:5001"
echo "   🤖 Ollama:        http://localhost:11434"
echo "   📊 Pipelines:     http://localhost:9099"
echo ""
echo "💡 ARM64 Performance Tips:"
echo "   • Use smaller embedding models (all-MiniLM-L6-v2 recommended)"
echo "   • Enable document processing bypass for faster responses"
echo "   • Monitor memory usage: docker stats"
echo "   • First model download will be slow - be patient!"
echo ""
echo "🐛 Troubleshooting:"
echo "   • Check logs: docker-compose logs -f [service-name]"
echo "   • Monitor resources: docker stats"
echo "   • Restart if needed: docker-compose restart [service-name]"
