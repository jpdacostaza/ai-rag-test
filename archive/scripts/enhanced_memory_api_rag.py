#!/usr/bin/env python3
"""
Enhanced Memory API with RAG Dual-Database Architecture
======================================================

This API provides:
- Redis for short-term memory (fast access)
- ChromaDB for long-term memory (semantic search)
- Proper explicit memory handling
- RAG-optimized retrieval
"""

import os
import sys
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add paths for imports
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/services')

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Import RAG service
try:
    from services.rag_dual_database_service import rag_service
    RAG_SERVICE_AVAILABLE = True
except ImportError:
    RAG_SERVICE_AVAILABLE = False
    print("⚠️ RAG service not available, using fallback")

# Request/Response Models
class MemoryStoreRequest(BaseModel):
    user_id: str = Field(..., description="User ID")
    content: str = Field(..., description="Memory content")
    context: Optional[str] = Field(None, description="Memory context")
    importance: float = Field(0.5, ge=0.0, le=1.0, description="Memory importance (0.0-1.0)")
    explicit: bool = Field(False, description="Is this an explicit 'remember this' command")
    source: str = Field("api", description="Source of the memory")

class MemoryRetrieveRequest(BaseModel):
    user_id: str = Field(..., description="User ID")
    query: Optional[str] = Field(None, description="Semantic search query")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of memories to retrieve")

class ExplicitMemoryRequest(BaseModel):
    user_id: str = Field(..., description="User ID")
    user_input: str = Field(..., description="User's explicit memory command")
    context: Optional[str] = Field(None, description="Context for the memory")

# FastAPI app
app = FastAPI(
    title="Enhanced Memory API with RAG",
    description="Dual-database memory system with Redis + ChromaDB",
    version="2.0.0"
)

# Global service instance
memory_service = None

@app.on_event("startup")
async def startup_event():
    """Initialize the RAG memory service"""
    global memory_service
    
    try:
        if RAG_SERVICE_AVAILABLE:
            memory_service = rag_service
            success = await memory_service.initialize()
            if success:
                print("✅ RAG dual-database service initialized successfully")
            else:
                print("⚠️ RAG service initialized with limited functionality")
        else:
            print("⚠️ Memory API started without RAG service")
            
    except Exception as e:
        print(f"❌ Failed to initialize RAG service: {e}")

@app.get("/health")
async def health_check():
    """Enhanced health check with RAG service status"""
    if memory_service:
        health_status = await memory_service.health_check()
        return JSONResponse({
            "status": "healthy",
            "service": "enhanced-memory-api",
            "version": "2.0.0",
            "rag_service_available": memory_service.initialized,
            "database_status": health_status,
            "timestamp": datetime.now().isoformat()
        })
    else:
        return JSONResponse({
            "status": "limited",
            "service": "enhanced-memory-api",
            "version": "2.0.0",
            "rag_service_available": False,
            "timestamp": datetime.now().isoformat()
        })

@app.post("/api/memory/store")
async def store_memory(request: MemoryStoreRequest):
    """Store memory using RAG dual-database strategy"""
    try:
        if not memory_service:
            raise HTTPException(status_code=503, detail="Memory service not available")

        result = await memory_service.store_memory(
            user_id=request.user_id,
            content=request.content,
            context=request.context,
            importance=request.importance,
            explicit=request.explicit,
            source=request.source
        )
        
        return JSONResponse({
            "success": True,
            "memory_id": result["memory_id"],
            "storage_strategy": result["storage_strategy"],
            "redis_stored": result["redis_stored"],
            "chroma_stored": result["chroma_stored"],
            "importance": result["importance"],
            "explicit": result["explicit"],
            "user_id": request.user_id,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e),
            "user_id": request.user_id,
            "timestamp": datetime.now().isoformat()
        }, status_code=500)

@app.post("/api/memory/store_explicit")
async def store_explicit_memory(request: ExplicitMemoryRequest):
    """Store explicit memory from 'remember this' commands"""
    try:
        if not memory_service:
            raise HTTPException(status_code=503, detail="Memory service not available")

        # Parse explicit memory commands
        content = _extract_memory_content(request.user_input)
        
        # Classify the type of memory
        importance = _classify_memory_importance(content, request.context)
        
        result = await memory_service.store_memory(
            user_id=request.user_id,
            content=content,
            context=request.context,
            importance=importance,
            explicit=True,  # Always explicit for this endpoint
            source="explicit_command"
        )
        
        return JSONResponse({
            "success": True,
            "memory_id": result["memory_id"],
            "original_input": request.user_input,
            "extracted_content": content,
            "storage_strategy": result["storage_strategy"],
            "redis_stored": result["redis_stored"],
            "chroma_stored": result["chroma_stored"],
            "importance": result["importance"],
            "explicit": True,
            "user_id": request.user_id,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e),
            "user_id": request.user_id,
            "timestamp": datetime.now().isoformat()
        }, status_code=500)

@app.post("/api/memory/retrieve")
async def retrieve_memories(request: MemoryRetrieveRequest):
    """Retrieve memories using RAG dual-database strategy"""
    try:
        if not memory_service:
            raise HTTPException(status_code=503, detail="Memory service not available")

        memories = await memory_service.get_memories(
            user_id=request.user_id,
            query=request.query,
            limit=request.limit
        )
        
        # Format memories for response
        formatted_memories = []
        for memory in memories:
            formatted_memory = {
                "memory_id": memory.get("memory_id", ""),
                "content": memory.get("content", ""),
                "context": memory.get("context"),
                "importance": memory.get("importance", 0.5),
                "explicit": memory.get("explicit", False),
                "source": memory.get("source", "unknown"),
                "source_db": memory.get("source_db", "unknown"),
                "timestamp": memory.get("timestamp", "")
            }
            formatted_memories.append(formatted_memory)
        
        return JSONResponse({
            "success": True,
            "memories": formatted_memories,
            "count": len(formatted_memories),
            "query": request.query,
            "user_id": request.user_id,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "memories": [],
            "count": 0,
            "error": str(e),
            "user_id": request.user_id,
            "timestamp": datetime.now().isoformat()
        }, status_code=500)

@app.get("/api/memory/stats/{user_id}")
async def get_memory_stats(user_id: str):
    """Get comprehensive memory statistics"""
    try:
        if not memory_service:
            raise HTTPException(status_code=503, detail="Memory service not available")

        stats = await memory_service.get_storage_stats(user_id)
        
        return JSONResponse({
            "success": True,
            "user_id": user_id,
            "total_memories": stats["total_memories"],
            "explicit_memories": stats["explicit_memories"],
            "redis_stats": stats["redis"],
            "chroma_stats": stats["chroma"],
            "storage_distribution": stats["storage_distribution"],
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "user_id": user_id,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, status_code=500)

@app.get("/api/memory/search/{user_id}")
async def semantic_search(user_id: str, query: str, limit: int = 10):
    """Perform semantic search across memories"""
    try:
        if not memory_service:
            raise HTTPException(status_code=503, detail="Memory service not available")

        memories = await memory_service.get_memories(
            user_id=user_id,
            query=query,
            limit=limit
        )
        
        # Focus on semantic matches from ChromaDB
        semantic_matches = [m for m in memories if m.get("source_db") == "chroma"]
        
        return JSONResponse({
            "success": True,
            "query": query,
            "semantic_matches": len(semantic_matches),
            "total_results": len(memories),
            "memories": memories,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "query": query,
            "error": str(e),
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }, status_code=500)

def _extract_memory_content(user_input: str) -> str:
    """Extract actual content from explicit memory commands"""
    # Remove explicit memory keywords
    keywords = [
        "remember", "don't forget", "please remember", "keep in mind",
        "note that", "make sure to remember", "store this",
        "save this information", "memorize"
    ]
    
    content = user_input.lower()
    for keyword in keywords:
        if keyword in content:
            parts = content.split(keyword, 1)
            if len(parts) > 1:
                content = parts[1].strip()
                content = content.lstrip("that ").lstrip("this ").lstrip(":")
                break
    
    return content.strip()

def _classify_memory_importance(content: str, context: str = None) -> float:
    """Classify memory importance based on content and context"""
    content_lower = content.lower()
    
    # High importance keywords
    high_importance_keywords = [
        "name", "email", "phone", "address", "password", "allergy", "allergic",
        "medical", "emergency", "deadline", "appointment", "meeting", "birthday",
        "anniversary", "account", "login", "credential"
    ]
    
    # Medium importance keywords
    medium_importance_keywords = [
        "prefer", "like", "dislike", "favorite", "setting", "configuration",
        "project", "work", "colleague", "friend", "family"
    ]
    
    # Check context
    if context:
        context_lower = context.lower()
        if context_lower in ["profile", "personal", "health", "security", "important"]:
            return 0.9
        elif context_lower in ["preference", "setting", "work", "project"]:
            return 0.7
        elif context_lower in ["temporary", "session", "ui", "interaction"]:
            return 0.3
    
    # Check content
    for keyword in high_importance_keywords:
        if keyword in content_lower:
            return 0.9
    
    for keyword in medium_importance_keywords:
        if keyword in content_lower:
            return 0.7
    
    # Default to medium importance for explicit memories
    return 0.6

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)
