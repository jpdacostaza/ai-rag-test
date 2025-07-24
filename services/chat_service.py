"""
Chat Service
============

This service handles all chat-related business logic, extracted from the monolithic
chat endpoint to follow single responsibility principle and improve testability.
"""

import logging
import time
from typing import Optional, List, Dict, Any
from datetime import datetime

from models.models import ChatRequest, ChatResponse
from services.llm_service import call_llm
from services.tool_service import tool_service
from services.user_profiles import user_profile_manager
from utilities.web_search_tool import should_trigger_web_search, search_web, format_web_results_for_chat
from utilities.simple_error_handling import handle_errors
from core.logging_config import get_logger

logger = logging.getLogger(__name__)


class ChatContext:
    """Context object for chat processing."""
    
    def __init__(self):
        self.user_id: str = ""
        self.message: str = ""
        self.request_id: str = ""
        self.memories: List[Dict] = []
        self.history: List[Dict] = []
        self.is_time_query: bool = False
        self.cache_key: str = ""


class ChatService:
    """
    Service for handling chat operations with proper separation of concerns.
    """
    
    def __init__(self, cache_service, memory_service, database_manager):
        self.cache_service = cache_service
        self.memory_service = memory_service
        self.database_manager = database_manager
        self.logger = get_logger(__name__)
    
    @handle_errors("process_chat", default_value=ChatResponse(message="I'm having trouble processing your request right now."))
    async def process_chat(self, request: ChatRequest) -> ChatResponse:
        """
        Main chat processing logic - clean and focused.
        
        Args:
            request: Chat request containing user_id and message
            
        Returns:
            ChatResponse: Generated response
        """
        # Build context
        context = await self._build_context(request)
        
        # Check cache first
        cached_response = await self._check_cache(context)
        if cached_response:
            return cached_response
        
        # Process with tools or LLM
        response = await self._generate_response(context)
        
        # Store conversation and cache response
        await self._store_conversation(context, response)
        await self._cache_response(context, response)
        
        return ChatResponse(message=response)
    
    async def _build_context(self, request: ChatRequest) -> ChatContext:
        """Build context for chat processing."""
        context = ChatContext()
        context.user_id = request.user_id
        context.message = request.message
        context.request_id = f"req_{int(time.time())}_{context.user_id[:8]}"
        
        # Extract and save user information
        user_info = user_profile_manager.extract_user_info(context.message)
        if user_info:
            user_profile_manager.update_profile(context.user_id, user_info)
            logger.info(f"[PROFILE] Saved user info for {context.user_id}: {user_info}")
        
        # Generate cache key
        context.cache_key = self._generate_cache_key(context.user_id, context.message)
        
        # Check if this is a time-sensitive query
        context.is_time_query = self._is_time_sensitive_query(context.message)
        
        return context
    
    async def _check_cache(self, context: ChatContext) -> Optional[ChatResponse]:
        """Check for cached response."""
        if context.is_time_query:
            return None
        
        try:
            if self.cache_service:
                cached_response = self.cache_service.get(context.cache_key)
                if cached_response:
                    if isinstance(cached_response, dict):
                        cached_response["request_id"] = context.request_id
                        logger.info(f"[CACHE] Cache hit for key: {context.cache_key}")
                        return ChatResponse(**cached_response)
                    elif isinstance(cached_response, str) and cached_response.strip():
                        logger.info(f"[CACHE] Cache hit (legacy format) for key: {context.cache_key}")
                        return ChatResponse(message=cached_response)
        except Exception as e:
            logger.warning(f"[CACHE] Cache check failed: {e}")
        
        logger.info(f"[CACHE] Cache miss for key: {context.cache_key}")
        return None
    
    async def _generate_response(self, context: ChatContext) -> str:
        """Generate response using tools or LLM."""
        # Try tool detection first
        tool_used, tool_response, tool_name, debug_info = tool_service.detect_and_execute_tool(
            context.message, context.user_id, context.request_id
        )
        
        if tool_used:
            logger.info(f"[TOOL] Used {tool_name} tool for user {context.user_id}")
            return str(tool_response)
        
        # Use LLM with memory and context
        return await self._generate_llm_response(context)
    
    async def _generate_llm_response(self, context: ChatContext) -> str:
        """Generate LLM response with memory and context."""
        try:
            # Get memory and history
            await self._load_memory_and_history(context)
            
            # Build LLM context
            system_prompt, messages = await self._build_llm_context(context)
            
            # Call LLM
            response = await call_llm(messages)
            
            # Enhance with web search if needed
            response = await self._enhance_with_web_search(context, response)
            
            # Add personalized greeting if appropriate
            response = self._add_personalized_greeting(context, response)
            
            return str(response)
            
        except Exception as e:
            logger.error(f"[LLM] LLM response generation failed for user {context.user_id}: {e}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again."
    
    async def _load_memory_and_history(self, context: ChatContext):
        """Load user memories and chat history."""
        try:
            # Load memories using async memory function
            from routes.chat import get_user_memories
            context.memories = await get_user_memories(
                context.user_id, 
                context.message, 
                self.memory_service, 
                n_results=3
            )
            logger.info(f"[MEMORY] Retrieved {len(context.memories)} memory chunks for user {context.user_id}")
            
            # Load history
            from services.database_manager import get_chat_history
            context.history = await get_chat_history(f"user:{context.user_id}", limit=5)
            logger.info(f"[HISTORY] Retrieved {len(context.history or [])} history entries for user {context.user_id}")
            
        except Exception as e:
            logger.warning(f"[CONTEXT] Failed to load context for user {context.user_id}: {e}")
            context.memories = []
            context.history = []
    
    async def _build_llm_context(self, context: ChatContext) -> tuple[str, List[Dict]]:
        """Build system prompt and messages for LLM."""
        from config.config_unified import DEFAULT_SYSTEM_PROMPT
        
        system_prompt = DEFAULT_SYSTEM_PROMPT
        
        # Add user profile information
        user_context = user_profile_manager.build_context_for_llm(context.user_id)
        if user_context:
            system_prompt += f" User Profile Information: {user_context}"
            logger.info(f"[PROFILE] Added user context for {context.user_id}")
        
        # Build conversation context
        full_context = ""
        
        # Add memories
        if context.memories:
            memory_text = "\n".join([str(m) for m in context.memories])
            full_context += f"Relevant memories:\n{memory_text}\n\n"
        
        # Add recent conversation history
        if context.history:
            conversation_context = ""
            for entry in context.history[-5:]:  # Last 5 entries
                if isinstance(entry, dict):
                    user_msg = entry.get("message", "")
                    assistant_msg = entry.get("response", "")
                    if user_msg:
                        conversation_context += f"User: {user_msg}\n"
                    if assistant_msg:
                        conversation_context += f"Assistant: {assistant_msg}\n"
            
            if conversation_context:
                full_context += f"Previous conversation:\n{conversation_context}\n"
        
        # Build messages
        messages = [{"role": "system", "content": system_prompt}]
        
        if full_context:
            messages.append({"role": "system", "content": full_context})
        
        messages.append({"role": "user", "content": context.message})
        
        return system_prompt, messages
    
    async def _enhance_with_web_search(self, context: ChatContext, response: str) -> str:
        """Enhance response with web search if appropriate."""
        try:
            if should_trigger_web_search(context.message, response):
                logger.info(f"[WEB_SEARCH] Triggering web search for user {context.user_id}")
                search_results = await search_web(context.message, max_results=3)
                
                if search_results.get("results"):
                    web_info = format_web_results_for_chat(search_results)
                    
                    # Enhance response based on uncertainty indicators
                    if any(phrase in response.lower() for phrase in ["i don't know", "i'm not sure", "i don't have"]):
                        response = web_info
                    else:
                        response = f"{response}\n\n{web_info}"
                    
                    logger.info(f"[WEB_SEARCH] Enhanced response with {len(search_results['results'])} web results")
                
        except Exception as e:
            logger.error(f"[WEB_SEARCH] Failed for user {context.user_id}: {e}")
        
        return response
    
    def _add_personalized_greeting(self, context: ChatContext, response: str) -> str:
        """Add personalized greeting for returning users."""
        if any(greeting in context.message.lower() for greeting in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]):
            personalized_greeting = user_profile_manager.get_user_greeting(context.user_id)
            if personalized_greeting != "Hello! I'm here to help you.":
                response = f"{personalized_greeting} {response}"
                logger.info(f"[PROFILE] Added personalized greeting for {context.user_id}")
        
        return response
    
    async def _store_conversation(self, context: ChatContext, response: str):
        """Store conversation in Redis and optionally as memory."""
        try:
            # Store in Redis
            from services.database_manager import store_chat_history
            message_data = {
                "user_message": context.message,
                "assistant_response": response,
                "timestamp": time.time(),
            }
            await store_chat_history(f"user:{context.user_id}", [message_data])
            logger.info(f"[REDIS] Stored chat history for user {context.user_id}")
            
            # Store as memory if important
            from routes.chat import should_store_as_memory, store_conversation_memory
            if should_store_as_memory(context.message, response):
                logger.info(f"[MEMORY] Storing conversation as long-term memory for user {context.user_id}")
                await store_conversation_memory(context.user_id, context.message, response, [])
            
        except Exception as e:
            logger.warning(f"[STORAGE] Failed to store conversation for user {context.user_id}: {e}")
    
    async def _cache_response(self, context: ChatContext, response: str):
        """Cache the response for future use."""
        if context.is_time_query or not response or not response.strip():
            return
        
        try:
            if self.cache_service:
                response_data = {"response": response}
                success = self.cache_service.set(context.cache_key, response_data)
                if success:
                    logger.info(f"[CACHE] Cached response for key: {context.cache_key}")
                else:
                    logger.warning(f"[CACHE] Failed to cache response for user {context.user_id}")
        except Exception as e:
            logger.warning(f"[CACHE] Cache set failed: {e}")
    
    def _generate_cache_key(self, user_id: str, message: str) -> str:
        """Generate cache key for the request."""
        import hashlib
        message_hash = hashlib.md5(message.encode()).hexdigest()[:8]
        return f"chat:{user_id}:{message_hash}"
    
    def _is_time_sensitive_query(self, message: str) -> bool:
        """Check if the query is time-sensitive and should bypass cache."""
        import re
        
        timeanddate_pattern = re.compile(r"time(?:\\s*(?:in|for|at))?\\s+([a-zA-Z ]+)", re.IGNORECASE)
        
        return (
            "timeanddate.com" in message.lower()
            or (
                timeanddate_pattern.search(message)
                and not any(
                    x in message.lower()
                    for x in ["weather", "convert", "calculate", "exchange rate", "system info", "news", "search"]
                )
            )
            or "time" in message.lower()
        )
