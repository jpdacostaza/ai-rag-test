# Troubleshooting Guide - OpenWebUI Enhanced Memory System

## 🚨 Quick Diagnosis

### System Health Check
```bash
# Run comprehensive health check
docker-compose ps && \
curl -s http://localhost:3000/api/health && \
curl -s http://localhost:8001/health && \
echo "All services checked"
```

### Common Symptoms & Quick Fixes

| Symptom | Quick Fix | Command |
|---------|-----------|---------|
| 🔴 Memory not working | Restart memory services | `docker-compose restart memory_api redis chroma` |
| 🔴 LLM not responding | Download model | `docker exec ollama ollama pull llama3.2:3b` |
| 🔴 OpenWebUI 502 error | Restart backend | `docker-compose restart backend` |
| 🔴 Can't access port 8080 | Check port conflicts | `netstat -tulpn \| grep :8080` |
| 🔴 High memory usage | Clean Docker | `docker system prune -a` |

## 🔍 Detailed Troubleshooting

### 1. Memory System Issues

#### Memory Not Storing/Retrieving
**Symptoms:**
- Chat responses don't include previous context
- Memory API returns empty results
- No conversation continuity

**Diagnosis:**
```bash
# Check memory API status
curl http://localhost:8001/health

# Test manual memory storage
curl -X POST http://localhost:8001/api/memory/store \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "content": "test memory"}'

# Check if stored
curl http://localhost:8001/api/memory/retrieve/test
```

**Solutions:**
```bash
# 1. Restart memory services
docker-compose restart memory_api redis chroma

# 2. Check memory API logs
docker-compose logs memory_api

# 3. Verify database connections
docker-compose exec redis redis-cli ping
curl http://localhost:8000/api/v1/heartbeat

# 4. Clear corrupted data
docker-compose exec redis redis-cli FLUSHALL
```

#### Enhanced Memory Pipeline Not Working
**Symptoms:**
- Memory function not visible in OpenWebUI
- Pipeline registration fails
- Authentication errors

**Diagnosis:**
```bash
# Check if pipeline is imported
# Go to OpenWebUI > Admin > Functions
# Look for "Enhanced Memory System"

# Check pipeline logs in OpenWebUI
# Admin > Logs > Function Logs
```

**Solutions:**
```bash
# 1. Re-import pipeline
.\scripts\import\import_memory_function.ps1  # Windows
./scripts/import/import_memory_function.sh   # Linux/Mac

# 2. Manual import
# - Open http://localhost:8080
# - Admin > Functions > Import Function
# - Upload: storage/pipelines/enhanced_memory_pipeline.py

# 3. Check user authentication
# Ensure user is logged in to OpenWebUI
# Check user_id is being passed correctly
```

### 2. LLM Service Issues

#### Ollama Not Responding
**Symptoms:**
- Chat requests timeout
- "Model not available" errors
- Slow response times

**Diagnosis:**
```bash
# Check Ollama service
docker-compose ps ollama
docker-compose logs ollama

# List available models
docker exec ollama ollama list

# Test direct communication
curl http://localhost:11434/api/generate \
  -d '{"model": "llama3.2:3b", "prompt": "Hello", "stream": false}'
```

**Solutions:**
```bash
# 1. Download required model
docker exec ollama ollama pull llama3.2:3b

# 2. Restart Ollama service
docker-compose restart ollama

# 3. Check available disk space
df -h

# 4. Increase memory allocation (in docker-compose.yml)
# ollama:
#   deploy:
#     resources:
#       limits:
#         memory: 8G

# 5. Use smaller model if memory limited
docker exec ollama ollama pull llama3.2:1b
```

#### Model Loading Errors
**Symptoms:**
- "Failed to load model" messages
- Out of memory errors
- CUDA/GPU errors

**Solutions:**
```bash
# 1. Use CPU-only mode (add to docker-compose.yml)
# ollama:
#   environment:
#     - OLLAMA_GPU_ENABLED=false

# 2. Reduce model size
docker exec ollama ollama pull phi:2.7b  # Smaller model

# 3. Clear model cache
docker exec ollama ollama rm llama3.2:3b
docker exec ollama ollama pull llama3.2:3b

# 4. Check system resources
free -h
docker stats ollama
```

### 3. Database Connection Issues

#### Redis Connection Failed
**Symptoms:**
- Memory storage fails
- Redis connection timeout errors
- "Connection refused" messages

**Diagnosis:**
```bash
# Check Redis container
docker-compose ps redis
docker-compose logs redis

# Test Redis connection
docker-compose exec redis redis-cli ping

# Check Redis configuration
docker-compose exec redis redis-cli CONFIG GET "*"
```

**Solutions:**
```bash
# 1. Restart Redis
docker-compose restart redis

# 2. Check Redis data persistence
docker volume ls | grep redis

# 3. Clear Redis data if corrupted
docker-compose exec redis redis-cli FLUSHALL

# 4. Check Redis memory usage
docker-compose exec redis redis-cli INFO memory

# 5. Increase Redis memory (docker-compose.yml)
# redis:
#   command: redis-server --maxmemory 2gb
```

#### ChromaDB Connection Issues
**Symptoms:**
- Vector search not working
- ChromaDB API errors
- Long-term memory retrieval fails

**Diagnosis:**
```bash
# Check ChromaDB container
docker-compose ps chroma
docker-compose logs chroma

# Test ChromaDB API
curl http://localhost:8000/api/v1/heartbeat
curl http://localhost:8000/api/v1/collections
```

**Solutions:**
```bash
# 1. Restart ChromaDB
docker-compose restart chroma

# 2. Clear ChromaDB data
docker volume rm backend_chroma-data
docker-compose up -d chroma

# 3. Check ChromaDB persistence
docker volume inspect backend_chroma-data

# 4. Verify ChromaDB version compatibility
docker-compose pull chroma
```

### 4. API Gateway Issues

#### Backend API Not Responding
**Symptoms:**
- 502 Bad Gateway errors
- API timeouts
- Connection refused on port 3000

**Diagnosis:**
```bash
# Check backend container
docker-compose ps backend
docker-compose logs backend

# Test backend health
curl http://localhost:3000/api/health

# Check backend dependencies
curl http://localhost:8001/health  # Memory API
curl http://localhost:11434/api/tags  # Ollama
```

**Solutions:**
```bash
# 1. Restart backend
docker-compose restart backend

# 2. Check for port conflicts
sudo netstat -tulpn | grep :3000

# 3. Rebuild backend container
docker-compose build --no-cache backend
docker-compose up -d backend

# 4. Check environment variables
docker-compose exec backend env | grep -E "(OLLAMA|MEMORY|REDIS)"
```

#### OpenWebUI Connection Issues
**Symptoms:**
- Can't access http://localhost:8080
- Login page not loading
- 502/503 errors

**Solutions:**
```bash
# 1. Check OpenWebUI container
docker-compose ps open-webui
docker-compose logs open-webui

# 2. Restart OpenWebUI
docker-compose restart open-webui

# 3. Reset OpenWebUI database
docker-compose down
docker volume rm backend_open-webui
docker-compose up -d

# 4. Check backend connectivity from OpenWebUI
docker-compose exec open-webui curl http://backend:3000/api/health
```

### 5. Performance Issues

#### High Memory Usage
**Symptoms:**
- System becomes slow
- Out of memory errors
- Docker containers being killed

**Diagnosis:**
```bash
# Check system memory
free -h

# Check Docker container memory usage
docker stats

# Check specific container memory
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

**Solutions:**
```bash
# 1. Limit container memory (docker-compose.yml)
services:
  ollama:
    deploy:
      resources:
        limits:
          memory: 4G
  backend:
    deploy:
      resources:
        limits:
          memory: 1G

# 2. Use smaller models
docker exec ollama ollama pull phi:2.7b  # 1.6GB vs 2.2GB

# 3. Clean up Docker
docker system prune -a --volumes

# 4. Optimize Redis memory
docker-compose exec redis redis-cli CONFIG SET maxmemory 512mb
docker-compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

#### Slow Response Times
**Symptoms:**
- Chat responses take >30 seconds
- API calls timeout
- UI becomes unresponsive

**Solutions:**
```bash
# 1. Check CPU usage
top
docker stats

# 2. Optimize model settings (smaller model)
# In OpenWebUI: Settings > Models > Select phi:2.7b

# 3. Reduce context length
# In chat: Settings > Advanced > Context Length: 4096

# 4. Enable streaming
# In chat: Settings > Advanced > Stream Response: ON

# 5. Optimize memory retrieval
# Reduce MAX_MEMORIES in environment variables
```

### 6. Network and Port Issues

#### Port Conflicts
**Symptoms:**
- "Port already in use" errors
- Services can't start
- Connection refused errors

**Diagnosis:**
```bash
# Check what's using ports
sudo netstat -tulpn | grep -E ":8080|:3000|:8001|:6379|:8000|:11434"

# For Windows
netstat -an | findstr "8080 3000 8001 6379 8000 11434"
```

**Solutions:**
```bash
# 1. Stop conflicting services
sudo systemctl stop apache2  # If using port 8080
sudo systemctl stop nginx    # If using port 8080

# 2. Change ports in docker-compose.yml
# ports:
#   - "8081:8080"  # Use 8081 instead of 8080

# 3. Find and kill processes
sudo lsof -ti:8080 | xargs sudo kill -9
```

#### DNS Resolution Issues
**Symptoms:**
- Service-to-service communication fails
- "Name resolution failed" errors
- Internal network connectivity issues

**Solutions:**
```bash
# 1. Restart Docker network
docker-compose down
docker network prune
docker-compose up -d

# 2. Check Docker network
docker network ls
docker network inspect backend_default

# 3. Test internal connectivity
docker-compose exec backend ping redis
docker-compose exec backend ping chroma
docker-compose exec backend ping ollama
```

## 🛠️ Advanced Debugging

### Log Analysis
```bash
# Comprehensive log collection
mkdir -p logs
docker-compose logs backend > logs/backend.log
docker-compose logs memory_api > logs/memory_api.log
docker-compose logs ollama > logs/ollama.log
docker-compose logs redis > logs/redis.log
docker-compose logs chroma > logs/chroma.log

# Search for errors
grep -i error logs/*.log
grep -i exception logs/*.log
grep -i failed logs/*.log
```

### Database Debugging
```bash
# Redis debugging
docker-compose exec redis redis-cli
> INFO
> KEYS *
> GET user:memory:*

# ChromaDB debugging
curl http://localhost:8000/api/v1/collections
curl http://localhost:8000/api/v1/collections/memories/count
```

### Container Health Debugging
```bash
# Check container health
docker inspect backend | grep -A 10 "Health"

# Manual health checks
docker-compose exec backend curl localhost:3000/api/health
docker-compose exec memory_api curl localhost:8080/health
```

## 📞 Support and Resources

### Getting Help
1. **Check logs first**: `docker-compose logs [service_name]`
2. **Verify configuration**: Check environment variables and ports
3. **Test individual components**: Use curl commands to test each service
4. **Check resources**: Monitor CPU, memory, and disk usage
5. **Review documentation**: Refer to setup guide and API documentation

### Common Error Codes
- **502 Bad Gateway**: Backend service down or unreachable
- **Connection refused**: Service not running or port blocked
- **Out of memory**: Insufficient system resources
- **Model not found**: LLM model not downloaded
- **Authentication failed**: User not logged in or invalid session

### Diagnostic Commands Cheat Sheet
```bash
# Service status
docker-compose ps

# Service logs
docker-compose logs -f [service_name]

# Health checks
curl http://localhost:3000/api/health    # Backend
curl http://localhost:8001/health        # Memory API
curl http://localhost:11434/api/tags     # Ollama

# Resource usage
docker stats

# Network connectivity
docker-compose exec backend ping redis
docker-compose exec backend ping chroma
docker-compose exec backend ping ollama

# Database checks
docker-compose exec redis redis-cli ping
curl http://localhost:8000/api/v1/heartbeat

# Container restart
docker-compose restart [service_name]

# Complete reset
docker-compose down && docker system prune -a && docker-compose up -d
```

---

*If you continue to experience issues after following this guide, please check the project documentation or contact support with the specific error messages and logs.*
