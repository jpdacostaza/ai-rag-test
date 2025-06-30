#!/bin/bash
# secure_deployment.sh - Generate secure tokens for production deployment

set -e

echo "🔐 Setting up secure deployment configuration..."

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "⚠️  This script is designed for Linux. Some commands may not work on other systems."
fi

# Check required tools
if ! command -v openssl &> /dev/null; then
    echo "❌ openssl not found. Installing..."
    sudo apt-get update && sudo apt-get install -y openssl
fi

if ! command -v uuidgen &> /dev/null; then
    echo "❌ uuidgen not found. Installing..."
    sudo apt-get update && sudo apt-get install -y uuid-runtime
fi

# Backup existing .env if it exists
if [ -f .env ]; then
    BACKUP_FILE=".env.backup.$(date +%Y%m%d_%H%M%S)"
    echo "📋 Backing up existing .env to $BACKUP_FILE"
    cp .env "$BACKUP_FILE"
fi

# Generate secure tokens
echo "🔑 Generating secure tokens..."
JWT_SECRET=$(openssl rand -hex 32)
BACKEND_API_KEY=$(uuidgen)
PIPELINES_API_KEY=$(uuidgen)
FUNCTIONS_API_KEY=$(uuidgen)
SECRET_KEY=$(openssl rand -hex 32)

# Create secure .env file
echo "📝 Creating secure .env configuration..."
cat > .env << EOF
# Security Configuration - Generated $(date)
# DO NOT SHARE THESE VALUES OR COMMIT TO VERSION CONTROL

# JWT Configuration
JWT_SECRET=$JWT_SECRET
JWT_ALGORITHM=HS256
SECRET_KEY=$SECRET_KEY

# API Keys - Unique for this deployment
API_KEY=$BACKEND_API_KEY
PIPELINES_API_KEY=$PIPELINES_API_KEY
FUNCTIONS_API_KEY=$FUNCTIONS_API_KEY

# External API Keys (REPLACE WITH YOUR ACTUAL KEYS)
OPENAI_API_KEY=your_openai_key_here
WEATHERAPI_KEY=your_weather_key_here

# Database Configuration  
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# ChromaDB Configuration
CHROMA_HOST=chroma
CHROMA_PORT=8000
CHROMA_PERSIST_DIRECTORY=./storage/chroma

# Ollama Configuration
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2:3b

# Service Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=9099
MEMORY_API_PORT=8000

# Performance Settings
MAX_REQUESTS_PER_MINUTE=60
CACHE_TTL=604800
SIMILARITY_THRESHOLD=0.92

# Security Settings
ENABLE_RATE_LIMITING=true
ENABLE_CORS=true
ENABLE_DEBUG=false

# Logging
LOG_LEVEL=INFO
ENABLE_COLORED_LOGS=false

# Memory System
EMBEDDING_MODEL=intfloat/e5-small-v2
EMBEDDING_PROVIDER=huggingface
EOF

# Secure the .env file
chmod 600 .env
if [ -n "$SUDO_USER" ]; then
    chown $SUDO_USER:$SUDO_USER .env
else
    chown $USER:$USER .env
fi

# Update docker-compose.yml to use environment variables
echo "🐳 Updating docker-compose.yml for secure deployment..."

# Create a backup of docker-compose.yml
cp docker-compose.yml docker-compose.yml.backup

# Replace hardcoded values with environment variables (basic replacements)
sed -i 's/JWT_SECRET=change_this_in_production/JWT_SECRET=${JWT_SECRET}/' docker-compose.yml
sed -i 's/API_KEY=f2b985dd-219f-45b1-a90e-170962cc7082/API_KEY=${API_KEY}/' docker-compose.yml
sed -i 's/PIPELINES_API_KEY=0p3n-w3bu!/PIPELINES_API_KEY=${PIPELINES_API_KEY}/' docker-compose.yml

echo ""
echo "✅ Secure deployment configuration complete!"
echo ""
echo "🔑 Generated secure tokens:"
echo "   JWT_SECRET: ${JWT_SECRET:0:16}..."
echo "   API_KEY: $BACKEND_API_KEY"
echo "   PIPELINES_KEY: $PIPELINES_API_KEY"  
echo "   FUNCTIONS_KEY: $FUNCTIONS_API_KEY"
echo ""
echo "⚠️  CRITICAL NEXT STEPS:"
echo "1. Edit .env and replace placeholder API keys with your actual keys:"
echo "   nano .env"
echo ""
echo "2. Add your actual OpenAI API key:"
echo "   OPENAI_API_KEY=sk-your-actual-key-here"
echo ""
echo "3. Verify .env file permissions (should be 600):"
echo "   ls -la .env"
echo ""
echo "4. Start services:"
echo "   docker-compose up -d"
echo ""
echo "📋 Backup files created:"
echo "   - docker-compose.yml.backup"
if [ -f .env.backup.* ]; then
    echo "   - $(ls .env.backup.* | tail -1)"
fi
echo ""
echo "🔒 Security reminders:"
echo "   - Never commit .env to version control"
echo "   - Keep backup of tokens in secure location"
echo "   - Rotate tokens periodically"
echo "   - Monitor access logs regularly"
