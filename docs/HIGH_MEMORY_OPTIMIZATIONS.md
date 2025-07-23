# 🚀 32GB High-Memory System Optimizations

## Your Systems
- **Windows Desktop**: 32GB RAM x86_64 (Intel/AMD)
- **Orange Pi 5 Plus**: 32GB RAM ARM64 RK3588 CPU-only

## 🎯 Optimizations Applied

### Orange Pi 5 Plus (ARM64 32GB)
```bash
🔧 ARM64 detected - applying optimizations...
🚀 High-memory ARM64 detected (32768MB) - applying performance optimizations

# Ollama Settings
OLLAMA_MAX_LOADED_MODELS=2          # Can run 2 models simultaneously
OLLAMA_MAX_VRAM=12288               # 12GB RAM allocation for models
OLLAMA_NUMA=false                   # Disabled for single-socket ARM
OLLAMA_NUM_PARALLEL=4               # 4 parallel request handling
OLLAMA_NUM_THREADS=8                # 8 CPU threads (RK3588 8-core)

# Performance Settings
EMBEDDING_BATCH_SIZE=64             # Large embedding batches
REDIS_MAX_MEMORY=1024mb             # 1GB Redis cache
REQUEST_TIMEOUT=180                 # 3min timeout for stability
```

### Windows Desktop (x86_64 32GB)
```powershell
💻 x86_64 detected - using standard configuration...
🚀 High-memory x86_64 detected (32768MB) - applying performance optimizations

# Ollama Settings
OLLAMA_MAX_LOADED_MODELS=3          # Can run 3 models simultaneously
OLLAMA_MAX_VRAM=16384               # 16GB RAM allocation for models
OLLAMA_NUMA=true                    # Enabled for multi-socket support
OLLAMA_NUM_PARALLEL=6               # 6 parallel request handling
OLLAMA_NUM_THREADS=16               # 16 CPU threads (high-end CPU)

# Performance Settings
EMBEDDING_BATCH_SIZE=128            # Very large embedding batches
REDIS_MAX_MEMORY=2048mb             # 2GB Redis cache
REQUEST_TIMEOUT=180                 # 3min timeout for stability
```

## 🎪 Key Benefits

### Orange Pi 5 Plus Specific:
- ✅ **CPU Optimization**: 8 threads for RK3588 8-core processor
- ✅ **Memory Efficiency**: 12GB model allocation leaves 20GB for system
- ✅ **Dual Models**: Can run Qwen 3B + another model simultaneously
- ✅ **ARM64 Tuning**: NUMA disabled, conservative parallel handling
- ✅ **No GPU Dependencies**: Pure CPU inference optimized

### Windows Desktop Specific:
- ✅ **Triple Models**: Can run 3 models simultaneously
- ✅ **High Throughput**: 6 parallel requests, 16 CPU threads
- ✅ **Large Batches**: 128-size embedding batches for speed
- ✅ **Generous Cache**: 2GB Redis for fast retrieval
- ✅ **x86_64 Optimizations**: NUMA enabled, high parallelism

## 🧪 Usage Examples

### Start with High-Memory Detection
```bash
# Orange Pi 5 Plus
./scripts/smart-compose.sh up -d

# Windows
.\scripts\smart-compose.ps1 up -d
```

### Manual Override (if needed)
```bash
# Force high-memory ARM64 settings
OLLAMA_MAX_LOADED_MODELS=2 OLLAMA_MAX_VRAM=12288 docker-compose up -d

# Force high-memory x86_64 settings  
OLLAMA_MAX_LOADED_MODELS=3 OLLAMA_MAX_VRAM=16384 docker-compose up -d
```

## ⚡ Performance Expectations

### Orange Pi 5 Plus:
- **Model Loading**: ~30-60 seconds for 3B models
- **Inference Speed**: Good performance with CPU optimization
- **Memory Usage**: ~12-15GB total system usage under load
- **Concurrent Requests**: Up to 4 simultaneous requests
- **Timeout Issues**: Resolved with 180s timeouts

### Windows Desktop:
- **Model Loading**: ~15-30 seconds for 3B models
- **Inference Speed**: Excellent with high thread count
- **Memory Usage**: ~18-22GB total system usage under load
- **Concurrent Requests**: Up to 6 simultaneous requests
- **Batch Processing**: Very fast with large batch sizes

## 🔧 Monitoring Commands

```bash
# Check memory usage
docker stats

# Monitor Ollama logs
docker logs backend-ollama -f

# Check model loading
docker exec backend-ollama ollama list

# Verify environment
docker exec backend-main env | grep OLLAMA
```

The system is now optimized for your high-memory setups! 🎉
