"""
Error Handling Patterns Migration Examples
==========================================

This file demonstrates how to migrate from the old scattered try/catch patterns
to the new unified error handling system using decorators and context managers.

Before and after examples for each major service type.
"""

from typing import List, Dict, Any, Optional
import asyncio

from utilities.error_patterns import (
    handle_service_errors,
    error_context,
    sync_error_context,
    ServiceErrorConfigs,
    ErrorHandlerConfig,
    ServiceType,
    ErrorAction,
    ErrorSeverity,
    handle_database_errors,
    handle_llm_errors,
    handle_memory_errors,
    handle_cache_errors
)


# ==============================================================================
# EXAMPLE 1: Database Operations (chat.py retrieve_user_memory)
# ==============================================================================

# [FAIL] OLD PATTERN (from routes/chat.py):
async def retrieve_user_memory_old(user_id: str, query: str, n_results: int = 5):
    """OLD: Scattered error handling with inconsistent logging."""
    memory_service = get_memory_service()
    
    if memory_service:
        try:
            memories = await memory_service.retrieve_memories(user_id, query, limit=n_results)
            memory_chunks = []
            for memory in memories:
                memory_chunks.append({
                    "content": memory.content,
                    "metadata": memory.metadata or {},
                    "distance": 1.0 - (memory.relevance_score or 0.0)
                })
            return memory_chunks
        except Exception as e:
            log_service_status("CHAT", "warning", f"New memory service failed, using legacy fallback: {e}")
            # Fall through to legacy system
    
    # Use legacy system
    log_service_status("CHAT", "info", f"Using legacy memory system for user {user_id}")
    try:
        from services.database_manager import retrieve_user_memory
        query_emb = await get_embedding(query)
        if query_emb is not None:
            return await retrieve_user_memory(db_manager, user_id, query_emb, n_results=n_results)
        else:
            return []
    except Exception as e:
        log_service_status("CHAT", "error", f"Legacy memory retrieval failed: {e}")
        return []


# [OK] NEW PATTERN:
@handle_memory_errors(operation_name="retrieve_user_memory")
async def retrieve_user_memory_new(user_id: str, query: str, n_results: int = 5):
    """NEW: Clean function with standardized error handling."""
    memory_service = get_memory_service()
    
    if memory_service:
        memories = await memory_service.retrieve_memories(user_id, query, limit=n_results)
        return [
            {
                "content": memory.content,
                "metadata": memory.metadata or {},
                "distance": 1.0 - (memory.relevance_score or 0.0)
            }
            for memory in memories
        ]
    
    # Legacy fallback
    from services.database_manager import retrieve_user_memory
    query_emb = await get_embedding(query)
    if query_emb is not None:
        return await retrieve_user_memory(db_manager, user_id, query_emb, n_results=n_results)
    else:
        return []


# Alternative with custom config:
@handle_service_errors(
    config=ErrorHandlerConfig(
        service_type=ServiceType.MEMORY,
        action=ErrorAction.FALLBACK,
        fallback_function=lambda: [],
        max_retries=2,
        severity=ErrorSeverity.MEDIUM
    ),
    service_name="ChatService",
    operation_name="retrieve_user_memory"
)
async def retrieve_user_memory_custom(user_id: str, query: str, n_results: int = 5):
    """NEW: With custom error handling configuration."""
    memory_service = get_memory_service()
    memories = await memory_service.retrieve_memories(user_id, query, limit=n_results)
    return [
        {
            "content": memory.content,
            "metadata": memory.metadata or {},
            "distance": 1.0 - (memory.relevance_score or 0.0)
        }
        for memory in memories
    ]


# ==============================================================================
# EXAMPLE 2: LLM Service Operations (services/llm_service.py)
# ==============================================================================

# [FAIL] OLD PATTERN:
async def call_ollama_old(messages: List[Dict], model: str):
    """OLD: Manual error handling and logging."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={"model": model, "messages": messages},
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()["message"]["content"]
    except httpx.TimeoutException as e:
        log_service_status("OLLAMA", "failed", f"Timeout calling Ollama: {e}")
        return "Error: Request timed out"
    except httpx.HTTPStatusError as e:
        log_service_status("OLLAMA", "failed", f"HTTP error calling Ollama: {e}")
        return f"Error: HTTP {e.response.status_code}"
    except Exception as e:
        log_service_status("OLLAMA", "failed", f"Ollama call failed: {e}")
        return f"Error: {str(e)}"


# [OK] NEW PATTERN:
@handle_llm_errors(operation_name="call_ollama")
async def call_ollama_new(messages: List[Dict], model: str):
    """NEW: Clean LLM call with standardized error handling."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={"model": model, "messages": messages},
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()["message"]["content"]


# ==============================================================================
# EXAMPLE 3: Database Connection Operations (database_manager.py)
# ==============================================================================

# [FAIL] OLD PATTERN:
async def initialize_redis_old(self):
    """OLD: Repetitive connection and error handling."""
    try:
        factory = get_connection_factory()
        self.redis_client = await factory.create_redis_connection(connection_name="database_manager")
        log_service_status("DATABASE_MANAGER", "info", "Redis connection established via DatabaseConnectionFactory")
        return True
    except Exception as e:
        log_service_status("DATABASE_MANAGER", "error", f"Failed to initialize Redis via DatabaseConnectionFactory: {e}")
        self.redis_client = None
        return False


# [OK] NEW PATTERN:
@handle_database_errors(operation_name="initialize_redis", default_value=False)
async def initialize_redis_new(self):
    """NEW: Clean initialization with standardized error handling."""
    factory = get_connection_factory()
    self.redis_client = await factory.create_redis_connection(connection_name="database_manager")
    return True


# ==============================================================================
# EXAMPLE 4: Complex Operations with Context Manager
# ==============================================================================

# [FAIL] OLD PATTERN:
async def process_user_message_old(user_id: str, message: str):
    """OLD: Multiple try/catch blocks for different operations."""
    start_time = time.time()
    
    try:
        # Extract user info
        user_info = extract_user_info(message)
        log_service_status("CHAT", "info", f"Extracted user info for {user_id}")
    except Exception as e:
        log_service_status("CHAT", "warning", f"Failed to extract user info: {e}")
        user_info = {}
    
    try:
        # Retrieve memories
        memories = await retrieve_user_memory(user_id, message)
        log_service_status("CHAT", "info", f"Retrieved {len(memories)} memories for {user_id}")
    except Exception as e:
        log_service_status("CHAT", "error", f"Memory retrieval failed: {e}")
        memories = []
    
    try:
        # Generate response
        response = await call_llm(messages, context=memories)
        log_service_status("CHAT", "info", f"Generated response for {user_id}")
    except Exception as e:
        log_service_status("CHAT", "error", f"LLM call failed: {e}")
        response = "I apologize, but I'm experiencing technical difficulties."
    
    try:
        # Store conversation
        await store_conversation(user_id, message, response)
        log_service_status("CHAT", "info", f"Stored conversation for {user_id}")
    except Exception as e:
        log_service_status("CHAT", "warning", f"Failed to store conversation: {e}")
    
    duration = time.time() - start_time
    log_service_status("CHAT", "info", f"Processed message for {user_id} in {duration:.2f}s")
    return response


# [OK] NEW PATTERN:
async def process_user_message_new(user_id: str, message: str):
    """NEW: Using error context manager for complex operations."""
    async with error_context(
        "ChatService", 
        "process_user_message",
        config=ServiceErrorConfigs.API,
        user_id=user_id,
        message_length=len(message)
    ) as ctx:
        
        # Extract user info (with individual error handling)
        ctx["user_info"] = await extract_user_info_safe(message)
        
        # Retrieve memories (decorated function handles errors)
        ctx["memories"] = await retrieve_user_memory_new(user_id, message)
        ctx["memory_count"] = len(ctx["memories"])
        
        # Generate response (decorated function handles errors)
        ctx["response"] = await call_llm_new(messages, context=ctx["memories"])
        
        # Store conversation (non-critical, can fail silently)
        await store_conversation_safe(user_id, message, ctx["response"])
        
        return ctx["response"]


# Supporting functions with individual error handling
@handle_service_errors(
    config=ErrorHandlerConfig(
        service_type=ServiceType.VALIDATION,
        action=ErrorAction.RETURN_DEFAULT,
        default_value={}
    ),
    operation_name="extract_user_info"
)
async def extract_user_info_safe(message: str):
    """Extract user info with safe error handling."""
    return extract_user_info(message)


@handle_cache_errors(operation_name="store_conversation")
async def store_conversation_safe(user_id: str, message: str, response: str):
    """Store conversation with non-blocking error handling."""
    await store_conversation(user_id, message, response)


# ==============================================================================
# EXAMPLE 5: Validation Operations (scattered across multiple files)
# ==============================================================================

# [FAIL] OLD PATTERN:
def validate_user_id_old(user_id: str) -> bool:
    """OLD: Manual validation with scattered error handling."""
    try:
        if not user_id:
            print("[FAIL] User ID is empty")
            return False
        
        if not user_id.strip():
            print("[FAIL] User ID is whitespace only")
            return False
        
        if len(user_id) < 3:
            print("[FAIL] User ID too short")
            return False
        
        # Additional validation logic...
        return True
        
    except Exception as e:
        print(f"[FAIL] Validation error: {e}")
        return False


# [OK] NEW PATTERN:
@handle_service_errors(
    config=ServiceErrorConfigs.VALIDATION,
    service_name="AuthValidator",
    operation_name="validate_user_id"
)
def validate_user_id_new(user_id: str) -> bool:
    """NEW: Clean validation with standardized error handling."""
    if not user_id or not user_id.strip():
        raise ValueError("User ID cannot be empty or whitespace")
    
    if len(user_id) < 3:
        raise ValueError("User ID must be at least 3 characters long")
    
    # Additional validation logic...
    return True


# ==============================================================================
# EXAMPLE 6: Utility Functions (flush_databases.py, utilities/)
# ==============================================================================

# [FAIL] OLD PATTERN:
async def flush_redis_old():
    """OLD: Manual error handling in utility functions."""
    try:
        print("[SYNC] Connecting to Redis...")
        factory = get_connection_factory()
        redis_client = await factory.create_redis_connection(connection_name="flush_script")
        
        # Test connection
        redis_client.ping()
        print("[OK] Redis connection successful")
        
        # Get memory count before flush
        memory_keys = redis_client.keys("memory:*")
        print(f"[CHART] Found {len(memory_keys)} memory keys in Redis")
        
        if len(memory_keys) > 0:
            # Delete memory keys
            deleted_count = redis_client.delete(*memory_keys)
            print(f" Deleted {deleted_count} memory keys from Redis")
        else:
            print("[OK] Redis already clean - no memory keys found")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Redis flush error: {e}")
        return False


# [OK] NEW PATTERN:
@handle_database_errors(operation_name="flush_redis", default_value=False)
async def flush_redis_new():
    """NEW: Clean utility function with standardized error handling."""
    print("[SYNC] Connecting to Redis...")
    factory = get_connection_factory()
    redis_client = await factory.create_redis_connection(connection_name="flush_script")
    
    # Test connection
    redis_client.ping()
    print("[OK] Redis connection successful")
    
    # Get memory count before flush
    memory_keys = redis_client.keys("memory:*")
    print(f"[CHART] Found {len(memory_keys)} memory keys in Redis")
    
    if len(memory_keys) > 0:
        # Delete memory keys
        deleted_count = redis_client.delete(*memory_keys)
        print(f" Deleted {deleted_count} memory keys from Redis")
    else:
        print("[OK] Redis already clean - no memory keys found")
    
    return True


# ==============================================================================
# MIGRATION SUMMARY
# ==============================================================================

"""
Key Benefits of the New Error Handling Patterns:

1. **Consistency**: All services use the same error handling approach
2. **Reduced Code**: ~80% reduction in try/catch boilerplate
3. **Better Logging**: Standardized logging with context and severity
4. **Retry Logic**: Built-in retry mechanisms with exponential backoff
5. **Fallback Support**: Graceful degradation with fallback functions
6. **Type Safety**: Proper type hints and return type handling
7. **Maintainability**: Centralized error handling configuration

Migration Steps:

1. Import the new utilities:
   ```python
   from utilities.error_patterns import (
       handle_service_errors, handle_database_errors, handle_llm_errors,
       error_context, ServiceErrorConfigs
   )
   ```

2. Replace manual try/catch blocks with decorators:
   - `@handle_database_errors()` for database operations
   - `@handle_llm_errors()` for LLM calls
   - `@handle_memory_errors()` for memory operations
   - `@handle_cache_errors()` for cache operations

3. Use context managers for complex operations:
   ```python
   async with error_context("ServiceName", "operation_name") as ctx:
       # Your operation here
       ctx["additional_context"] = "value"
   ```

4. Remove manual error logging - it's now handled automatically

5. Test the migration with the same error conditions to ensure behavior is preserved

Files to migrate (identified with 50+ error patterns):
- routes/chat.py (10+ patterns)
- services/llm_service.py (4+ patterns)
- database_manager.py (8+ patterns)
- watchdog.py (6+ patterns)
- utilities/*.py files (15+ patterns)
- memory system files (10+ patterns)
- validation utilities (5+ patterns)
"""
