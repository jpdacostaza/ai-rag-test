# ARM64 Optimization Guide for Orange Pi 5 Plus

## Document Upload Process Analysis

When you upload a document on ARM64 architecture, here's what happens and why timeouts occur:

### 1. Document Processing Flow

```
File Upload → Text Extraction → Chunking → Embedding Generation → Vector Storage → LLM Query → Timeout
   ~1s            ~2s           ~1s           ~15-30s            ~2s        ~60s+      FAIL
```

### 2. ARM64-Specific Issues

**Memory Constraints:**
- Orange Pi 5 Plus: 32GB RAM (good, but different memory architecture)
- ARM64 has different memory access patterns vs x86_64
- ChromaDB + Redis + Ollama + Embeddings competing for memory

**CPU Performance:**
- ARM Cortex-A76 cores are powerful but different instruction set
- Embedding models (sentence-transformers) not optimized for ARM64
- Model inference takes 2-3x longer than equivalent x86_64 CPU

**Timeout Issues:**
- Default 60s timeout too short for ARM64 model processing
- Document embedding generation can take 20-30s on ARM64
- LLM inference adds another 30-60s under load

### 3. Applied Optimizations

#### A. Timeout Adjustments
```python
# services/llm_service.py - Extended timeouts for ARM64
timeout = httpx.Timeout(timeout=180.0, connect=30.0, read=120.0, write=30.0)
```

#### B. Memory Management
```yaml
# docker-compose.arm64.yml
OLLAMA_MAX_LOADED_MODELS=1     # Only one model in memory
OLLAMA_MAX_VRAM=4096           # Limit VRAM usage
EMBEDDING_BATCH_SIZE=8         # Smaller embedding batches
```

#### C. Processing Optimizations
```python
# utilities/rag.py - ARM64 optimized chunks
DEFAULT_CHUNK_SIZE = 600       # Smaller chunks (vs 1000)
DEFAULT_CHUNK_OVERLAP = 50     # Less overlap (vs 200)
DEFAULT_SEARCH_LIMIT = 2       # Fewer search results (vs 5)
```

### 4. Recommended Settings for Orange Pi 5 Plus

#### OpenWebUI Document Settings:
```
Top K: 2                    # Reduced from 5
Chunk Size: 600            # Reduced from 1000
Chunk Overlap: 50          # Reduced from 200
Enable bypass settings: ON  # For speed
```

#### Environment Variables:
```bash
ARM64_OPTIMIZED=true
LLM_TIMEOUT=180
EMBEDDING_BATCH_SIZE=8
OLLAMA_MAX_LOADED_MODELS=1
```

### 5. Startup Commands

**🔥 NEW: Smart Auto-Detection (Recommended):**
```bash
# One-time setup (detects ARM64 automatically)
./setup/setup-smart-compose.sh

# Then use normal docker-compose commands
docker-compose up -d    # Automatically applies ARM64 optimizations if detected
```

**Manual ARM64 startup:**
```bash
./start-arm64.sh
```

**Manual with optimizations:**
```bash
export ARM64_OPTIMIZED=true
docker-compose -f docker-compose.yml -f docker-compose.arm64.yml up -d
```

**Smart compose wrapper:**
```bash
# Uses smart detection automatically
./scripts/smart-compose.sh up -d
```

### 6. Performance Monitoring

**Check resource usage:**
```bash
# Monitor all containers
docker stats

# Check specific service
docker logs backend-ollama -f
docker logs backend-main -f
```

**Memory pressure indicators:**
- High swap usage
- Container restarts
- OOM (Out of Memory) kills in logs

### 7. Troubleshooting Document Upload Timeouts

#### Issue: "Cannot connect to Ollama service"
**Cause:** ARM64 model processing exceeds 60s timeout

**Solutions:**
1. Use ARM64-optimized config (already applied)
2. Pre-load your model:
   ```bash
   docker exec backend-ollama ollama pull gemma3:4b
   ```
3. Monitor during upload:
   ```bash
   docker logs backend-ollama -f &
   docker logs backend-main -f
   ```

#### Issue: Slow embedding generation
**Cause:** `sentence-transformers/all-MiniLM-L6-v2` not ARM64-optimized

**Solutions:**
1. Use smaller embedding model (already configured)
2. Process documents in smaller batches
3. Enable document bypass settings in OpenWebUI

#### Issue: Memory pressure
**Symptoms:**
- Container restarts
- Slow responses
- Swap usage

**Solutions:**
1. Reduce `OLLAMA_MAX_VRAM` to 2048MB
2. Use only one model at a time
3. Restart services periodically:
   ```bash
   docker-compose restart backend-ollama
   ```

### 8. Expected Performance on Orange Pi 5 Plus

**Document Upload:**
- Small PDF (1-5 pages): 30-45 seconds
- Medium PDF (10-20 pages): 60-90 seconds  
- Large PDF (50+ pages): 2-5 minutes

**Chat Response (with RAG):**
- Simple query: 10-20 seconds
- Complex query with web search: 30-60 seconds

**First-time model load:**
- Initial download: 5-15 minutes (depending on internet)
- Model loading: 30-60 seconds

### 9. Further Optimizations

If still experiencing issues:

1. **Use lighter model:**
   ```bash
   docker exec backend-ollama ollama pull gemma:2b
   ```

2. **Disable web search temporarily:**
   - Set bypass settings in OpenWebUI
   - Reduces processing overhead

3. **Process documents offline:**
   - Upload during low-usage periods
   - Use curl for bulk uploads

4. **Monitor and tune:**
   ```bash
   # Watch memory usage
   watch -n 1 'free -h && echo "---" && docker stats --no-stream'
   ```

### 10. Success Indicators

Your system is working optimally when:
- Document uploads complete in < 2 minutes
- Chat responses arrive in < 30 seconds  
- No container restarts in logs
- Memory usage stable under 80%
- No timeout errors in logs
- **Auto-starts on boot** with ARM64 optimizations applied

### 11. Smart Auto-Detection Setup (RECOMMENDED)

The easiest way to ensure ARM64 optimizations are always applied:

**One-time setup:**
```bash
# Run this once to enable smart detection
./setup/setup-smart-compose.sh
```

**What this does:**
- ✅ **Automatic ARM64 detection** - No manual configuration needed
- ✅ **Docker auto-restart** - Containers restart on boot with `restart: always`
- ✅ **Smart environment variables** - ARM64 settings applied automatically
- ✅ **No systemd needed** - Uses Docker's built-in restart capabilities

**How it works on boot:**
1. **Docker starts containers** automatically (restart: always)
2. **Smart wrapper detects** `uname -m` architecture 
3. **ARM64 optimizations applied** if `aarch64`/`arm64` detected:
   ```bash
   ARM64_OPTIMIZED=true
   LLM_TIMEOUT=180
   EMBEDDING_BATCH_SIZE=8
   OLLAMA_MAX_LOADED_MODELS=1
   ```
4. **Containers use optimized settings** automatically

**Usage after setup:**
```bash
# All these automatically detect ARM64 and apply optimizations:
docker-compose up -d
docker-compose restart
./scripts/smart-compose.sh up -d

# If smart-compose installed system-wide:
smart-compose up -d
```

### 12. Legacy Auto-Startup (Alternative)

If you prefer systemd-based startup:

### 12. Legacy Auto-Startup (Alternative)

If you prefer systemd-based startup:

**One-time setup:**
```bash
# Install the auto-startup service
sudo ./setup/install-autostart.sh
```

**Service management:**
```bash
# Check status
sudo systemctl status ai-rag-backend-arm64

# Start/stop manually
sudo systemctl start ai-rag-backend-arm64
sudo systemctl stop ai-rag-backend-arm64

# View logs
sudo journalctl -u ai-rag-backend-arm64 -f
tail -f /var/log/ai-rag-backend.log

# Disable auto-startup (if needed)
sudo systemctl disable ai-rag-backend-arm64
```

**Systemd approach:**
1. System waits 30 seconds for network/Docker to be ready
2. Automatically runs `start-arm64.sh` with all optimizations
3. Applies ARM64 environment variables and resource limits
4. Starts all services with the `docker-compose.arm64.yml` override
5. Logs everything to `/var/log/ai-rag-backend.log`

The optimizations I've applied should resolve your timeout issues. The key was extending the timeout from 60s to 180s and reducing processing overhead with smaller chunks and batch sizes optimized for ARM64 architecture.
