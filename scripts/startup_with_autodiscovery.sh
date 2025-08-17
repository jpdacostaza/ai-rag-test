#!/bin/bash
# OpenWebUI Backend Startup with API Auto-Discovery
# This script handles the automated startup including API key discovery

set -e

echo "🚀 OpenWebUI Backend Startup"
echo "============================"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
cd "$BACKEND_DIR"

# Function to check prerequisites
check_prerequisites() {
    echo "🔍 Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker not found. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose not found. Please install Docker Compose first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        echo "❌ Docker daemon not running. Please start Docker first."
        exit 1
    fi
    
    echo "✅ Prerequisites OK"
}

# Function to fix script permissions
fix_script_permissions() {
    echo "🔧 Fixing script permissions..."
    find scripts/ -name "*.sh" -type f -exec chmod +x {} \; 2>/dev/null || true
    find scripts/ -name "*.py" -type f -exec chmod +x {} \; 2>/dev/null || true
    echo "✅ Script permissions fixed"
}

# Function to cleanup any stuck containers
cleanup_stuck_containers() {
    echo "🧹 Cleaning up any stuck containers..."
    
    # Stop and remove containers that might be stuck
    docker-compose down --remove-orphans 2>/dev/null || true
    
    # Clean up any dangling containers
    docker container prune -f 2>/dev/null || true
    
    echo "✅ Cleanup complete"
}

# Function to start core services first
start_core_services() {
    echo "🚀 Starting core services..."
    
    # Start infrastructure services first
    docker-compose up -d storage-init redis chroma
    
    echo "⏳ Waiting for core infrastructure..."
    sleep 15
    
    # Start Ollama
    docker-compose up -d ollama
    
    echo "⏳ Waiting for Ollama to initialize..."
    sleep 20
    
    echo "✅ Core services started"
}

# Function to start application services
start_app_services() {
    echo "🚀 Starting application services..."
    
    # Start backend and memory services
    docker-compose up -d backend memory-api
    
    echo "⏳ Waiting for backend services..."
    sleep 15
    
    # Start pipelines
    docker-compose up -d pipelines
    
    echo "⏳ Waiting for pipelines..."
    sleep 10
    
    echo "✅ Application services started"
}

# Function to start OpenWebUI and wait for setup
start_openwebui() {
    echo "🌐 Starting OpenWebUI..."
    
    docker-compose up -d openwebui
    
    echo "⏳ Waiting for OpenWebUI to become ready..."
    
    # Wait for OpenWebUI health check with timeout
    local attempts=0
    while [ $attempts -lt 60 ]; do
        if timeout 5 curl -s http://localhost:8080/health &> /dev/null; then
            echo "✅ OpenWebUI health check passed"
            break
        fi
        sleep 5
        attempts=$((attempts + 1))
        
        if [ $attempts -eq 60 ]; then
            echo "⚠️  OpenWebUI health check timeout - but continuing"
        fi
    done
    
    # Additional wait for full initialization
    echo "⏳ Allowing time for OpenWebUI full initialization..."
    sleep 30
    
    echo "✅ OpenWebUI startup phase complete"
}

# Function to handle API key discovery and function installation
setup_function_installer() {
    echo "🔑 Setting up API-based function installer..."
    
    # Start the API key auto-discovery process
    echo "🔍 Starting API key auto-discovery..."
    docker-compose up -d api-function-installer
    
    # Run the auto-discovery script inside the container
    echo "⏳ Running API key auto-discovery (this may take a few minutes)..."
    
    # Give the container time to start
    sleep 10
    
    # Run auto-discovery
    if docker exec backend-api-function-installer python3 /app/scripts/api_key_autodiscovery.py; then
        echo "✅ API key auto-discovery completed successfully"
        
        # Wait a moment for the container to restart itself
        sleep 15
        
        # Check if function installer is working
        echo "🔍 Verifying function installer operation..."
        docker-compose logs api-function-installer | tail -20
        
    else
        echo "⚠️  API key auto-discovery failed - manual configuration may be needed"
        echo ""
        echo "📋 Manual Setup Instructions:"
        echo "1. Access OpenWebUI: http://localhost:8080"
        echo "2. Create an admin account"
        echo "3. Go to Settings > Account > API Keys"
        echo "4. Generate an API key"
        echo "5. Update scripts/api_function_installer.py with your credentials"
        echo "6. Restart the installer: docker-compose restart api-function-installer"
        echo ""
    fi
}

# Function to start remaining services
start_remaining_services() {
    echo "🚀 Starting remaining services..."
    
    # Start API Gateway
    docker-compose up -d api-gateway
    
    echo "⏳ Waiting for all services to stabilize..."
    sleep 20
    
    echo "✅ All services started"
}

# Function to perform quick health checks
quick_health_check() {
    echo "🔍 Performing quick health checks..."
    
    echo "📊 Container status:"
    docker-compose ps
    
    echo ""
    echo "🔍 Quick connectivity tests:"
    
    # Quick checks with timeouts
    if timeout 3 docker exec backend-redis redis-cli ping &> /dev/null; then
        echo "   ✅ Redis: Connected"
    else
        echo "   ⚠️  Redis: Not responding"
    fi
    
    if timeout 3 curl -s http://localhost:8000/api/v1/heartbeat &> /dev/null; then
        echo "   ✅ ChromaDB: Connected"
    else
        echo "   ⚠️  ChromaDB: Not responding"
    fi
    
    if timeout 3 curl -s http://localhost:8080/health &> /dev/null; then
        echo "   ✅ OpenWebUI: Connected"
    else
        echo "   ⚠️  OpenWebUI: Still loading"
    fi
    
    if timeout 3 curl -s http://localhost:5001/health &> /dev/null; then
        echo "   ✅ Memory API: Connected"
    else
        echo "   ⚠️  Memory API: Still starting"
    fi
    
    if timeout 3 curl -s http://localhost:8888/gateway/health &> /dev/null; then
        echo "   ✅ API Gateway: Connected"
    else
        echo "   ⚠️  API Gateway: Still starting"
    fi
    
    echo ""
    echo "ℹ️  Note: Some services may need additional time to fully initialize"
}

# Function to show completion information
show_completion_info() {
    echo ""
    echo "🎉 OpenWebUI Backend Startup Complete!"
    echo "======================================"
    echo ""
    echo "🌐 Access Your Services:"
    echo "   OpenWebUI:     http://localhost:8080"
    echo "   API Gateway:   http://localhost:8888"
    echo "   Memory API:    http://localhost:5001"
    echo "   ChromaDB:      http://localhost:8000"
    echo ""
    echo "🔑 Function Installation:"
    echo "   The system automatically configured API keys for function installation."
    echo "   Check the API Function Installer logs if functions don't appear:"
    echo "   docker-compose logs api-function-installer"
    echo ""
    echo "📋 Management Commands:"
    echo "   Status:        docker-compose ps"
    echo "   Logs:          docker-compose logs -f [service-name]"
    echo "   Stop:          docker-compose stop"
    echo "   Restart:       docker-compose restart"
    echo "   Clean start:   $0 --clean"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "   View all logs: docker-compose logs"
    echo "   Restart all:   docker-compose restart"
    echo "   Clean reset:   docker-compose down && $0"
    echo ""
    echo "✅ Your OpenWebUI backend is ready!"
    echo "   Services will continue initializing in the background."
}

# Main execution flow
main() {
    echo "Starting automated backend startup..."
    
    check_prerequisites
    fix_script_permissions
    cleanup_stuck_containers
    start_core_services
    start_app_services
    start_openwebui
    setup_function_installer
    start_remaining_services
    quick_health_check
    show_completion_info
}

# Handle command line arguments
case "${1:-}" in
    --clean)
        echo "🧹 Performing clean startup..."
        docker-compose down --volumes --remove-orphans
        main
        ;;
    --status)
        echo "📊 Service Status:"
        docker-compose ps
        quick_health_check
        ;;
    --help)
        echo "Enhanced OpenWebUI Backend Startup"
        echo ""
        echo "This script provides automated startup including:"
        echo "  • API key auto-discovery"
        echo "  • Automatic function installation"
        echo "  • Complete service orchestration"
        echo ""
        echo "Usage: $0 [option]"
        echo ""
        echo "Options:"
        echo "  (no args)   Start the backend with full automation"
        echo "  --clean     Stop all services and start fresh"
        echo "  --status    Check status of all services"
        echo "  --help      Show this help message"
        echo ""
        ;;
    *)
        main
        ;;
esac
