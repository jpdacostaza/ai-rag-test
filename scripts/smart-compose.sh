#!/bin/bash
# Smart Docker Compose wrapper with unified configuration
# Auto-detects ARM64 and applies optimizations to the main docker-compose.yml

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

# Function to detect ARM64 architecture
detect_arm64() {
    local arch=$(uname -m)
    case "$arch" in
        aarch64|arm64)
            return 0  # Is ARM64
            ;;
        *)
            return 1  # Not ARM64
            ;;
    esac
}

# Function to set ARM64 environment variables for the unified compose file
set_arm64_env() {
    echo "🔧 ARM64 detected - applying optimizations..."
    export ARM64_OPTIMIZED=true
    export OLLAMA_NUMA=false
    
    # Detect available memory for optimal settings
    local total_mem=$(free -m | grep '^Mem:' | awk '{print $2}' 2>/dev/null || echo "16384")
    
    if [ "$total_mem" -ge 30000 ]; then
        # High memory ARM64 (32GB+) - Orange Pi 5 Plus with 32GB
        echo "🚀 High-memory ARM64 detected (${total_mem}MB) - applying performance optimizations"
        export OLLAMA_MAX_LOADED_MODELS=2         # Can handle 2 models with 32GB
        export OLLAMA_MAX_VRAM=12288              # 12GB VRAM allocation
        export EMBEDDING_BATCH_SIZE=64            # Larger batches for better performance
        export REDIS_MAX_MEMORY=1024mb            # 1GB Redis cache
        export OLLAMA_NUM_PARALLEL=4              # 4 parallel requests for high-memory ARM64
        export OLLAMA_NUM_THREADS=8               # 8 CPU threads (RK3588 has 8 cores)
    else
        # Standard ARM64 (16GB or less)
        echo "💾 Standard ARM64 detected (${total_mem}MB) - applying conservative optimizations"
        export OLLAMA_MAX_LOADED_MODELS=1
        export OLLAMA_MAX_VRAM=4096
        export EMBEDDING_BATCH_SIZE=16
        export REDIS_MAX_MEMORY=256mb
        export OLLAMA_NUM_PARALLEL=2              # 2 parallel requests for standard ARM64
        export OLLAMA_NUM_THREADS=4               # 4 CPU threads for conservative use
    fi
    
    echo "📄 Using unified docker-compose.yml with ARM64 optimizations"
}

# Function to set standard environment variables for x86_64
set_standard_env() {
    echo "💻 x86_64 detected - using standard configuration..."
    export ARM64_OPTIMIZED=false
    export OLLAMA_NUMA=true
    
    # Detect available memory for optimal settings (Windows/Linux)
    local total_mem
    if command -v free >/dev/null 2>&1; then
        # Linux
        total_mem=$(free -m | grep '^Mem:' | awk '{print $2}')
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        total_mem=$(($(sysctl -n hw.memsize) / 1024 / 1024))
    else
        # Default assumption for Windows or unknown
        total_mem=32768
    fi
    
    if [ "$total_mem" -ge 30000 ]; then
        # High memory x86_64 (32GB+)
        echo "🚀 High-memory x86_64 detected (${total_mem}MB) - applying performance optimizations"
        export OLLAMA_MAX_LOADED_MODELS=3         # Can handle 3 models with good RAM
        export OLLAMA_MAX_VRAM=16384              # 16GB VRAM allocation
        export EMBEDDING_BATCH_SIZE=128           # Large batches for performance
        export REDIS_MAX_MEMORY=2048mb            # 2GB Redis cache
        export OLLAMA_NUM_PARALLEL=6              # 6 parallel requests for high-end systems
        export OLLAMA_NUM_THREADS=16              # 16 CPU threads for high-end systems
    else
        # Standard x86_64 (16GB or less)
        echo "💾 Standard x86_64 detected (${total_mem}MB) - applying standard optimizations"
        export OLLAMA_MAX_LOADED_MODELS=2
        export OLLAMA_MAX_VRAM=8192
        export EMBEDDING_BATCH_SIZE=32
        export REDIS_MAX_MEMORY=512mb
        export OLLAMA_NUM_PARALLEL=4              # 4 parallel requests for standard systems
        export OLLAMA_NUM_THREADS=8               # 8 CPU threads for standard systems
    fi
    
    echo "📄 Using unified docker-compose.yml with standard optimizations"
}

# Function to run docker-compose with unified configuration
run_docker_compose() {
    cd "$BACKEND_DIR" || exit 1
    
    if detect_arm64; then
        echo "🔍 ARM64 architecture detected ($(uname -m))"
        set_arm64_env
    else
        echo "� x86_64 architecture detected ($(uname -m))"
        set_standard_env
    fi
    
    echo "✅ Using unified docker-compose.yml with auto-detected optimizations"
    exec docker compose "$@"
}

# Run docker-compose with all passed arguments
run_docker_compose "$@"
