# Scripts Directory

This directory contains utility scripts organized by purpose.

## Directory Structure

```
scripts/
├── README.md              # This file
├── monitoring/            # Real-time monitoring and health check scripts
│   ├── realtime_monitor.py      # Real-time duplicate detection monitor
│   └── metrics_health_check.py  # Production metrics health verification
├── setup/                 # Initial setup and configuration scripts
│   ├── auto_deduplication_setup.py  # Auto-deduplication integration setup
│   └── copy_prompt_to_functions.py  # Copy unified prompt for filter access
└── maintenance/           # Maintenance and cleanup scripts
    └── activate_cleanup.py     # Manual duplicate cleanup activation
```

## Usage

### Monitoring Scripts

**Real-time Duplicate Monitor** (`monitoring/realtime_monitor.py`)
- Monitors database for new file uploads
- Detects and alerts about duplicate files in real-time
- Shows current duplicate statistics

```bash
# Test current duplicates
python scripts/monitoring/realtime_monitor.py

# Start real-time monitoring
python scripts/monitoring/realtime_monitor.py monitor

# Run in Docker container
docker exec -d backend-openwebui python /app/backend/scripts/monitoring/realtime_monitor.py monitor
```

**Production Metrics Health Check** (`monitoring/metrics_health_check.py`)
- Comprehensive metrics system verification
- ARM Linux compatibility testing
- Performance benchmarking and health reporting
- Production readiness validation

```bash
# Run comprehensive health check
python scripts/monitoring/metrics_health_check.py

# Run in Docker container for production validation
docker exec backend-openwebui python /app/backend/scripts/monitoring/metrics_health_check.py
```

### Setup Scripts

**Auto-deduplication Setup** (`setup/auto_deduplication_setup.py`)
- Sets up auto-deduplication hooks and monitoring
- Creates integration scripts for OpenWebUI
- Tests duplicate detection functionality

```bash
python scripts/setup/auto_deduplication_setup.py
```

**Copy Unified Prompt** (`setup/copy_prompt_to_functions.py`)
- Copies unified_prompt.json to functions directory
- Enables cross-container access for filters

```bash
cd scripts/setup
python copy_prompt_to_functions.py
```

### Maintenance Scripts

**Activate Cleanup** (`maintenance/activate_cleanup.py`)
- **WARNING**: Performs actual file deletion
- Manually triggers duplicate cleanup with confirmation
- Provides detailed cleanup statistics

```bash
# Run with extreme caution - deletes files permanently
python scripts/maintenance/activate_cleanup.py
```

## Integration with OpenWebUI

These scripts are designed to work with the OpenWebUI backend system:

- **Monitoring**: Watches `/app/backend/data/webui.db` for changes
- **Setup**: Configures filters and functions for auto-deduplication
- **Maintenance**: Safely manages storage optimization

## Safety Features

- **Confirmation prompts** for destructive operations
- **Conservative cleanup** (keeps oldest files by default)
- **Session limits** to prevent excessive cleanup
- **Comprehensive logging** for audit trails
- **Error handling** for graceful failure recovery

## Related Components

- **Filters**: `functions/filters/enhanced_duplicate_detection_filter_v2.py`
- **Configuration**: `config/unified_prompt.json`
- **Database**: `/app/backend/data/webui.db`
- **Vector Store**: `/app/backend/data/chroma`

## Development Notes

When modifying these scripts:

1. **Test thoroughly** in development environment first
2. **Update Docker paths** when moving files
3. **Maintain backward compatibility** where possible
4. **Document changes** in this README
5. **Follow safety conventions** for destructive operations
