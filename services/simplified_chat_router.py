"""
Simplified Enhanced Chat Router for Initial Testing
===================================================

A simplified version that focuses on intent classification and basic routing
without the full autonomous agent complexity.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

from services.llm_service import llm_service
from services.tool_service import tool_service
from core.unified_logging import get_logger, log_service_status


class ConversationIntent(Enum):
    """Different types of conversation intents."""
    SIMPLE_QUERY = "simple_query"
    TOOL_OPERATION = "tool_operation"
    COMPLEX_TASK = "complex_task"
    CONVERSATION = "conversation"


class ResponseStrategy(Enum):
    """Different response strategies."""
    DIRECT_RESPONSE = "direct"
    TOOL_ASSISTED = "tool_assisted"
    ENHANCED_RESPONSE = "enhanced"


class SimplifiedChatRouter:
    """Simplified chat router for initial testing."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # Simple intent patterns
        self.tool_keywords = [
            "weather", "time", "convert", "search", "calculate",
            "news", "exchange rate", "python", "wikipedia"
        ]
        
        self.complex_keywords = [
            "plan", "analyze", "research", "comprehensive", "detailed",
            "multi-step", "organize", "strategy", "compare"
        ]
    
    async def route_conversation(
        self, 
        user_message: str, 
        user_id: str, 
        conversation_history: List[Dict[str, str]] = None,
        session_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Route conversation using simplified decision-making."""
        try:
            # 1. Quick intent classification
            intent = self._classify_intent_simple(user_message)
            
            # 2. Determine strategy
            if intent == ConversationIntent.TOOL_OPERATION:
                return await self._handle_tool_assisted(user_message, user_id)
            elif intent == ConversationIntent.COMPLEX_TASK:
                return await self._handle_enhanced_response(user_message, user_id)
            else:
                return await self._handle_direct_response(user_message, user_id)
        
        except Exception as e:
            self.logger.error(f"Chat routing failed: {e}")
            return {
                "status": "error",
                "response": "I encountered an issue processing your request. Let me try a simpler approach.",
                "strategy_used": "fallback"
            }
    
    def _classify_intent_simple(self, message: str) -> ConversationIntent:
        """Simple intent classification based on keywords."""
        message_lower = message.lower()
        
        # Check for tool operations
        if any(keyword in message_lower for keyword in self.tool_keywords):
            return ConversationIntent.TOOL_OPERATION
        
        # Check for complex tasks
        if any(keyword in message_lower for keyword in self.complex_keywords):
            return ConversationIntent.COMPLEX_TASK
        
        # Default to simple query
        return ConversationIntent.SIMPLE_QUERY
    
    async def _handle_tool_assisted(
        self, 
        user_message: str, 
        user_id: str
    ) -> Dict[str, Any]:
        """Handle requests that need tool assistance."""
        
        log_service_status("SIMPLIFIED_ROUTER", "info", "Routing to tool-assisted response")
        
        # Try tool execution first
        tool_used, tool_response, tool_name, debug_info = tool_service.detect_and_execute_tool(
            user_message, user_id, f"simplified_router_{int(datetime.now().timestamp())}"
        )
        
        if tool_used:
            # Enhance tool response with LLM context
            enhancement_prompt = f"""
            A tool was used to help answer this user question:
            
            User Question: {user_message}
            Tool Used: {tool_name}
            Tool Response: {tool_response}
            
            Provide a natural, conversational response that incorporates the tool results.
            Make it helpful and contextual.
            """
            
            messages = [{"role": "user", "content": enhancement_prompt}]
            enhanced_response = await llm_service.call_llm(messages)
            
            return {
                "status": "success",
                "response": enhanced_response,
                "strategy_used": "tool_assisted",
                "tool_details": {
                    "tool_name": tool_name,
                    "tool_response": tool_response
                }
            }
        else:
            # Fallback to direct response if no tool matches
            return await self._handle_direct_response(user_message, user_id)
    
    async def _handle_enhanced_response(
        self, 
        user_message: str, 
        user_id: str
    ) -> Dict[str, Any]:
        """Handle complex requests with enhanced processing."""
        
        log_service_status("SIMPLIFIED_ROUTER", "info", "Routing to enhanced response")
        
        # Use LLM with enhanced prompting for complex tasks
        enhanced_prompt = f"""
        You are an AI assistant with enhanced reasoning capabilities. The user has asked a complex question that requires thoughtful analysis.
        
        User Question: {user_message}
        
        Please provide a comprehensive, well-structured response that:
        1. Addresses all aspects of the question
        2. Provides detailed analysis where appropriate
        3. Offers actionable insights or recommendations
        4. Uses clear organization and formatting
        
        Be thorough but also clear and helpful.
        """
        
        messages = [{"role": "user", "content": enhanced_prompt}]
        response = await llm_service.call_llm(messages)
        
        return {
            "status": "success",
            "response": response,
            "strategy_used": "enhanced_response"
        }
    
    async def _handle_direct_response(
        self, 
        user_message: str, 
        user_id: str
    ) -> Dict[str, Any]:
        """Handle simple requests with direct LLM response."""
        
        log_service_status("SIMPLIFIED_ROUTER", "info", "Routing to direct response")
        
        # Simple LLM call for straightforward questions
        messages = [{"role": "user", "content": user_message}]
        response = await llm_service.call_llm(messages)
        
        return {
            "status": "success",
            "response": response,
            "strategy_used": "direct_response"
        }


# Global simplified chat router instance
simplified_chat_router = SimplifiedChatRouter()


async def route_chat_with_autonomy(
    user_message: str,
    user_id: str,
    conversation_history: List[Dict[str, str]] = None,
    session_context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Simplified autonomous chat routing function."""
    return await simplified_chat_router.route_conversation(
        user_message, user_id, conversation_history, session_context
    )
