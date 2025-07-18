# Services Archive Manifest

## Archived on: July 18, 2025

This folder contains legacy and specialized service implementations that were moved from the main `/services` directory during codebase cleanup.

## Archived Services:

### Specialized Memory Services (Superseded)
- `rag_dual_database_service.py` - Specialized RAG dual-database implementation
  - **Status**: Superseded by unified `memory_service.py`
  - **Reason**: Functionality consolidated into main memory service
  - **Last Modified**: July 17, 2025

- `robust_memory_service.py` - Network resilience memory service
  - **Status**: Network fallback implementation
  - **Reason**: Docker networking issues resolved, fallback no longer needed
  - **Last Modified**: July 17, 2025

- `memory_service_enhanced.py` - Enhanced memory service with AI features
  - **Status**: Advanced features implementation
  - **Reason**: Can be merged into main service if AI features needed
  - **Last Modified**: July 14, 2025

## Active Services Remaining:
- `memory_service.py` - Primary unified memory service
- `database_manager.py` - Core database operations
- `chat_service.py` - Chat functionality
- `llm_service.py` - Language model integration
- `tool_service.py` - Tool management
- And other core services...

## Recovery:
If any of these specialized services are needed, they can be moved back and their features can be integrated into the main services.
