#!/bin/bash
# Installation script for ARM64 auto-startup service
# Run this script once to enable automatic startup on boot

set -e

echo "🚀 Installing AI RAG Backend ARM64 Auto-Startup Service"
echo "======================================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root (use sudo)"
    exit 1
fi

# Get the current directory (should be the backend root)
BACKEND_DIR="$(pwd)"
echo "📂 Backend directory: $BACKEND_DIR"

# Get the current user (for running containers)
REAL_USER="${SUDO_USER:-$USER}"
echo "👤 Will run containers as user: $REAL_USER"

# Update the autostart script with correct paths
echo "📝 Updating autostart script paths..."
sed -i "s|BACKEND_DIR=\"/opt/backend\"|BACKEND_DIR=\"$BACKEND_DIR\"|g" scripts/autostart-arm64.sh
sed -i "s|USER=\"pi\"|USER=\"$REAL_USER\"|g" scripts/autostart-arm64.sh

# Update the systemd service with correct paths
sed -i "s|/opt/backend|$BACKEND_DIR|g" setup/ai-rag-backend-arm64.service

# Make autostart script executable
chmod +x scripts/autostart-arm64.sh
echo "✅ Made autostart script executable"

# Copy systemd service file
cp setup/ai-rag-backend-arm64.service /etc/systemd/system/
echo "✅ Copied systemd service file"

# Reload systemd and enable service
systemctl daemon-reload
systemctl enable ai-rag-backend-arm64.service
echo "✅ Enabled auto-startup service"

# Check service status
if systemctl is-enabled ai-rag-backend-arm64.service >/dev/null 2>&1; then
    echo "✅ Service successfully enabled for auto-startup"
else
    echo "❌ Failed to enable service"
    exit 1
fi

echo ""
echo "🎉 ARM64 Auto-Startup Installation Complete!"
echo ""
echo "📋 Service Management Commands:"
echo "   Start now:     sudo systemctl start ai-rag-backend-arm64"
echo "   Stop:          sudo systemctl stop ai-rag-backend-arm64"
echo "   Status:        sudo systemctl status ai-rag-backend-arm64"
echo "   Logs:          sudo journalctl -u ai-rag-backend-arm64 -f"
echo "   Disable:       sudo systemctl disable ai-rag-backend-arm64"
echo ""
echo "🔄 The service will now automatically start on every boot with ARM64 optimizations!"
echo "📊 Logs will be written to: /var/log/ai-rag-backend.log"
echo ""
echo "🧪 Test it now (optional):"
echo "   sudo systemctl start ai-rag-backend-arm64"
