#!/bin/bash
# Quick Start Script - Non-blocking version that doesn't wait too long
# This script starts services and exits quickly without extensive health checking

set -e

echo "🚀 OpenWebUI Backend Quick Start"
echo "================================"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
cd "$BACKEND_DIR"

# Function to fix script permissions quickly
fix_permissions() {
    echo "🔧 Fixing script permissions..."
    find scripts/ -name "*.sh" -type f -exec chmod +x {} \; 2>/dev/null || true
    find scripts/ -name "*.py" -type f -exec chmod +x {} \; 2>/dev/null || true
    echo "✅ Permissions fixed"
}

# Function to start services
start_services() {
    echo "🚀 Starting services..."
    
    # Stop any existing services first
    docker-compose down --remove-orphans 2>/dev/null || true
    
    # Start services
    docker-compose up -d
    
    echo "✅ Services started"
}

# Function to check basic service startup (quick check only)
quick_health_check() {
    echo "⏳ Quick health check (30 seconds max)..."
    
    sleep 10  # Give services a moment to start
    
    # Quick checks with short timeouts
    echo "   📊 Container status:"
    docker-compose ps
    
    echo ""
    echo "   🔍 Quick connectivity test:"
    
    # Redis - 3 attempts
    for i in {1..3}; do
        if timeout 2 docker exec backend-redis redis-cli ping &> /dev/null; then
            echo "   ✅ Redis: Connected"
            break
        elif [ $i -eq 3 ]; then
            echo "   ⚠️  Redis: Not ready yet"
        fi
        sleep 2
    done
    
    # ChromaDB - 3 attempts
    for i in {1..3}; do
        if timeout 2 curl -s http://localhost:8000/api/v1/heartbeat &> /dev/null; then
            echo "   ✅ ChromaDB: Connected"
            break
        elif [ $i -eq 3 ]; then
            echo "   ⚠️  ChromaDB: Not ready yet"
        fi
        sleep 2
    done
    
    # OpenWebUI - 5 attempts
    for i in {1..5}; do
        if timeout 2 curl -s http://localhost:8080/health &> /dev/null; then
            echo "   ✅ OpenWebUI: Connected"
            break
        elif [ $i -eq 5 ]; then
            echo "   ⚠️  OpenWebUI: Still starting (this is normal)"
        fi
        sleep 3
    done
    
    echo "✅ Quick health check complete"
}

# Function to show access information
show_info() {
    echo ""
    echo "🎯 Quick Start Complete!"
    echo "========================"
    echo ""
    echo "🌐 Services are starting at:"
    echo "   OpenWebUI:    http://localhost:8080"
    echo "   API Gateway:  http://localhost:8888"
    echo "   Memory API:   http://localhost:5001"
    echo ""
    echo "⏰ Services may take 2-5 minutes to fully load"
    echo ""
    echo "📋 Useful commands:"
    echo "   Check status:    docker-compose ps"
    echo "   View logs:       docker-compose logs -f"
    echo "   Stop services:   docker-compose stop"
    echo "   Full restart:    docker-compose restart"
    echo ""
    echo "🔍 If services don't respond immediately:"
    echo "   - Wait a few more minutes for initial startup"
    echo "   - Check logs: docker-compose logs -f openwebui"
    echo "   - Restart if needed: docker-compose restart"
    echo ""
    echo "✅ Backend is starting! Check the URLs above in a few minutes."
}

# Main execution
main() {
    echo "Starting quick deployment..."
    
    fix_permissions
    start_services
    quick_health_check
    show_info
    
    echo ""
    echo "🏁 Quick start script finished!"
    echo "   Services are running in the background."
    echo "   Use 'docker-compose logs -f' to monitor progress."
}

# Handle arguments
case "${1:-}" in
    --help)
        echo "OpenWebUI Backend Quick Start"
        echo ""
        echo "This script starts services quickly without waiting for full initialization."
        echo "Services will continue starting in the background after the script exits."
        echo ""
        echo "Usage: $0"
        echo ""
        ;;
    *)
        main
        ;;
esac
