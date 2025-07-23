# 🚀 Unified Docker Compose Configuration

## Overview
We've successfully merged all ARM64 optimizations into the main `docker-compose.yml` file with automatic platform detection. You no longer need separate override files!

## ✅ What's Changed

### Files Unified:
- ❌ `docker-compose.arm64.yml` (archived - no longer needed)
- ❌ `.env.auto` (merged into `.env`)
- ✅ `docker-compose.yml` (now includes all optimizations)
- ✅ `.env` (includes cross-platform settings)

### Smart Scripts Enhanced:
- `scripts/smart-compose.sh` (Linux/macOS)
- `scripts/smart-compose.ps1` (Windows)

## 🔧 How It Works

### Automatic Detection:
The smart-compose scripts automatically detect your architecture and set optimal values:

**ARM64 Devices (Orange Pi, Raspberry Pi, M1/M2 Macs):**
```bash
ARM64_OPTIMIZED=true
OLLAMA_MAX_LOADED_MODELS=1
OLLAMA_MAX_VRAM=4096
OLLAMA_NUMA=false
EMBEDDING_BATCH_SIZE=16
REDIS_MAX_MEMORY=256mb
```

**x86_64 Devices (Windows, Intel/AMD):**
```bash
ARM64_OPTIMIZED=false
OLLAMA_MAX_LOADED_MODELS=2
OLLAMA_MAX_VRAM=8192
OLLAMA_NUMA=true
EMBEDDING_BATCH_SIZE=32
REDIS_MAX_MEMORY=512mb
```

### All Platforms Get:
- ✅ 180s timeouts for stability
- ✅ Conservative health checks
- ✅ Memory management
- ✅ Cross-platform compatibility

## 🎯 Usage

### Method 1: Smart Scripts (Recommended)
```bash
# Linux/macOS
./scripts/smart-compose.sh up -d

# Windows PowerShell
.\scripts\smart-compose.ps1 up -d
```

### Method 2: Direct Docker Compose
```bash
# Standard startup (auto-detects from .env)
docker-compose up -d

# Manual override for ARM64
ARM64_OPTIMIZED=true OLLAMA_MAX_LOADED_MODELS=1 docker-compose up -d
```

### Method 3: Environment Files
Create `.env.local` to override defaults:
```bash
# For ARM64 optimization on any platform
ARM64_OPTIMIZED=true
OLLAMA_MAX_LOADED_MODELS=1
OLLAMA_MAX_VRAM=4096
EMBEDDING_BATCH_SIZE=16
```

## 🎉 Benefits

1. **Single Configuration** → Easier maintenance
2. **Cross-Platform** → Works everywhere
3. **Auto-Optimized** → No manual tuning needed
4. **Backward Compatible** → Existing setups work
5. **Environment Flexible** → Easy to override

## 🧪 Testing

Your system will now:
- ✅ Auto-detect Windows x86_64 and use optimal settings
- ✅ Auto-detect ARM64 and apply conservative settings
- ✅ Apply 180s timeouts to prevent connection issues
- ✅ Use unified configuration for consistency

The Qwen model timeout issues should be resolved with the new 180s timeout configuration!
