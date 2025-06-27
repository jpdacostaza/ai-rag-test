#!/usr/bin/env python3
"""
Simple Memory API Server
A minimal FastAPI server providing memory and learning endpoints for pipeline testing.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Simple in-memory storage for testing
memory_store: Dict[str, List[Dict[str, Any]]] = {}
learning_interactions: List[Dict[str, Any]] = []

app = FastAPI(title="Simple Memory API", version="1.0.0")

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
    threshold: float = 0.7


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


@app.get("/")
async def root():
    return {"message": "Simple Memory API Server", "endpoints": ["/api/memory/retrieve", "/api/learning/process_interaction"]}


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": time.time()}


@app.post("/api/memory/retrieve")
async def retrieve_memory(request: MemoryRetrieveRequest = Body(...)):
    """
    Retrieve memories for a user query.
    """
    try:
        print(f"🔍 Memory retrieval for user {request.user_id}, query: {request.query[:50]}...")
        
        # Get memories for this user
        user_memories = memory_store.get(request.user_id, [])
        
        # Simple keyword matching for demo
        relevant_memories = []
        query_words = request.query.lower().split()
        
        for memory in user_memories:
            content = memory.get("content", "").lower()
            relevance_score = 0.0
            
            # Count matching words
            for word in query_words:
                if word in content:
                    relevance_score += 0.2
            
            if relevance_score >= request.threshold:
                relevant_memories.append({
                    "content": memory.get("content", ""),
                    "metadata": memory.get("metadata", {}),
                    "relevance_score": relevance_score
                })
        
        # Sort by relevance and limit results
        relevant_memories.sort(key=lambda x: x["relevance_score"], reverse=True)
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
    try:
        print(f"🧠 Learning interaction for user {request.user_id}")
        print(f"   Message: {request.user_message[:100]}...")
        
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
        
        # Simple extraction of user information
        message = request.user_message.lower()
        if any(keyword in message for keyword in ["my name is", "i am", "i work", "i like", "i love", "my favorite"]):
            memory_store[request.user_id].append({
                "content": request.user_message,
                "metadata": {
                    "conversation_id": request.conversation_id,
                    "timestamp": time.time(),
                    "source": "learning_interaction"
                }
            })
            print(f"💾 Stored memory for user {request.user_id}")
        
        print(f"✅ Learning interaction processed")
        
        return {
            "status": "success",
            "user_id": request.user_id,
            "processed": True,
            "memories_count": len(memory_store.get(request.user_id, [])),
            "interactions_count": len(learning_interactions)
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
    }


if __name__ == "__main__":
    print("🚀 Starting Simple Memory API Server...")
    print("📡 Endpoints:")
    print("   POST /api/memory/retrieve")
    print("   POST /api/learning/process_interaction") 
    print("   GET /debug/stats")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
