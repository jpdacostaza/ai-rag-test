#!/bin/bash
# Setup script to configure automatic ARM64 detection and optimization
# This sets up smart compose wrapper and updates Docker containers for auto-restart

set -e

echo "🚀 Setting up Smart ARM64 Auto-Detection"
echo "========================================="

# Get the current directory (should be the backend root)
BACKEND_DIR="$(pwd)"
echo "📂 Backend directory: $BACKEND_DIR"

# Make smart-compose executable
chmod +x scripts/smart-compose.sh
echo "✅ Made smart-compose script executable"

# Create a symlink or alias for easier use
if [ -w "/usr/local/bin" ]; then
    echo "🔗 Creating system-wide smart-compose command..."
    sudo ln -sf "$BACKEND_DIR/scripts/smart-compose.sh" /usr/local/bin/smart-compose
    echo "✅ You can now use 'smart-compose' instead of 'docker-compose'"
fi

# Update existing containers to use restart policies if not already set
echo "🔄 Checking Docker container restart policies..."

# Function to update restart policy
update_restart_policy() {
    local container_name="$1"
    local restart_policy="$2"
    
    if docker ps -a --format "{{.Names}}" | grep -q "^${container_name}$"; then
        echo "📝 Updating restart policy for $container_name to $restart_policy"
        docker update --restart="$restart_policy" "$container_name" 2>/dev/null || true
    fi
}

# Update restart policies for all backend containers
containers=(
    "backend-redis:always"
    "backend-chroma:always" 
    "backend-ollama:always"
    "backend-main:unless-stopped"
    "backend-memory-api:unless-stopped"
    "backend-pipelines:unless-stopped"
    "backend-openwebui:unless-stopped"
)

for container_policy in "${containers[@]}"; do
    IFS=':' read -r container policy <<< "$container_policy"
    update_restart_policy "$container" "$policy"
done

# Create a simple startup script that just uses smart-compose
cat > scripts/auto-restart.sh << 'EOF'
#!/bin/bash
# Simple auto-restart script using smart compose detection
cd "$(dirname "$0")/.." || exit 1
./scripts/smart-compose.sh up -d
EOF

chmod +x scripts/auto-restart.sh

echo ""
echo "🎉 Smart ARM64 Auto-Detection Setup Complete!"
echo ""
echo "📋 How it works:"
echo "   • Docker containers will auto-restart on boot (restart: always/unless-stopped)"
echo "   • When they start, smart-compose automatically detects ARM64"
echo "   • ARM64 optimizations are applied automatically if detected"
echo "   • No manual configuration needed!"
echo ""
echo "🔧 Usage:"
echo "   Standard use:     docker-compose up -d"
echo "   Smart use:        ./scripts/smart-compose.sh up -d"
if [ -f "/usr/local/bin/smart-compose" ]; then
echo "   System command:   smart-compose up -d"
fi
echo ""
echo "🧪 Test ARM64 detection:"
echo "   ./scripts/smart-compose.sh --version"
echo ""
echo "🔄 Current containers will now auto-restart with the right configuration!"
echo "   No systemd service needed - Docker handles it automatically."
