# Complete Setup and Deployment Guide

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Docker and Docker Compose installed
- Git (for cloning the repository)
- 8GB+ RAM recommended
- Internet connection for downloading models

### One-Command Setup
```bash
# Clone and start everything
git clone <repository-url>
cd backend
docker-compose up -d

# Import memory function to OpenWebUI (Windows)
.\scripts\import\import_memory_function.ps1

# Test the system
.\tests\memory\test_memory_simple.ps1
```

## 🏗️ Detailed Setup Instructions

### 1. Environment Setup

#### Windows Setup
```powershell
# Install Docker Desktop
# Download from: https://desktop.docker.com/

# Verify installation
docker --version
docker-compose --version

# Clone repository
git clone <repository-url>
cd backend
```

#### Linux Setup
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
sudo pip install docker-compose

# Clone repository
git clone <repository-url>
cd backend
```

#### macOS Setup
```bash
# Install Docker Desktop
# Download from: https://desktop.docker.com/

# Using Homebrew
brew install docker docker-compose

# Clone repository
git clone <repository-url>
cd backend
```

### 2. Configuration

#### Environment Variables (.env file)
```bash
# Core Model Configuration
DEFAULT_MODEL=llama3.2:3b
OLLAMA_BASE_URL=http://ollama:11434
USE_OLLAMA=true

# Memory System Configuration
MEMORY_API_URL=http://memory_api:8080
MEMORY_THRESHOLD=0.1
MAX_MEMORIES=5
MEMORY_AUTO_STORE=true

# Database Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=
CHROMA_HOST=chroma
CHROMA_PORT=8000

# API Configuration
BACKEND_PORT=3000
MEMORY_API_PORT=5001
OPENWEBUI_PORT=8080

# Performance Settings
LLM_TIMEOUT=30
API_TIMEOUT=30
WEB_SEARCH_TIMEOUT=10
MAX_CONCURRENT_REQUESTS=10

# Security Settings
JWT_SECRET_KEY=your-secret-key-here
CORS_ALLOWED_ORIGINS=*
```

#### Service Ports
| Service | Internal Port | External Port | Description |
|---------|---------------|---------------|-------------|
| OpenWebUI | 8080 | 8080 | Main web interface |
| Backend API | 3000 | 3000 | Core API endpoints |
| Memory API | 8080 | 5001 | Memory service |
| Redis | 6379 | 6379 | Short-term storage |
| ChromaDB | 8000 | 8000 | Vector database |
| Ollama | 11434 | 11434 | LLM service |
| Pipelines | 9099 | 9099 | OpenWebUI pipelines |

### 3. Service Startup

#### Start All Services
```bash
# Start in background
docker-compose up -d

# View startup logs
docker-compose logs -f

# Check service status
docker-compose ps
```

#### Verify Services
```bash
# Check all services are running
docker-compose ps

# Expected output:
# NAME                    STATUS              PORTS
# backend                 Up 2 minutes        0.0.0.0:3000->3000/tcp
# memory_api              Up 2 minutes        0.0.0.0:5001->5001/tcp
# redis                   Up 2 minutes        0.0.0.0:6379->6379/tcp
# chroma                  Up 2 minutes        0.0.0.0:8000->8000/tcp
# ollama                  Up 2 minutes        0.0.0.0:11434->11434/tcp
# open-webui              Up 2 minutes        0.0.0.0:8080->8080/tcp
```

#### Health Checks
```bash
# Backend API health
curl http://localhost:3000/api/health

# Memory API health  
curl http://localhost:5001/health

# Ollama service
curl http://localhost:11434/api/tags

# OpenWebUI (should show login page)
curl http://localhost:8080
```

### 4. Memory System Setup

#### Import Memory Pipeline to OpenWebUI

**Windows:**
```powershell
# Automated import script
.\scripts\import\import_memory_function.ps1

# Manual import (if script fails)
# 1. Open http://localhost:8080
# 2. Go to Admin Settings > Functions  
# 3. Click "Import Function"
# 4. Upload: storage/pipelines/enhanced_memory_pipeline.py
```

**Linux/macOS:**
```bash
# Automated import script
./scripts/import/import_memory_function.sh

# Manual import steps same as Windows
```

#### Verify Memory System
```bash
# Test memory storage
curl -X POST http://localhost:8001/api/memory/store \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "content": "User likes coffee in the morning"}'

# Test memory retrieval
curl http://localhost:8001/api/memory/retrieve/test_user

# Expected response:
# {
#   "memories": [
#     {
#       "content": "User likes coffee in the morning",
#       "timestamp": "2025-07-13T10:30:00Z",
#       "relevance_score": 1.0
#     }
#   ],
#   "total": 1
# }
```

### 5. Model Setup

#### Download Default Model
```bash
# Ollama will auto-download on first use
# Manual download (optional):
docker exec ollama ollama pull llama3.2:3b

# List available models
docker exec ollama ollama list
```

#### Configure Additional Models
```bash
# Download larger model (if you have enough RAM)
docker exec ollama ollama pull llama3.1:8b

# Download code-specific model
docker exec ollama ollama pull codellama:7b

# Update model in OpenWebUI settings
# Go to Settings > Models > Select Model
```

## 🔧 Advanced Configuration

### Custom Model Configuration
```python
# In config/model_liberation.json
{
  "models": [
    {
      "name": "llama3.2:3b",
      "display_name": "Llama 3.2 3B",
      "context_length": 8192,
      "temperature": 0.7,
      "recommended_use": "general"
    },
    {
      "name": "codellama:7b", 
      "display_name": "Code Llama 7B",
      "context_length": 16384,
      "temperature": 0.1,
      "recommended_use": "coding"
    }
  ]
}
```

### Memory System Tuning
```python
# In memory API configuration
MEMORY_THRESHOLD = 0.1          # Similarity threshold for retrieval
MAX_MEMORIES = 5                # Max memories per retrieval
REDIS_TTL = 86400              # 24 hours in seconds
PROMOTION_THRESHOLD = 3         # Accesses before ChromaDB promotion
```

### Performance Optimization
```yaml
# docker-compose.override.yml
version: '3.8'
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
          
  ollama:
    deploy:
      resources:
        limits:
          memory: 8G
        reservations:
          memory: 4G
```

## 🐛 Troubleshooting

### Common Issues and Solutions

#### 1. Services Won't Start
```bash
# Check Docker daemon
sudo systemctl status docker

# Check port conflicts
netstat -tulpn | grep :8080

# Check disk space
df -h

# Solution: Free up disk space, stop conflicting services
sudo systemctl start docker
docker-compose down && docker-compose up -d
```

#### 2. Memory System Not Working
```bash
# Check memory API logs
docker-compose logs memory_api

# Check Redis connection
docker-compose exec redis redis-cli ping

# Check ChromaDB connection
curl http://localhost:8000/api/v1/heartbeat

# Solution: Restart memory services
docker-compose restart memory_api redis chroma
```

#### 3. LLM Not Responding
```bash
# Check Ollama service
docker-compose logs ollama

# Check model availability
docker exec ollama ollama list

# Test Ollama directly
curl http://localhost:11434/api/generate \
  -d '{"model": "llama3.2:3b", "prompt": "Hello"}'

# Solution: Download model, restart Ollama
docker exec ollama ollama pull llama3.2:3b
docker-compose restart ollama
```

#### 4. OpenWebUI Login Issues
```bash
# Check OpenWebUI logs
docker-compose logs open-webui

# Reset OpenWebUI database
docker-compose down
docker volume rm backend_open-webui
docker-compose up -d

# Create admin user
# Go to http://localhost:8080 and register first user
```

### Performance Issues

#### High Memory Usage
```bash
# Check memory usage
docker stats

# Reduce model size
# Use smaller model: llama3.2:1b instead of llama3.2:3b

# Optimize Docker
docker system prune -a
```

#### Slow Response Times
```bash
# Check system resources
htop

# Optimize Redis
# Add to docker-compose.yml:
# redis:
#   command: redis-server --maxmemory 1gb --maxmemory-policy allkeys-lru

# Use SSD storage for better I/O
```

## 📊 Monitoring and Maintenance

### Health Monitoring Script
```bash
#!/bin/bash
# health_check.sh
echo "=== System Health Check ==="

# Check all services
docker-compose ps

# Check API endpoints
echo "Backend API:" && curl -s http://localhost:3000/api/health | jq '.status'
echo "Memory API:" && curl -s http://localhost:8001/health | jq '.status' 
echo "Ollama:" && curl -s http://localhost:11434/api/tags | jq '.models | length'

# Check resource usage
echo "=== Resource Usage ==="
docker stats --no-stream
```

### Log Rotation
```bash
# Add to crontab: crontab -e
0 0 * * * docker-compose logs --tail=1000 > /var/log/openwebui/app.log 2>&1
0 0 * * * docker system prune -f
```

### Backup Strategy
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/openwebui_$DATE"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup Redis data
docker exec redis redis-cli BGSAVE
docker cp redis:/data/dump.rdb $BACKUP_DIR/

# Backup ChromaDB data
docker cp chroma:/chroma/chroma.sqlite3 $BACKUP_DIR/

# Backup configuration
cp -r config/ $BACKUP_DIR/
cp docker-compose.yml $BACKUP_DIR/
cp .env $BACKUP_DIR/

echo "Backup completed: $BACKUP_DIR"
```

## 🚀 Production Deployment

### Security Checklist
- [ ] Change default passwords
- [ ] Configure HTTPS/SSL certificates
- [ ] Set up firewall rules
- [ ] Enable authentication
- [ ] Configure CORS properly
- [ ] Set up log monitoring
- [ ] Enable automated backups

### Production docker-compose.yml
```yaml
version: '3.8'
services:
  backend:
    build: .
    environment:
      - NODE_ENV=production
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      
  # Add nginx reverse proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
```

---

*For additional support, check the troubleshooting guide or contact the development team.*
