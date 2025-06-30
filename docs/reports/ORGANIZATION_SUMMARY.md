# Project Organization Summary

## Folder Structure

### `/demo-tests/` - All Test and Demo Files
- **Purpose:** Contains all testing, debugging, and demonstration files
- **Subfolders:**
  - `cache-tests/` - Cache system specific tests
  - `debug-tools/` - Debugging utilities and tools  
  - `demos/` - Demo applications and examples
  - `integration-tests/` - Full system integration tests
  - `model-tests/` - AI model specific tests
  - `performance-tests/` - Performance benchmarking
  - `results/` - Test result files and reports

### `/readme/` - All Documentation Files
- **Purpose:** Contains all markdown documentation and reports
- **Content:** Technical reports, test results, status updates, guides

### `/storage/` - Data Storage
- **Purpose:** Persistent data storage (created at runtime)

### `/utils/` - Utility Modules  
- **Purpose:** Shared utility functions and helpers

### Root Directory - Core Application
- **Purpose:** Main application files only
- `main.py` - FastAPI backend entry point
- `app.py` - Application configuration  
- `ai_tools.py` - AI tool implementations
- `database_manager.py` - Database operations
- `cache_manager.py` - Redis cache operations
- `human_logging.py` - Enhanced logging system
- `cpu_enforcer.py` - CPU-only mode enforcement
- `error_handler.py` - Error handling utilities
- `README.md` - Project main documentation
- `requirements.txt` - Python dependencies
- `docker-compose.yml` - Container orchestration
- `Dockerfile` - Container build instructions

## File Organization Rules

### Test Files → `/demo-tests/`
- `test_*.py` - Unit tests
- `demo_*.py` - Demo applications  
- `*_test.py` - Test files
- `comprehensive_*.py` - Integration tests
- `debug_*.py` - Debug utilities
- `*.sh` test scripts
- Test result JSON files

### Documentation → `/readme/`
- `*.md` files (except root README.md)
- Technical reports
- Status updates
- Test result documentation
- Project guides and summaries

### Core Application → Root
- Main application modules
- Configuration files
- Docker files
- Primary documentation (README.md)
- Dependencies (requirements.txt)

## Benefits of This Organization

1. **Clear Separation of Concerns**
   - Production code in root
   - Tests isolated in demo-tests/
   - Documentation centralized in readme/

2. **Easy Navigation**
   - Developers know where to find specific file types
   - Reduced clutter in root directory
   - Logical grouping of related files

3. **Maintenance Friendly**
   - Easy to exclude test/demo files from production
   - Clear project structure for new contributors
   - Simplified deployment (root + utils only)

4. **Git Management**
   - Clear commit patterns by folder
   - Easy to track changes to specific components
   - Simplified .gitignore patterns
