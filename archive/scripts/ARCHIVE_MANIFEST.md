# Scripts Archive Manifest

## Archived on: July 18, 2025

This folder contains legacy and deprecated scripts that were moved from the main `/scripts` directory to clean up the codebase.

## Archived Scripts: (Total: 12 scripts)

### Empty/Broken Scripts
- `fix_rag.py` - Empty file (0 bytes), was broken

### Placeholder/Minimal Scripts  
- `enhanced_integration.py` - Simple placeholder router with no real functionality

### Duplicate/Old Version Scripts
- `enhanced_memory_api_rag.py` - Duplicate of `fixed_memory_api_v2.py`
- `fixed_memory_api.py` - Old version replaced by `fixed_memory_api_v2.py`

### Migration/Cleanup Tools (No longer needed)
- `analyze_legacy_code.py` - Used during codebase migration, now obsolete
- `reorganize_project.py` - Used during project reorganization, now obsolete  
- `extended_cleanup.py` - Used during cleanup phase, now obsolete
- `fix_error_patterns.py` - Used during error pattern fixes, now obsolete

### Development/Testing Scripts (Not needed in production)
- `test_installer.py` - Comprehensive test suite, development artifact only
- `improved_installer.py` - Old installer superseded by `unified_installer.py`

### Unused Modules
- `enhanced_web_search_trigger.py` - Web search trigger system, no active usage found

## Why These Were Archived:
1. **Code Quality**: Removing empty, duplicate, and placeholder files
2. **Maintenance**: Reducing confusion about which scripts are actively used
3. **Docker Builds**: Preventing unused scripts from being copied into containers
4. **Development Clarity**: Making it clear which scripts are part of the current system

## Active Scripts Remaining:
- All scripts referenced in Dockerfiles remain active
- All utility and monitoring scripts remain active
- All recent scripts (July 17, 2025) remain active

## Recovery:
If any of these scripts are needed, they can be moved back from this archive folder.
