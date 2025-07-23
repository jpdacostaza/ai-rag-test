# Deprecated ARM64 Configuration Archive

This directory contains the old `docker-compose.arm64.yml` file that was used before we implemented the unified configuration system.

## What Changed:

✅ **Before**: Separate ARM64 override file
- Required: `docker-compose -f docker-compose.yml -f docker-compose.arm64.yml up`
- Duplicated configuration between files
- Manual architecture detection needed

✅ **Now**: Unified configuration with environment variables
- Single file: `docker-compose.yml` with `${ARM64_OPTIMIZED}` variables
- Automatic detection via `scripts/smart-compose.sh` and `scripts/smart-compose.ps1`
- Cross-platform compatibility

## How to Use the New System:

### Option 1: Smart Scripts (Recommended)
```bash
# Linux/macOS
./scripts/smart-compose.sh up -d

# Windows
.\scripts\smart-compose.ps1 up -d
```

### Option 2: Manual Environment Variables
```bash
# For ARM64 devices
export ARM64_OPTIMIZED=true
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_MAX_VRAM=4096
docker compose up -d

# For x86_64 devices (default)
docker compose up -d
```

## Benefits of Unified Configuration:
- ✅ Single source of truth
- ✅ Cross-platform compatibility  
- ✅ Automatic optimization detection
- ✅ Easier maintenance
- ✅ Environment variable flexibility
