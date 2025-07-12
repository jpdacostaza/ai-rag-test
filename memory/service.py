"""
Memory Service
==============

High-level memory service that orchestrates memory operations.
"""

import time
import uuid
from typing import Dict, List, Optional, Any

from .core import MemoryClient, MemoryConfig, MemoryQuery, MemoryRecord, LearningInteraction
from .providers.factory import MemoryProviderFactory


class MemoryService:
    """High-level memory service for application integration."""
    
    def __init__(self, config: MemoryConfig, logger: Optional[callable] = None):
        """
        Initialize the memory service.
        
        Args:
            config: Memory configuration
            logger: Optional logging function
        """
        self.config = config
        self.log = logger or self._default_logger
        self.conversation_tracker = {}
        
        # Initialize memory provider
        self.provider = MemoryProviderFactory.create_provider(
            provider_type="api",
            config=config,
            logger=logger
        )
    
    def _default_logger(self, message: str, level: str = "INFO") -> None:
        """Default logger that does nothing."""
        pass
    
    async def get_relevant_memories(
        self, 
        user_id: str, 
        query_text: str, 
        limit: Optional[int] = None,
        threshold: Optional[float] = None
    ) -> List[MemoryRecord]:
        """
        Retrieve memories relevant to a query.
        
        Args:
            user_id: User identifier
            query_text: Text to search for relevant memories
            limit: Maximum number of memories (defaults to config)
            threshold: Relevance threshold (defaults to config)
            
        Returns:
            List of relevant memory records
        """
        # Validate user_id
        if not user_id or not user_id.strip():
            self.log(f"Invalid user_id provided for memory retrieval: {user_id}", "WARNING")
            return []
        
        try:
            query = MemoryQuery(
                user_id=user_id.strip(),
                query_text=query_text,
                limit=limit or self.config.max_memories,
                threshold=threshold or self.config.relevance_threshold
            )
            
            response = await self.provider.retrieve_memories(query)
            
            if response.success:
                self.log(f"Retrieved {len(response.memories)} memories for user {user_id}")
                return response.memories
            else:
                self.log(f"Failed to retrieve memories: {response.error}", "ERROR")
                return []
        except Exception as e:
            self.log(f"Error in get_relevant_memories: {e}", "ERROR")
            return []
    
    async def store_conversation_memory(
        self,
        user_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store a conversation memory.
        
        Args:
            user_id: User identifier
            content: Memory content
            metadata: Optional metadata
            
        Returns:
            bool: Success status
        """
        memory = MemoryRecord(
            user_id=user_id,
            content=content,
            metadata=metadata or {},
            source="conversation"
        )
        
        return await self.provider.store_memory(memory)
    
    async def track_conversation_and_store(
        self,
        user_id: str,
        messages: List[Dict[str, Any]]
    ) -> bool:
        """
        Track conversation turns and auto-store when threshold is met.
        
        Args:
            user_id: User identifier
            messages: List of conversation messages
            
        Returns:
            bool: True if interaction was stored, False otherwise
        """
        if not self.config.auto_store_enabled:
            return False
            
        # Track conversation count
        self.conversation_tracker[user_id] = self.conversation_tracker.get(user_id, 0) + 1
        
        # Check if threshold is met
        if self.conversation_tracker[user_id] >= self.config.auto_store_threshold:
            # Extract interaction
            user_message, assistant_response = self._extract_interaction(messages)
            
            if user_message and assistant_response:
                interaction = LearningInteraction(
                    user_id=user_id,
                    conversation_id=str(uuid.uuid4()),
                    user_message=user_message,
                    assistant_response=assistant_response,
                    timestamp=time.time(),
                    source="auto_store"
                )
                
                success = await self.provider.store_interaction(interaction)
                if success:
                    self.conversation_tracker[user_id] = 0  # Reset counter
                    return True
        
        return False
    
    def format_memories_for_injection(self, memories: List[MemoryRecord]) -> str:
        """
        Format memories for injection into conversation context.
        
        Args:
            memories: List of memory records
            
        Returns:
            Formatted memory context string
        """
        if not memories:
            return ""
            
        formatted = "## Relevant Context from Previous Conversations:\n\n"
        
        for i, memory in enumerate(memories, 1):
            relevance = memory.relevance_score or 0
            formatted += f"**Context {i}** (relevance: {relevance:.2f}):\n"
            formatted += f"{memory.content}\n\n"
            
        formatted += "---\n\n"
        return formatted
    
    def inject_memory_context(
        self, 
        body: Dict[str, Any], 
        memory_context: str
    ) -> Dict[str, Any]:
        """
        Inject memory context into conversation body.
        
        Args:
            body: Conversation body with messages
            memory_context: Formatted memory context
            
        Returns:
            Modified conversation body
        """
        messages = body.get("messages", [])
        
        if not messages or not memory_context:
            return body
            
        # Find the last user message and inject context
        for i in range(len(messages) - 1, -1, -1):
            if messages[i].get("role") == "user":
                original_content = messages[i].get("content", "")
                enhanced_content = f"{memory_context}{original_content}"
                messages[i]["content"] = enhanced_content
                break
                
        body["messages"] = messages
        return body
    
    async def health_check(self) -> bool:
        """
        Check if memory service is healthy.
        
        Returns:
            bool: Health status
        """
        return await self.provider.health_check()
    
    def _extract_interaction(self, messages: List[Dict[str, Any]]) -> tuple[str, str]:
        """Extract user and assistant messages from conversation."""
        user_message = ""
        assistant_response = ""
        
        for msg in reversed(messages):
            if msg.get("role") == "user" and not user_message:
                user_message = msg.get("content", "")
            elif msg.get("role") == "assistant" and not assistant_response:
                assistant_response = msg.get("content", "")
                
        return user_message, assistant_response
