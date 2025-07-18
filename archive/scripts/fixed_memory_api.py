#!/usr/bin/env python3
"""
Fixed Memory API for OpenWebUI Enhanced Memory System
====================================================

This replaces the integrated_memory_startup.py with a proper Memory API
that matches the expected endpoints and response formats.

Fixed Issues:
- Endpoint mismatches (/store vs /api/memory/store_explicit)
- Response format inconsistencies (boolean vs objects)
- Missing API functionality for interaction processing
- Proper error handling and logging
"""

import os
import sys
import time
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add paths for imports
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/core')

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Import memory service
try:
    from services.memory_service import MemoryService, create_memory_service, MemoryProviderType
    from core.logging_config import get_logger
    MEMORY_SERVICE_AVAILABLE = True
except ImportError:
    MEMORY_SERVICE_AVAILABLE = False
    print("⚠️ Memory service not available, using fallback")

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
CHROMA_HOST = os.getenv("CHROMA_HOST", "chroma")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))

# Request/Response Models
class MemoryStoreRequest(BaseModel):
    user_id: str
    content: str
    context: Optional[str] = None
    importance: float = 0.5
    forced: bool = False
    source: str = "api"

class MemoryRetrieveRequest(BaseModel):
    user_id: str
    query: str
    limit: int = 10
    threshold: float = 0.1

class LearningInteractionRequest(BaseModel):
    user_id: str
    conversation_id: Optional[str] = None
    user_message: str
    assistant_response: str
    context: Optional[str] = None
    timestamp: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class MemoryResponse(BaseModel):
    content: str
    metadata: Dict[str, Any]
    similarity_score: Optional[float] = None
    distance: Optional[float] = None

# FastAPI app
app = FastAPI(title="Fixed Memory API", description="Corrected Memory API with proper endpoints")

# Global memory service
memory_service = None
logger = None

@app.on_event("startup")
async def startup_event():
    """Initialize the memory service."""
    global memory_service, logger
    
    try:
        if MEMORY_SERVICE_AVAILABLE:
            logger = get_logger(__name__)
            # Use DATABASE provider since API provider would create circular dependency
            memory_service = create_memory_service(MemoryProviderType.DATABASE)
            logger.info("✅ Memory service initialized")
        else:
            print("✅ Memory API started with basic functionality")
            
    except Exception as e:
        error_msg = f"❌ Failed to initialize memory service: {e}"
        if logger:
            logger.error(error_msg)
        else:
            print(error_msg)

# Health endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "service": "memory-api",
        "memory_service_available": memory_service is not None,
        "timestamp": datetime.now().isoformat()
    })

# Legacy store endpoint (for backward compatibility)
@app.post("/store")
async def legacy_store_memory(data: dict):
    """Legacy store endpoint for backward compatibility."""
    try:
        user_id = data.get("user_id")
        content = data.get("content")
        metadata = data.get("metadata", {})
        
        if not user_id or not content:
            raise HTTPException(status_code=400, detail="user_id and content are required")
        
        if memory_service:
            success = await memory_service.store_memory(
                user_id=user_id,
                content=content,
                context=metadata.get("context"),
                importance=metadata.get("importance", 0.5),
                source="legacy_api"
            )
            
            return JSONResponse({
                "success": success,
                "memory_id": f"mem_{user_id}_{int(time.time())}",
                "stored": success
            })
        else:
            # Fallback response
            return JSONResponse({
                "success": False,
                "error": "Memory service not available"
            })
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage failed: {str(e)}")

# Legacy retrieve endpoint (for backward compatibility)
@app.get("/retrieve/{user_id}")
async def legacy_retrieve_memories(user_id: str, query: Optional[str] = None):
    """Legacy retrieve endpoint for backward compatibility."""
    try:
        if memory_service and query:
            memories = await memory_service.get_relevant_memories(user_id, query, limit=10)
            
            # Convert to expected format
            memory_list = []
            for memory in memories:
                memory_list.append({
                    "content": memory.content,
                    "metadata": memory.metadata.__dict__ if hasattr(memory.metadata, '__dict__') else {},
                    "similarity_score": getattr(memory, 'similarity_score', 0.0)
                })
            
            return JSONResponse(memory_list)
        else:
            return JSONResponse([])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")

# Proper Memory API endpoints (matching expected interface)
@app.post("/api/memory/store_explicit")
async def store_memory_explicit(request: MemoryStoreRequest):
    """Store memory explicitly with proper response format."""
    try:
        if not memory_service:
            raise HTTPException(status_code=503, detail="Memory service not available")
        
        success = await memory_service.store_memory(
            user_id=request.user_id,
            content=request.content,
            context=request.context,
            importance=request.importance,
            explicit=request.forced,
            source=request.source
        )
        
        memory_id = f"mem_{request.user_id}_{int(time.time())}"
        
        return JSONResponse({
            "memory_id": memory_id,
            "storage_location": "memory_service",
            "status": "stored" if success else "failed",
            "success": success
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage failed: {str(e)}")

@app.post("/api/memory/store")
async def store_memory_simple(request: MemoryStoreRequest):
    """Store memory with simple endpoint (compatibility)."""
    try:
        if not memory_service:
            return JSONResponse({
                "success": False,
                "memory_id": f"mem_{request.user_id}_{int(time.time())}",
                "stored": False,
                "error": "Memory service not available"
            })

        # Create memory entry using the memory service
        success = await memory_service.store_memory(
            user_id=request.user_id,
            content=request.content,
            context=request.context,
            importance=request.importance,
            explicit=request.forced,
            source=request.source
        )
        
        memory_id = f"mem_{request.user_id}_{int(time.time())}"
        
        return JSONResponse({
            "success": success,
            "memory_id": memory_id,
            "stored": success,
            "storage_location": "memory_service",
            "user_id": request.user_id,
            "timestamp": time.time()
        })
        
    except Exception as e:
        logger.error(f"Failed to store memory: {str(e)}")
        return JSONResponse({
            "success": False,
            "memory_id": f"mem_{request.user_id}_{int(time.time())}",
            "stored": False,
            "error": str(e)
        })

@app.post("/api/memory/retrieve")
async def retrieve_memories(request: MemoryRetrieveRequest):
    """Retrieve memories with proper response format."""
    try:
        if not memory_service:
            return JSONResponse({
                "memories": [],
                "count": 0,
                "user_id": request.user_id
            })
        
        memories = await memory_service.get_relevant_memories(
            user_id=request.user_id,
            context=request.query,
            max_memories=request.limit
        )
        
        # Convert to proper format
        memory_results = []
        for memory in memories:
            memory_results.append({
                "content": memory.content,
                "metadata": memory.metadata.__dict__ if hasattr(memory.metadata, '__dict__') else {},
                "similarity_score": getattr(memory, 'similarity_score', 0.0),
                "distance": 1.0 - getattr(memory, 'similarity_score', 0.0)
            })
        
        return JSONResponse({
            "memories": memory_results,
            "count": len(memory_results),
            "user_id": request.user_id
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")

@app.post("/api/learning/process_interaction")
async def process_learning_interaction(request: LearningInteractionRequest):
    """Process and store learning interaction."""
    try:
        if not memory_service:
            raise HTTPException(status_code=503, detail="Memory service not available")
        
        # Store the conversation
        success = await memory_service.track_conversation(
            user_id=request.user_id,
            user_message=request.user_message,
            assistant_response=request.assistant_response
        )
        
        return JSONResponse({
            "processed": True,
            "memory_stored": success,
            "status": "success" if success else "failed",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.get("/api/memory/stats/{user_id}")
async def get_memory_stats(user_id: str):
    """Get memory statistics for user."""
    try:
        if not memory_service:
            return JSONResponse({
                "user_id": user_id,
                "total_memories": 0,
                "memory_types": {},
                "storage_breakdown": {"service": 0}
            })
        
        # Get memories to count them
        memories = await memory_service.get_relevant_memories(user_id, "", max_memories=1000)
        
        return JSONResponse({
            "user_id": user_id,
            "total_memories": len(memories),
            "memory_types": {"conversation": len(memories)},
            "storage_breakdown": {"service": len(memories)}
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats failed: {str(e)}")

@app.delete("/api/memory/{user_id}/{memory_id}")
async def delete_memory(user_id: str, memory_id: str):
    """Delete specific memory."""
    try:
        # Memory service doesn't have delete functionality yet
        return JSONResponse({
            "deleted": False,
            "memory_id": memory_id,
            "note": "Delete functionality not implemented in memory service"
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API documentation."""
    return JSONResponse({
        "message": "Fixed Memory API Service",
        "status": "running",
        "memory_service_available": memory_service is not None,
        "endpoints": [
            "GET /health - Health check",
            "POST /store - Legacy store endpoint", 
            "GET /retrieve/{user_id} - Legacy retrieve endpoint",
            "POST /api/memory/store_explicit - Store memory",
            "POST /api/memory/store - Store memory (simple)",
            "POST /api/memory/retrieve - Retrieve memories",
            "POST /api/learning/process_interaction - Process conversation",
            "GET /api/memory/stats/{user_id} - Memory statistics",
            "DELETE /api/memory/{user_id}/{memory_id} - Delete memory"
        ],
        "timestamp": datetime.now().isoformat()
    })

if __name__ == "__main__":
    print("🧠 Starting Fixed Memory API...")
    uvicorn.run(app, host="0.0.0.0", port=5001, log_level="info")
