# Functions Directory

This directory contains all OpenWebUI functions (filters and tools) that are automatically installed and managed across the AI backend system.

## Structure

```
functions/
├── filters/          # OpenWebUI filters (inlet/outlet processing)
│   ├── auto_web_search_filter.py
│   ├── enhanced_memory_function_filter_v5_1_final.py
│   └── global_date_time_filter.py
├── tools/            # OpenWebUI tools (function calling)
│   └── weather_tool.py
└── README.md         # This file
```

## Function Types

### Filters
Filters process messages in the inlet/outlet stages:
- **Auto Web Search Filter**: Automatic web search fallback for non-tool-calling models
- **Enhanced Memory Filter**: Stores conversations in the memory API
- **Global Date Time Filter**: Provides current date/time context

### Tools  
Tools provide function calling capabilities:
- **Weather Tool**: Netherlands weather data from KNMI API

## Auto-Installation

Functions in this directory are automatically installed when containers start via the `function-auto-installer` service.

### Manual Installation
```bash
# Run the auto-installer manually
docker-compose up function-auto-installer

# Or install specific functions via OpenWebUI Admin -> Functions
```

### Configuration
Set environment variables in docker-compose.yml:
```yaml
- AUTO_INSTALL_FUNCTIONS=true    # Enable auto-installation
- FUNCTION_AUTO_ENABLE=true      # Auto-enable installed functions
```

## Development

### Adding New Functions
1. Place `.py` files in `filters/` or `tools/` subdirectories
2. Ensure the file contains `class Filter:` or `class Tools:` 
3. Functions will be auto-discovered and installed on next container restart

### Function Requirements
- Must have proper class definition (`Filter` or `Tools`)
- Should include metadata (name, description, version)
- Follow OpenWebUI function API standards

### Testing
Functions are automatically validated during installation. Check logs:
```bash
docker logs backend-function-auto-installer
```

## Global Availability

Functions installed here are available globally across:
- All OpenWebUI conversations
- All user sessions  
- All models (where applicable)

This centralized approach ensures consistent functionality across the entire AI backend system.
