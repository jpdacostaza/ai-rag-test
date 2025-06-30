#!/bin/bash
"""
Simple Function Auto-installer
=============================

This script can be run directly to install the memory function.
It's designed to be lightweight and self-contained.
"""

set -e

# Configuration
OPENWEBUI_URL=${OPENWEBUI_URL:-"http://localhost:3000"}
FUNCTION_FILE=${FUNCTION_FILE:-"./memory_function.py"}
MAX_RETRIES=${MAX_RETRIES:-30}
RETRY_DELAY=${RETRY_DELAY:-10}

echo "🚀 Simple Memory Function Auto-Installer"
echo "========================================"
echo "OpenWebUI URL: $OPENWEBUI_URL"
echo "Function File: $FUNCTION_FILE"

# Function to check if OpenWebUI is ready
wait_for_openwebui() {
    echo "🔍 Waiting for OpenWebUI to be ready..."
    
    for i in $(seq 1 $MAX_RETRIES); do
        if curl -s -f "$OPENWEBUI_URL/api/v1/auths" > /dev/null 2>&1; then
            echo "✅ OpenWebUI is ready!"
            return 0
        fi
        echo "⏳ Attempt $i/$MAX_RETRIES - waiting ${RETRY_DELAY}s..."
        sleep $RETRY_DELAY
    done
    
    echo "❌ OpenWebUI did not become ready within timeout"
    return 1
}

# Function to install the memory function
install_function() {
    echo "🔧 Installing memory function..."
    
    if [ ! -f "$FUNCTION_FILE" ]; then
        echo "❌ Function file not found: $FUNCTION_FILE"
        return 1
    fi
    
    # Read the function code and escape it for JSON
    FUNCTION_CODE=$(cat "$FUNCTION_FILE" | python3 -c "import sys, json; print(json.dumps(sys.stdin.read()))")
    
    # Create the JSON payload
    cat > /tmp/function_payload.json <<EOF
{
    "id": "memory_function",
    "name": "Enhanced Memory Function", 
    "type": "function",
    "content": $FUNCTION_CODE,
    "is_active": true,
    "is_global": true
}
EOF

    # Try to install/update the function
    if curl -s -f "$OPENWEBUI_URL/api/v1/functions/" > /dev/null 2>&1; then
        # Check if function exists
        EXISTING=$(curl -s "$OPENWEBUI_URL/api/v1/functions/" | python3 -c "
import sys, json
try:
    functions = json.load(sys.stdin)
    for func in functions:
        if func.get('id') == 'memory_function':
            print('exists')
            break
    else:
        print('new')
except:
    print('new')
")
        
        if [ "$EXISTING" = "exists" ]; then
            echo "⚠️  Function exists, updating..."
            RESPONSE=$(curl -s -X PUT "$OPENWEBUI_URL/api/v1/functions/memory_function" \
                -H "Content-Type: application/json" \
                -d @/tmp/function_payload.json)
        else
            echo "📦 Installing new function..."
            RESPONSE=$(curl -s -X POST "$OPENWEBUI_URL/api/v1/functions/" \
                -H "Content-Type: application/json" \
                -d @/tmp/function_payload.json)
        fi
        
        # Check response
        if echo "$RESPONSE" | python3 -c "
import sys, json
try:
    result = json.load(sys.stdin)
    if result.get('id') == 'memory_function':
        print('✅ Function installed successfully!')
        print(f'   ID: {result.get(\"id\")}')
        print(f'   Name: {result.get(\"name\")}')
        exit(0)
    else:
        print('❌ Unexpected response')
        print(result)
        exit(1)
except Exception as e:
    print(f'❌ Error parsing response: {e}')
    exit(1)
"; then
            echo "✅ Installation successful!"
            return 0
        else
            echo "❌ Installation failed"
            return 1
        fi
    else
        echo "❌ Cannot access OpenWebUI functions API"
        return 1
    fi
}

# Verify installation
verify_installation() {
    echo "🔍 Verifying installation..."
    
    FUNCTIONS=$(curl -s "$OPENWEBUI_URL/api/v1/functions/")
    if echo "$FUNCTIONS" | python3 -c "
import sys, json
try:
    functions = json.load(sys.stdin)
    for func in functions:
        if func.get('id') == 'memory_function':
            print('✅ Function verified successfully!')
            print(f'   Active: {\"Yes\" if func.get(\"is_active\") else \"No\"}')
            print(f'   Global: {\"Yes\" if func.get(\"is_global\") else \"No\"}')
            exit(0)
    print('⚠️  Function not found in verification')
    exit(1)
except Exception as e:
    print(f'⚠️  Verification error: {e}')
    exit(1)
"; then
        return 0
    else
        return 1
    fi
}

# Main execution
main() {
    # Wait for OpenWebUI
    if ! wait_for_openwebui; then
        exit 1
    fi
    
    # Install function
    if ! install_function; then
        exit 1
    fi
    
    # Verify installation
    verify_installation
    
    echo "🎉 Auto-installation completed successfully!"
}

# Run if called directly
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi
