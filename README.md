# OpenWebUI Backend with API Auto-Discovery

This is a comprehensive OpenWebUI backend that automatically handles API key discovery and function installation.

## Quick Start

### Option 1: Full Startup with API Auto-Discovery (Recommended)
```bash
# Handles API key discovery and function installation automatically
chmod +x scripts/startup_with_autodiscovery.sh
./scripts/startup_with_autodiscovery.sh
```

### Option 2: Standard Startup
```bash
# Standard startup without auto-discovery
chmod +x scripts/zero_config_startup.sh
./scripts/zero_config_startup.sh
```

### Option 3: Quick Start (Fast, minimal waiting)
```bash
# Quick startup that doesn't wait for full initialization
chmod +x scripts/quick_start.sh
./scripts/quick_start.sh
```

## What Gets Started

- **Storage Init**: Directory setup and permissions
- **Redis**: Caching and session storage
- **ChromaDB**: Vector database for embeddings
- **Ollama**: Local LLM inference
- **Backend**: Main API server
- **Memory API**: Advanced memory management
- **Pipelines**: Data processing
- **OpenWebUI**: Frontend interface
- **Function Installer**: Automatic function installation with API discovery
- **API Gateway**: Enhanced routing and rate limiting

## Access Points

After startup:
- **OpenWebUI**: http://localhost:8080
- **API Gateway**: http://localhost:8888
- **Memory API**: http://localhost:5001
- **ChromaDB**: http://localhost:8000

## API Key Auto-Discovery

The system automatically:
1. Waits for OpenWebUI to be ready
2. Creates default admin account (admin@localhost.local / admin123456)
3. Extracts API keys from the database
4. Updates the function installer with correct credentials
5. Installs all functions automatically

## Management Commands

```bash
# Check status
docker-compose ps

# View logs
docker-compose logs -f [service-name]

# Stop services
docker-compose stop

# Restart specific service
docker-compose restart [service-name]

# Clean restart
./scripts/startup_with_autodiscovery.sh --clean

# Check service status
./scripts/startup_with_autodiscovery.sh --status
```

## Manual API Configuration (if auto-discovery fails)

If automatic API discovery fails:

1. Access OpenWebUI: http://localhost:8080
2. Create admin account
3. Go to Settings > Account > API Keys
4. Generate API key
5. Set environment variables:
   ```bash
   export OPENWEBUI_API_KEY="your-api-key"
   export OPENWEBUI_JWT_TOKEN="your-jwt-token"
   ```
6. Restart function installer:
   ```bash
   docker-compose restart api-function-installer
   ```

## Architecture Features

- **No manual intervention required** for API keys
- **Automatic function installation** via official APIs
- **Persistent storage** for all data
- **Health checking** for all services
- **Proper dependency ordering** 
- **Restart policies** for reliability
- **Enterprise-grade** security and monitoring

## Troubleshooting

### Services not responding
```bash
# Check all service status
docker-compose ps

# View logs for specific service
docker-compose logs -f openwebui

# Restart all services
docker-compose restart
```

### Function installation issues
```bash
# Check function installer logs
docker-compose logs api-function-installer

# Manual restart of function installer
docker-compose restart api-function-installer
```

### Permission issues
```bash
# Fix script permissions
find scripts/ -name "*.sh" -exec chmod +x {} \;

# Fix storage permissions
sudo chown -R $USER:$USER storage/
```

The system is designed to handle most issues automatically through health checks and restart policies.
