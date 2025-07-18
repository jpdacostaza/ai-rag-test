"""
Complete Memory API for OpenWebUI Enhanced Memory System
Provides Redis + ChromaDB integration with auto-setup
"""

import os
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import redis.asyncio as redis
import chromadb
from chromadb.config import Settings

# FastAPI app
app = FastAPI(title="Enhanced Memory API", description="Memory service with Redis + ChromaDB")

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
CHROMA_HOST = os.getenv("CHROMA_HOST", "chroma")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))

# Global connections
redis_client = None
chroma_client = None
chroma_collection = None

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
    user_message: str
    assistant_response: str
    context: Optional[str] = None

class MemoryResponse(BaseModel):
    content: str
    metadata: Dict[str, Any]
    similarity_score: Optional[float] = None
    distance: Optional[float] = None

# Startup/shutdown
@app.on_event("startup")
async def startup_event():
    """Initialize connections"""
    global redis_client, chroma_client, chroma_collection
    
    try:
        # Redis connection
        redis_client = redis.from_url(REDIS_URL)
        await redis_client.ping()
        print("✅ Redis connected")
        
        # ChromaDB connection
        chroma_client = chromadb.HttpClient(
            host=CHROMA_HOST,
            port=CHROMA_PORT,
            settings=Settings(allow_reset=True)
        )
        
        # Get or create collection
        try:
            chroma_collection = chroma_client.get_collection("user_memories")
        except:
            chroma_collection = chroma_client.create_collection("user_memories")
        
        print("✅ ChromaDB connected")
        
    except Exception as e:
        print(f"❌ Startup failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup connections"""
    global redis_client
    if redis_client:
        await redis_client.close()

# Health endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    redis_ok = False
    chroma_ok = False
    
    try:
        if redis_client:
            await redis_client.ping()
            redis_ok = True
    except:
        pass
    
    try:
        if chroma_collection:
            chroma_collection.count()
            chroma_ok = True
    except:
        pass
    
    return JSONResponse({
        "status": "healthy" if (redis_ok and chroma_ok) else "degraded",
        "redis_connected": redis_ok,
        "chromadb_connected": chroma_ok,
        "memory_count": chroma_collection.count() if chroma_ok else 0
    })

# Memory storage endpoint
@app.post("/api/memory/store_explicit")
async def store_memory(request: MemoryStoreRequest):
    """Store memory explicitly"""
    try:
        memory_id = f"mem_{request.user_id}_{int(time.time())}"
        timestamp = datetime.now().isoformat()
        
        # Store in Redis for quick access
        redis_key = f"memory:{request.user_id}:{memory_id}"
        redis_data = {
            "content": request.content,
            "context": request.context or "",
            "importance": request.importance,
            "source": request.source,
            "timestamp": timestamp
        }
        
        await redis_client.hset(redis_key, mapping=redis_data)
        await redis_client.expire(redis_key, 86400)  # 24 hours
        
        # Store in ChromaDB for semantic search
        chroma_collection.add(
            documents=[request.content],
            metadatas=[{
                "user_id": request.user_id,
                "context": request.context or "",
                "importance": request.importance,
                "source": request.source,
                "timestamp": timestamp,
                "memory_id": memory_id
            }],
            ids=[memory_id]
        )
        
        return JSONResponse({
            "memory_id": memory_id,
            "storage_location": "redis+chromadb",
            "status": "stored"
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage failed: {str(e)}")

# Regular memory storage endpoint  
@app.post("/api/memory/store")
async def store_memory_regular(request: MemoryStoreRequest):
    """Store memory with normal importance and filtering"""
    try:
        # Apply filtering logic for normal storage
        content_length = len(request.content)
        
        # Skip very short or repetitive content for normal storage
        if content_length < 10:
            return JSONResponse({
                "memory_id": None,
                "storage_location": "skipped",
                "status": "skipped_too_short",
                "reason": "Content too short for normal storage"
            })
        
        # Reduce importance for normal storage (unless forced)
        importance = min(request.importance, 0.5) if not request.forced else request.importance
        
        memory_id = f"mem_{request.user_id}_{int(time.time())}"
        timestamp = datetime.now().isoformat()
        
        # Store in Redis for quick access
        redis_key = f"memory:{request.user_id}:{memory_id}"
        redis_data = {
            "content": request.content,
            "context": request.context or "",
            "importance": importance,
            "source": request.source,
            "timestamp": timestamp
        }
        
        await redis_client.hset(redis_key, mapping=redis_data)
        await redis_client.expire(redis_key, 86400)  # 24 hours
        
        # Store in ChromaDB for semantic search
        chroma_collection.add(
            documents=[request.content],
            metadatas=[{
                "user_id": request.user_id,
                "context": request.context or "",
                "importance": importance,
                "source": request.source,
                "timestamp": timestamp,
                "memory_id": memory_id
            }],
            ids=[memory_id]
        )
        
        return JSONResponse({
            "memory_id": memory_id,
            "storage_location": "redis+chromadb",
            "status": "stored",
            "importance": importance
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage failed: {str(e)}")

# Memory retrieval endpoint
@app.post("/api/memory/retrieve")
async def retrieve_memories(request: MemoryRetrieveRequest):
    """Retrieve memories for user"""
    try:
        memories = []
        
        # Query ChromaDB for semantic matches
        results = chroma_collection.query(
            query_texts=[request.query],
            n_results=request.limit,
            where={"user_id": request.user_id}
        )
        
        if results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                distance = results['distances'][0][i] if results['distances'] else 0.0
                
                # Only include if below threshold
                if distance <= request.threshold:
                    memories.append({
                        "content": doc,
                        "metadata": metadata,
                        "distance": distance,
                        "similarity_score": 1.0 - distance
                    })
        
        return JSONResponse({
            "memories": memories,
            "count": len(memories),
            "user_id": request.user_id
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")

# Learning interaction endpoint
@app.post("/api/learning/process_interaction")
async def process_learning_interaction(request: LearningInteractionRequest):
    """Process and store learning interaction"""
    try:
        # Create conversation memory
        conversation = f"User: {request.user_message}\nAssistant: {request.assistant_response}"
        
        # Store as memory
        store_request = MemoryStoreRequest(
            user_id=request.user_id,
            content=conversation,
            context=request.context or "conversation",
            importance=0.7,
            source="conversation"
        )
        
        result = await store_memory(store_request)
        
        return {
            "processed": True,
            "memory_stored": True,
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

# Memory stats endpoint
@app.get("/api/memory/stats/{user_id}")
async def get_memory_stats(user_id: str):
    """Get memory statistics for user"""
    try:
        # Count memories in ChromaDB
        results = chroma_collection.query(
            query_texts=[""],
            n_results=1000,  # Large number to get all
            where={"user_id": user_id}
        )
        
        total_memories = len(results['documents'][0]) if results['documents'] else 0
        
        # Count by source
        memory_types = {}
        if results['metadatas']:
            for metadata in results['metadatas'][0]:
                source = metadata.get('source', 'unknown')
                memory_types[source] = memory_types.get(source, 0) + 1
        
        return JSONResponse({
            "user_id": user_id,
            "total_memories": total_memories,
            "memory_types": memory_types,
            "storage_breakdown": {
                "chromadb": total_memories,
                "redis": 0  # Would need to scan Redis keys
            }
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats failed: {str(e)}")

# Delete memory endpoint
@app.delete("/api/memory/{user_id}/{memory_id}")
async def delete_memory(user_id: str, memory_id: str):
    """Delete specific memory"""
    try:
        # Delete from Redis
        redis_key = f"memory:{user_id}:{memory_id}"
        await redis_client.delete(redis_key)
        
        # Delete from ChromaDB
        try:
            chroma_collection.delete(ids=[memory_id])
        except:
            pass  # May not exist
        
        return JSONResponse({
            "deleted": True,
            "memory_id": memory_id
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return JSONResponse({
        "message": "Enhanced Memory API Service", 
        "status": "running",
        "endpoints": [
            "/health",
            "/api/memory/store",
            "/api/memory/store_explicit",
            "/api/memory/retrieve", 
            "/api/learning/process_interaction",
            "/api/memory/stats/{user_id}",
            "/api/memory/{user_id}/{memory_id}"
        ]
    })

if __name__ == "__main__":
    import uvicorn
    import logging
    
    # Disable uvicorn access logging to prevent duplicate logs
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.disabled = True
    uvicorn_access.setLevel(logging.CRITICAL)
    uvicorn_access.propagate = False
    
    # Also disable uvicorn error logging for cleaner output
    uvicorn_error = logging.getLogger("uvicorn.error")
    uvicorn_error.disabled = True
    uvicorn_error.setLevel(logging.CRITICAL) 
    uvicorn_error.propagate = False
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=5001,
        access_log=False,  # Disable access logging
        log_level="critical"  # Only critical uvicorn logs
    )
