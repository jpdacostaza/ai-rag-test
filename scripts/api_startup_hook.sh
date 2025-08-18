#!/bin/bash
# API-Based Function Auto-Installer with Auto-Discovery
# This script handles both API key discovery and function installation

set -e

echo "[STARTUP] API-Based Function Auto-Installer with Auto-Discovery"
echo "========================================================"

# Function to check if OpenWebUI is ready
wait_for_openwebui_basic() {
    local max_attempts=60
    local attempt=0
    
    echo "[INFO] Waiting for OpenWebUI basic health..."
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f "http://openwebui:8080/health" >/dev/null 2>&1; then
            echo "[SUCCESS] OpenWebUI health endpoint responding"
            return 0
        fi
        
        attempt=$((attempt + 1))
        if [ $((attempt % 10)) -eq 0 ]; then
            echo "   Still waiting... (attempt $attempt/$max_attempts)"
        fi
        sleep 5
    done
    
    echo "[WARNING] OpenWebUI health check timeout"
    return 1
}

# Function to run auto-discovery
run_autodiscovery() {
    echo "[STARTUP] Starting API key auto-discovery..."
    echo "[DEBUG] Checking Python availability..."
    
    if ! command -v python3 >/dev/null 2>&1; then
        echo "[ERROR] Python3 not found!"
        return 1
    fi
    
    echo "[SUCCESS] Python3 available: $(python3 --version)"
    echo "[DEBUG] Checking script file..."
    
    if [ ! -f "/app/scripts/api_key_autodiscovery.py" ]; then
        echo "[ERROR] Auto-discovery script not found!"
        return 1
    fi
    
    echo "[SUCCESS] Auto-discovery script found"
    echo "[DEBUG] Testing Python imports..."
    
    if ! python3 -c "import httpx, json, time, os, sys" 2>/dev/null; then
        echo "[ERROR] Required Python modules not available!"
        echo "[DEBUG] Available modules:"
        python3 -c "import sys; print('\n'.join(sys.modules.keys()))" | head -20
        return 1
    fi
    
    echo "[SUCCESS] Required modules available"
    echo "[DEBUG] Running auto-discovery with verbose output..."
    
    if python3 /app/scripts/api_key_autodiscovery.py; then
        echo "[SUCCESS] API key auto-discovery successful"
        return 0
    else
        local exit_code=$?
        echo "[WARNING] Auto-discovery failed with exit code: $exit_code"
        echo "[DEBUG] Checking for any generated files..."
        ls -la /app/backend/data/ 2>/dev/null || echo "No data directory found"
        return 1
    fi
}

# Function to run function installer
run_function_installer() {
    echo "[INFO] Running function installer..."
    
    if python3 /app/scripts/api_function_installer.py; then
        echo "[SUCCESS] Function installation completed successfully"
        return 0
    else
        echo "[WARNING] Function installation had issues"
        return 1
    fi
}

# Function to run continuous monitoring
run_monitoring() {
    echo "[MONITOR] Starting continuous monitoring mode..."
    echo "[INFO] Container will check for admin users every minute until functions are installed"
    echo "[INFO] After successful installation, will validate for 5 minutes then shutdown"
    
    while true; do
        echo ""
        echo "[CHECK] [$(date)] Checking for admin user and functions..."
        
        # First, quickly check if we already have working credentials
        if python3 /app/scripts/api_function_installer.py >/dev/null 2>&1; then
            echo "[SUCCESS] Functions already installed and working!"
            echo "[SHUTDOWN] All systems operational - exiting immediately"
            exit 0
        else
            echo "[WARNING] No working credentials - checking for new admin users..."
            
            # Only run auto-discovery if function installer failed
            if run_autodiscovery; then
                echo "[SUCCESS] Auto-discovery successful - admin user found!"
                
                # Now try function installation
                if python3 /app/scripts/api_function_installer.py; then
                    echo "[SUCCESS] Function installation completed successfully!"
                    echo "[SHUTDOWN] Mission accomplished - exiting immediately"
                    exit 0
                else
                    echo "[WARNING] Function installation failed - will retry next cycle"
                fi
            else
                echo "[WARNING] No admin user with API key found yet"
                echo "[INFO] Waiting for admin user creation at http://localhost:8080"
            fi
        fi
        
        echo "[INFO] Next check in 1 minute..."
        sleep 60  # 1 minute
    done
}

# Main execution
main() {
    echo "Starting API-based setup with auto-discovery..."
    
    # Step 1: Wait for OpenWebUI
    if ! wait_for_openwebui_basic; then
        echo "[ERROR] OpenWebUI not ready - exiting"
        exit 1
    fi
    
    # Step 2: Run auto-discovery (this extracts API keys from existing users)
    if run_autodiscovery; then
        echo "[SUCCESS] Auto-discovery successful - proceeding with function installation"
        
        # Step 3: Run initial function installation
        if run_function_installer; then
            echo "[SUCCESS] Initial setup complete"
        else
            echo "[WARNING] Initial setup had issues"
        fi
    else
        echo "[WARNING] Auto-discovery failed - no admin user found yet"
        echo "[INFO] Continuing in monitoring mode - will retry when admin user is created"
    fi
    
    echo ""
    echo "[MONITOR] Setup phase complete - transitioning to monitoring mode"
    echo "[INFO] Container will remain active for continuous function monitoring"
    
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
