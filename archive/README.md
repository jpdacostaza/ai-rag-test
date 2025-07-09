# Archive Folder

This folder contains deprecated and obsolete files that are no longer used in the current system but are preserved for historical reference.

## 📁 **Contents**

### Docker Files

#### `Dockerfile` (Deprecated - Moved July 8, 2025)
- **Reason for archiving**: This generic Dockerfile was replaced by service-specific Dockerfiles
- **Replacement files**:
  - `Dockerfile.backend` - Main backend API service
  - `Dockerfile.memory` - Memory API service  
  - `Dockerfile.function-installer` - Function installer service
- **Status**: Not referenced in current docker-compose.yml
- **Note**: Contains deprecation notice in header

#### `Dockerfile.bak` (Backup - Moved July 8, 2025)
- **Reason for archiving**: Backup copy of deprecated Dockerfile
- **Original date**: July 2, 2025
- **Status**: Duplicate of above Dockerfile

### Database Files

#### `database.py.bak` (Backup - Moved July 8, 2025) 
- **Reason for archiving**: Backup from database consolidation process
- **Replacement**: Functionality consolidated into `database_manager.py`
- **Original date**: July 2, 2025
- **Status**: Legacy database module backup

## 🔍 **Current Active Dockerfiles**

The following Dockerfiles are still actively used:

1. **`Dockerfile.backend`** - Main backend API container
   - Used by: `backend` service in docker-compose.yml
   - Purpose: FastAPI application with full backend functionality

2. **`Dockerfile.memory`** - Memory API container
   - Used by: `memory_api` service in docker-compose.yml
   - Purpose: Integrated memory system with auto-setup

3. **`Dockerfile.function-installer`** - Function installer container
   - Used by: `function_installer` service in docker-compose.yml
   - Purpose: One-time installer for memory functions in OpenWebUI

## 📝 **Archive Policy**

Files are moved to archive when:
- ✅ They are explicitly deprecated and no longer used
- ✅ They have been replaced by better implementations
- ✅ They are not referenced in any active configuration
- ✅ Removal has been verified to not break existing functionality

Files are kept for:
- 📚 Historical reference
- 🔍 Understanding evolution of the project
- 🚀 Potential future reference for similar implementations

---

*This archive folder helps maintain a clean project structure while preserving historical context.*
