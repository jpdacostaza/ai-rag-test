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
from utilities.error_patterns import handle_api_errors, handle_service_errors, ErrorHandlerConfig
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
@handle_service_errors(
    operation_name="get_user_memories",
    config=ErrorHandlerConfig(
        max_retries=1,
        log_traceback=True)
)
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
@handle_service_errors(
    operation_name="get_cache_manager",
    config=ErrorHandlerConfig(
        max_retries=1,
        log_traceback=True)
)
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
@handle_api_errors(
    operation_name="chat_endpoint"
)
async def chat_endpoint(request: Request, body: dict = Body(...)):
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
        
    print(f"[CONSOLE DEBUG] Chat endpoint called for user {chat.user_id}, message: {chat.message[:50]}...")
    logging.info(f"[DEBUG] Chat endpoint called for user {chat.user_id}")

    try:
        user_message = chat.message
        user_id = chat.user_id
        user_response = None

        # Validate input
        if not user_message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        # Extract and save user information from message
        user_info = user_profile_manager.extract_user_info(user_message)
        if user_info:
            user_profile_manager.update_profile(user_id, user_info)
            log_service_status("memory", "info", f"Saved user info for {user_id}: {user_info}")

        # Check cache first - unified cache implementation
        cache_key = generate_cache_key(user_id, user_message)

        # Bypass cache for time queries to ensure real-time lookup
        is_time_query = False
        timeanddate_pattern = re.compile(r"time(?:\\s*(?:in|for|at))?\\s+([a-zA-Z ]+)", re.IGNORECASE)
        if (
            "timeanddate.com" in user_message.lower()
            or (
                timeanddate_pattern.search(user_message)
                and not any(
                    x in user_message.lower()
                    for x in [
                        "weather",
                        "convert",
                        "calculate",
                        "exchange rate",
                        "system info",
                        "news",
                        "search",
                    ]
                )
            )
            or "time" in user_message.lower()
        ):
            is_time_query = True

        if not is_time_query:
            try:
                cache_manager = get_cache()
                cached_response = cache_manager.get(cache_key) if cache_manager else None
                if cached_response and isinstance(cached_response, dict):
                    log_service_status("cache", "info", f"Cache hit for key: {cache_key}")
                    # Update request_id and return cached response
                    cached_data = cached_response.copy()
                    cached_data["request_id"] = request_id
                    duration = (time.time() - start_time) * 1000
                    log_service_status(
                        "api",
                        "info",
                        f"[REQUEST] 📝 Info - [{request_id}] POST /chat - Completed 200 in {duration:.2f}ms (cached)")
                    return ChatResponse(**cached_data)
                elif cached_response and str(cached_response).strip():
                    # Handle old string-based cache entries
                    log_service_status("cache", "info", f"Cache hit (legacy format) for key: {cache_key}")
                    duration = (time.time() - start_time) * 1000
                    log_service_status(
                        "api",
                        "info",
                        f"[REQUEST] 📝 Info - [{request_id}] POST /chat - Completed 200 in {duration:.2f}ms (cached)")
                    return ChatResponse(response=str(cached_response))
            except Exception as cache_error:
                log_service_status("cache", "warning", f"Cache check failed: {str(cache_error)}")

        log_service_status("cache", "info", f"Cache miss for key: {cache_key}")
        logging.debug(f"[REQUEST {request_id}] Chat request from user {user_id}: {user_message[:100]}...")

        # --- Retrieve chat history and memory ---
        async def get_history():
            return await get_chat_history(f"user:{user_id}", limit=10)

        try:
            history = await get_history()
        except Exception as e:
            history = []
            logging.warning(f"[CHAT_HISTORY] Failed to retrieve history for user {user_id}: {e}")

        logging.debug(f"[CHAT_HISTORY] Retrieved {len(history or [])} history entries for user {user_id}")

        # --- Tool detection and execution ---
        tool_used, tool_response, tool_name, debug_info = tool_service.detect_and_execute_tool(
            user_message, user_id, request_id
        )

        # If no tool matched, use LLM with memory/context
        print(f"[CONSOLE DEBUG] About to check tool_used: {tool_used}")
        logging.info(f"[DEBUG] Tool detection complete: tool_used={tool_used}")

        if not tool_used:
            logging.info(f"[DEBUG] No tool used, proceeding with LLM query for user {user_id}")

            async def llm_query():
                print(f"[CONSOLE DEBUG] LLM query function called for user {user_id}")
                logging.info(f"[DEBUG] LLM query function called for user {user_id}")
                # Embed user query and retrieve relevant memory
                query_emb = await get_embedding(user_message)
                print(f"[CONSOLE DEBUG] Generated embedding for user {user_id}: {query_emb is not None}")
                logging.info(f"[DEBUG] Generated embedding for user {user_id}: {query_emb is not None}")

                # Get memory service from dependency injection
                memory_service = get_memory_service()
                memory_chunks = await get_user_memories(user_id, user_message, memory_service, n_results=3)
                logging.info(
                    f"[DEBUG] Retrieved {len(memory_chunks) if memory_chunks else 0} memory chunks for user {user_id}"
                )

                # Compose LLM context with explicit instructions for plain text responses
                system_prompt = DEFAULT_SYSTEM_PROMPT

                # Add user profile information to system prompt
                user_context = user_profile_manager.build_context_for_llm(user_id)
                if user_context:
                    system_prompt += f" User Profile Information: {user_context}"
                    logging.info(f"[PROFILE] Added user context for {user_id}: {user_context[:100]}...")

                # Check for system prompt changes (simplified - just log for now)
                cache_manager = get_cache_manager()
                if cache_manager:
                    logging.debug(f"[CACHE] Using cache manager with system prompt")

                # Ensure memory_chunks is a list and handle None values
                memory_chunks = memory_chunks or []

                # Build conversation context from history
                conversation_context = ""
                if history:
                    # Format chat history as conversation for context
                    for entry in history[-5:]:  # Last 5 entries
                        if isinstance(entry, dict):
                            user_msg = entry.get("message", "")
                            assistant_msg = entry.get("response", "")
                            if user_msg:
                                conversation_context += f"User: {user_msg}\n"
                            if assistant_msg:
                                conversation_context += f"Assistant: {assistant_msg}\n"

                # Combine memory and conversation context
                full_context = ""
                if memory_chunks:
                    full_context += "Relevant memories:\n" + "\n".join([str(m) for m in memory_chunks]) + "\n\n"
                if conversation_context:
                    full_context += "Previous conversation:\n" + conversation_context + "\n"

                # Build messages for LLM
                messages = [{"role": "system", "content": system_prompt}]

                # Add context as system message if we have any
                if full_context:
                    messages.append({"role": "system", "content": full_context})

                # Add current user message
                messages.append({"role": "user", "content": user_message})

                # Debug logging
                logging.debug(f"[LLM] Calling LLM with {len(messages)} messages for user {user_id}")
                if full_context:
                    logging.debug(
                        f"[LLM] Including context: memory_chunks={len(memory_chunks)}, conversation_entries={len(history) if history else 0}"
                    )

                return await call_llm(messages)

            try:
                logging.info(f"[DEBUG] Calling LLM query function for user {user_id}")
                user_response = await llm_query()
                logging.info(f"[DEBUG] LLM returned response for user {user_id}: {repr(user_response)}")
                logging.debug(
                    f"[LLM] Received response for user {user_id}: {len(str(user_response)) if user_response else 0} chars"
                )

                # Check if web search is needed after getting initial LLM response
                if should_trigger_web_search(user_message, str(user_response)):
                    logging.info(
                        f"[WEB_SEARCH] Triggering web search for user {user_id} - query: {user_message[:100]}..."
                    )
                    try:
                        # Perform web search
                        search_results = await search_web(user_message, max_results=3)

                        if search_results.get("results"):
                            # Format web search results
                            web_info = format_web_results_for_chat(search_results)

                            # Enhance the response with web search results
                            if any(
                                phrase in str(user_response).lower()
                                for phrase in ["i don't know", "i'm not sure", "i don't have"]
                            ):
                                # Replace uncertain response with web search results
                                user_response = web_info
                            else:
                                # Append web search results to existing response
                                user_response = f"{user_response}\n\n{web_info}"

                            debug_info.append(
                                f"[WEB_SEARCH] Enhanced response with {len(search_results['results'])} web results"
                            )
                            logging.info(f"[WEB_SEARCH] Successfully enhanced response for user {user_id}")
                        else:
                            debug_info.append("[WEB_SEARCH] No web results found")
                            logging.warning(f"[WEB_SEARCH] No results found for query: {user_message[:100]}...")

                    except Exception as search_error:
                        logging.error(f"[WEB_SEARCH] Failed for user {user_id}: {search_error}")
                        debug_info.append(f"[WEB_SEARCH] Search failed: {str(search_error)[:50]}...")

                # Add personalized greeting for returning users
                if any(
                    greeting in user_message.lower()
                    for greeting in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]
                ):
                    personalized_greeting = user_profile_manager.get_user_greeting(user_id)
                    if personalized_greeting != "Hello! I'm here to help you.":
                        user_response = f"{personalized_greeting} {user_response}"
                        logging.info(f"[PROFILE] Added personalized greeting for {user_id}")

            except Exception as e:
                logging.error(f"[DEBUG] LLM query failed for user {user_id}: {e}")
                user_response = (
                    "I apologize, but I'm having trouble processing your request right now. Please try again."
                )

            debug_info.append("[LLM] Used LLM with memory and conversation context")
        else:
            user_response = tool_response
            logging.debug(f"[TOOL] Tool '{tool_name}' returned response for user {user_id}")
            debug_info.append(f"[TOOL] Used {tool_name} tool")

        # --- Store chat in Redis ---
        try:
            message_data = {
                "user_message": user_message,
                "assistant_response": str(user_response),
                "timestamp": time.time(),
            }
            await store_chat_history(f"user:{user_id}", [message_data])
        except Exception as e:
            logging.warning(f"[REDIS] Failed to store chat history for user {user_id}: {e}")

        # --- Automatic memory storage for important conversations ---
        print(f"[CONSOLE DEBUG] Checking if conversation should be stored as memory...")

        if should_store_as_memory(user_message, str(user_response)):
            print(f"[CONSOLE DEBUG] Storing conversation as long-term memory for user {user_id}")

            def store_memory():
                """
                Store the current conversation as long-term memory.
                
                Creates a memory document from the user message and assistant response,
                then indexes it for future retrieval. Used for important conversations
                that should be remembered across sessions.
                """
                import asyncio
                
                async def async_store_memory():
                    # Try new memory service first
                    memory_service = get_memory_service()
                    stored_via_new_service = False
                    
                    if memory_service and MEMORY_SERVICE_AVAILABLE:
                        try:
                            # Create a structured memory for better retrieval
                            memory_content = f"User: {user_message}\nAssistant: {str(user_response)}"
                            success = await memory_service.store_conversation_memory(
                                user_id=user_id,
                                content=memory_content,
                                metadata={
                                    "type": "chat_conversation",
                                    "timestamp": time.time(),
                                    "user_message": user_message,
                                    "assistant_response": str(user_response)
                                }
                            )
                            if success:
                                stored_via_new_service = True
                                logging.info(f"[MEMORY] Stored conversation via new memory service for user {user_id}")
                                debug_info.append("[MEMORY] Stored via new memory service")
                        except Exception as e:
                            logging.warning(f"[MEMORY] New memory service failed: {e}")
                    
                    # Fallback to legacy system if new service failed or not available
                    if not stored_via_new_service:
                        memory_text = f"User: {user_message}\nAssistant: {str(user_response)}"
                        doc_id = f"chat_{user_id}_{int(time.time())}"
                        chunks_stored = index_user_document(db_manager, user_id, doc_id, "chat_conversation", memory_text)
                        logging.info(f"[MEMORY] Stored conversation as memory ({chunks_stored} chunks) for user {user_id}")
                        debug_info.append(f"[MEMORY] Stored as long-term memory ({chunks_stored} chunks)")
                
                # Run the async function
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Create a task if we're in an async context
                        asyncio.create_task(async_store_memory())
                    else:
                        loop.run_until_complete(async_store_memory())
                except Exception as e:
                    logging.error(f"[MEMORY] Failed to store memory: {e}")
                    # Fallback to legacy system only
                    memory_text = f"User: {user_message}\nAssistant: {str(user_response)}"
                    doc_id = f"chat_{user_id}_{int(time.time())}"
                    chunks_stored = index_user_document(db_manager, user_id, doc_id, "chat_conversation", memory_text)
                    logging.info(f"[MEMORY] Stored conversation as memory ({chunks_stored} chunks) for user {user_id}")
                    debug_info.append(f"[MEMORY] Stored as long-term memory ({chunks_stored} chunks)")

            safe_execute(
                store_memory,
                error_handler=lambda e: MemoryErrorHandler.handle_memory_error(
                    e, "store_conversation", user_id, request_id
                ))
        else:
            print(f"[CONSOLE DEBUG] Conversation not stored as memory (no personal info detected)")

        # --- Cache the response (unified implementation) ---
        if not is_time_query and user_response and str(user_response).strip():
            try:
                cache_manager = get_cache()
                if cache_manager:
                    # Create response object to cache
                    response_data = {"response": str(user_response)}
                    success = cache_manager.set(cache_key, response_data)
                    if success:
                        log_service_status("cache", "info", f"Cached response for key: {cache_key}")
                        debug_info.append(f"[CACHE] Response cached (key: {cache_key})")
                    else:
                        log_service_status("cache", "warning", f"Failed to cache response for user {user_id}")
            except Exception as cache_error:
                log_service_status("cache", "warning", f"Cache set failed: {str(cache_error)}")
        else:
            if is_time_query:
                logging.info("[CACHE] Skipping cache for time-sensitive query")
            else:
                logging.info("[CACHE] Skipping cache for empty response")

        # Always log debug info, but do not include in user-facing response
        logging.debug(f"[DEBUG INFO] {' | '.join(debug_info)}")
        logging.debug(f"[REQUEST {request_id}] Successfully processed chat request for user {user_id}")

        # Create response
        response = ChatResponse(response=str(user_response) if user_response is not None else "")

        return response

    except Exception as e:
        # Log error with service status
        log_service_status("CHAT", "error", f"Error in chat endpoint: {e}")
        # Use the specialized chat error handler
        error_response = ChatErrorHandler.handle_chat_error(e, user_id, user_message, request_id)
        return ChatResponse(response=error_response["response"])
