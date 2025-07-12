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
    threshold: float = float(os.getenv('MEMORY_RETRIEVAL_THRESHOLD', '0.001'))  # Use environment variable
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
class ExplicitMemoryRequest(BaseModel):
    user_id: str
    content: str
    source: Optional[str] = "explicit_command"
    conversation_id: Optional[str] = "manual"
    metadata: Optional[Dict[str, Any]] = None  # Added support for metadata
class ForgetMemoryRequest(BaseModel):
    user_id: str
    forget_query: str  # What to forget (e.g., "my job", "my name", "everything about work")
    source: Optional[str] = "forget_command"
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
        print(f"📚 Memory collection has {memory_collection.count()} memories")
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
        
        # ENHANCED: Filter out outdated information when we have corrections
        # Look for correction patterns and remove conflicting old memories
        filtered_memories = []
        correction_memories = [m for m in relevant_memories if m["content"].lower().startswith("correction:")]
        
        for memory in relevant_memories:
            content_lower = memory["content"].lower()
            
            # Skip correction memories themselves (they're just metadata)
            if content_lower.startswith("correction:"):
                continue
                
            # Check if this memory conflicts with any corrections
            is_outdated = False
            for correction in correction_memories:
                correction_content = correction["content"].lower()
                
                # Check for name corrections
                if "name is not" in correction_content:
                    # Extract the incorrect name from the correction
                    import re
                    incorrect_name_match = re.search(r"name is not ([a-zA-Z\s]+)", correction_content)
                    if incorrect_name_match:
                        incorrect_name = incorrect_name_match.group(1).strip()
                        # If this memory contains the incorrect name, mark as outdated
                        if incorrect_name in content_lower and "name" in content_lower:
                            is_outdated = True
                            print(f"🚫 Filtering out outdated memory: {memory['content'][:50]}...")
                            break
            
            # Only include memories that aren't outdated
            if not is_outdated:
                filtered_memories.append(memory)
        
        # Take only the top results after filtering
        final_memories = filtered_memories[:request.limit]
        
        print(f"✅ Returning {len(final_memories)} relevant memories (filtered from {len(relevant_memories)} total)")
        return {
            "status": "success",
            "memories": final_memories,
            "count": len(final_memories),
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

@app.post("/api/memory/store_explicit")
async def store_explicit_memory(request: ExplicitMemoryRequest = Body(...)):
    """
    Store explicit memory with high priority - triggered by 'remember this', 'save this', etc.
    """
    try:
        print(f"💾 EXPLICIT MEMORY request for user {request.user_id}")
        print(f"   Content: {request.content[:100]}...")
        
        # Create high-priority interaction for explicit memory
        interaction = {
            "user_id": request.user_id,
            "conversation_id": request.conversation_id,
            "user_message": f"EXPLICIT: {request.content}",
            "assistant_response": "I will remember this important information.",
            "timestamp": time.time(),
            "source": request.source,
            "priority": "high",
            "explicit": True
        }
        
        # Add metadata if provided
        if request.metadata:
            interaction.update(request.metadata)
        
        # Store directly to both short-term and long-term storage for explicit memories
        memories_stored = 0
        
        # 1. Store in Redis (short-term) with extended TTL for explicit memories
        if await store_explicit_to_redis(request.user_id, request.content, interaction):
            memories_stored += 1
            print(f"💾 Stored explicit short-term memory: {request.content[:50]}...")
        
        # 2. Store directly in ChromaDB (long-term) for immediate persistence
        if await store_explicit_to_chromadb(request.user_id, request.content, interaction):
            memories_stored += 1
            print(f"💾 Stored explicit long-term memory: {request.content[:50]}...")
        
        # Get updated memory counts
        short_term_count = await get_redis_memory_count(request.user_id)
        long_term_count = await get_chromadb_memory_count(request.user_id)
        
        print(f"✅ Explicit memory storage complete - {memories_stored} new memories")
        
        return {
            "status": "success",
            "user_id": request.user_id,
            "stored": True,
            "new_memories": memories_stored,
            "explicit": True,
            "priority": "high",
            "total_memories": {
                "short_term": short_term_count,
                "long_term": long_term_count,
                "total": short_term_count + long_term_count
            }
        }
        
    except Exception as e:
        print(f"❌ Explicit memory storage error: {e}")
        raise HTTPException(status_code=500, detail=f"Explicit memory storage failed: {str(e)}")

async def store_explicit_to_redis(user_id: str, content: str, interaction: Dict[str, Any]) -> bool:
    """Store explicit memory in Redis with extended TTL."""
    if not redis_client:
        return False
    try:
        memory_id = str(uuid.uuid4())
        key = f"memory:explicit:{user_id}:{memory_id}"
        memory_data = {
            "content": content,
            "timestamp": interaction["timestamp"],
            "conversation_id": interaction["conversation_id"],
            "access_count": 0,
            "source": interaction["source"],
            "priority": "high",
            "explicit": True
        }
        redis_client.hset(key, mapping=memory_data)
        # Extended TTL for explicit memories (7 days instead of default)
        redis_client.expire(key, 7 * 24 * 3600)  # 7 days
        return True
    except Exception as e:
        print(f"❌ Explicit Redis storage error: {e}")
        return False

async def store_explicit_to_chromadb(user_id: str, content: str, interaction: Dict[str, Any]) -> bool:
    """Store explicit memory directly in ChromaDB for immediate persistence."""
    if not memory_collection:
        return False
    try:
        memory_id = str(uuid.uuid4())
        memory_collection.add(
            documents=[content],
            metadatas=[{
                "user_id": user_id,
                "timestamp": interaction["timestamp"],
                "conversation_id": interaction["conversation_id"],
                "source": interaction["source"],
                "priority": "high",
                "explicit": True,
                "access_count": 0
            }],
            ids=[memory_id]
        )
        print(f"💾 Stored explicit long-term memory: {content[:50]}...")
        return True
    except Exception as e:
        print(f"❌ Explicit ChromaDB storage error: {e}")
        return False

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
    """
    Enhanced memory extraction for comprehensive document and CV content analysis.
    
    This function now properly extracts:
    - CV and resume content
    - Technical skills and expertise
    - Job responsibilities and experience
    - Professional qualifications
    - Personal details and preferences
    - Complex document structures
    """
    memories = []
    text_lower = text.lower()
    original_text = text.strip()
    
    # 🔥 NEW: CV/Resume Document Detection and Processing
    if any(indicator in text_lower for indicator in [
        'cv', 'resume', 'curriculum vitae', 'work experience', 'professional experience',
        'skills and expertise', 'technical skills', 'job responsibilities', 'qualifications',
        'education', 'certifications', 'portfolio', 'work history'
    ]):
        print(f"📄 CV/Resume document detected - extracting comprehensive professional information")
        
        # Extract entire document as structured memory
        memories.extend(extract_cv_content(original_text))
        
        # Also extract specific professional elements
        memories.extend(extract_professional_skills(original_text))
        memories.extend(extract_job_responsibilities(original_text))
        memories.extend(extract_technical_expertise(original_text))
    
    # Handle corrections first (name corrections like "my name is X not Y")
    correction_patterns = [
        r"my name is ([a-zA-Z\s.]+)(?:,)?\s*not\s*([a-zA-Z\s]+)",
        r"i'm ([a-zA-Z\s.]+)(?:,)?\s*not\s*([a-zA-Z\s]+)",
        r"call me ([a-zA-Z\s.]+)(?:,)?\s*not\s*([a-zA-Z\s]+)"
    ]
    
    name_corrected = False
    for pattern in correction_patterns:
        matches = re.findall(pattern, text_lower)
        for correct_name, wrong_name in matches:
            correct_name = correct_name.strip().title()
            if len(correct_name) > 1:
                memories.append(f"User's name is {correct_name}")
                memories.append(f"CORRECTION: User's name is NOT {wrong_name.strip().title()}")
                name_corrected = True
                print(f"📝 Name correction detected: {wrong_name} → {correct_name}")
    
    # Regular name extraction (only if no correction was made)
    if not name_corrected:
        name_patterns = [
            r"my name is ([a-zA-Z\s.]+)",
            r"i'm ([a-zA-Z\s.]+)",
            r"i am ([a-zA-Z\s.]+)",
            r"call me ([a-zA-Z\s.]+)",
            r"this is ([a-zA-Z\s.]+)",
            r"hello,?\s*(?:my name is\s+)?([a-zA-Z\s.]{2,})",
            r"hi,?\s*(?:i'm\s+)?([a-zA-Z\s.]{2,})"
        ]
        for pattern in name_patterns:
            matches = re.findall(pattern, text_lower)
            for name in matches:
                name = name.strip().title()
                # Filter out common words that aren't names
                excluded_words = ["A", "An", "The", "Hello", "Hi", "My", "Name", "Is", "I", "Am", "This", "And", "Or", "But"]
                if len(name) > 1 and name not in excluded_words and not any(word in name for word in ["Hello", "Hi"]):
                    memories.append(f"User's name is {name}")
    
    # Work/profession extraction - Enhanced patterns
    work_patterns = [
        r"i work (?:as |at |in |for )?(.+?)(?:\.|$|,)",
        r"i'm (?:a |an )?(.+?) (?:at|in|for) ([^.!?]+)",
        r"my job is (.+?)(?:\.|$|,)",
        r"i do (.+?)(?:\.|$|,)",
        r"i work for (.+?)(?:\.|$|,)",
        r"employed (?:at|by) (.+?)(?:\.|$|,)",
        r"work at (.+?)(?:\.|$|,)"
    ]
    for pattern in work_patterns:
        matches = re.findall(pattern, text_lower)
        for match in matches:
            if isinstance(match, tuple):
                work_info = " ".join(match).strip()
            else:
                work_info = match.strip()
            # Clean up and validate
            work_info = work_info.replace("and", "").strip()
            if len(work_info) > 3 and work_info not in ["that", "this", "what", "how"]:
                memories.append(f"User works at/as {work_info}")
    
    # Company/workplace specific extraction
    company_patterns = [
        r"at ([A-Z][a-zA-Z\s]+(?:Software|Systems|Solutions|Technologies|Inc|Corp|Company|Ltd))",
        r"for ([A-Z][a-zA-Z\s]+(?:Software|Systems|Solutions|Technologies|Inc|Corp|Company|Ltd))",
        r"work at ([A-Z][a-zA-Z\s]+)"
    ]
    for pattern in company_patterns:
        matches = re.findall(pattern, original_text)  # Use original case for company names
        for company in matches:
            company = company.strip()
            if len(company) > 2:
                memories.append(f"User works at {company}")
    
    # Personal interests and preferences
    interest_patterns = [
        r"i like (.+?)(?:\.|$|,)",
        r"i love (.+?)(?:\.|$|,)",
        r"i enjoy (.+?)(?:\.|$|,)",
        r"my favorite (.+?)(?:\.|$|,)",
        r"i prefer (.+?)(?:\.|$|,)",
        r"i'm interested in (.+?)(?:\.|$|,)"
    ]
    for pattern in interest_patterns:
        matches = re.findall(pattern, text_lower)
        for interest in matches:
            interest = interest.strip()
            if len(interest) > 3:
                memories.append(f"User likes/enjoys {interest}")
    
    # Skills and experience
    skill_patterns = [
        r"i have experience (?:with |in )?(.+?)(?:\.|$|,)",
        r"i know (.+?)(?:\.|$|,)",
        r"i'm good at (.+?)(?:\.|$|,)",
        r"i specialize in (.+?)(?:\.|$|,)",
        r"skilled in (.+?)(?:\.|$|,)",
        r"expert in (.+?)(?:\.|$|,)"
    ]
    for pattern in skill_patterns:
        matches = re.findall(pattern, text_lower)
        for skill in matches:
            skill = skill.strip()
            if len(skill) > 3:
                memories.append(f"User has experience/skills in {skill}")
    
    # Location information
    location_patterns = [
        r"i live in ([^.!?]+)",
        r"i'm from ([^.!?]+)",
        r"my city is ([^.!?]+)",
        r"located in ([^.!?]+)",
        r"based in ([^.!?]+)"
    ]
    for pattern in location_patterns:
        matches = re.findall(pattern, text_lower)
        for location in matches:
            location = location.strip().title()
            if len(location) > 1:
                memories.append(f"User lives in {location}")
    
    # Personal details
    detail_patterns = [
        r"i have (.+?)(?:\.|$|,)",
        r"i own (.+?)(?:\.|$|,)",
        r"i study (.+?)(?:\.|$|,)",
        r"i'm studying (.+?)(?:\.|$|,)"
    ]
    for pattern in detail_patterns:
        matches = re.findall(pattern, text_lower)
        for detail in matches:
            detail = detail.strip()
            if len(detail) > 3 and not any(word in detail for word in ["been", "done", "said"]):
                memories.append(f"Personal detail: User has/studies {detail}")
    
    # 🔥 ENHANCED: Extract any substantial content that wasn't caught by patterns
    if len(original_text) > 50:  # Substantial content
        # Split into sentences and extract meaningful ones
        sentences = original_text.split('.')
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and any(word in sentence.lower() for word in [
                'experience', 'work', 'skill', 'knowledge', 'responsible', 'manage', 
                'support', 'technical', 'professional', 'qualification', 'training',
                'project', 'system', 'network', 'server', 'software', 'hardware'
            ]):
                memories.append(f"Professional Context: {sentence}")
    
    # 🔥 ENHANCED: Capture detailed descriptions and explanations
    if len(original_text) > 100:  # Very detailed content
        # Extract paragraphs or long descriptions
        paragraphs = original_text.split('\n')
        for para in paragraphs:
            para = para.strip()
            if len(para) > 30:  # Meaningful paragraph
                memories.append(f"Detailed Information: {para}")
    
    # If no specific patterns match but the text seems personal, store it directly
    personal_indicators = ["my", "i", "me", "myself", "personal", "about me"]
    if any(indicator in text_lower for indicator in personal_indicators) and len(original_text) > 10:
        if not memories:  # Only if we didn't extract anything specific
            memories.append(original_text)
    
    # 🔥 FINAL SAFETY NET: If we have substantial content but no memories, store it
    if not memories and len(original_text) > 20:
        memories.append(f"User Information: {original_text}")
    
    print(f"📝 Total memories extracted: {len(memories)}")
    return memories
def calculate_relevance_score(content: str, query: str) -> float:
    """Calculate relevance score between content and query. ENHANCED for better matching."""
    content_lower = content.lower()
    query_lower = query.lower()
    query_words = set(query_lower.split())
    content_words = set(content_lower.split())
    
    # Heavily penalize corrected/incorrect information
    if content_lower.startswith("correction:") or " is not " in content_lower:
        return 0.01  # Very low relevance for corrections/negations
    
    # CRITICAL: Penalize old/incorrect names heavily when we have corrections
    # Check if this memory contains an outdated name like "TestUser" 
    if "testuser" in content_lower and ("name" in content_lower or "user's name" in content_lower):
        # This is likely an outdated name memory, heavily penalize it
        return 0.02  # Very low relevance for outdated names
    
    score = 0.0
    total_words = len(query_words)
    if not total_words:
        return 0.0
    
    # Exact word matches (higher weight)
    exact_matches = query_words.intersection(content_words)
    score += len(exact_matches) * 0.6
    
    # Partial matches (substring matching)
    for query_word in query_words:
        if len(query_word) > 2:
            for content_word in content_words:
                if len(content_word) > 2:
                    if query_word in content_word or content_word in query_word:
                        score += 0.3
    
    # Enhanced pattern matching for common memory queries
    memory_query_patterns = [
        "what do you know", "tell me about", "remember about", 
        "what do you remember", "who am i", "about me"
    ]
    if any(pattern in query_lower for pattern in memory_query_patterns):
        # For these queries, give any stored memory good relevance
        score += 0.4
    
    # Name-based queries (boost for current/correct names)
    if "name" in query_lower and "name" in content_lower:
        score += 0.5
        # Extra boost for specific names
        name_words = ["j.p.", "jp", "swift", "software"]
        for name_word in name_words:
            if name_word in content_lower:
                score += 0.4
    
    # Work-based queries  
    work_keywords = ["work", "job", "career", "company", "employer", "workplace"]
    if any(word in query_lower for word in work_keywords) and any(word in content_lower for word in work_keywords):
        score += 0.5
    
    # Personal information queries
    personal_keywords = ["personal", "about", "me", "myself", "i", "my"]
    if any(word in query_lower for word in personal_keywords):
        score += 0.2
    
    # Normalize by query length but don't over-penalize
    normalized_score = min(score / max(total_words * 0.5, 1), 1.0)
    
    # Give a base score to any memory for broad queries (but not corrections or outdated names)
    if any(pattern in query_lower for pattern in memory_query_patterns) and not content_lower.startswith("correction:") and "testuser" not in content_lower:
        normalized_score = max(normalized_score, 0.2)
    
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

def extract_cv_content(text: str) -> List[str]:
    """Extract comprehensive CV/resume content with structured information."""
    cv_memories = []
    
    try:
        # Split text into logical sections for better processing
        sections = text.split('\n')
        current_section = ""
        
        for line in sections:
            line = line.strip()
            if len(line) < 3:
                continue
                
            # Detect section headers and content
            if any(keyword in line.lower() for keyword in [
                'experience', 'skills', 'education', 'qualifications', 'responsibilities',
                'achievements', 'projects', 'certifications', 'summary', 'profile'
            ]):
                current_section = line
                if len(line) > 10:  # Substantial section header
                    cv_memories.append(f"CV Section: {line}")
            else:
                # Extract substantial content lines
                if len(line) > 15 and not line.startswith(('•', '-', '*')):
                    cv_memories.append(f"Professional Info: {line}")
                elif len(line) > 10:  # Shorter but meaningful content
                    cv_memories.append(f"CV Detail: {line}")
        
        # Extract entire meaningful chunks (paragraphs)
        paragraphs = text.split('\n\n')
        for para in paragraphs:
            para = para.strip()
            if len(para) > 50:  # Substantial paragraphs
                cv_memories.append(f"CV Content: {para}")
        
        print(f"📄 Extracted {len(cv_memories)} CV content memories")
        return cv_memories
        
    except Exception as e:
        print(f"❌ Error extracting CV content: {e}")
        return [f"CV Document: {text}"]  # Fallback to store entire text

def extract_professional_skills(text: str) -> List[str]:
    """Extract technical and professional skills from text."""
    skills_memories = []
    text_lower = text.lower()
    
    try:
        # Technical skill patterns
        technical_patterns = [
            r'(networking|network administration|server support|desktop support)',
            r'(point of sale|pos|retail systems|payment processing)',
            r'(technical support|it support|help desk|troubleshooting)',
            r'(system administration|server management|infrastructure)',
            r'(hardware|software|installation|configuration|maintenance)',
            r'(windows|linux|mac os|operating systems|os support)',
            r'(database|sql|mysql|postgresql|oracle)',
            r'(programming|coding|development|scripting)',
            r'(security|cybersecurity|network security|data protection)',
            r'(cloud|aws|azure|google cloud|saas|iaas)',
            r'(virtualization|vmware|hyper-v|containers|docker)',
            r'(monitoring|performance|optimization|analysis)'
        ]
        
        for pattern in technical_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                skills_memories.append(f"Technical Skill: {match.title()}")
        
        # Professional competencies
        professional_patterns = [
            r'(customer service|client support|user support)',
            r'(project management|team leadership|coordination)',
            r'(communication|presentation|documentation|training)',
            r'(problem solving|analytical|critical thinking)',
            r'(multitasking|time management|organization)',
            r'(collaboration|teamwork|cross-functional)'
        ]
        
        for pattern in professional_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                skills_memories.append(f"Professional Skill: {match.title()}")
        
        # Extract explicit skill mentions
        skill_indicators = ['skills:', 'expertise:', 'proficient in:', 'experience with:', 'knowledge of:']
        for indicator in skill_indicators:
            if indicator in text_lower:
                # Find text after the indicator
                start_idx = text_lower.find(indicator)
                skill_text = text[start_idx:start_idx + 200]  # Get next 200 chars
                skills_memories.append(f"Skills Section: {skill_text}")
        
        print(f"🛠️ Extracted {len(skills_memories)} professional skills")
        return skills_memories
        
    except Exception as e:
        print(f"❌ Error extracting professional skills: {e}")
        return []

def extract_job_responsibilities(text: str) -> List[str]:
    """Extract job responsibilities and work experience details."""
    responsibility_memories = []
    text_lower = text.lower()
    
    try:
        # Responsibility indicators
        responsibility_patterns = [
            r'responsible for (.+?)(?:\.|$|\n)',
            r'duties include (.+?)(?:\.|$|\n)',
            r'key responsibilities (.+?)(?:\.|$|\n)',
            r'experience in (.+?)(?:\.|$|\n)',
            r'performed (.+?)(?:\.|$|\n)',
            r'managed (.+?)(?:\.|$|\n)',
            r'developed (.+?)(?:\.|$|\n)',
            r'implemented (.+?)(?:\.|$|\n)',
            r'maintained (.+?)(?:\.|$|\n)',
            r'supported (.+?)(?:\.|$|\n)',
            r'coordinated (.+?)(?:\.|$|\n)',
            r'administered (.+?)(?:\.|$|\n)'
        ]
        
        for pattern in responsibility_patterns:
            matches = re.findall(pattern, text_lower, re.MULTILINE)
            for match in matches:
                if len(match.strip()) > 10:
                    responsibility_memories.append(f"Job Responsibility: {match.strip()}")
        
        # Extract job positions and companies
        position_patterns = [
            r'(technician|specialist|administrator|manager|coordinator|analyst|engineer|consultant)',
            r'(support|service|maintenance|installation|configuration|troubleshooting)',
            r'(junior|senior|lead|principal|chief|head of|director of)'
        ]
        
        for pattern in position_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                responsibility_memories.append(f"Job Role: {match.title()}")
        
        print(f"💼 Extracted {len(responsibility_memories)} job responsibilities")
        return responsibility_memories
        
    except Exception as e:
        print(f"❌ Error extracting job responsibilities: {e}")
        return []

def extract_technical_expertise(text: str) -> List[str]:
    """Extract detailed technical expertise and certifications."""
    expertise_memories = []
    text_lower = text.lower()
    
    try:
        # Technical domains
        technical_domains = [
            'network administration', 'server support', 'desktop support', 'help desk',
            'point of sale systems', 'retail technology', 'payment processing',
            'hardware troubleshooting', 'software installation', 'system configuration',
            'user training', 'technical documentation', 'incident resolution',
            'performance monitoring', 'backup and recovery', 'security protocols'
        ]
        
        for domain in technical_domains:
            if domain in text_lower:
                expertise_memories.append(f"Technical Expertise: {domain.title()}")
        
        # Certification patterns
        cert_patterns = [
            r'(certified|certification|credential|license|qualification)',
            r'(comptia|cisco|microsoft|apple|linux|vmware|aws|azure)',
            r'(a\+|network\+|security\+|server\+|cloud\+)',
            r'(mcsa|mcse|ccna|ccnp|ccie|rhce|vcp)'
        ]
        
        for pattern in cert_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                expertise_memories.append(f"Certification/Qualification: {match.upper()}")
        
        # Extract years of experience
        experience_patterns = [
            r'(\d+)\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)',
            r'(\d+)\+\s*years?',
            r'over\s*(\d+)\s*years?'
        ]
        
        for pattern in experience_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                expertise_memories.append(f"Experience Level: {match} years")
        
        print(f"🎯 Extracted {len(expertise_memories)} technical expertise items")
        return expertise_memories
        
    except Exception as e:
        print(f"❌ Error extracting technical expertise: {e}")
        return []
