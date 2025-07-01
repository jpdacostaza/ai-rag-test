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
class MemorySaveRequest(BaseModel):
    user_id: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    category: Optional[str] = "explicit"
class MemoryDeleteRequest(BaseModel):
    user_id: str
    query: str  # What to search for to delete
    exact_match: bool = False  # If True, delete exact matches only
class MemoryForgetRequest(BaseModel):
    user_id: str
    content: str  # Specific content to forget
class MemoryClearRequest(BaseModel):
    user_id: str
    confirm: bool = False  # Safety flag
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

@app.post("/api/memory/save")
async def save_memory(request: MemorySaveRequest = Body(...)):
    """
    Explicitly save a memory for a user (when they say "remember this").
    """
    try:
        print(f"💾 Explicit memory save for user {request.user_id}: {request.content[:50]}...")
        
        # Create interaction-like object for storage
        interaction = {
            "user_id": request.user_id,
            "conversation_id": f"explicit_{int(time.time())}",
            "user_message": request.content,
            "assistant_response": "Memory saved",
            "timestamp": time.time(),
            "metadata": request.metadata or {},
            "category": request.category
        }
        
        # Store directly (both short and long term)
        stored = False
        if await store_to_redis(request.user_id, request.content, interaction):
            print(f"✅ Stored in Redis: {request.content[:50]}...")
            stored = True
            
        if await store_to_chromadb(request.user_id, request.content, interaction):
            print(f"✅ Stored in ChromaDB: {request.content[:50]}...")
            stored = True
        
        if stored:
            return {
                "status": "success",
                "message": "Memory saved successfully",
                "content": request.content,
                "user_id": request.user_id
            }
        else:
            return {
                "status": "error",
                "message": "Failed to save memory",
                "user_id": request.user_id
            }
            
    except Exception as e:
        print(f"❌ Memory save error: {e}")
        raise HTTPException(status_code=500, detail=f"Memory save failed: {str(e)}")

@app.post("/api/memory/delete")
async def delete_memory(request: MemoryDeleteRequest = Body(...)):
    """
    Delete specific memories based on query.
    """
    try:
        print(f"🗑️ Memory deletion for user {request.user_id}, query: {request.query}")
        
        deleted_count = 0
        
        # Delete from Redis
        redis_deleted = await delete_from_redis(request.user_id, request.query, request.exact_match)
        deleted_count += redis_deleted
        
        # Delete from ChromaDB
        chromadb_deleted = await delete_from_chromadb(request.user_id, request.query, request.exact_match)
        deleted_count += chromadb_deleted
        
        print(f"✅ Deleted {deleted_count} memories (Redis: {redis_deleted}, ChromaDB: {chromadb_deleted})")
        
        return {
            "status": "success",
            "message": f"Deleted {deleted_count} memories",
            "deleted_count": deleted_count,
            "user_id": request.user_id,
            "query": request.query
        }
        
    except Exception as e:
        print(f"❌ Memory deletion error: {e}")
        raise HTTPException(status_code=500, detail=f"Memory deletion failed: {str(e)}")

@app.post("/api/memory/forget")
async def forget_memory(request: MemoryForgetRequest = Body(...)):
    """
    Forget a specific memory by exact content match.
    """
    try:
        print(f"🧠 Forgetting memory for user {request.user_id}: {request.content[:50]}...")
        
        # This is just a wrapper around delete with exact_match=True
        delete_request = MemoryDeleteRequest(
            user_id=request.user_id,
            query=request.content,
            exact_match=True
        )
        
        result = await delete_memory(delete_request)
        result["message"] = f"Forgot memory: {request.content[:50]}..."
        
        return result
        
    except Exception as e:
        print(f"❌ Memory forget error: {e}")
        raise HTTPException(status_code=500, detail=f"Memory forget failed: {str(e)}")

@app.get("/api/memory/list/{user_id}")
async def list_memories(user_id: str, limit: int = 20):
    """
    List all memories for a user.
    """
    try:
        print(f"📋 Listing memories for user {user_id}")
        
        # Get all memories using broad retrieval
        request = MemoryRetrieveRequest(
            user_id=user_id,
            query="",
            limit=limit,
            threshold=0.0
        )
        
        result = await retrieve_memory(request)
        
        return {
            "status": "success",
            "memories": result["memories"],
            "count": result["count"],
            "user_id": user_id,
            "sources": result["sources"]
        }
        
    except Exception as e:
        print(f"❌ Memory list error: {e}")
        raise HTTPException(status_code=500, detail=f"Memory list failed: {str(e)}")

@app.post("/api/memory/clear")
async def clear_memories(request: MemoryClearRequest = Body(...)):
    """
    Clear all memories for a user (requires confirmation).
    """
    try:
        if not request.confirm:
            return {
                "status": "error",
                "message": "Confirmation required. Set 'confirm': true to proceed.",
                "user_id": request.user_id
            }
            
        print(f"🗑️ Clearing ALL memories for user {request.user_id}")
        
        deleted_count = 0
        
        # Clear from Redis
        redis_deleted = await clear_user_redis_memories(request.user_id)
        deleted_count += redis_deleted
        
        # Clear from ChromaDB
        chromadb_deleted = await clear_user_chromadb_memories(request.user_id)
        deleted_count += chromadb_deleted
        
        print(f"✅ Cleared {deleted_count} memories (Redis: {redis_deleted}, ChromaDB: {chromadb_deleted})")
        
        return {
            "status": "success",
            "message": f"Cleared all {deleted_count} memories",
            "deleted_count": deleted_count,
            "user_id": request.user_id
        }
        
    except Exception as e:
        print(f"❌ Memory clear error: {e}")
        raise HTTPException(status_code=500, detail=f"Memory clear failed: {str(e)}")

# Helper Functions for Memory Operations
# =====================================

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
            try:
                memory_data = redis_client.get(key)
                if memory_data:
                    memory = json.loads(memory_data)
                    memories.append({
                        "content": memory.get("content", ""),
                        "metadata": memory.get("metadata", {}),
                        "timestamp": memory.get("timestamp", 0),
                        "source": "redis"
                    })
            except Exception as e:
                print(f"❌ Error retrieving Redis memory {key}: {e}")
        return memories
    except Exception as e:
        print(f"❌ Redis retrieval error: {e}")
        return []

async def retrieve_from_chromadb(user_id: str, query: str, limit: int) -> List[Dict[str, Any]]:
    """Retrieve memories from ChromaDB long-term storage."""
    if not memory_collection:
        return []
    try:
        # Query ChromaDB with embedding search
        results = memory_collection.query(
            query_texts=[query] if query else [""],
            n_results=min(limit, 100),
            where={"user_id": user_id} if user_id else None
        )
        
        memories = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] and results["metadatas"][0] else {}
                memories.append({
                    "content": doc,
                    "metadata": metadata,
                    "timestamp": metadata.get("timestamp", 0),
                    "source": "chromadb"
                })
        return memories
    except Exception as e:
        print(f"❌ ChromaDB retrieval error: {e}")
        return []

async def store_to_redis(user_id: str, content: str, interaction: Dict[str, Any]) -> bool:
    """Store memory in Redis short-term storage."""
    if not redis_client:
        return False
    try:
        memory_id = str(uuid.uuid4())
        key = f"memory:{user_id}:{memory_id}"
        
        memory_data = {
            "content": content,
            "metadata": interaction.get("metadata", {}),
            "timestamp": interaction.get("timestamp", time.time()),
            "conversation_id": interaction.get("conversation_id", ""),
            "source": "redis"
        }
        
        # Store with TTL (24 hours)
        redis_client.setex(key, SHORT_TERM_TTL, json.dumps(memory_data))
        return True
    except Exception as e:
        print(f"❌ Redis storage error: {e}")
        return False

async def store_to_chromadb(user_id: str, content: str, interaction: Dict[str, Any]) -> bool:
    """Store memory in ChromaDB long-term storage."""
    if not memory_collection:
        return False
    try:
        memory_id = str(uuid.uuid4())
        
        metadata = {
            "user_id": user_id,
            "timestamp": interaction.get("timestamp", time.time()),
            "conversation_id": interaction.get("conversation_id", ""),
            "category": interaction.get("category", "general"),
            "source": "chromadb"
        }
        metadata.update(interaction.get("metadata", {}))
        
        memory_collection.add(
            documents=[content],
            metadatas=[metadata],
            ids=[memory_id]
        )
        return True
    except Exception as e:
        print(f"❌ ChromaDB storage error: {e}")
        return False

async def delete_from_redis(user_id: str, query: str, exact_match: bool = False) -> int:
    """Delete memories from Redis based on query."""
    if not redis_client:
        return 0
    try:
        pattern = f"memory:{user_id}:*"
        keys = redis_client.keys(pattern)
        deleted_count = 0
        
        for key in keys:
            try:
                memory_data = redis_client.get(key)
                if memory_data:
                    memory = json.loads(memory_data)
                    content = memory.get("content", "").lower()
                    query_lower = query.lower()
                    
                    should_delete = False
                    if exact_match:
                        should_delete = content == query_lower
                    else:
                        should_delete = query_lower in content
                    
                    if should_delete:
                        redis_client.delete(key)
                        deleted_count += 1
                        print(f"🗑️ Deleted Redis memory: {memory.get('content', '')[:50]}...")
            except Exception as e:
                print(f"❌ Error deleting Redis memory {key}: {e}")
        
        return deleted_count
    except Exception as e:
        print(f"❌ Redis deletion error: {e}")
        return 0

async def delete_from_chromadb(user_id: str, query: str, exact_match: bool = False) -> int:
    """Delete memories from ChromaDB based on query."""
    if not memory_collection:
        return 0
    try:
        # First, find matching memories
        results = memory_collection.query(
            query_texts=[query],
            n_results=100,
            where={"user_id": user_id}
        )
        
        ids_to_delete = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                doc_lower = doc.lower()
                query_lower = query.lower()
                
                should_delete = False
                if exact_match:
                    should_delete = doc_lower == query_lower
                else:
                    should_delete = query_lower in doc_lower
                
                if should_delete and results["ids"] and results["ids"][0]:
                    ids_to_delete.append(results["ids"][0][i])
                    print(f"🗑️ Will delete ChromaDB memory: {doc[:50]}...")
        
        # Delete the memories
        if ids_to_delete:
            memory_collection.delete(ids=ids_to_delete)
        
        return len(ids_to_delete)
    except Exception as e:
        print(f"❌ ChromaDB deletion error: {e}")
        return 0

async def clear_user_redis_memories(user_id: str) -> int:
    """Clear all Redis memories for a user."""
    if not redis_client:
        return 0
    try:
        pattern = f"memory:{user_id}:*"
        keys = redis_client.keys(pattern)
        if keys:
            deleted_count = redis_client.delete(*keys)
            print(f"🗑️ Cleared {deleted_count} Redis memories for user {user_id}")
            return deleted_count
        return 0
    except Exception as e:
        print(f"❌ Redis clear error: {e}")
        return 0

async def clear_user_chromadb_memories(user_id: str) -> int:
    """Clear all ChromaDB memories for a user."""
    if not memory_collection:
        return 0
    try:
        # Get all documents for this user
        results = memory_collection.get(where={"user_id": user_id})
        
        if results["ids"]:
            memory_collection.delete(ids=results["ids"])
            deleted_count = len(results["ids"])
            print(f"🗑️ Cleared {deleted_count} ChromaDB memories for user {user_id}")
            return deleted_count
        return 0
    except Exception as e:
        print(f"❌ ChromaDB clear error: {e}")
        return 0

async def get_redis_memory_count(user_id: str) -> int:
    """Get count of Redis memories for a user."""
    if not redis_client:
        return 0
    try:
        pattern = f"memory:{user_id}:*"
        keys = redis_client.keys(pattern)
        return len(keys)
    except Exception as e:
        print(f"❌ Redis count error: {e}")
        return 0

async def get_chromadb_memory_count(user_id: str) -> int:
    """Get count of ChromaDB memories for a user."""
    if not memory_collection:
        return 0
    try:
        results = memory_collection.get(where={"user_id": user_id})
        return len(results["ids"]) if results["ids"] else 0
    except Exception as e:
        print(f"❌ ChromaDB count error: {e}")
        return 0

def extract_memories(text: str) -> List[str]:
    """Extract memorable information from user text."""
    memories = []
    text_lower = text.lower()
    
    # Check for explicit memory requests first
    if any(keyword in text_lower for keyword in ["remember that", "remember this", "don't forget", "save this", "store this"]):
        # User explicitly wants to remember something
        # Extract the content after the memory keyword
        for keyword in ["remember that", "remember this", "don't forget", "save this", "store this"]:
            if keyword in text_lower:
                # Get the text after the keyword
                parts = text_lower.split(keyword, 1)
                if len(parts) > 1 and parts[1].strip():
                    # Use the original text (with proper case) for the memory
                    original_parts = text.split(keyword, 1)
                    if len(original_parts) > 1:
                        memory_content = original_parts[1].strip()
                        if memory_content:
                            memories.append(memory_content)
                            return memories  # Return early to avoid other pattern matching
        
        # If we found an explicit memory request, also store the full text as fallback
        if len(text.strip()) > 20:
            memories.append(text.strip())
            return memories
    
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
    
    # Schedule and time-related information
    if any(keyword in text_lower for keyword in ["meeting", "appointment", "schedule", "every", "deadline", "due"]):
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
    
    # Personal projects and commitments
    if any(keyword in text_lower for keyword in ["project", "working on", "building", "creating"]):
        memories.append(text.strip())
    
    # Important dates and events
    if any(keyword in text_lower for keyword in ["birthday", "anniversary", "vacation", "trip", "event"]):
        memories.append(text.strip())
    
    # General memorable statements (if not already captured)
    memorable_indicators = [
        "i have", "i will", "i need", "i want", "i'm going to", "i plan to",
        "my", "important", "note that"
    ]
    if any(indicator in text_lower for indicator in memorable_indicators) and len(memories) == 0:
        # Only add as general memory if no specific patterns matched
        if len(text.strip()) > 10:  # Avoid very short statements
            memories.append(text.strip())
    
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
    
    # Normalize score
    return min(score / total_words, 1.0) if total_words > 0 else 0.0

# End of Helper Functions
# =======================

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
    print("   POST /api/memory/save")
    print("   POST /api/memory/delete")
    print("   POST /api/memory/forget")
    print("   POST /api/memory/clear")
    print("   GET  /api/memory/list/{user_id}")
    print("   POST /api/learning/process_interaction")
    print("   GET  /health")
    print("   GET  /debug/stats")
    uvicorn.run(app, host="0.0.0.0", port=8000)
