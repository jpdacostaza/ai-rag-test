"""
Standalone pipeline routes for OpenWebUI compatibility
"""
import json
import time
from fastapi import APIRouter, Body, Depends, HTTPException
from typing import Optional
from datetime import datetime
from human_logging import log_service_status
from error_handler import log_error
from database_manager import db_manager
from database import index_document_chunks, retrieve_user_memory, get_embedding, index_user_document

# Create the router
router = APIRouter()

# Simple API key verification for pipelines
def verify_api_key(api_key: Optional[str] = None):
    """Simple API key verification - implement proper security as needed"""
    # For now, accept any key for development - replace with proper validation
    return api_key or "development"

@router.get("/api/v1/pipelines/list")
async def list_pipelines_v1():
    """OpenWebUI v1 API: List available pipelines"""
    log_service_status("PIPELINES", "info", "OpenWebUI v1 pipeline list request received")
    
    pipeline_data = [{
        "id": "memory_pipeline", 
        "name": "Memory Pipeline",
        "object": "pipeline",
        "type": "filter",
        "description": "Advanced memory pipeline for OpenWebUI with conversation persistence and context injection",
        "author": "Backend Team",
        "author_url": "http://localhost:8001",
        "version": "1.0.0",
        "license": "MIT",
        "requirements": [],
        "url": "http://localhost:8001",
        "meta": {
            "capabilities": ["memory", "context", "learning"],
            "supported_models": ["*"],
            "tags": ["memory", "context", "conversation"]
        }
    }]
    
    log_service_status("PIPELINES", "ready", f"OpenWebUI v1: Returned {len(pipeline_data)} pipelines")
    return {"data": pipeline_data}

@router.post("/v1/inlet")
async def pipeline_inlet(
    request: dict = Body(...),
    api_key: str = Depends(verify_api_key)
):
    """Pipeline inlet - inject memory context into messages before LLM processing"""
    try:
        # DEBUG: Log the full request structure to understand OpenWebUI's format
        log_service_status("PIPELINE_DEBUG", "info", f"Full request structure: {json.dumps(request, indent=2)}")
        
        # Extract user information - try multiple possible formats
        user_id = None
        if "user" in request and isinstance(request["user"], dict):
            user_id = request["user"].get("id")
        elif "user" in request and isinstance(request["user"], str):
            user_id = request["user"]
        elif "user_id" in request:
            user_id = request["user_id"]
        
        # If no user found, use default
        if not user_id:
            user_id = "default"
            
        log_service_status("PIPELINE_DEBUG", "info", f"Extracted user_id: {user_id}")
        
        messages = request.get("messages", [])
        
        if not messages:
            return request
              # Get the latest user message
        latest_message = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                latest_message = msg
                break
        
        if not latest_message or not latest_message.get("content"):
            return request
            
        user_query = latest_message["content"]
        log_service_status("PIPELINE_INLET", "info", f"Processing query for user {user_id}")
        
        # Check if user is sharing personal information and store it as memory
        memory_keywords = [
            "my name is", "i am", "i'm", "call me", "i'm called",
            "i live in", "i work", "i study", "my job", "i work as",
            "my favorite", "i like", "i love", "i hate", "i prefer",
            "remember that", "don't forget", "important:",
            "my birthday", "my age", "years old", "from", "born in",
            "i'm from", "i come from", "my hobby", "my hobbies"
        ]
          # Check if this message contains personal information
        user_query_lower = user_query.lower()
        contains_personal_info = any(keyword in user_query_lower for keyword in memory_keywords)
        
        if contains_personal_info and user_id != "default":
            # Store this as a memory for the user
            try:
                import time
                doc_id = f"personal_info_{user_id}_{int(time.time())}"
                chunks_stored = index_user_document(db_manager, user_id, doc_id, "Personal Information", user_query)
                if chunks_stored:
                    log_service_status("PIPELINE_MEMORY", "info", f"Stored personal info as memory for user {user_id}")
                else:
                    log_service_status("PIPELINE_MEMORY", "warning", f"Failed to store memory for user {user_id}")
            except Exception as e:
                log_service_status("PIPELINE_MEMORY", "error", f"Error storing memory for user {user_id}: {str(e)}")
        
        # Retrieve relevant memories
        query_embedding = get_embedding(db_manager, user_query)
        if query_embedding is not None:
            memories = retrieve_user_memory(db_manager, user_id, query_embedding, n_results=3)
            
            if memories:
                # Format memory context
                memory_context = "Based on our previous conversations:\n"
                for i, memory in enumerate(memories[:3]):
                    content = memory.get('content', '')[:200]
                    memory_context += f"- {content}...\n"
                
                # Inject memory into the user's message
                enhanced_content = f"{memory_context}\n---\n{user_query}"
                latest_message["content"] = enhanced_content
                
                log_service_status("PIPELINE_INLET", "ready", f"Enhanced message with {len(memories)} memories")
            else:
                log_service_status("PIPELINE_INLET", "info", f"No memories found for user {user_id}")
        
        return request        
    except Exception as e:
        log_error(e, "pipeline_inlet", user_id or "unknown", "pipeline")
        # Return original request if enhancement fails
        return request

@router.post("/v1/outlet")
async def pipeline_outlet(
    request: dict = Body(...),
    api_key: str = Depends(verify_api_key)
):
    """Pipeline outlet - store conversation for future memory"""
    try:
        # Extract information
        user_id = request.get("user", {}).get("id", "default")
        messages = request.get("messages", [])
        
        if len(messages) < 2:
            return request
        
        # Find the latest user and assistant messages
        user_message = ""
        assistant_message = ""
        
        for msg in reversed(messages):
            if msg.get("role") == "assistant" and not assistant_message:
                assistant_message = msg.get("content", "")
            elif msg.get("role") == "user" and not user_message:
                user_message = msg.get("content", "")
                
            if user_message and assistant_message:
                break
        
        if user_message and assistant_message:
            # Store the interaction as memory using document upload
            log_service_status("PIPELINE_OUTLET", "info", f"Storing conversation for user {user_id}")
            
            # Create conversation content
            interaction_content = f"User: {user_message}\nAssistant: {assistant_message}"
            
            # Store using the document indexing system  
            timestamp = datetime.now().isoformat()
            doc_id = f"conversation_{user_id}_{int(datetime.now().timestamp())}"
            doc_name = f"Conversation: {timestamp}"
            
            # Create chunks from the content
            chunks = [{
                "content": interaction_content,
                "metadata": {
                    "user_id": user_id,
                    "type": "conversation",
                    "timestamp": timestamp,
                    "source": "pipeline_outlet"
                }
            }]
            
            # Store using the existing database function
            success = index_document_chunks(db_manager, user_id, doc_id, doc_name, chunks)
            
            if success:
                log_service_status("PIPELINE_OUTLET", "ready", f"Conversation stored for user {user_id}")
            else:
                log_service_status("PIPELINE_OUTLET", "warning", f"Failed to store conversation for user {user_id}")
        
        return request
        
    except Exception as e:
        log_error(e, "pipeline_outlet", user_id, "pipeline")
        return request

@router.get("/test")
async def test_router():
    """Simple test endpoint to verify router is working"""
    return {"status": "Router is working!", "router": "pipelines_v1_router"}
