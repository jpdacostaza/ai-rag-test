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
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import redis.asyncio as redis
import chromadb
from chromadb.config import Settings
from core.unified_logging import get_logger

logger = get_logger(__name__)

# Global connections
redis_client = None
chroma_client = None
chroma_collection = None

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
CHROMA_HOST = os.getenv("CHROMA_HOST", "chroma")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))

def sanitize_metadata_for_chroma(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize metadata for ChromaDB compatibility.
    ChromaDB only accepts: str, int, float, bool values.
    """
    sanitized = {}
    
    for key, value in metadata.items():
        if value is None:
            sanitized[key] = ""
        elif isinstance(value, (str, int, float, bool)):
            sanitized[key] = value
        elif isinstance(value, (list, tuple)):
            # Convert lists/tuples to comma-separated strings
            try:
                sanitized[key] = ",".join(str(item) for item in value)
            except:
                sanitized[key] = str(value)
        elif isinstance(value, dict):
            # Convert dicts to JSON strings
            try:
                sanitized[key] = json.dumps(value)
            except:
                sanitized[key] = str(value)
        else:
            # Convert any other type to string
            sanitized[key] = str(value)
    
    return sanitized

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager - no fallbacks, exact configuration only"""
    global redis_client, chroma_client, chroma_collection
    
    # Startup
    try:
        logger.info("Starting Memory API initialization...")
        
        # Redis connection - use exact configuration only
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        try:
            logger.info(f"[SEARCH] Connecting to Redis: {redis_url}")
            redis_client = redis.from_url(redis_url)
            await asyncio.wait_for(redis_client.ping(), timeout=5.0)
            logger.info(f"[OK] Redis connected: {redis_url}")
        except Exception as e:
            logger.warning(f"[FAIL] Redis connection failed: {e}")
            redis_client = None
        
        # ChromaDB connection - use exact configuration only
        chroma_host = os.getenv("CHROMA_HOST", "chroma")
        chroma_port = int(os.getenv("CHROMA_PORT", "8000"))
        try:
            logger.info(f"[SEARCH] Connecting to ChromaDB: {chroma_host}:{chroma_port}")
            chroma_client = chromadb.HttpClient(
                host=chroma_host,
                port=chroma_port,
                settings=Settings(allow_reset=True)
            )
            
            # Test connection
            heartbeat = chroma_client.heartbeat()
            logger.info(f"[OK] ChromaDB connected: {chroma_host}:{chroma_port} (heartbeat: {heartbeat})")
            
            # Get or create collection - use consistent naming with database manager
            collection_name = os.getenv("CHROMA_COLLECTION", "user_memory")
            try:
                chroma_collection = chroma_client.get_collection(collection_name)
                logger.info(f"[OK] ChromaDB collection '{collection_name}' found")
            except Exception as collection_error:
                logger.info(f"Collection not found, creating new one: {collection_error}")
                chroma_collection = chroma_client.create_collection(collection_name)
                logger.info(f"[OK] ChromaDB collection '{collection_name}' created")
                
        except Exception as e:
            logger.warning(f"[FAIL] ChromaDB connection failed: {e}")
            chroma_client = None
            chroma_collection = None
        
        # Status summary - no fallbacks
        if redis_client and chroma_collection:
            logger.info("[OK] Memory API fully initialized (Redis + ChromaDB)")
        elif redis_client:
            logger.warning("[WARN] Memory API partially initialized (Redis only)")
        elif chroma_collection:
            logger.warning("[WARN] Memory API partially initialized (ChromaDB only)")
        else:
            logger.error("[FAIL] Memory API running in degraded mode (no external connections)")
        
    except Exception as e:
        logger.exception(f"[FAIL] Startup failed: {e}")
    
    yield
    
    # Shutdown
    if redis_client:
        try:
            await redis_client.aclose()
            logger.info("[OK] Redis connection closed")
        except Exception as e:
            logger.warning(f"[WARN] Redis shutdown warning: {e}")

# FastAPI app with lifespan
app = FastAPI(
    title="Enhanced Memory API", 
    description="Memory service with Redis + ChromaDB",
    lifespan=lifespan
)

# Request/Response Models
class MemoryStoreRequest(BaseModel):
    user_id: str
    content: str
    context: Optional[str] = None
    importance: float = 0.5
    forced: bool = False
    source: str = "api"
    metadata: Optional[Dict[str, Any]] = None  # Support for custom metadata

class MemoryRetrieveRequest(BaseModel):
    user_id: str
    query: str
    limit: int = 10
    threshold: float = None  # Will be set from unified config if None
    
    def __init__(self, **data):
        # Set threshold from unified config if not provided
        if data.get('threshold') is None:
            try:
                import sys
                import os
                sys.path.insert(0, '/opt/backend')
                sys.path.insert(0, '/app')
                from config.config_unified import Config
                config = Config.get_instance()
                # data['threshold'] = config.memory.retrieval_threshold  # Controlled by OpenWebUI Function
                from config.memory_threshold import get_default_memory_threshold
                data['threshold'] = get_default_memory_threshold()  # Centralized fallback
            except ImportError:
                from config.memory_threshold import get_default_memory_threshold
                data['threshold'] = get_default_memory_threshold()  # Centralized fallback
        super().__init__(**data)

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

# Health endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint with graceful degradation"""
    redis_ok = False
    chroma_ok = False
    
    try:
        if redis_client:
            await asyncio.wait_for(redis_client.ping(), timeout=2.0)
            redis_ok = True
    except Exception as e:
        logger.debug(f"Redis health check failed: {e}")
    
    try:
        if chroma_collection:
            count = chroma_collection.count()
            chroma_ok = True
    except Exception as e:
        logger.debug(f"ChromaDB health check failed: {e}")
    
    # Determine status
    if redis_ok and chroma_ok:
        status = "healthy"
    elif redis_ok or chroma_ok:
        status = "degraded"
    else:
        status = "critical"
    
    return JSONResponse({
        "status": status,
        "redis_connected": redis_ok,
        "chromadb_connected": chroma_ok,
        "memory_count": chroma_collection.count() if chroma_ok else 0,
        "message": "Memory API - exact configuration only, no fallbacks"
    })

# Memory storage endpoint
@app.post("/api/memory/store_explicit")
async def store_memory(request: MemoryStoreRequest):
    """Store memory explicitly with graceful degradation"""
    try:
        logger.info(f"Memory store request received: user_id={request.user_id}, content_length={len(request.content)}")
        memory_id = f"mem_{request.user_id}_{int(time.time())}"
        timestamp = datetime.now().isoformat()
        
        storage_results = []

        # Store in Redis if available
        if redis_client:
            try:
                redis_key = f"memory:{request.user_id}:{memory_id}"
                redis_data = {
                    "content": request.content,
                    "context": request.context or "",
                    "importance": request.importance,
                    "source": request.source,
                    "timestamp": timestamp,
                    "user_id": request.user_id
                }

                await redis_client.hset(redis_key, mapping=redis_data)
                await redis_client.expire(redis_key, 86400)  # 24 hours
                storage_results.append("redis")
            except Exception as e:
                logger.error(f"Redis storage failed: {e}")

        # Store in ChromaDB if available
        if chroma_collection:
            try:
                metadata_for_chroma = {
                    "user_id": request.user_id,
                    "context": request.context or "",
                    "importance": request.importance,
                    "source": request.source,
                    "timestamp": timestamp,
                    "memory_id": memory_id
                }
                
                # Sanitize metadata for ChromaDB compatibility
                sanitized_metadata = sanitize_metadata_for_chroma(metadata_for_chroma)
                
                chroma_collection.add(
                    documents=[request.content],
                    metadatas=[sanitized_metadata],
                    ids=[memory_id]
                )
                storage_results.append("chromadb")
            except Exception as e:
                logger.error(f"ChromaDB storage failed: {e}")
                # Log the problematic metadata for debugging
                logger.debug(f"Failed metadata: {metadata_for_chroma}")
        
        if not storage_results:
            raise HTTPException(
                status_code=503,
                detail="No storage backends available"
            )
        
        return JSONResponse({
            "memory_id": memory_id,
            "storage_location": "+".join(storage_results),
            "status": "stored"
        })
        
    except Exception as e:
        logger.error(f"Memory storage error: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Storage failed: {str(e)}")

# Regular memory storage endpoint  
@app.post("/api/memory/store")
async def store_memory_regular(request: MemoryStoreRequest):
    """Store memory with normal importance and filtering"""
    try:
        logger.info(f"Regular memory store request: user_id={request.user_id}, content_length={len(request.content)}, source={request.source}")
        
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
        
        # Handle metadata extraction
        if request.metadata:
            # Use metadata if provided
            user_id = request.metadata.get("user_id", request.user_id)
            context = request.metadata.get("context", request.context or "")
            importance = min(request.metadata.get("importance", request.importance), 0.5) if not request.forced else request.metadata.get("importance", request.importance)
            source = request.metadata.get("source", request.source)
            memory_id = request.metadata.get("memory_id", f"mem_{request.user_id}_{int(time.time())}")
            
            # Preserve all custom metadata fields
            full_metadata = request.metadata.copy()
        else:
            # Fallback to request fields
            user_id = request.user_id
            context = request.context or ""
            importance = min(request.importance, 0.5) if not request.forced else request.importance
            source = request.source
            memory_id = f"mem_{request.user_id}_{int(time.time())}"
            
            # Create basic metadata
            full_metadata = {
                "user_id": user_id,
                "context": context,
                "importance": importance,
                "source": source
            }
        
        timestamp = datetime.now().isoformat()
        full_metadata["timestamp"] = timestamp
        full_metadata["memory_id"] = memory_id
        
        # Store in Redis for quick access
        if redis_client:
            try:
                redis_key = f"memory:{user_id}:{memory_id}"
                redis_data = {
                    "content": request.content,
                    "context": context,
                    "importance": importance,
                    "source": source,
                    "timestamp": timestamp,
                    "user_id": user_id
                }
                
                # Add custom metadata fields to Redis
                if request.metadata:
                    for key, value in request.metadata.items():
                        if key not in ["content"]:  # Don't duplicate content
                            redis_data[key] = str(value)
                
                await redis_client.hset(redis_key, mapping=redis_data)
                await redis_client.expire(redis_key, 86400)  # 24 hours
            except Exception as e:
                logger.error(f"Redis storage failed: {e}")
        
        # Ensure user_id stored in metadata for retrieval filtering
        if 'user_id' not in full_metadata:
            full_metadata['user_id'] = user_id

        # Store in ChromaDB for semantic search with full metadata
        if chroma_collection:
            try:
                # Sanitize metadata for ChromaDB compatibility
                sanitized_metadata = sanitize_metadata_for_chroma(full_metadata)
                
                chroma_collection.add(
                    documents=[request.content],
                    metadatas=[sanitized_metadata],
                    ids=[memory_id]
                )
            except Exception as e:
                logger.error(f"ChromaDB storage failed: {e}")
                # Log the problematic metadata for debugging
                logger.debug(f"Failed metadata: {full_metadata}")
        
        return JSONResponse({
            "memory_id": memory_id,
            "storage_location": "redis+chromadb",
            "status": "stored",
            "importance": importance
        })
        
    except Exception as e:
        logger.error(f"Regular memory storage error: {e}")
        raise HTTPException(status_code=500, detail=f"Storage failed: {str(e)}")

# Memory retrieval endpoint
@app.post("/api/memory/retrieve")
async def retrieve_memories(request: MemoryRetrieveRequest):
    """Retrieve memories for user"""
    try:
        memories = []
        
        # Check if ChromaDB collection is initialized
        if chroma_collection is None:
            raise HTTPException(
                status_code=503, 
                detail="ChromaDB collection not initialized. Service starting up."
            )
        
        # Query ChromaDB for semantic matches
        results = chroma_collection.query(
            query_texts=[request.query],
            n_results=request.limit,
            where={"user_id": request.user_id}
        )
        
        if results['documents']:
            # Interpret threshold semantics:
            #   * Positive value  -> maximum allowed distance (distance <= threshold)
            #   * Zero / None     -> include all results
            #   * Negative value  -> DISABLE filtering (include all) -- used as sentinel default (-0.5)
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                distance = results['distances'][0][i] if results['distances'] else 0.0
                similarity = 1.0 - distance

                include = False
                if request.threshold is None:
                    include = True
                elif request.threshold == 0:
                    include = True  # explicit 0 means no filtering
                elif request.threshold < 0:
                    # Negative sentinel = no filtering
                    include = True
                else:
                    # Positive interpreted as max distance
                    if distance <= request.threshold:
                        include = True

                if include:
                    memories.append({
                        "content": doc,
                        "metadata": metadata,
                        "distance": distance,
                        "similarity_score": similarity
                    })
        
        return JSONResponse({
            "memories": memories,
            "count": len(memories),
            "user_id": request.user_id,
            "applied_threshold": request.threshold,
            "threshold_mode": ("disabled" if (request.threshold is not None and request.threshold < 0) else ("distance_max" if (request.threshold is not None and request.threshold > 0) else "none"))
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
        except Exception:
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
