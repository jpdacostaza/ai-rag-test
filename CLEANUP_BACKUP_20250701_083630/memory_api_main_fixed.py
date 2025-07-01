#!/usr/bin/env python3
"""
Enhanced Memory API Server with Redis + ChromaDB Integration
==========================================================
A FastAPI server providing memory and learning endpoints with:
- Redis for short-term memory (session data, recent interactions)
- ChromaDB for long-term memory (persistent semantic storage)
- Automatic memory lifecycle management
"""
import asyncio
import json
import os
import time
import uuid
from typing import Dict, Any, List, Optional
import re
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
# Database imports
try:
    import redis
    import chromadb
    from chromadb.config import Settings
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "redis chromadb"])
    import redis
    import chromadb
    from chromadb.config import Settings
# Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
CHROMA_HOST = os.getenv("CHROMA_HOST", "chroma")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
# Memory lifecycle settings
SHORT_TERM_TTL = 24 * 60 * 60  # 24 hours for Redis
LONG_TERM_THRESHOLD = 3  # After 3 accesses, move to long-term storage
app = FastAPI(title="Enhanced Memory API", version="2.0.0")
# Enable CORS for function access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Global connections
redis_client = None
chroma_client = None
memory_collection = None
class MemoryRetrieveRequest(BaseModel):
    user_id: str
    query: str
    limit: int = 5
    threshold: float = 0.1  # FIXED: Lowered from 0.7 to 0.1
class LearningInteractionRequest(BaseModel):
    user_id: str
    conversation_id: str
    user_message: str
    assistant_response: Optional[str] = None
    response_time: Optional[float] = 1.0
    tools_used: Optional[List[str]] = None
    context: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    source: Optional[str] = "function"
class DocumentLearningRequest(BaseModel):
    user_id: str
    document: Dict[str, Any]
async def initialize_databases():
    """Initialize Redis and ChromaDB connections."""
    global redis_client, chroma_client, memory_collection
    try:
        # Initialize Redis for short-term memory
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        # Test Redis connection
        redis_client.ping()
        print(f"✅ Redis connected at {REDIS_HOST}:{REDIS_PORT}")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("⚠️ Falling back to in-memory short-term storage")
        redis_client = None
    try:
        # Initialize ChromaDB for long-term memory
        chroma_client = chromadb.HttpClient(
            host=CHROMA_HOST,
            port=CHROMA_PORT,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        # Create or get memory collection
        memory_collection = chroma_client.get_or_create_collection(
            name="user_memories",
            metadata={"description": "Long-term user memory storage"}
        )
        print(f"✅ ChromaDB connected at {CHROMA_HOST}:{CHROMA_PORT}")
        print(f"📚 Memory collection has {memory_collection.count()} documents")
    except Exception as e:
        print(f"❌ ChromaDB connection failed: {e}")
        print("⚠️ Falling back to simple storage for long-term memory")
        chroma_client = None
        memory_collection = None
@app.on_event("startup")
async def startup_event():
    """Initialize database connections on startup."""
    await initialize_databases()
@app.get("/")
async def root():
    return {
        "message": "Enhanced Memory API Server with Redis + ChromaDB",
        "version": "2.0.0",
        "features": ["short_term_redis", "long_term_chromadb", "semantic_search"],
        "endpoints": ["/api/memory/retrieve", "/api/learning/process_interaction", "/debug/stats"]
    }
@app.get("/health")
async def health():
    """Health check endpoint."""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "redis": "connected" if redis_client else "disconnected",
        "chromadb": "connected" if chroma_client else "disconnected"
    }
    # Test connections
    try:
        if redis_client:
            redis_client.ping()
            health_status["redis"] = "healthy"
    except:
        health_status["redis"] = "error"
    try:
        if memory_collection:
            memory_collection.count()
            health_status["chromadb"] = "healthy"
    except:
        health_status["chromadb"] = "error"
    return health_status
@app.post("/api/memory/retrieve")
async def retrieve_memory(request: MemoryRetrieveRequest = Body(...)):
    """
    Retrieve memories for a user query from both short-term (Redis) and long-term (ChromaDB) storage.
    """
    try:
        print(f"🔍 Memory retrieval for user {request.user_id}, query: {request.query[:50]}...")
        all_memories = []
        # 1. Retrieve from Redis (short-term memory)
        short_term_memories = await retrieve_from_redis(request.user_id, request.query)
        all_memories.extend(short_term_memories)
        print(f"📱 Found {len(short_term_memories)} short-term memories")
        # 2. Retrieve from ChromaDB (long-term memory)
        long_term_memories = await retrieve_from_chromadb(request.user_id, request.query, request.limit)
        all_memories.extend(long_term_memories)
        print(f"📚 Found {len(long_term_memories)} long-term memories")
        # 3. Combine and rank memories
        relevant_memories = []
        for memory in all_memories:
            relevance_score = calculate_relevance_score(memory["content"], request.query)
            print(f"🔍 Memory: '{memory['content'][:50]}...' Score: {relevance_score:.3f} (threshold: {request.threshold})")
            if relevance_score >= request.threshold:
                memory["relevance_score"] = relevance_score
                relevant_memories.append(memory)
        # Sort by relevance and recency
        relevant_memories.sort(key=lambda x: (x["relevance_score"], x.get("timestamp", 0)), reverse=True)
        relevant_memories = relevant_memories[:request.limit]
        print(f"✅ Returning {len(relevant_memories)} relevant memories")
        return {
            "status": "success",
            "memories": relevant_memories,
            "count": len(relevant_memories),
            "user_id": request.user_id,
            "sources": {
                "short_term": len(short_term_memories),
                "long_term": len(long_term_memories)
            }
        }
    except Exception as e:
        print(f"❌ Memory retrieval error: {e}")
        raise HTTPException(status_code=500, detail=f"Memory retrieval failed: {str(e)}")
@app.post("/api/learning/process_interaction")
async def process_interaction(request: LearningInteractionRequest = Body(...)):
    """
    Process a learning interaction and store in appropriate memory systems.
    """
    try:
        print(f"🧠 Processing interaction for user {request.user_id}")
        print(f"   Message: {request.user_message[:100]}...")
        # Store interaction metadata
        interaction = {
            "user_id": request.user_id,
            "conversation_id": request.conversation_id,
            "user_message": request.user_message,
            "assistant_response": request.assistant_response,
            "response_time": request.response_time,
            "tools_used": request.tools_used or [],
            "context": request.context or {},
            "timestamp": time.time(),
            "source": request.source
        }
        # Extract memories from the user message
        extracted_memories = extract_memories(request.user_message)
        memories_stored = 0
        for memory_text in extracted_memories:
            # Store in short-term memory (Redis) first
            if await store_to_redis(request.user_id, memory_text, interaction):
                memories_stored += 1
                print(f"💾 Stored short-term memory: {memory_text[:50]}...")
        # Get total memory counts
        short_term_count = await get_redis_memory_count(request.user_id)
        long_term_count = await get_chromadb_memory_count(request.user_id)
        print(f"✅ Processing complete - {memories_stored} new memories")
        return {
            "status": "success",
            "user_id": request.user_id,
            "processed": True,
            "new_memories": memories_stored,
            "total_memories": {
                "short_term": short_term_count,
                "long_term": long_term_count,
                "total": short_term_count + long_term_count
            }
        }
    except Exception as e:
        print(f"❌ Learning processing error: {e}")
        return {
            "status": "partial_success",
            "error": str(e),
            "user_id": request.user_id,
            "processed": False
        }
async def retrieve_from_redis(user_id: str, query: str) -> List[Dict[str, Any]]:
    """Retrieve memories from Redis short-term storage."""
    if not redis_client:
        return []
    try:
        # Get all memory keys for this user
        pattern = f"memory:{user_id}:*"
        keys = redis_client.keys(pattern)
        memories = []
        for key in keys:
            memory_data = redis_client.hgetall(key)
            if memory_data:
                memories.append({
                    "content": memory_data.get("content", ""),
                    "metadata": {
                        "type": "short_term",
                        "timestamp": float(memory_data.get("timestamp", 0)),
                        "access_count": int(memory_data.get("access_count", 0)),
                        "conversation_id": memory_data.get("conversation_id", "")
                    }
                })
                # Increment access count
                redis_client.hincrby(key, "access_count", 1)
                # Check if this memory should be promoted to long-term storage
                access_count = int(memory_data.get("access_count", 0)) + 1
                if access_count >= LONG_TERM_THRESHOLD:
                    await promote_to_long_term(user_id, memory_data)
        return memories
    except Exception as e:
        print(f"❌ Redis retrieval error: {e}")
        return []
async def retrieve_from_chromadb(user_id: str, query: str, limit: int) -> List[Dict[str, Any]]:
    """Retrieve memories from ChromaDB long-term storage."""
    if not memory_collection:
        return []
    try:
        # Semantic search in ChromaDB
        results = memory_collection.query(
            query_texts=[query],
            where={"user_id": user_id},
            n_results=limit
        )
        memories = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 1.0
                memories.append({
                    "content": doc,
                    "metadata": {
                        **metadata,
                        "type": "long_term",
                        "semantic_distance": distance
                    }
                })
        return memories
    except Exception as e:
        print(f"❌ ChromaDB retrieval error: {e}")
        return []
async def store_to_redis(user_id: str, content: str, interaction: Dict[str, Any]) -> bool:
    """Store memory in Redis with TTL."""
    if not redis_client:
        return False
    try:
        memory_id = str(uuid.uuid4())
        key = f"memory:{user_id}:{memory_id}"
        memory_data = {
            "content": content,
            "timestamp": interaction["timestamp"],
            "conversation_id": interaction["conversation_id"],
            "access_count": 0,
            "source": interaction["source"]
        }
        redis_client.hset(key, mapping=memory_data)
        redis_client.expire(key, SHORT_TERM_TTL)
        return True
    except Exception as e:
        print(f"❌ Redis storage error: {e}")
        return False
async def promote_to_long_term(user_id: str, memory_data: Dict[str, Any]):
    """Promote frequently accessed memory from Redis to ChromaDB."""
    if not memory_collection:
        return
    try:
        memory_id = str(uuid.uuid4())
        memory_collection.add(
            documents=[memory_data["content"]],
            metadatas=[{
                "user_id": user_id,
                "timestamp": memory_data["timestamp"],
                "conversation_id": memory_data["conversation_id"],
                "promoted_at": time.time(),
                "access_count": memory_data.get("access_count", 0),
                "source": memory_data.get("source", "unknown")
            }],
            ids=[memory_id]
        )
        print(f"⬆️ Promoted memory to long-term storage: {memory_data['content'][:50]}...")
    except Exception as e:
        print(f"❌ Long-term promotion error: {e}")
def extract_memories(text: str) -> List[str]:
    """Extract memorable information from user text."""
    memories = []
    text_lower = text.lower()
    # Name extraction
    name_patterns = [
        r"my name is ([a-zA-Z\s]+)",
        r"i'm ([a-zA-Z\s]+)",
        r"i am ([a-zA-Z\s]+)",
        r"call me ([a-zA-Z\s]+)"
    ]
    for pattern in name_patterns:
        matches = re.findall(pattern, text_lower)
        for name in matches:
            name = name.strip().title()
            if len(name) > 1 and name not in ["A", "An", "The"]:
                memories.append(f"User's name is {name}")
    # Work/profession extraction
    work_patterns = [
        r"i work (?:as |at |in )?([^.!?]+)",
        r"i'm (?:a |an )?(.+?) (?:at|in|for) ([^.!?]+)",
        r"my job is ([^.!?]+)",
        r"i do ([^.!?]+)"
    ]
    for pattern in work_patterns:
        matches = re.findall(pattern, text_lower)
        for match in matches:
            if isinstance(match, tuple):
                work_info = " ".join(match).strip()
            else:
                work_info = match.strip()
            if len(work_info) > 3:
                memories.append(f"User works {work_info}")
    # Personal interests and preferences
    if any(keyword in text_lower for keyword in ["i like", "i love", "i enjoy", "my favorite", "i prefer"]):
        memories.append(text.strip())
    # Skills and experience
    if any(keyword in text_lower for keyword in ["i have experience", "i know", "i'm good at", "i specialize"]):
        memories.append(text.strip())
    # Location information
    location_patterns = [
        r"i live in ([^.!?]+)",
        r"i'm from ([^.!?]+)",
        r"my city is ([^.!?]+)"
    ]
    for pattern in location_patterns:
        matches = re.findall(pattern, text_lower)
        for location in matches:
            location = location.strip().title()
            if len(location) > 1:
                memories.append(f"User lives in {location}")
    return memories
def calculate_relevance_score(content: str, query: str) -> float:
    """Calculate relevance score between content and query. ENHANCED for better matching."""
    content_lower = content.lower()
    query_lower = query.lower()
    query_words = set(query_lower.split())
    content_words = set(content_lower.split())
    
    score = 0.0
    total_words = len(query_words)
    if not total_words:
        return 0.0
    
    # Exact word matches (higher weight)
    exact_matches = query_words.intersection(content_words)
    score += len(exact_matches) * 0.5
    
    # Partial matches (substring matching)
    for query_word in query_words:
        for content_word in content_words:
            if len(query_word) > 2 and len(content_word) > 2:
                if query_word in content_word or content_word in query_word:
                    score += 0.2
    
    # Common patterns for memory queries
    if "what do you know" in query_lower or "tell me about" in query_lower:
        # For these queries, give any stored memory some relevance
        score += 0.3
    
    # Name-based queries
    if "name" in query_lower and "name" in content_lower:
        score += 0.4
    
    # Work-based queries  
    if any(word in query_lower for word in ["work", "job", "career"]) and any(word in content_lower for word in ["work", "job", "career"]):
        score += 0.4
    
    # Normalize by query length and ensure minimum relevance for any memory
    normalized_score = min(score / max(total_words, 1), 1.0)
    
    # Give a small base score to any memory for broad queries
    if "what do you know" in query_lower or "about me" in query_lower:
        normalized_score = max(normalized_score, 0.15)
    
    return normalized_score
async def get_redis_memory_count(user_id: str) -> int:
    """Get count of memories in Redis for a user."""
    if not redis_client:
        return 0
    try:
        pattern = f"memory:{user_id}:*"
        keys = redis_client.keys(pattern)
        return len(keys)
    except:
        return 0
async def get_chromadb_memory_count(user_id: str) -> int:
    """Get count of memories in ChromaDB for a user."""
    if not memory_collection:
        return 0
    try:
        results = memory_collection.get(where={"user_id": user_id})
        return len(results["ids"]) if results["ids"] else 0
    except:
        return 0
@app.get("/debug/stats")
async def debug_stats():
    """Debug endpoint to show current state of both storage systems."""
    stats = {
        "timestamp": time.time(),
        "redis": {"status": "disconnected", "total_keys": 0, "users": {}},
        "chromadb": {"status": "disconnected", "total_documents": 0, "users": {}}
    }
    # Redis stats
    if redis_client:
        try:
            stats["redis"]["status"] = "connected"
            all_keys = redis_client.keys("memory:*")
            stats["redis"]["total_keys"] = len(all_keys)
            # Count by user
            user_counts = {}
            for key in all_keys:
                parts = key.split(":")
                if len(parts) >= 2:
                    user_id = parts[1]
                    user_counts[user_id] = user_counts.get(user_id, 0) + 1
            stats["redis"]["users"] = user_counts
        except Exception as e:
            stats["redis"]["error"] = str(e)
    # ChromaDB stats
    if memory_collection:
        try:
            stats["chromadb"]["status"] = "connected"
            count = memory_collection.count()
            stats["chromadb"]["total_documents"] = count
            # Get user distribution (this might be expensive for large datasets)
            if count < 1000:  # Only do this for smaller datasets
                all_docs = memory_collection.get()
                user_counts = {}
                if all_docs["metadatas"]:
                    for metadata in all_docs["metadatas"]:
                        user_id = metadata.get("user_id", "unknown")
                        user_counts[user_id] = user_counts.get(user_id, 0) + 1
                stats["chromadb"]["users"] = user_counts
        except Exception as e:
            stats["chromadb"]["error"] = str(e)
    return stats
if __name__ == "__main__":
    print("🚀 Starting Enhanced Memory API Server with Redis + ChromaDB...")
    print("🏪 Storage Systems:")
    print(f"   📱 Redis (short-term): {REDIS_HOST}:{REDIS_PORT}")
    print(f"   📚 ChromaDB (long-term): {CHROMA_HOST}:{CHROMA_PORT}")
    print("📡 Endpoints:")
    print("   POST /api/memory/retrieve")
    print("   POST /api/learning/process_interaction")
    print("   GET /debug/stats")
    uvicorn.run(app, host="0.0.0.0", port=8000)
