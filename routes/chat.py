"""
Chat endpoints and logic.
"""
import logging
import re
import uuid
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException

from config import DEFAULT_SYSTEM_PROMPT
from database_manager import (
    db_manager, get_cache, set_cache, get_chat_history, 
    store_chat_history, get_embedding, index_user_document, retrieve_user_memory
)
from error_handler import CacheErrorHandler, ChatErrorHandler, MemoryErrorHandler, safe_execute
from human_logging import log_service_status
from models import ChatRequest, ChatResponse
from services.llm_service import call_llm
from services.tool_service import tool_service

chat_router = APIRouter()

# Stub functions
def get_cache_manager():
    """Stub function to get cache manager."""
    return None

def should_store_as_memory(message: str, response: str) -> bool:
    """Determine if a conversation should be stored as long-term memory."""
    memory_keywords = [
        "my name is", "i am", "i'm", "call me", 
        "i live in", "i work", "i study", "my job",
        "my favorite", "i like", "i love", "i hate",
        "i prefer", "remember that", "don't forget",
        "important:", "note:", "my birthday",
        "my age", "years old", "from", "born in"
    ]
    
    # Check if user is sharing personal information
    message_lower = message.lower()
    for keyword in memory_keywords:
        if keyword in message_lower:
            return True
            
    # Store responses to "who am i" or "what do you know about me" type questions
    if any(phrase in message_lower for phrase in ["who am i", "about me", "know about me"]):
        return True
        
    return False

@chat_router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat: ChatRequest, request: Request):
    # Use request ID from middleware
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    print(f"[CONSOLE DEBUG] Chat endpoint called for user {chat.user_id}, message: {chat.message[:50]}...")
    logging.info(f"[DEBUG] Chat endpoint called for user {chat.user_id}")

    try:
        user_message = chat.message
        user_id = chat.user_id
        user_response = None

        # Validate input
        if not user_message.strip():
            raise HTTPException(
                status_code=400, 
                detail="Message cannot be empty"
            )

        logging.debug(
            f"[REQUEST {request_id}] Chat request from user {user_id}: {user_message[:100]}..."
        )

        # --- Check cache before tool/LLM logic ---
        cache_key = f"chat:{user_id}:{user_message}"
        cached = None
        logging.debug(f"[CACHE] Checking cache for key: {cache_key}")
        
        # Bypass cache for time queries to ensure real-time lookup
        is_time_query = False
        timeanddate_pattern = re.compile(
            r"time(?:\\s*(?:in|for|at))?\\s+([a-zA-Z ]+)", re.IGNORECASE
        )
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
            cached = get_cache(db_manager, cache_key)
            if cached and str(cached).strip():  # Only return non-empty cached responses
                logging.info(f"[CACHE] Returning cached response for user {user_id}")
                return ChatResponse(response=str(cached))

        # --- Retrieve chat history and memory ---
        def get_history():
            return get_chat_history(user_id, limit=10)

        history = safe_execute(
            get_history,
            fallback_value=[],
            error_handler=lambda e: CacheErrorHandler.handle_cache_error(
                e, "get_history", f"history:{user_id}", user_id, request_id
            ),
        )
        
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
                query_emb = get_embedding(user_message)
                print(f"[CONSOLE DEBUG] Generated embedding for user {user_id}: {query_emb is not None}")
                logging.info(f"[DEBUG] Generated embedding for user {user_id}: {query_emb is not None}")
                
                memory_chunks = (
                    retrieve_user_memory(user_id, user_message, limit=3)
                    if query_emb is not None
                    else []
                )
                logging.info(f"[DEBUG] Retrieved {len(memory_chunks) if memory_chunks else 0} memory chunks for user {user_id}")

                # Compose LLM context with explicit instructions for plain text responses
                system_prompt = DEFAULT_SYSTEM_PROMPT

                # Check for system prompt changes and invalidate cache if needed
                cache_manager = get_cache_manager()
                if cache_manager:
                    cache_manager.check_system_prompt_change(system_prompt)
                
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
                messages = [
                    {"role": "system", "content": system_prompt}
                ]
                
                # Add context as system message if we have any
                if full_context:
                    messages.append({"role": "system", "content": full_context})
                
                # Add current user message
                messages.append({"role": "user", "content": user_message})
                
                # Debug logging
                logging.debug(f"[LLM] Calling LLM with {len(messages)} messages for user {user_id}")
                if full_context:
                    logging.debug(f"[LLM] Including context: memory_chunks={len(memory_chunks)}, conversation_entries={len(history) if history else 0}")
                
                return await call_llm(messages)

            try:
                logging.info(f"[DEBUG] Calling LLM query function for user {user_id}")
                user_response = await llm_query()
                logging.info(f"[DEBUG] LLM returned response for user {user_id}: {repr(user_response)}")
                logging.debug(f"[LLM] Received response for user {user_id}: {len(str(user_response)) if user_response else 0} chars")
            except Exception as e:
                logging.error(f"[DEBUG] LLM query failed for user {user_id}: {e}")
                user_response = "I apologize, but I'm having trouble processing your request right now. Please try again."
            
            debug_info.append("[LLM] Used LLM with memory and conversation context")
        else:
            user_response = tool_response
            logging.debug(f"[TOOL] Tool '{tool_name}' returned response for user {user_id}")
            debug_info.append(f"[TOOL] Used {tool_name} tool")

        # --- Store chat in Redis ---
        def store_chat():
            store_chat_history(user_id, user_message, str(user_response))

        safe_execute(
            store_chat,
            error_handler=lambda e: CacheErrorHandler.handle_cache_error(
                e, "store_chat", f"chat:{user_id}", user_id, request_id
            ),
        )
        
        # --- Automatic memory storage for important conversations ---
        print(f"[CONSOLE DEBUG] Checking if conversation should be stored as memory...")
        
        if should_store_as_memory(user_message, str(user_response)):
            print(f"[CONSOLE DEBUG] Storing conversation as long-term memory for user {user_id}")
            
            def store_memory():
                # Create a memory document from the conversation
                memory_text = f"User: {user_message}\nAssistant: {str(user_response)}"
                chunks_stored = index_user_document(user_id, memory_text)
                logging.info(f"[MEMORY] Stored conversation as memory ({chunks_stored} chunks) for user {user_id}")
                debug_info.append(f"[MEMORY] Stored as long-term memory ({chunks_stored} chunks)")

            safe_execute(
                store_memory,
                error_handler=lambda e: MemoryErrorHandler.handle_memory_error(
                    e, "store_conversation", user_id, request_id
                ),
            )
        else:
            print(f"[CONSOLE DEBUG] Conversation not stored as memory (no personal info detected)")

        # --- Cache the response (after generating user_response) ---
        def cache_response():
            if not is_time_query and user_response and str(user_response).strip():  # Only cache non-empty responses
                set_cache(
                    db_manager,
                    cache_key,
                    str(user_response),
                    expire=600
                )
                logging.info(f"[CACHE] Response cached for user {user_id} (key: {cache_key})")
                debug_info.append(f"[CACHE] Response cached (key: {cache_key})")
            else:
                if is_time_query:
                    logging.info("[CACHE] Skipping cache for time-sensitive query")
                else:
                    logging.info("[CACHE] Skipping cache for empty response")

        safe_execute(
            cache_response,
            error_handler=lambda e: CacheErrorHandler.handle_cache_error(
                e, "set", cache_key, user_id, request_id
            ),
        )

        # Always log debug info, but do not include in user-facing response
        logging.debug(f"[DEBUG INFO] {' | '.join(debug_info)}")
        logging.debug(
            f"[REQUEST {request_id}] Successfully processed chat request for user {user_id}"
        )

        return ChatResponse(response=str(user_response) if user_response is not None else "")

    except Exception as e:
        # Log error with service status
        log_service_status('CHAT', 'error', f'Error in chat endpoint: {e}')
        # Use the specialized chat error handler
        error_response = ChatErrorHandler.handle_chat_error(e, user_id, user_message, request_id)
        return ChatResponse(response=error_response["response"])
