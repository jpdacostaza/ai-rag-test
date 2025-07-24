"""
Memory management endpoints for direct memory operations.
Provides REST API endpoints for memory storage, retrieval, and management.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel

from core.logging_config import log_service_status
from services.database_manager import db_manager
from utilities.error_patterns import handle_api_errors
from services.auth_validator import AuthValidator

# Create router with proper prefix and tags
memory_router = APIRouter(prefix="/api/memory", tags=["memory"])

# Request/Response models
class MemoryStoreRequest(BaseModel):
    """Request model for storing memory."""
    user_id: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    importance: Optional[float] = 0.5
    memory_type: Optional[str] = "conversation"

class MemoryQueryRequest(BaseModel):
    """Request model for querying memory."""
    user_id: str
    query: str
    limit: Optional[int] = 5
    min_score: Optional[float] = 0.0

class MemoryResponse(BaseModel):
    """Response model for memory operations."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class MemoryListResponse(BaseModel):
    """Response model for memory list operations."""
    success: bool
    memories: List[Dict[str, Any]]
    total_count: int

@memory_router.get("/health", response_model=Dict[str, str])
@handle_api_errors("memory_health_check")
async def memory_health_check():
    """Check memory system health status."""
    try:
        # Check database manager health
        if not db_manager:
            raise HTTPException(status_code=503, detail="Database manager not available")
        
        health_status = await db_manager.get_health_status()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "redis": health_status.get("redis", {}).get("status", "unknown"),
            "chromadb": health_status.get("chromadb", {}).get("status", "unknown"),
            "embeddings": health_status.get("embeddings", {}).get("status", "unknown")
        }
    except Exception as e:
        log_service_status("MEMORY", "error", f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Memory system unhealthy: {str(e)}")

@memory_router.post("/store", response_model=MemoryResponse)
@handle_api_errors("store_memory")
async def store_memory(request: MemoryStoreRequest):
    """Store a memory for a user."""
    try:
        # Validate user
        auth_validator = AuthValidator()
        validated_user = auth_validator.extract_and_validate_user({"id": request.user_id})
        
        if not validated_user or not validated_user.user_id:
            raise HTTPException(status_code=400, detail="Invalid user_id")
        
        # Ensure database manager is available
        if not db_manager:
            raise HTTPException(status_code=503, detail="Database manager not available")
        
        await db_manager.ensure_initialized()
        
        # Store in vector database (ChromaDB)
        metadata = request.metadata or {}
        metadata.update({
            "user_id": validated_user.user_id,
            "timestamp": datetime.now().isoformat(),
            "importance": request.importance,
            "memory_type": request.memory_type
        })
        
        success = await db_manager.store_vector_data(request.content, metadata)
        
        if success:
            log_service_status("MEMORY", "info", f"Memory stored for user {validated_user.user_id}")
            return MemoryResponse(
                success=True,
                message="Memory stored successfully",
                data={"user_id": validated_user.user_id, "content_length": len(request.content)}
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to store memory")
            
    except HTTPException:
        raise
    except Exception as e:
        log_service_status("MEMORY", "error", f"Error storing memory: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@memory_router.post("/query", response_model=MemoryListResponse)
@handle_api_errors("query_memory")
async def query_memory(request: MemoryQueryRequest):
    """Query memories for a user using semantic search."""
    try:
        # Validate user
        auth_validator = AuthValidator()
        validated_user = auth_validator.extract_and_validate_user({"id": request.user_id})
        
        if not validated_user or not validated_user.user_id:
            raise HTTPException(status_code=400, detail="Invalid user_id")
        
        # Ensure database manager is available
        if not db_manager:
            raise HTTPException(status_code=503, detail="Database manager not available")
        
        await db_manager.ensure_initialized()
        
        # Query vector database
        results = await db_manager.query_chroma(request.query, request.limit)
        
        if results and results.get("matches"):
            # Filter by user_id and minimum score
            user_memories = []
            for match in results["matches"]:
                metadata = match.get("metadata", {})
                if metadata.get("user_id") == validated_user.user_id:
                    # Calculate similarity score (1 - distance)
                    distance = match.get("distance", 1.0)
                    similarity_score = max(0.0, 1.0 - distance)
                    
                    if similarity_score >= request.min_score:
                        user_memories.append({
                            "content": match.get("document", ""),
                            "metadata": metadata,
                            "similarity_score": similarity_score,
                            "distance": distance
                        })
            
            log_service_status("MEMORY", "info", f"Retrieved {len(user_memories)} memories for user {validated_user.user_id}")
            return MemoryListResponse(
                success=True,
                memories=user_memories,
                total_count=len(user_memories)
            )
        else:
            return MemoryListResponse(
                success=True,
                memories=[],
                total_count=0
            )
            
    except HTTPException:
        raise
    except Exception as e:
        log_service_status("MEMORY", "error", f"Error querying memory: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@memory_router.get("/user/{user_id}", response_model=MemoryListResponse)
@handle_api_errors("get_user_memories")
async def get_user_memories(
    user_id: str,
    limit: int = Query(default=10, ge=1, le=100),
    memory_type: Optional[str] = Query(default=None)
):
    """Get all memories for a specific user."""
    try:
        # Validate user
        auth_validator = AuthValidator()
        validated_user = auth_validator.extract_and_validate_user({"id": user_id})
        
        if not validated_user or not validated_user.user_id:
            raise HTTPException(status_code=400, detail="Invalid user_id")
        
        # For now, return empty list as this requires more complex ChromaDB querying
        # In a full implementation, you would query ChromaDB with user_id filter
        log_service_status("MEMORY", "info", f"Memory retrieval requested for user {validated_user.user_id}")
        
        return MemoryListResponse(
            success=True,
            memories=[],
            total_count=0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_service_status("MEMORY", "error", f"Error retrieving user memories: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@memory_router.delete("/user/{user_id}", response_model=MemoryResponse)
@handle_api_errors("clear_user_memories")
async def clear_user_memories(user_id: str):
    """Clear all memories for a specific user."""
    try:
        # Validate user
        auth_validator = AuthValidator()
        validated_user = auth_validator.extract_and_validate_user({"id": user_id})
        
        if not validated_user or not validated_user.user_id:
            raise HTTPException(status_code=400, detail="Invalid user_id")
        
        # Note: This is a placeholder implementation
        # Full implementation would require ChromaDB collection filtering and deletion
        log_service_status("MEMORY", "warning", f"Memory clear requested for user {validated_user.user_id} (not implemented)")
        
        return MemoryResponse(
            success=False,
            message="Memory clear not implemented yet",
            data={"user_id": validated_user.user_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_service_status("MEMORY", "error", f"Error clearing user memories: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@memory_router.get("/stats", response_model=Dict[str, Any])
@handle_api_errors("memory_stats")
async def get_memory_stats():
    """Get memory system statistics."""
    try:
        if not db_manager:
            raise HTTPException(status_code=503, detail="Database manager not available")
        
        health_status = await db_manager.get_health_status()
        cache_stats = db_manager.get_cache_stats()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "database_health": health_status,
            "cache_stats": cache_stats,
            "memory_system": {
                "redis_available": await db_manager.is_redis_available(),
                "chromadb_available": await db_manager.is_chromadb_available(),
                "embeddings_available": db_manager.is_embeddings_available()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_service_status("MEMORY", "error", f"Error getting memory stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
