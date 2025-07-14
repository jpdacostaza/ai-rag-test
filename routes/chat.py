"""
Chat endpoints and logic.
"""

import logging
import re
import time
import uuid
import hashlib
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, Depends, Body

from config.config_unified import DEFAULT_SYSTEM_PROMPT
from services.chat_service import ChatService
from services.dependencies import get_chat_service
from services.database_manager import (
    db_manager, 
    get_embedding, 
    get_cache, 
    set_cache,
    store_chat_history,
    index_user_document,
    get_chat_history
)
from core.error_handler import CacheErrorHandler, ChatErrorHandler, MemoryErrorHandler, safe_execute
from core.human_logging import log_service_status
from models.models import ChatRequest, ChatResponse
from services.llm_service import call_llm
from services.tool_service import tool_service
from services.user_profiles import user_profile_manager
from utilities.web_search_tool import should_trigger_web_search, search_web, format_web_results_for_chat

# Import consolidation frameworks
from utilities.simple_error_handling import handle_api_errors, handle_errors
from services.auth_validator import AuthValidator

# Import memory service with fallback
try:
    from services.memory_service import MemoryService
    MEMORY_SERVICE_AVAILABLE = True
except ImportError:
    MemoryService = None
    MEMORY_SERVICE_AVAILABLE = False

chat_router = APIRouter()


def get_memory_service():
    """Get memory service from main app."""
    # Import here to avoid circular imports
    from core.main import get_memory_service_or_legacy
    return get_memory_service_or_legacy()


# Helper function to retrieve memories using unified memory service
@handle_errors("get_user_memories", default_value=[])
async def get_user_memories(user_id: Optional[str], query: str, memory_service = None, n_results: int = 3):
    """
    Retrieve user memories using unified memory service with AuthValidator.
    
    Args:
        user_id: User identifier
        query: Query text
        memory_service: Memory service instance (will fallback if None)
        n_results: Number of results to return
        
    Returns:
        List of memory chunks in legacy format for compatibility
    """
    # Use AuthValidator for consistent user validation
    auth_validator = AuthValidator()
    validated_user = await auth_validator.extract_and_validate_user({"id": user_id})
    
    if not validated_user or not validated_user.user_id:
        log_service_status("CHAT", "warning", f"Invalid user_id for memory retrieval: {user_id}")
        return []

    # Get memory service if not provided
    if not memory_service:
        memory_service = get_memory_service()
    
    if memory_service:
        # Use unified memory service (with built-in fallback handling)
        log_service_status("CHAT", "info", f"Using unified memory service for user {validated_user.user_id}")
        memories = await memory_service.get_relevant_memories(
            user_id=validated_user.user_id,
            context=query,
            max_memories=n_results
        )
        
        # Convert to legacy format for compatibility
        memory_chunks = []
        for memory in memories:
            memory_chunks.append({
                "document": memory.content,
                "metadata": memory.metadata or {},
                "distance": 1.0 - (memory.relevance_score or 0.0)  # Convert relevance to distance
            })
        return memory_chunks
    else:
        log_service_status("CHAT", "warning", "Memory service not available, no memories returned")
        return []


# Stub functions
@handle_errors("get_cache_manager", default_value=None)
def get_cache_manager():
    """Get cache manager from database_manager."""
    return get_cache()


def generate_cache_key(user_id: str, message: str) -> str:
    """Generate a cache key for chat requests."""
    # Use hash of message to keep key consistent but not too long
    message_hash = hashlib.md5(message.encode()).hexdigest()[:8]
    return f"chat:{user_id}:{message_hash}"


def should_store_as_memory(message: str, response: str) -> bool:
    """Determine if a conversation should be stored as long-term memory."""
    memory_keywords = [
        "my name is",
        "i am",
        "i'm",
        "call me",
        "i live in",
        "i work",
        "i study",
        "my job",
        "my favorite",
        "i like",
        "i love",
        "i hate",
        "i prefer",
        "remember that",
        "don't forget",
        "important:",
        "note:",
        "my birthday",
        "my age",
        "years old",
        "from",
        "born in",
        "my profession",
        "my career",
        "my location",
        "my interests",
        "my hobbies",
        "my family",
    ]

    # Check if user is sharing personal information
    message_lower = message.lower()
    for keyword in memory_keywords:
        if keyword in message_lower:
            return True

    # Store responses to "who am i" or "what do you know about me" type questions
    if any(phrase in message_lower for phrase in ["who am i", "about me", "know about me", "remember me"]):
        return True

    # Store any conversation where user info was extracted
    user_info = user_profile_manager.extract_user_info(message)
    if user_info:
        return True

    return False


def validate_openwebui_user_id(user_id: str) -> bool:
    """
    Legacy wrapper for AuthValidator compatibility.
    
    Args:
        user_id: The user identifier to validate
        
    Returns:
        bool: True if valid OpenWebUI user ID
    """
    # Use AuthValidator for consistent validation
    auth_validator = AuthValidator()
    return auth_validator.is_valid_user_id(user_id)


def extract_authenticated_user_id(messages: list) -> Optional[str]:
    """
    Extract the authenticated user ID injected by the Enhanced Memory Pipeline.
    
    Args:
        messages: List of messages from the request
        
    Returns:
        Optional[str]: The authenticated user ID if found
    """
    if not messages:
        return None
    
    # Look for pipeline-injected authenticated user ID
    for msg in messages:
        if (msg.get("role") == "system" and 
            msg.get("content", "").startswith("AUTHENTICATED_USER_ID:")):
            try:
                content = msg.get("content", "")
                pipeline_user_id = content.replace("AUTHENTICATED_USER_ID:", "").strip()
                
                if pipeline_user_id and validate_openwebui_user_id(pipeline_user_id):
                    log_service_status("CHAT", "info", f"✅ Found valid authenticated user ID: {pipeline_user_id}")
                    return pipeline_user_id
                else:
                    log_service_status("CHAT", "warning", f"❌ Invalid user ID from pipeline: {pipeline_user_id}")
            except Exception as e:
                log_service_status("CHAT", "error", f"Failed to extract pipeline user ID: {e}")
    
    return None


@chat_router.post("/chat/completions_legacy")
@handle_api_errors("chat_endpoint")
async def chat_endpoint(
    request: Request, 
    body: dict = Body(...),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Chat endpoint that supports both legacy format (user_id, message) and OpenAI format (model, messages).
    Automatically detects the format and handles accordingly.
    """
    # Use request ID from middleware
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    start_time = time.time()
    
    # Detect if this is OpenAI format (has 'model' and 'messages' fields) or legacy format (has 'user_id' and 'message')
    if "model" in body and "messages" in body:
        # OpenAI format - delegate to the OpenAI handler
        from core.main import openai_chat_completions
        return await openai_chat_completions(request, body)
    
    # Legacy format - validate and parse
    try:
        chat = ChatRequest(**body)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid request format. Expected either OpenAI format (model, messages) or legacy format (user_id, message). Error: {str(e)}"
        )
    
    # Validate input
    if not chat.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Process chat using the service
    response = await chat_service.process_chat(chat)
    
    # Log completion
    duration = (time.time() - start_time) * 1000
    log_service_status(
        "api",
        "info", 
        f"[REQUEST] 📝 Info - [{request_id}] POST /chat - Completed 200 in {duration:.2f}ms"
    )
    
    return response


# Keep the async store_conversation_memory function for the ChatService
async def store_conversation_memory(user_id: str, user_message: str, assistant_response: str, debug_info: list) -> bool:
    """
    Store conversation as long-term memory using proper async patterns.
    
    Args:
        user_id: The user's ID
        user_message: The user's message
        assistant_response: The assistant's response  
        debug_info: List to append debug information to
        
    Returns:
        bool: True if successfully stored, False otherwise
    """
    try:
        # Try new memory service first
        memory_service = get_memory_service()
        stored_via_new_service = False
        
        if memory_service and MEMORY_SERVICE_AVAILABLE:
            try:
                # Create a structured memory for better retrieval
                memory_content = f"User: {user_message}\nAssistant: {assistant_response}"
                success = await memory_service.store_conversation_memory(
                    user_id=user_id,
                    content=memory_content,
                    metadata={
                        "type": "chat_conversation",
                        "timestamp": time.time(),
                        "user_message": user_message,
                        "assistant_response": assistant_response
                    }
                )
                if success:
                    stored_via_new_service = True
                    logging.info(f"[MEMORY] Stored conversation via new memory service for user {user_id}")
                    debug_info.append("[MEMORY] Stored via new memory service")
                    return True
            except Exception as e:
                logging.warning(f"[MEMORY] New memory service failed: {e}")
        
        # Fallback to legacy system if new service failed or not available
        if not stored_via_new_service:
            memory_text = f"User: {user_message}\nAssistant: {assistant_response}"
            doc_id = f"chat_{user_id}_{int(time.time())}"
            chunks_stored = index_user_document(db_manager, user_id, doc_id, "chat_conversation", memory_text)
            logging.info(f"[MEMORY] Stored conversation as memory ({chunks_stored} chunks) for user {user_id}")
            debug_info.append(f"[MEMORY] Stored as long-term memory ({chunks_stored} chunks)")
            return chunks_stored > 0
            
    except Exception as e:
        logging.error(f"[MEMORY] Failed to store conversation memory for user {user_id}: {e}")
        return False
