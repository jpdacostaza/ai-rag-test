# Backend Directory Structure

## 📁 Root Directory
- Core application files (main.py, config.py, etc.)
- Docker configuration files
- Requirements and environment files

## 📁 Key Directories

### /docs/ - Documentation
- guides/ - Setup and usage guides
- status/ - Project status reports and logs
- 	emplates/ - Configuration templates

### /scripts/ - Automation Scripts
- import/ - Memory function import scripts
- memory/ - Memory system utilities
- 	est/ - Test execution scripts

### /tests/ - Test Files
- data/ - Test data and JSON files
- memory/ - Memory-specific PowerShell tests
- integration/ - Integration test files

### /config/ - Configuration
- JSON configuration files
- Templates and schemas

### /memory/ - Memory System
- Memory pipeline implementations
- Memory-related modules

### /handlers/ - Exception Handlers
- Error handling modules

### /pipelines/ - OpenWebUI Pipelines
- Pipeline route definitions

### /routes/ - API Routes
- REST API endpoint definitions

### /services/ - Business Logic
- Core service implementations

### /utilities/ - Helper Functions
- Utility modules and helpers

### /archive/ - Archived Files
- Old/deprecated files for reference

## 🚀 Getting Started
1. Review README.md for setup instructions
2. Check docs/guides/ for detailed guides
3. Use scripts in scripts/ for automation
4. Run tests from 	ests/ directory

## 📝 Key Files
- main.py - Main application entry point
- docker-compose.yml - Docker services configuration
- equirements.txt - Python dependencies
- nhanced_memory_api.py - Memory system API
- openwebui_api_bridge.py - OpenWebUI integration bridge
