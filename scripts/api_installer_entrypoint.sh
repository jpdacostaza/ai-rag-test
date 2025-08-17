#!/bin/bash
# API Function Installer Entrypoint with Auto-Discovery
# This script runs inside the api-function-installer container

set -e

echo "🔧 API Function Installer with Auto-Discovery"
echo "============================================="

# Configuration
MAX_AUTODISCOVERY_ATTEMPTS=10
AUTODISCOVERY_DELAY=30

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] [INSTALLER] $1"
}

# Function to check if OpenWebUI is ready
wait_for_openwebui() {
    log "Waiting for OpenWebUI to be ready..."
    
    local attempts=0
    while [ $attempts -lt 60 ]; do
        if curl -s http://openwebui:8080/health &> /dev/null; then
            log "✅ OpenWebUI health check passed"
            return 0
        fi
        
        sleep 10
        attempts=$((attempts + 1))
    done
    
    log "⚠️  OpenWebUI health check timeout"
    return 1
}

# Function to run auto-discovery
run_autodiscovery() {
    log "🔍 Starting API key auto-discovery..."
    
    local attempts=0
    while [ $attempts -lt $MAX_AUTODISCOVERY_ATTEMPTS ]; do
        if python3 /app/scripts/api_key_autodiscovery.py; then
            log "✅ API key auto-discovery successful"
            return 0
        else
            log "❌ Auto-discovery attempt $((attempts + 1))/$MAX_AUTODISCOVERY_ATTEMPTS failed"
            attempts=$((attempts + 1))
            
            if [ $attempts -lt $MAX_AUTODISCOVERY_ATTEMPTS ]; then
                log "⏳ Waiting ${AUTODISCOVERY_DELAY}s before retry..."
                sleep $AUTODISCOVERY_DELAY
            fi
        fi
    done
    
    log "❌ Auto-discovery failed after $MAX_AUTODISCOVERY_ATTEMPTS attempts"
    return 1
}

# Function to run the function installer
run_installer() {
    log "🚀 Running API-based function installer..."
    
    # First try with current configuration
    if python3 /app/scripts/api_function_installer.py; then
        log "✅ Function installation completed successfully"
        return 0
    else
        log "❌ Function installation failed"
        return 1
    fi
}

# Function to run continuous monitoring
run_monitoring() {
    log "🔄 Starting continuous monitoring mode..."
    
    while true; do
        log "📋 Checking for function updates..."
        
        # Run installer to check for changes
        if python3 /app/scripts/api_function_installer.py; then
            log "✅ Function check completed"
        else
            log "⚠️  Function check had issues"
        fi
        
        # Wait before next check (30 minutes)
        log "⏳ Next check in 30 minutes..."
        sleep 1800
    done
}

# Main execution
main() {
    log "Starting API Function Installer service..."
    
    # Step 1: Wait for OpenWebUI
    if ! wait_for_openwebui; then
        log "❌ OpenWebUI not ready - exiting"
        exit 1
    fi
    
    # Step 2: Run auto-discovery
    if ! run_autodiscovery; then
        log "⚠️  Auto-discovery failed - trying with existing configuration"
    fi
    
    # Step 3: Run initial function installation
    if ! run_installer; then
        log "⚠️  Initial function installation failed"
        log "📋 Manual configuration may be required:"
        log "   1. Access OpenWebUI at http://localhost:8080"
        log "   2. Create admin account and get API key"
        log "   3. Update environment variables or restart container"
    fi
    
    # Step 4: Start continuous monitoring
    run_monitoring
}

# Handle different modes
case "${1:-}" in
    --once)
        log "Running in one-time mode..."
        wait_for_openwebui
        run_autodiscovery
        run_installer
        ;;
    --autodiscovery-only)
        log "Running auto-discovery only..."
        wait_for_openwebui
        run_autodiscovery
        ;;
    --install-only)
        log "Running installation only..."
        run_installer
        ;;
    --help)
        echo "API Function Installer Entrypoint"
        echo ""
        echo "Usage: $0 [option]"
        echo ""
        echo "Options:"
        echo "  (no args)            Run full service (continuous)"
        echo "  --once               Run once then exit"
        echo "  --autodiscovery-only Run auto-discovery only"
        echo "  --install-only       Run installation only"
        echo "  --help               Show this help"
        echo ""
        ;;
    *)
        main
        ;;
esac
