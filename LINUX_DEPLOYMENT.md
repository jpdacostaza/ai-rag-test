# 🐧 Linux Deployment Checklist for LLM Backend

## Pre-Deployment Requirements

### **System Requirements**
- [ ] Linux server (Ubuntu 20.04+ recommended)
- [ ] Docker installed and running
- [ ] Docker Compose v2+ installed
- [ ] User `llama` with UID 1000 (will be created by setup script)
- [ ] Minimum 8GB RAM, 20GB storage
- [ ] Internet access for model downloads

### **File Structure Setup**
- [ ] All files deployed to `/opt/backend/`
- [ ] Proper ownership: `chown -R llama:llama /opt/backend/`
- [ ] Execute permissions on scripts: `chmod +x /opt/backend/*.sh`

## Deployment Steps

### **1. Initial Setup**
```bash
# Switch to deployment directory
cd /opt/backend

# Verify files are present
ls -la  # Should show all project files

# Run permission setup (as root/sudo)
sudo ./fix-permissions.sh
```

### **2. Configuration**
- [ ] Environment variables set (check .env if using)
- [ ] API keys configured (WeatherAPI, OpenAI if needed)
- [ ] Port accessibility (3000 for web UI, 8001 for API)

### **3. Docker Deployment**
```bash
# Start all services
docker-compose up --build -d

# Monitor startup
docker logs -f backend-llm-backend
```

### **4. First-Run Verification**
- [ ] All containers running: `docker-compose ps`
- [ ] Health check passes: `curl http://localhost:8001/health`
- [ ] Model download completed (check logs for llama3.2:3b)
- [ ] Embedding model loaded (Qwen3-Embedding-0.6B)
- [ ] OpenWebUI accessible: `curl http://localhost:3000`

## Service Configuration Details

### **Container User Setup**
```yaml
# In docker-compose.yml - Already configured
user: "1000:1000"  # Runs as llama user for security
```

### **Volume Mappings**
```yaml
volumes:
  - ./storage/backend:/opt/backend/data
  - ./storage/models:/opt/models/sentence_transformers
  - ./storage/chroma:/chroma
  - ./storage/redis:/data
  - ./storage/ollama:/root/.ollama
  - ./storage/openwebui:/app/backend/data
```

### **Environment Variables for Linux**
```yaml
environment:
  - SENTENCE_TRANSFORMERS_HOME=/opt/models/sentence_transformers
  - TRANSFORMERS_CACHE=/opt/models/sentence_transformers
  - HF_HOME=/opt/models/sentence_transformers
  # Prevents home directory creation issues
```

## Post-Deployment Testing

### **Health Checks**
```bash
# Test all health endpoints
curl http://localhost:8001/health
curl http://localhost:8001/health/detailed
curl http://localhost:8001/capabilities
```

### **Tool Testing**
```bash
# Test chat with tools
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "message": "What time is it?"}'
```

### **Expected Success Indicators**
- [ ] All containers show "Up" status
- [ ] Health endpoint returns 3/3 services healthy
- [ ] Chat requests return proper responses
- [ ] Tool functions work (time, weather, calculator)
- [ ] No permission errors in logs
- [ ] Embedding model loaded successfully

## Troubleshooting Common Issues

### **Permission Problems**
```bash
# If containers fail to write to storage
sudo ./fix-permissions.sh
docker-compose restart
```

### **Model Download Issues**
```bash
# Check model download progress
docker logs backend-ollama
docker logs backend-llm-backend | grep MODEL
```

### **Memory Issues**
```bash
# Check container resource usage
docker stats
# Increase system memory if needed
```

### **Network Issues**
```bash
# Check container network
docker network ls
docker network inspect backend_backend-net
```

## Monitoring Commands

### **Log Monitoring**
```bash
# Real-time logs
docker logs -f backend-llm-backend
docker logs -f backend-ollama

# Service status
docker-compose ps
systemctl status docker
```

### **Storage Monitoring**
```bash
# Check disk usage
du -sh /opt/backend/storage/*
df -h  # Overall disk space
```

### **Performance Monitoring**
```bash
# Container resources
docker stats

# System resources
htop
free -h
```

## Backup and Maintenance

### **Data Backup**
```bash
# Create backup
cd /opt/backend
tar -czf backup-$(date +%Y%m%d).tar.gz storage/

# Restore backup
tar -xzf backup-YYYYMMDD.tar.gz
```

### **Updates**
```bash
# Update code
git pull
docker-compose build --no-cache
docker-compose up -d
```

### **Maintenance**
```bash
# Clean up old images
docker system prune -a

# Restart services
docker-compose restart

# Full restart
docker-compose down
docker-compose up -d
```

---

## 🚀 Production Ready Checklist

When all items are checked, your LLM Backend is ready for production use:

**System Status:**
- [ ] All containers running and healthy
- [ ] No permission errors in logs
- [ ] All 10 AI tools operational
- [ ] OpenWebUI accessible and responsive
- [ ] Health monitoring active
- [ ] Storage directories properly mounted
- [ ] User `llama` configured correctly

**Security:**
- [ ] Non-root container execution
- [ ] Proper file permissions (755/644)
- [ ] API key authentication enabled
- [ ] Internal network isolation
- [ ] Firewall rules configured

**Performance:**
- [ ] Model preloaded in memory
- [ ] Embedding system operational
- [ ] Cache systems (Redis) working
- [ ] Response times < 2 seconds
- [ ] Memory usage stable

Your enterprise-grade LLM backend is ready! 🎉
