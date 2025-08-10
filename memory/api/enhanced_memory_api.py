"""
Enhanced Memory API - RAG Dual-Database System
==============================================

This module provides the main Memory API service that was referenced in README.md
but was missing from the codebase. This service provides a FastAPI-based REST API
for memory storage and retrieval using the dual-database RAG architecture.

The service integrates with:
- Redis (short-term memory)
- ChromaDB (long-term semantic memory)
- Enhanced Memory Pipeline
- OpenWebUI integration

This file bridges the gap between the documented architecture and implementation.
"""

import asyncio
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# Import unified configuration
from config.config_unified import Config

# Import services
from services.memory_service import MemoryService, get_memory_service
from services.database_manager import db_manager
from core.unified_logging import get_logger, log_service_status
from utilities.error_patterns import handle_api_errors, StandardizedErrorResponse

logger = get_logger(__name__)

# Request/Response Models
class MemoryStoreRequest(BaseModel):
    """Request model for storing memory."""
    user_id: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    importance: Optional[float] = 0.5
    memory_type: Optional[str] = "conversation"

class MemoryRetrieveRequest(BaseModel):
    """Request model for retrieving memories."""
    user_id: str
    query: str
    limit: Optional[int] = 5
    min_score: Optional[float] = 0.0

class MemoryResponse(BaseModel):
    """Response model for memory operations."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    memories: Optional[List[Dict[str, Any]]] = None

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    redis_status: str
    chroma_status: str
    system_version: str


# FastAPI app
app = FastAPI(
    title="Enhanced Memory API",
    description="RAG Dual-Database Memory System API",
    version="1.0.0"
)

@app.get("/health", response_model=HealthResponse)
@handle_api_errors("memory_api_health")
async def health_check():
    """Enhanced health check with RAG system status."""
    try:
        # Check database manager health
        health_status = await db_manager.get_health_status() if db_manager else {}
        
        redis_status = health_status.get("redis", {}).get("status", "unknown")
        chroma_status = health_status.get("chromadb", {}).get("status", "unknown")
        
        overall_status = "healthy" if redis_status == "connected" and chroma_status == "connected" else "degraded"
        
        return HealthResponse(
            status=overall_status,
            timestamp=datetime.now().isoformat(),
            redis_status=redis_status,
            chroma_status=chroma_status,
            system_version="1.0.0"
        )
    except Exception as e:
        log_service_status("MEMORY_API", "error", f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Memory API health check failed")

@app.post("/api/memory/store", response_model=MemoryResponse)
@handle_api_errors("store_memory")
async def store_memory(request: MemoryStoreRequest):
    """Store memory using unified memory service."""
    try:
        memory_service = get_memory_service()
        if not memory_service:
            raise HTTPException(status_code=503, detail="Memory service not available")
        
        # Store memory with metadata
        success = await memory_service.store_memory(
            user_id=request.user_id,
            content=request.content,
            context=request.metadata or {},
            importance=request.importance
        )
        
        if success:
            log_service_status("MEMORY_API", "info", f"Memory stored for user {request.user_id}")
            return MemoryResponse(
                success=True,
                message="Memory stored successfully",
                data={"user_id": request.user_id, "importance": request.importance}
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to store memory")
            
    except Exception as e:
        log_service_status("MEMORY_API", "error", f"Store memory failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Memory storage failed: {str(e)}")

@app.post("/api/memory/retrieve", response_model=MemoryResponse)
@handle_api_errors("retrieve_memory")
async def retrieve_memories(request: MemoryRetrieveRequest):
    """Retrieve memories using unified memory service."""
    try:
        memory_service = get_memory_service()
        if not memory_service:
            raise HTTPException(status_code=503, detail="Memory service not available")
        
        # Retrieve relevant memories
        memories = await memory_service.get_relevant_memories(
            user_id=request.user_id,
            context=request.query,
            max_memories=request.limit
        )
        
        # Convert to API format
        memory_list = []
        for memory in memories:
            # memory.metadata is a dataclass (MemoryMetadata); convert safely
            metadata_obj = memory.metadata
            metadata_dict = {
                "user_id": metadata_obj.user_id,
                "timestamp": metadata_obj.timestamp,
                "source": metadata_obj.source,
                "importance": metadata_obj.importance,
                "memory_type": metadata_obj.memory_type,
                "context": metadata_obj.context,
                "conversation_id": metadata_obj.conversation_id,
                "explicit": metadata_obj.explicit
            } if metadata_obj else {}

            relevance = None
            # Prefer similarity_score if populated
            if memory.similarity_score is not None:
                relevance = memory.similarity_score
            elif memory.distance is not None:
                relevance = 1.0 - memory.distance
            else:
                relevance = 0.0

            memory_list.append({
                "content": memory.content,
                "metadata": metadata_dict,
                "relevance_score": relevance,
                "timestamp": metadata_dict.get("timestamp", "")
            })
        
        log_service_status("MEMORY_API", "info", f"Retrieved {len(memory_list)} memories for user {request.user_id}")
        return MemoryResponse(
            success=True,
            message=f"Retrieved {len(memory_list)} memories",
            memories=memory_list
        )
        
    except Exception as e:
        log_service_status("MEMORY_API", "error", f"Retrieve memory failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Memory retrieval failed: {str(e)}")

@app.post("/api/learning/process_interaction")
@handle_api_errors("process_interaction")
async def process_interaction(interaction_data: Dict[str, Any]):
    """Process learning interaction for storage."""
    try:
        memory_service = get_memory_service()
        if not memory_service:
            raise HTTPException(status_code=503, detail="Memory service not available")
        
        user_id = interaction_data.get("user_id")
        user_message = interaction_data.get("user_message", "")
        assistant_response = interaction_data.get("assistant_response", "")
        
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        # Store the interaction
        success = await memory_service.track_conversation(
            user_id=user_id,
            user_message=user_message,
            assistant_response=assistant_response
        )
        
        if success:
            return {"success": True, "message": "Interaction processed successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to process interaction")
            
    except Exception as e:
        log_service_status("MEMORY_API", "error", f"Process interaction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Interaction processing failed: {str(e)}")

@app.get("/api/memory/stats/{user_id}")
@handle_api_errors("memory_stats")
async def get_memory_stats(user_id: str):
    """Get memory statistics for a user."""
    try:
        memory_service = get_memory_service()
        if not memory_service:
            raise HTTPException(status_code=503, detail="Memory service not available")
        
        # Get statistics from memory service
        memories = await memory_service.get_relevant_memories(user_id=user_id, context="", max_memories=1000)
        
        # Basic statistics
        stats = {
            "user_id": user_id,
            "total_memory_count": len(memories),
            "redis_memory_count": 0,  # Would need specific Redis query
            "chroma_memory_count": len(memories),  # Assuming ChromaDB is primary
            "timestamp": datetime.now().isoformat()
        }
        
        return stats
        
    except Exception as e:
        log_service_status("MEMORY_API", "error", f"Memory stats failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Memory statistics failed: {str(e)}")

# Startup/Shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize memory API on startup."""
    log_service_status("MEMORY_API", "info", "Enhanced Memory API starting up...")
    
    # Ensure database manager is initialized
    if db_manager:
        await db_manager.ensure_initialized()
        log_service_status("MEMORY_API", "ready", "Enhanced Memory API ready")
    else:
        log_service_status("MEMORY_API", "warning", "Database manager not available")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    log_service_status("MEMORY_API", "info", "Enhanced Memory API shutting down...")

def run_memory_api():
    """Run the Enhanced Memory API server."""
    config = Config.get_instance()
    port = getattr(config.memory, 'api_port', 5001)
    
    log_service_status("MEMORY_API", "info", f"Starting Enhanced Memory API on port {port}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )

if __name__ == "__main__":
    run_memory_api()
