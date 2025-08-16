"""
Enhanced Chat Router with Autonomous Decision Making
====================================================

This module extends the chat system with autonomous reasoning capabilities:
- Intent classification and routing
- Multi-step conversation planning
- Context-aware response strategies
-        # 2. Search memory for relevant context
        relevant_memories = await self.memory_api.search_memories(
            user_id=user_id,
            query=user_message,
            limit=3,
            threshold=0.7
        )
        
        # Handle case where search_memories returns None
        if relevant_memories is None:
            relevant_memories = []c tool selection and orchestration
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

from services.llm_service import llm_service
from services.tool_service import tool_service
from services.autonomous_agent import autonomous_agent
from memory.api.enhanced_memory_api import EnhancedMemoryAPI
from core.unified_logging import get_logger, log_service_status


class ConversationIntent(Enum):
    """Different types of conversation intents."""
    SIMPLE_QUERY = "simple_query"           # Direct question/answer
    COMPLEX_TASK = "complex_task"           # Multi-step task requiring planning
    INFORMATION_GATHERING = "info_gathering" # Research and data collection
    PROBLEM_SOLVING = "problem_solving"     # Analytical reasoning
    TOOL_OPERATION = "tool_operation"       # Specific tool usage
    CREATIVE_TASK = "creative_task"         # Content generation, brainstorming
    CONVERSATION = "conversation"           # General conversation
    AUTONOMOUS_REQUEST = "autonomous_req"   # Request requiring autonomous planning


class ResponseStrategy(Enum):
    """Different response strategies."""
    DIRECT_RESPONSE = "direct"              # Immediate LLM response
    TOOL_ASSISTED = "tool_assisted"         # Single tool + LLM response
    AUTONOMOUS_EXECUTION = "autonomous"     # Full autonomous planning/execution
    HYBRID_APPROACH = "hybrid"              # Combination of approaches


class EnhancedChatRouter:
    """Routes conversations with autonomous decision-making capabilities."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.memory_api = EnhancedMemoryAPI()
        
        # Intent classification patterns
        self.intent_patterns = {
            ConversationIntent.AUTONOMOUS_REQUEST: [
                "plan", "organize", "research", "analyze", "investigate",
                "find out", "help me with", "work on", "complete",
                "multi-step", "complex", "detailed analysis"
            ],
            ConversationIntent.TOOL_OPERATION: [
                "weather", "time", "convert", "search", "calculate",
                "news", "exchange rate", "python", "wikipedia"
            ],
            ConversationIntent.PROBLEM_SOLVING: [
                "solve", "figure out", "troubleshoot", "debug",
                "optimize", "improve", "fix", "resolve"
            ],
            ConversationIntent.INFORMATION_GATHERING: [
                "tell me about", "what is", "explain", "describe",
                "compare", "differences", "overview", "summary"
            ]
        }
    
    async def route_conversation(
        self, 
        user_message: str, 
        user_id: str, 
        conversation_history: List[Dict[str, str]] = None,
        session_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Route conversation using autonomous decision-making."""
        try:
            # 1. Classify intent and determine complexity
            intent, complexity_score = await self._classify_intent(user_message, conversation_history)
            
            # 2. Determine optimal response strategy
            strategy = await self._determine_strategy(intent, complexity_score, user_message)
            
            # 3. Execute based on strategy
            if strategy == ResponseStrategy.AUTONOMOUS_EXECUTION:
                return await self._handle_autonomous_execution(user_message, user_id, session_context)
            elif strategy == ResponseStrategy.TOOL_ASSISTED:
                return await self._handle_tool_assisted(user_message, user_id, session_context)
            elif strategy == ResponseStrategy.HYBRID_APPROACH:
                return await self._handle_hybrid_approach(user_message, user_id, session_context)
            else:
                return await self._handle_direct_response(user_message, user_id, session_context)
        
        except Exception as e:
            self.logger.error(f"Chat routing failed: {e}")
            return {
                "status": "error",
                "response": "I encountered an issue processing your request. Let me try a simpler approach.",
                "strategy_used": "fallback"
            }
    
    async def _classify_intent(
        self, 
        user_message: str, 
        conversation_history: List[Dict[str, str]] = None
    ) -> Tuple[ConversationIntent, float]:
        """Classify user intent and assess complexity."""
        
        # Quick pattern matching for obvious cases
        message_lower = user_message.lower()
        
        for intent, keywords in self.intent_patterns.items():
            if any(keyword in message_lower for keyword in keywords):
                complexity = self._assess_complexity(user_message, intent)
                return intent, complexity
        
        # Use LLM for more sophisticated classification
        classification_prompt = f"""
        Analyze this user message and classify the intent:
        
        Message: {user_message}
        
        Conversation History: {json.dumps(conversation_history or [], indent=2)}
        
        Classify the intent as one of:
        1. simple_query - Direct question needing simple answer
        2. complex_task - Multi-step task requiring planning
        3. info_gathering - Research or data collection needed
        4. problem_solving - Analytical reasoning required
        5. tool_operation - Specific tool usage needed
        6. autonomous_req - Requires autonomous planning and execution
        7. conversation - General conversation
        
        Also assess complexity on scale 1-10 (10 = very complex).
        
        Respond with JSON: {{"intent": "intent_name", "complexity": 5, "reasoning": "explanation"}}
        """
        
        messages = [{"role": "user", "content": classification_prompt}]
        response = await llm_service.call_llm(messages)
        
        try:
            result = json.loads(response)
            intent_str = result.get("intent", "simple_query")
            complexity = float(result.get("complexity", 5))
            
            # Convert string to enum
            intent = ConversationIntent(intent_str)
            
            log_service_status("CHAT_ROUTER", "info", 
                             f"Classified intent: {intent.value}, complexity: {complexity}")
            
            return intent, complexity
            
        except (json.JSONDecodeError, ValueError):
            # Fallback classification
            return ConversationIntent.SIMPLE_QUERY, 3.0
    
    def _assess_complexity(self, message: str, intent: ConversationIntent) -> float:
        """Assess complexity score for a message."""
        base_complexity = {
            ConversationIntent.SIMPLE_QUERY: 2.0,
            ConversationIntent.TOOL_OPERATION: 3.0,
            ConversationIntent.INFORMATION_GATHERING: 4.0,
            ConversationIntent.PROBLEM_SOLVING: 6.0,
            ConversationIntent.COMPLEX_TASK: 7.0,
            ConversationIntent.AUTONOMOUS_REQUEST: 8.0,
            ConversationIntent.CONVERSATION: 2.0,
            ConversationIntent.CREATIVE_TASK: 5.0
        }.get(intent, 5.0)
        
        # Adjust based on message characteristics
        words = len(message.split())
        if words > 50:
            base_complexity += 1.0
        elif words < 10:
            base_complexity -= 0.5
        
        # Check for complexity indicators
        complexity_indicators = [
            "multiple", "several", "various", "complex", "detailed",
            "comprehensive", "thorough", "in-depth", "step-by-step",
            "analyze", "compare", "evaluate", "research"
        ]
        
        message_lower = message.lower()
        indicator_count = sum(1 for indicator in complexity_indicators 
                            if indicator in message_lower)
        base_complexity += indicator_count * 0.5
        
        return min(max(base_complexity, 1.0), 10.0)
    
    async def _determine_strategy(
        self, 
        intent: ConversationIntent, 
        complexity_score: float, 
        user_message: str
    ) -> ResponseStrategy:
        """Determine optimal response strategy."""
        
        # Strategy decision matrix
        if complexity_score >= 7.0 or intent == ConversationIntent.AUTONOMOUS_REQUEST:
            return ResponseStrategy.AUTONOMOUS_EXECUTION
        
        elif intent == ConversationIntent.TOOL_OPERATION:
            return ResponseStrategy.TOOL_ASSISTED
        
        elif complexity_score >= 5.0 and intent in [
            ConversationIntent.COMPLEX_TASK,
            ConversationIntent.PROBLEM_SOLVING,
            ConversationIntent.INFORMATION_GATHERING
        ]:
            return ResponseStrategy.HYBRID_APPROACH
        
        else:
            return ResponseStrategy.DIRECT_RESPONSE
    
    async def _handle_autonomous_execution(
        self, 
        user_message: str, 
        user_id: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle requests requiring autonomous planning and execution."""
        
        log_service_status("CHAT_ROUTER", "info", "Routing to autonomous execution")
        
        # Use autonomous agent for complex multi-step tasks
        autonomous_result = await autonomous_agent.process_autonomous_request(
            user_message, user_id, context
        )
        
        return {
            "status": "success",
            "response": autonomous_result.get("summary", "Task completed autonomously."),
            "strategy_used": "autonomous_execution",
            "autonomous_details": autonomous_result,
            "execution_metadata": {
                "plan_confidence": autonomous_result.get("plan_confidence", 0.0),
                "tasks_executed": autonomous_result.get("tasks_executed", 0)
            }
        }
    
    async def _handle_tool_assisted(
        self, 
        user_message: str, 
        user_id: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle requests that need specific tool assistance."""
        
        log_service_status("CHAT_ROUTER", "info", "Routing to tool-assisted response")
        
        # Try tool execution first
        tool_used, tool_response, tool_name, debug_info = tool_service.detect_and_execute_tool(
            user_message, user_id, f"chat_router_{int(datetime.now().timestamp())}"
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
                    "tool_response": tool_response,
                    "debug_info": debug_info
                }
            }
        else:
            # Fallback to direct response if no tool matches
            return await self._handle_direct_response(user_message, user_id, context)
    
    async def _handle_hybrid_approach(
        self, 
        user_message: str, 
        user_id: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle requests using a hybrid approach (tools + reasoning + memory)."""
        
        log_service_status("CHAT_ROUTER", "info", "Routing to hybrid approach")
        
        # 1. Search memory for relevant context
        relevant_memories = await self.memory_api.search_memories(
            user_id=user_id,
            query=user_message,
            limit=3,
            threshold=0.7
        )
        
        # 2. Try tool execution
        tool_used, tool_response, tool_name, debug_info = tool_service.detect_and_execute_tool(
            user_message, user_id, f"hybrid_{int(datetime.now().timestamp())}"
        )
        
        # 3. Combine everything for comprehensive response
        hybrid_prompt = f"""
        Provide a comprehensive response to this user question using available information:
        
        User Question: {user_message}
        
        Relevant Memory Context:
        {json.dumps([mem.get('content', '') for mem in relevant_memories], indent=2)}
        
        Tool Information:
        Tool Used: {tool_name if tool_used else 'None'}
        Tool Response: {tool_response if tool_used else 'No tool response'}
        
        Provide a thorough, well-reasoned response that:
        1. Addresses the user's question directly
        2. Incorporates relevant context from memory
        3. Uses tool results if available
        4. Provides additional insights or analysis as appropriate
        """
        
        messages = [{"role": "user", "content": hybrid_prompt}]
        comprehensive_response = await llm_service.call_llm(messages)
        
        return {
            "status": "success",
            "response": comprehensive_response,
            "strategy_used": "hybrid_approach",
            "components_used": {
                "memory_results": len(relevant_memories),
                "tool_used": tool_used,
                "tool_name": tool_name if tool_used else None
            }
        }
    
    async def _handle_direct_response(
        self, 
        user_message: str, 
        user_id: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle simple requests with direct LLM response."""
        
        log_service_status("CHAT_ROUTER", "info", "Routing to direct response")
        
        # Simple LLM call for straightforward questions
        messages = [{"role": "user", "content": user_message}]
        response = await llm_service.call_llm(messages)
        
        return {
            "status": "success",
            "response": response,
            "strategy_used": "direct_response"
        }


# Global enhanced chat router instance
enhanced_chat_router = EnhancedChatRouter()


async def route_chat_with_autonomy(
    user_message: str,
    user_id: str,
    conversation_history: List[Dict[str, str]] = None,
    session_context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Convenience function for autonomous chat routing."""
    return await enhanced_chat_router.route_conversation(
        user_message, user_id, conversation_history, session_context
    )
