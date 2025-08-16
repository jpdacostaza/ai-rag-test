#!/bin/bash
# OpenWebUI SQLite Function Importer Entrypoint
# This script imports functions directly into OpenWebUI's SQLite database

set -e

echo "🚀 Starting OpenWebUI SQLite Function Importer"
echo "==============================================="

# Wait a bit for OpenWebUI to fully start and create database
echo "⏳ Waiting for OpenWebUI to stabilize..."
sleep 30

# Run the SQLite importer
echo "🔄 Running SQLite function importer..."
python /app/scripts/sqlite_function_importer.py

# Exit status
if [ $? -eq 0 ]; then
    echo "✅ Function import completed successfully"
    echo "📋 Functions are now in OpenWebUI database"
    echo "🔄 Refresh the OpenWebUI page to see imported functions"
else
    echo "❌ Function import failed - check logs for details"
    exit 1
fi

echo "🏁 SQLite function importer finished"
