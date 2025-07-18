# Setup Scripts Archive Manifest

## Archived on: July 18, 2025

This folder contains legacy setup scripts that were moved from the main `/setup` directory during cleanup.

## Archived Setup Scripts:

### Legacy Memory Setup Scripts (Superseded)
- `setup_memory_pipelines.ps1` - Original pipeline setup (Windows)
  - **Status**: Legacy pipeline setup
  - **Superseded by**: `setup_complete_memory.ps1`
  - **Last Modified**: July 11, 2025

- `setup_memory_pipelines.sh` - Original pipeline setup (Linux)
  - **Status**: Legacy pipeline setup
  - **Superseded by**: `setup_complete_memory.sh`
  - **Last Modified**: July 11, 2025

- `setup_memory_pipelines_fixed.ps1` - Fixed pipeline setup
  - **Status**: Intermediate fix, superseded
  - **Superseded by**: `setup_complete_memory.ps1`
  - **Last Modified**: July 11, 2025

- `setup_unified_memory.ps1` - Unified memory setup (Windows)
  - **Status**: Legacy unified approach
  - **Superseded by**: `setup_complete_memory.ps1`
  - **Last Modified**: July 11, 2025

- `setup_unified_memory.sh` - Unified memory setup (Linux)
  - **Status**: Legacy unified approach
  - **Superseded by**: `setup_complete_memory.sh`
  - **Last Modified**: July 11, 2025

## Active Setup Scripts Remaining:
- `setup_complete_memory.ps1` - Current Windows memory setup
- `setup_complete_memory.sh` - Current Linux memory setup
- `setup-api-keys.ps1` - API key configuration (Windows)
- `setup-api-keys.sh` - API key configuration (Linux)
- `linux_setup.sh` - Complete Linux setup
- `deploy.ps1` - Windows deployment
- `deploy.sh` - Linux deployment

## Migration Path:
All archived scripts evolved into the current `setup_complete_memory.*` scripts which provide comprehensive memory system setup.

## Recovery:
These scripts are preserved for reference but should not be needed as their functionality is incorporated in current setup scripts.
