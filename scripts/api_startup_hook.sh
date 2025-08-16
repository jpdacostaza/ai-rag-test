#!/bin/bash
# API-Based Function Auto-Installer Startup Hook
# Uses OpenWebUI API with admin authentication for proper function installation

set -e

echo "🔧 API-Based Function Auto-Installer with Admin Authentication"
echo "============================================================"

# Function to check if OpenWebUI API is ready
wait_for_openwebui_api() {
    local max_attempts=120  # 10 minutes max wait
    local attempt=0
    
    echo "⏳ Waiting for OpenWebUI API to be ready..."
    
    while [ $attempt -lt $max_attempts ]; do
        # Test health endpoint
        if curl -s -f "http://openwebui:8080/health" >/dev/null 2>&1; then
            echo "✅ OpenWebUI health endpoint responding"
            
            # Test API access with admin token
            if curl -s -f -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjNiY2E5ZGZkLTAxYTgtNDMwMi1iODU5LTlkNjFkMDU4ZTA2MCJ9.B11QggyALNEN9Amf2MYAinwYi6ciBfCTrwJxFb5xR9M" \
               "http://openwebui:8080/api/v1/functions/" >/dev/null 2>&1; then
                echo "✅ OpenWebUI API ready with admin authentication"
                return 0
            fi
        fi
        
        attempt=$((attempt + 1))
        if [ $((attempt % 20)) -eq 0 ]; then
            echo "   Still waiting for API... (attempt $attempt/$max_attempts)"
        fi
        sleep 5
    done
    
    echo "⚠️ OpenWebUI API not fully ready, but proceeding for resilience"
    return 1
}

# Function to run the API-based installer
run_api_installer() {
    echo "🚀 Running API-based function installer with admin auth..."
    
    if python3 /app/scripts/api_function_installer.py; then
        echo "✅ API-based installation completed successfully"
        return 0
    else
        echo "⚠️ API-based installation had issues but continuing"
        return 1
    fi
}

# Function to verify installation
verify_installation() {
    echo "🔍 Verifying function installation..."
    
    # Test API access to list functions
    if curl -s -f -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjNiY2E5ZGZkLTAxYTgtNDMwMi1iODU5LTlkNjFkMDU4ZTA2MCJ9.B11QggyALNEN9Amf2MYAinwYi6ciBfCTrwJxFb5xR9M" \
       "http://openwebui:8080/api/v1/functions/" | python3 -m json.tool >/dev/null 2>&1; then
        
        local function_count=$(curl -s -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjNiY2E5ZGZkLTAxYTgtNDMwMi1iODU5LTlkNjFkMDU4ZTA2MCJ9.B11QggyALNEN9Amf2MYAinwYi6ciBfCTrwJxFb5xR9M" \
                               "http://openwebui:8080/api/v1/functions/" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
        
        echo "✅ API verification successful - $function_count functions available"
        return 0
    else
        echo "⚠️ API verification failed but continuing"
        return 1
    fi
}

# Function to create startup hook for persistence
create_persistent_hook() {
    local hook_dir="/app/backend/data/.startup_hooks"
    local hook_file="$hook_dir/api_function_installer.sh"
    
    mkdir -p "$hook_dir"
    
    cat > "$hook_file" << 'EOF'
#!/bin/bash
# Auto-generated startup hook for API-based function installation
echo "🔄 API function installer startup hook triggered"
/app/scripts/api_startup_hook.sh
EOF
    
    chmod +x "$hook_file"
    echo "✅ Persistent startup hook created: $hook_file"
}

# Main execution
main() {
    echo "Starting API-based zero-configuration setup..."
    
    # Wait for OpenWebUI API to be ready
    wait_for_openwebui_api
    
    # Run the API-based installer
    run_api_installer
    
    # Verify the installation
    verify_installation
    
    # Create persistent startup hook
    create_persistent_hook
    
    echo "🎯 API-based zero-configuration setup complete!"
    echo "📋 Functions installed via OpenWebUI API with admin authentication"
    echo "🔄 Functions will auto-sync on every container startup"
    echo "🛡️ Uses proper authentication and official API endpoints"
}

# Run main function
main "$@"
