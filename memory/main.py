from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import redis
import chromadb
import json
import os
from typing import List, Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Memory API", version="1.0.0")

# Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
CHROMA_HOST = os.getenv("CHROMA_HOST", "chroma")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))

# Initialize connections
redis_client = None
chroma_client = None

class MemoryEntry(BaseModel):
    id: str
    content: str
    metadata: Optional[Dict[str, Any]] = {}

class MemoryQuery(BaseModel):
    query: str
    limit: Optional[int] = 5

@app.on_event("startup")
async def startup_event():
    global redis_client, chroma_client
    try:
        # Initialize Redis
        redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        redis_client.ping()
        logger.info("Connected to Redis")
        
        # Initialize ChromaDB
        chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        logger.info("Connected to ChromaDB")
    except Exception as e:
        logger.error(f"Failed to connect to services: {e}")
        raise

@app.get("/")
async def root():
    return {"message": "Memory API is running"}

@app.get("/health")
async def health_check():
    try:
        # Check Redis
        redis_client.ping()
        
        # Check ChromaDB
        chroma_client.heartbeat()
        
        return {"status": "healthy", "redis": "connected", "chroma": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {e}")

@app.post("/memory")
async def store_memory(memory: MemoryEntry):
    try:
        # Store in Redis for fast access
        redis_client.hset(f"memory:{memory.id}", mapping={
            "content": memory.content,
            "metadata": json.dumps(memory.metadata)
        })
        
        # Store in ChromaDB for semantic search
        collection = chroma_client.get_or_create_collection("memories")
        collection.add(
            documents=[memory.content],
            ids=[memory.id],
            metadatas=[memory.metadata]
        )
        
        return {"status": "success", "id": memory.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store memory: {e}")

@app.get("/memory/{memory_id}")
async def get_memory(memory_id: str):
    try:
        # Get from Redis
        memory_data = redis_client.hgetall(f"memory:{memory_id}")
        if not memory_data:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        return {
            "id": memory_id,
            "content": memory_data["content"],
            "metadata": json.loads(memory_data.get("metadata", "{}"))
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve memory: {e}")

@app.post("/memory/search")
async def search_memories(query: MemoryQuery):
    try:
        collection = chroma_client.get_or_create_collection("memories")
        results = collection.query(
            query_texts=[query.query],
            n_results=query.limit
        )
        
        memories = []
        if results["ids"]:
            for i, memory_id in enumerate(results["ids"][0]):
                memories.append({
                    "id": memory_id,
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if results["distances"] else None
                })
        
        return {"memories": memories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search memories: {e}")

@app.delete("/memory/{memory_id}")
async def delete_memory(memory_id: str):
    try:
        # Delete from Redis
        deleted = redis_client.delete(f"memory:{memory_id}")
        
        # Delete from ChromaDB
        collection = chroma_client.get_or_create_collection("memories")
        collection.delete(ids=[memory_id])
        
        if deleted:
            return {"status": "success", "message": "Memory deleted"}
        else:
            raise HTTPException(status_code=404, detail="Memory not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete memory: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
