"""
Dependency Injection
===================

This module provides dependency injection for services, replacing the global
state pattern with proper FastAPI dependency injection.
"""

from typing import Optional
from fastapi import Depends

from services.database_manager import db_manager, get_cache
from services.chat_service import ChatService
from services.redis_service import RedisService
from services.vector_service import VectorService


def get_cache_service():
    """Get cache service dependency."""
    try:
        return get_cache()
    except Exception as e:
        import logging
        logging.warning(f"Cache service unavailable: {e}")
        return None


def get_memory_service():
    """Get memory service dependency."""
    try:
        # Import memory service with fallback
        from routes.chat import get_memory_service as _get_memory_service
        return _get_memory_service()
    except Exception as e:
        import logging
        logging.warning(f"Memory service unavailable: {e}")
        return None


def get_database_manager():
    """Get database manager dependency."""
    return db_manager


def get_redis_service() -> Optional[RedisService]:
    """Get Redis service dependency."""
    try:
        if db_manager and hasattr(db_manager, 'redis_client'):
            return RedisService(redis_client=db_manager.redis_client)
        return RedisService()  # Will handle fallback internally
    except Exception as e:
        import logging
        logging.warning(f"Redis service unavailable: {e}")
        return None


def get_vector_service() -> Optional[VectorService]:
    """Get Vector service dependency."""
    try:
        if db_manager and hasattr(db_manager, 'chroma_client'):
            return VectorService(chroma_client=db_manager.chroma_client)
        return VectorService()  # Will handle fallback internally
    except Exception as e:
        import logging
        logging.warning(f"Vector service unavailable: {e}")
        return None


def get_chat_service(
    cache_service=Depends(get_cache_service),
    memory_service=Depends(get_memory_service),
    database_manager=Depends(get_database_manager)
) -> ChatService:
    """Get chat service with injected dependencies."""
    return ChatService(
        cache_service=cache_service,
        memory_service=memory_service,
        database_manager=database_manager
    )


# Legacy compatibility functions (for gradual migration)
def get_legacy_redis_client():
    """Get Redis client from db_manager (legacy compatibility)."""
    if db_manager and hasattr(db_manager, 'redis_client'):
        return db_manager.redis_client
    return None


def get_legacy_vector_client():
    """Get vector client from db_manager (legacy compatibility).""" 
    if db_manager and hasattr(db_manager, 'chroma_client'):
        return db_manager.chroma_client
    return None
