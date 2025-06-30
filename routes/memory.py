"""
Memory and Learning API Routes

This module provides API endpoints for memory retrieval and learning interaction processing
required by the OpenWebUI Functions.
"""

import asyncio
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Body, Depends
from pydantic import BaseModel

from adaptive_learning import adaptive_learning_system
from database_manager import retrieve_user_memory
from human_logging import log_service_status
from error_handler import log_error

memory_router = APIRouter(prefix="/api", tags=["memory", "learning"])


class MemoryRetrieveRequest(BaseModel):
    user_id: str
    query: str
    limit: int = 5
    threshold: float = 0.1


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


@memory_router.post("/memory/retrieve")
async def retrieve_memory_for_function(request: MemoryRetrieveRequest = Body(...)):
    """
    Retrieve relevant memories for a user query.
    Used by OpenWebUI Functions for memory injection.
    """
    try:
        log_service_status("MEMORY_API", "info", f"Memory retrieval requested for user {request.user_id}")
        
        # Use the existing retrieve_user_memory function
        memories = await retrieve_user_memory(
            user_id=request.user_id,
            query=request.query,
            limit=request.limit
        )
        
        # Format memories for function consumption
        formatted_memories = []
        if memories:
            for memory in memories:
                # Convert distance to relevance score (distance is 0-2, where 0 is perfect match)
                # Convert to relevance score where 1.0 is perfect and 0.0 is no match
                distance = memory.get("distance", 2.0)
                relevance_score = max(0.0, 1.0 - (distance / 2.0))
                
                formatted_memories.append({
                    "content": memory.get("document", ""),
                    "metadata": memory.get("metadata", {}),
                    "relevance_score": relevance_score
                })
        
        return {
            "status": "success",
            "memories": formatted_memories,
            "count": len(formatted_memories),
            "user_id": request.user_id
        }
        
    except Exception as e:
        log_error(e, "memory_retrieval_api")
        raise HTTPException(status_code=500, detail=f"Memory retrieval failed: {str(e)}")


@memory_router.post("/memory/learn")
async def learn_from_document(request: DocumentLearningRequest = Body(...)):
    """
    Learn from a document and store it in the user's memory.
    """
    try:
        log_service_status("MEMORY_API", "info", f"Memory learning requested for user {request.user_id}")
        
        # Use the adaptive learning system to process and store the document
        document_id = await adaptive_learning_system.add_document_to_memory(
            user_id=request.user_id,
            document_content=request.document.get("content", ""),
            metadata=request.document.get("metadata", {})
        )
        
        return {
            "status": "success",
            "message": "Document learned successfully",
            "document_id": document_id,
            "user_id": request.user_id
        }
        
    except Exception as e:
        log_error(e, "memory_learning_api")
        raise HTTPException(status_code=500, detail=f"Memory learning failed: {str(e)}")


@memory_router.post("/learning/process_interaction")
async def process_learning_interaction(request: LearningInteractionRequest = Body(...)):
    """
    Process an interaction for adaptive learning.
    Used by OpenWebUI Functions to store learning data.
    """
    try:
        log_service_status("LEARNING_API", "info", f"Learning interaction received for user {request.user_id}")
        
        # Process the interaction using the adaptive learning system
        result = await adaptive_learning_system.process_interaction(
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            user_message=request.user_message,
            assistant_response=request.assistant_response or "",
            response_time=request.response_time or 1.0,
            tools_used=request.tools_used or []
        )
        
        return {
            "status": "success",
            "result": result,
            "user_id": request.user_id,
            "processed": True
        }
        
    except Exception as e:
        log_error(e, "learning_interaction_api")
        # Don't fail the function if learning fails
        return {
            "status": "partial_success",
            "error": str(e),
            "user_id": request.user_id,
            "processed": False
        }


@memory_router.get("/memory/health")
async def memory_health():
    """Health check for memory endpoints"""
    return {
        "status": "healthy",
        "endpoints": [
            "/api/memory/retrieve",
            "/api/learning/process_interaction"
        ],
        "timestamp": "2025-06-27"
    }
