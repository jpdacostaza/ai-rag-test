#!/bin/bash
# OpenWebUI Backend Startup Script
# This script provides automated startup with dependency management

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 OpenWebUI Backend Startup"
echo "============================"
echo "📍 Project root: $PROJECT_ROOT"

# Change to project directory
cd "$PROJECT_ROOT"

# Function to check if Docker and Docker Compose are available
check_prerequisites() {
    echo "🔍 Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose is not installed or not in PATH"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        echo "❌ Docker daemon is not running"
        exit 1
    fi
    
    echo "✅ Prerequisites check passed"
}

# Function to automatically fix script permissions (backup method)
fix_script_permissions() {
    echo "🔧 Ensuring script permissions as backup..."
    find scripts/ -name "*.sh" -type f -exec chmod +x {} \; 2>/dev/null || true
    find scripts/ -name "*.py" -type f -exec chmod +x {} \; 2>/dev/null || true
    echo "✅ Script permissions verified"
}

# Function to clean up any stuck containers
cleanup_stuck_containers() {
    echo "🧹 Cleaning up any stuck containers..."
    
    # Stop and remove any stuck storage-init containers
    docker stop backend-storage-init 2>/dev/null || true
    docker rm backend-storage-init 2>/dev/null || true
    
    # Stop any containers that might be in error state
    docker-compose stop 2>/dev/null || true
    
    echo "✅ Cleanup completed"
}

# Function to start services in proper order with dependency management
start_services() {
    echo "🚀 Starting services with automated dependency management..."
    
    # Start storage-init first (all other services depend on this)
    echo "📦 Starting storage initializer..."
    docker-compose up storage-init
    
    if [ $? -ne 0 ]; then
        echo "❌ Storage initialization failed"
        exit 1
    fi
    
    echo "✅ Storage initialization completed"
    
    # Start the entire stack (docker-compose will handle dependencies automatically)
    echo "🌟 Starting full OpenWebUI backend stack..."
    docker-compose up -d
    
    echo "✅ All services started"
}

# Function to wait for services to be ready
wait_for_services() {
    echo "⏳ Waiting for services to become ready..."
    
    # Wait for Redis
    echo "   ⏳ Waiting for Redis..."
    local redis_attempts=0
    while [ $redis_attempts -lt 30 ]; do
        if timeout 5 docker exec backend-redis redis-cli ping &> /dev/null; then
            echo "   ✅ Redis is ready"
            break
        fi
        if [ $redis_attempts -eq 29 ]; then
            echo "   ⚠️  Redis timeout after 60 seconds"
        fi
        sleep 2
        redis_attempts=$((redis_attempts + 1))
    done
    
    # Wait for ChromaDB
    echo "   ⏳ Waiting for ChromaDB..."
    local chroma_attempts=0
    while [ $chroma_attempts -lt 30 ]; do
        if timeout 5 curl -s http://localhost:8000/api/v1/heartbeat &> /dev/null; then
            echo "   ✅ ChromaDB is ready"
            break
        fi
        if [ $chroma_attempts -eq 29 ]; then
            echo "   ⚠️  ChromaDB timeout after 60 seconds"
        fi
        sleep 2
        chroma_attempts=$((chroma_attempts + 1))
    done
    
    # Wait for OpenWebUI (more conservative timeout and continue regardless)
    echo "   ⏳ Waiting for OpenWebUI..."
    local openwebui_attempts=0
    while [ $openwebui_attempts -lt 40 ]; do
        if timeout 5 curl -s http://localhost:8080/health &> /dev/null; then
            echo "   ✅ OpenWebUI is ready"
            break
        fi
        if [ $openwebui_attempts -eq 39 ]; then
            echo "   ⚠️  OpenWebUI timeout after 120 seconds - continuing anyway"
            echo "   ℹ️  OpenWebUI may still be starting up in the background"
            break
        fi
        sleep 3
        openwebui_attempts=$((openwebui_attempts + 1))
    done
    
    echo "✅ Core services startup phase complete"
}

# Function to verify the installation
verify_installation() {
    echo "🔍 Verifying installation..."
    
    # Check container status
    echo "📊 Container status:"
    docker-compose ps
    
    echo ""
    echo "📋 Service health check:"
    
    # Check Redis
    if timeout 3 docker exec backend-redis redis-cli ping &> /dev/null; then
        echo "   ✅ Redis: Healthy"
    else
        echo "   ❌ Redis: Unhealthy"
    fi
    
    # Check ChromaDB
    if timeout 3 curl -s http://localhost:8000/api/v1/heartbeat &> /dev/null; then
        echo "   ✅ ChromaDB: Healthy"
    else
        echo "   ❌ ChromaDB: Unhealthy"
    fi
    
    # Check OpenWebUI
    if timeout 3 curl -s http://localhost:8080/health &> /dev/null; then
        echo "   ✅ OpenWebUI: Healthy"
    else
        echo "   ⚠️  OpenWebUI: Not ready yet (may still be loading)"
    fi
    
    # Check Memory API
    if timeout 3 curl -s http://localhost:5001/health &> /dev/null; then
        echo "   ✅ Memory API: Healthy"
    else
        echo "   ⚠️  Memory API: Not responding (may still be starting)"
    fi
    
    # Check API Gateway
    if timeout 3 curl -s http://localhost:8888/gateway/health &> /dev/null; then
        echo "   ✅ API Gateway: Healthy"
    else
        echo "   ⚠️  API Gateway: Not responding (may still be starting)"
    fi
    
    echo ""
    echo "ℹ️  Note: Some services may take additional time to fully initialize"
}

# Function to show access information
show_access_info() {
    echo ""
    echo "🎯 Zero-Configuration Startup Complete!"
    echo "======================================="
    echo ""
    echo "🌐 Access URLs:"
    echo "   OpenWebUI:    http://localhost:8080"
    echo "   API Gateway:  http://localhost:8888"
    echo "   Memory API:   http://localhost:5001"
    echo "   ChromaDB:     http://localhost:8000"
    echo "   Redis:        localhost:6379"
    echo ""
    echo "📋 Management Commands:"
    echo "   Stop all:     docker-compose stop"
    echo "   Start all:    docker-compose start"
    echo "   Restart all:  docker-compose restart"
    echo "   View logs:    docker-compose logs -f [service-name]"
    echo "   Status:       docker-compose ps"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "   Re-run setup: $0"
    echo "   Clean start:  docker-compose down && $0"
    echo "   View logs:    docker-compose logs"
    echo ""
    echo "✅ Your OpenWebUI backend is ready to use!"
}

# Main execution flow
main() {
    echo "Starting zero-configuration automated setup..."
    
    check_prerequisites
    fix_script_permissions
    cleanup_stuck_containers
    start_services
    wait_for_services
    verify_installation
    show_access_info
}

# Handle command line arguments
case "${1:-}" in
    --clean)
        echo "🧹 Performing clean startup..."
        docker-compose down
        main
        ;;
    --status)
        echo "📊 Service Status:"
        docker-compose ps
        verify_installation
        ;;
    --help)
        echo "Zero-Configuration OpenWebUI Backend Startup"
        echo ""
        echo "Usage: $0 [option]"
        echo ""
        echo "Options:"
        echo "  (no args)   Start the backend normally"
        echo "  --clean     Stop all services and start fresh"
        echo "  --status    Check status of all services"
        echo "  --help      Show this help message"
        echo ""
        ;;
    *)
        main
        ;;
esac
