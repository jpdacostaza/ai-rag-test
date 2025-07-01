#!/bin/bash
# init_memory_function.sh - Initialize memory function in OpenWebUI
set -e

echo "🧠 Initializing Memory Function for OpenWebUI..."

# Create functions directory if it doesn't exist
mkdir -p /app/backend/data/functions

# Copy memory function if it exists in data directory
if [ -f "/app/backend/data/memory_function_working.py" ]; then
    cp /app/backend/data/memory_function_working.py /app/backend/data/functions/memory_function.py
    chmod 644 /app/backend/data/functions/memory_function.py
    echo "✅ Memory function installed to functions directory"
else
    echo "⚠️ Memory function source file not found"
fi

# List installed functions
echo "📁 Functions directory contents:"
ls -la /app/backend/data/functions/ 2>/dev/null || echo "Functions directory is empty"

echo "🎉 Memory function initialization complete!"
