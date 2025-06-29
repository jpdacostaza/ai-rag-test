#!/usr/bin/env python3
"""
Persistent Memory API Server
A FastAPI server providing memory and learning endpoints with file-based persistence.
"""

import asyncio
import json
import os
import time
from typing import Dict, Any, List, Optional
import re

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# File-based storage for persistence
DATA_DIR = "/app/data"
MEMORY_FILE = os.path.join(DATA_DIR, "memories.json")
INTERACTIONS_FILE = os.path.join(DATA_DIR, "interactions.json")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Load existing data
def load_data():
    """Load existing memory and interaction data from files."""
    memory_store = {}
    learning_interactions = []
    
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, 'r') as f:
                memory_store = json.load(f)
            print(f"📚 Loaded {sum(len(memories) for memories in memory_store.values())} memories for {len(memory_store)} users")
    except Exception as e:
        print(f"⚠️ Error loading memories: {e}")
        memory_store = {}
    
    try:
        if os.path.exists(INTERACTIONS_FILE):
            with open(INTERACTIONS_FILE, 'r') as f:
                learning_interactions = json.load(f)
            print(f"📊 Loaded {len(learning_interactions)} interactions")
    except Exception as e:
        print(f"⚠️ Error loading interactions: {e}")
        learning_interactions = []
    
    return memory_store, learning_interactions

def save_data(memory_store, learning_interactions):
    """Save memory and interaction data to files."""
    try:
        with open(MEMORY_FILE, 'w') as f:
            json.dump(memory_store, f, indent=2)
        
        with open(INTERACTIONS_FILE, 'w') as f:
            json.dump(learning_interactions, f, indent=2)
        
        print(f"💾 Saved {sum(len(memories) for memories in memory_store.values())} memories and {len(learning_interactions)} interactions")
    except Exception as e:
        print(f"❌ Error saving data: {e}")

# Initialize data
memory_store, learning_interactions = load_data()

app = FastAPI(title="Persistent Memory API", version="1.0.0")

# Enable CORS for pipeline access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MemoryRetrieveRequest(BaseModel):
    user_id: str
    query: str
    limit: int = 5
    threshold: float = 0.3  # Lower threshold for better matching


class LearningInteractionRequest(BaseModel):
    user_id: str
    conversation_id: str
    user_message: str
    assistant_response: Optional[str] = None
    response_time: Optional[float] = 1.0
    tools_used: Optional[List[str]] = None
    context: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    source: Optional[str] = "pipeline"


def extract_personal_info(message: str) -> List[str]:
    """Extract personal information from a message."""
    personal_info = []
    message_lower = message.lower()
    
    # Name patterns
    name_patterns = [
        r"my name is (\w+)",
        r"i'm (\w+)",
        r"i am (\w+)",
        r"call me (\w+)"
    ]
    
    for pattern in name_patterns:
        matches = re.findall(pattern, message_lower)
        for match in matches:
            personal_info.append(f"Name: {match.title()}")
    
    # Work patterns
    work_patterns = [
        r"i work at (\w+)",
        r"i work for (\w+)",
        r"i'm at (\w+)",
        r"i am at (\w+)"
    ]
    
    for pattern in work_patterns:
        matches = re.findall(pattern, message_lower)
        for match in matches:
            personal_info.append(f"Works at: {match.upper()}")
    
    # If no specific patterns, but contains personal keywords, store the whole message
    personal_keywords = ["my name", "i work", "i am", "i'm", "i like", "i love", "my favorite", "i do", "i have"]
    if any(keyword in message_lower for keyword in personal_keywords):
        personal_info.append(message)
    
    return personal_info


def calculate_relevance(memory_content: str, query: str) -> float:
    """Calculate relevance score between memory content and query."""
    memory_lower = memory_content.lower()
    query_lower = query.lower()
    
    # Exact phrase matching
    if query_lower in memory_lower:
        return 1.0
    
    # Word matching
    query_words = set(query_lower.split())
    memory_words = set(memory_lower.split())
    
    if not query_words:
        return 0.0
    
    # Calculate overlap
    overlap = len(query_words.intersection(memory_words))
    relevance = overlap / len(query_words)
    
    # Boost for personal info queries
    personal_queries = ["know about me", "about me", "my", "i am", "i work", "my name"]
    if any(pq in query_lower for pq in personal_queries):
        relevance += 0.3
    
    return min(relevance, 1.0)


@app.get("/")
async def root():
    return {
        "message": "Persistent Memory API Server", 
        "endpoints": ["/api/memory/retrieve", "/api/learning/process_interaction"],
        "stats": {
            "users_with_memories": len(memory_store),
            "total_memories": sum(len(memories) for memories in memory_store.values()),
            "total_interactions": len(learning_interactions)
        }
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": time.time()}


@app.post("/api/memory/retrieve")
async def retrieve_memory(request: MemoryRetrieveRequest = Body(...)):
    """
    Retrieve memories for a user query.
    """
    try:
        print(f"🔍 Memory retrieval for user {request.user_id}, query: '{request.query}'")
        
        # Get memories for this user
        user_memories = memory_store.get(request.user_id, [])
        print(f"📚 User has {len(user_memories)} total memories")
        
        if not user_memories:
            print("❌ No memories found for user")
            return {
                "status": "success",
                "memories": [],
                "count": 0,
                "user_id": request.user_id
            }
        
        # Calculate relevance for each memory
        relevant_memories = []
        
        for memory in user_memories:
            content = memory.get("content", "")
            relevance_score = calculate_relevance(content, request.query)
            
            print(f"   Memory: '{content[:50]}...' -> Score: {relevance_score:.2f}")
            
            if relevance_score >= request.threshold:
                relevant_memories.append({
                    "content": content,
                    "metadata": memory.get("metadata", {}),
                    "similarity_score": relevance_score  # Use similarity_score for compatibility
                })
        
        # Sort by relevance and limit results
        relevant_memories.sort(key=lambda x: x["similarity_score"], reverse=True)
        relevant_memories = relevant_memories[:request.limit]
        
        print(f"✅ Found {len(relevant_memories)} relevant memories")
        
        return {
            "status": "success",
            "memories": relevant_memories,
            "count": len(relevant_memories),
            "user_id": request.user_id
        }
        
    except Exception as e:
        print(f"❌ Memory retrieval error: {e}")
        raise HTTPException(status_code=500, detail=f"Memory retrieval failed: {str(e)}")


@app.post("/api/learning/process_interaction")
async def process_interaction(request: LearningInteractionRequest = Body(...)):
    """
    Process a learning interaction.
    """
    global memory_store, learning_interactions
    
    try:
        print(f"🧠 Learning interaction for user {request.user_id}")
        print(f"   Message: '{request.user_message}'")
        
        # Store the interaction
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
        
        learning_interactions.append(interaction)
        
        # Extract and store user information as memories
        if request.user_id not in memory_store:
            memory_store[request.user_id] = []
        
        # Extract personal information
        personal_info = extract_personal_info(request.user_message)
        
        memories_added = 0
        for info in personal_info:
            # Check if this memory already exists
            exists = False
            for existing_memory in memory_store[request.user_id]:
                if existing_memory.get("content", "").lower() == info.lower():
                    exists = True
                    break
            
            if not exists:
                memory_store[request.user_id].append({
                    "content": info,
                    "metadata": {
                        "conversation_id": request.conversation_id,
                        "timestamp": time.time(),
                        "source": "learning_interaction"
                    }
                })
                memories_added += 1
                print(f"💾 Stored new memory: '{info}'")
        
        # Save data to files
        save_data(memory_store, learning_interactions)
        
        print(f"✅ Learning interaction processed, {memories_added} new memories added")
        
        return {
            "status": "success",
            "user_id": request.user_id,
            "processed": True,
            "memories_count": len(memory_store.get(request.user_id, [])),
            "interactions_count": len(learning_interactions),
            "new_memories_added": memories_added
        }
        
    except Exception as e:
        print(f"❌ Learning processing error: {e}")
        return {
            "status": "partial_success",
            "error": str(e),
            "user_id": request.user_id,
            "processed": False
        }


@app.get("/debug/stats")
async def debug_stats():
    """Debug endpoint to show current state"""
    total_memories = sum(len(memories) for memories in memory_store.values())
    return {
        "users_with_memories": len(memory_store),
        "total_memories": total_memories,
        "total_interactions": len(learning_interactions),
        "memory_store": {user: len(memories) for user, memories in memory_store.items()},
        "data_files": {
            "memory_file_exists": os.path.exists(MEMORY_FILE),
            "interactions_file_exists": os.path.exists(INTERACTIONS_FILE),
            "data_dir": DATA_DIR
        }
    }


@app.get("/debug/user/{user_id}")
async def debug_user_memories(user_id: str):
    """Debug endpoint to show memories for a specific user"""
    user_memories = memory_store.get(user_id, [])
    return {
        "user_id": user_id,
        "memory_count": len(user_memories),
        "memories": user_memories
    }


if __name__ == "__main__":
    print("🚀 Starting Persistent Memory API Server...")
    print("📡 Endpoints:")
    print("   POST /api/memory/retrieve")
    print("   POST /api/learning/process_interaction") 
    print("   GET /debug/stats")
    print("   GET /debug/user/{user_id}")
    print(f"💾 Data directory: {DATA_DIR}")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
