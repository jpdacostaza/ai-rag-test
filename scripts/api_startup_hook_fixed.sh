#!/bin/bash
# API-Based Function Auto-Installer with Auto-Discovery
# This script handles both API key discovery and function installation

set -e

echo "🔧 API-Based Function Auto-Installer with Auto-Discovery"
echo "========================================================"

# Function to check if OpenWebUI is ready
wait_for_openwebui_basic() {
    local max_attempts=60
    local attempt=0
    
    echo "⏳ Waiting for OpenWebUI basic health..."
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f "http://openwebui:8080/health" >/dev/null 2>&1; then
            echo "✅ OpenWebUI health endpoint responding"
            return 0
        fi
        
        attempt=$((attempt + 1))
        if [ $((attempt % 10)) -eq 0 ]; then
            echo "   Still waiting... (attempt $attempt/$max_attempts)"
        fi
        sleep 5
    done
    
    echo "⚠️ OpenWebUI health check timeout"
    return 1
}

# Function to run auto-discovery
run_autodiscovery() {
    echo "🔍 Starting API key auto-discovery..."
    echo "📋 Debug: Checking Python availability..."
    
    if ! command -v python3 >/dev/null 2>&1; then
        echo "❌ Python3 not found!"
        return 1
    fi
    
    echo "✅ Python3 available: $(python3 --version)"
    echo "📋 Debug: Checking script file..."
    
    if [ ! -f "/app/scripts/api_key_autodiscovery.py" ]; then
        echo "❌ Auto-discovery script not found!"
        return 1
    fi
    
    echo "✅ Auto-discovery script found"
    echo "📋 Debug: Testing Python imports..."
    
    if ! python3 -c "import httpx, json, time, os, sys" 2>/dev/null; then
        echo "❌ Required Python modules not available!"
        echo "📋 Available modules:"
        python3 -c "import sys; print('\n'.join(sys.modules.keys()))" | head -20
        return 1
    fi
    
    echo "✅ Required modules available"
    echo "📋 Debug: Running auto-discovery with verbose output..."
    
    if python3 /app/scripts/api_key_autodiscovery.py; then
        echo "✅ API key auto-discovery successful"
        return 0
    else
        local exit_code=$?
        echo "⚠️ Auto-discovery failed with exit code: $exit_code"
        echo "📋 Debug: Checking for any generated files..."
        ls -la /app/backend/data/ 2>/dev/null || echo "No data directory found"
        return 1
    fi
}

# Function to run function installer
run_function_installer() {
    echo "🚀 Running function installer..."
    
    if python3 /app/scripts/api_function_installer.py; then
        echo "✅ Function installation completed successfully"
        return 0
    else
        echo "⚠️ Function installation had issues"
        return 1
    fi
}

# Function to run continuous monitoring
run_monitoring() {
    echo "🔄 Starting continuous monitoring mode..."
    
    while true; do
        echo "📋 Checking for function updates..."
        
        if python3 /app/scripts/api_function_installer.py; then
            echo "✅ Function check completed"
        else
            echo "⚠️ Function check had issues"
        fi
        
        echo "⏳ Next check in 30 minutes..."
        sleep 1800  # 30 minutes
    done
}

# Main execution
main() {
    echo "Starting API-based setup with auto-discovery..."
    
    # Step 1: Wait for OpenWebUI
    if ! wait_for_openwebui_basic; then
        echo "❌ OpenWebUI not ready - exiting"
        exit 1
    fi
    
    # Step 2: Run auto-discovery (this creates admin account and gets API keys)
    run_autodiscovery
    
    # Step 3: Run initial function installation
    if run_function_installer; then
        echo "✅ Initial setup complete"
    else
        echo "⚠️ Initial setup had issues"
    fi
    
    # Step 4: Start continuous monitoring
    run_monitoring
}

# Handle different modes
case "${1:-}" in
    --once)
        echo "Running in one-time mode..."
        wait_for_openwebui_basic
        run_autodiscovery
        run_function_installer
        ;;
    --autodiscovery-only)
        echo "Running auto-discovery only..."
        wait_for_openwebui_basic
        run_autodiscovery
        ;;
    --install-only)
        echo "Running installation only..."
        run_function_installer
        ;;
    *)
        main
        ;;
esac
