"""
Memory and Learning API Routes

This module provides API endpoints for memory retrieval and learning interaction processing
required by the OpenWebUI Functions. Updated to use the new memory architecture when available.
"""

import asyncio
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Body, Depends
from pydantic import BaseModel

from adaptive_learning import adaptive_learning_system
from human_logging import log_service_status
from error_handler import log_error

# Import new memory system with fallback
try:
    from memory import MemoryService, MemoryQuery
    MEMORY_SERVICE_AVAILABLE = True
except ImportError:
    MemoryService = None
    MemoryQuery = None
    MEMORY_SERVICE_AVAILABLE = False

memory_router = APIRouter(prefix="/api", tags=["memory", "learning"])


def get_memory_service():
    """Get memory service from main app."""
    # Import here to avoid circular imports
    from main import get_memory_service_or_legacy
    return get_memory_service_or_legacy()


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
async def retrieve_memory_for_function(
    request: MemoryRetrieveRequest = Body(...),
    memory_service = Depends(get_memory_service)
):
    """
    Retrieve relevant memories for a user query.
    Used by OpenWebUI Functions for memory injection.
    """
    try:
        log_service_status("MEMORY_API", "info", f"Memory retrieval requested for user {request.user_id}")
        
        # Use new memory service if available, otherwise fallback to legacy
        if memory_service and MEMORY_SERVICE_AVAILABLE:
            log_service_status("MEMORY_API", "info", "Using new memory service")
            
            # Use new memory architecture
            memories = await memory_service.get_relevant_memories(
                user_id=request.user_id,
                query_text=request.query,
                limit=request.limit,
                threshold=request.threshold
            )
            
            # Format for API compatibility
            formatted_memories = []
            for memory in memories:
                formatted_memories.append({
                    "content": memory.content,
                    "metadata": memory.metadata or {},
                    "relevance_score": memory.relevance_score or 0.0
                })
                
        else:
            log_service_status("MEMORY_API", "info", "Using legacy memory system")
            
            # Use legacy system as fallback - import here to avoid circular imports
            try:
                from database_manager import retrieve_user_memory
                memories = await retrieve_user_memory(
                    user_id=request.user_id,
                    query=request.query,
                    n_results=request.limit
                )
                
                # Format memories for function consumption (legacy format)
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
                        
            except Exception as e:
                log_service_status("MEMORY_API", "error", f"Legacy memory retrieval failed: {e}")
                formatted_memories = []
        
        return {
            "status": "success",
            "memories": formatted_memories,
            "count": len(formatted_memories),
            "user_id": request.user_id,
            "system": "new" if memory_service else "legacy"
        }
        
    except Exception as e:
        log_error(e, "memory_retrieve_api")
        # Don't fail the function if memory retrieval fails
        return {
            "status": "partial_success",
            "memories": [],
            "count": 0,
            "error": str(e),
            "user_id": request.user_id
        }


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
async def process_learning_interaction(
    request: LearningInteractionRequest = Body(...),
    memory_service = Depends(get_memory_service)
):
    """
    Process an interaction for adaptive learning.
    Used by OpenWebUI Functions to store learning data.
    """
    try:
        log_service_status("LEARNING_API", "info", f"Learning interaction received for user {request.user_id}")
        
        # Try new memory service first, then fallback to legacy
        if memory_service and MEMORY_SERVICE_AVAILABLE:
            log_service_status("LEARNING_API", "info", "Using new memory service for learning")
            
            # Use new memory service for conversation tracking and storage
            messages = [
                {"role": "user", "content": request.user_message},
                {"role": "assistant", "content": request.assistant_response or ""}
            ]
            
            result = await memory_service.track_conversation_and_store(
                user_id=request.user_id,
                messages=messages
            )
            
            return {
                "status": "success",
                "result": {"stored": result},
                "user_id": request.user_id,
                "processed": True,
                "system": "new"
            }
            
        else:
            log_service_status("LEARNING_API", "info", "Using legacy adaptive learning system")
            
            # Use legacy adaptive learning system
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
                "processed": True,
                "system": "legacy"
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
