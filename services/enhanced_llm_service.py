"""
Enhanced LLM Service with Advanced Prompt Caching
================================================

Provides LLM services with sophisticated caching strategies:
- Anthropic prompt caching with cache_control markers
- OpenAI compatible caching
- Multi-provider fallback with caching
- Cost optimization through intelligent caching
- Metrics and performance monitoring

Based on industry best practices from Anthropic and OpenAI documentation.
"""

import asyncio
import json
import os
from typing import Dict, List, Any, Optional, AsyncGenerator
import httpx

from core.unified_logging import get_logger, log_service_status
from services.prompt_cache_service import prompt_cache_service
from services.llm_service import LLMService

logger = get_logger(__name__)


class EnhancedLLMService(LLMService):
    """
    Enhanced LLM service with advanced prompt caching capabilities.
    
    Extends the base LLM service with:
    - Anthropic-style prompt caching
    - OpenAI compatible caching  
    - Provider-specific optimizations
    - Cost tracking and metrics
    """
    
    def __init__(self):
        """Initialize enhanced LLM service with caching."""
        super().__init__()
        self.anthropic_client = None
        self.openai_client = None
        self._init_api_clients()
        
    def _init_api_clients(self):
        """Initialize API clients for different providers."""
        # Initialize Anthropic client if API key available
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            try:
                import anthropic
                self.anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
                log_service_status("ENHANCED_LLM", "ready", "Anthropic client initialized")
            except ImportError:
                log_service_status("ENHANCED_LLM", "warning", "Anthropic package not available")
        
        # Initialize OpenAI client if API key available  
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                import openai
                self.openai_client = openai.AsyncOpenAI(api_key=openai_key)
                log_service_status("ENHANCED_LLM", "ready", "OpenAI client initialized")
            except ImportError:
                log_service_status("ENHANCED_LLM", "warning", "OpenAI package not available")

    async def call_anthropic_with_caching(
        self,
        messages: List[Dict[str, Any]],
        model: str = "claude-3-5-sonnet-20241022",
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 1024,
        enable_caching: bool = True
    ) -> str:
        """
        Call Anthropic API with advanced prompt caching.
        
        Args:
            messages: Conversation messages
            model: Anthropic model name
            system_prompt: System prompt to cache
            tools: Tool definitions to cache
            max_tokens: Maximum response tokens
            enable_caching: Whether to use prompt caching
        """
        if not self.anthropic_client:
            raise ValueError("Anthropic client not initialized. Please set ANTHROPIC_API_KEY.")
        
        try:
            # Check response cache first
            cache_key = self._generate_cache_key(messages, model)
            if enable_caching:
                cached_response = await self.cache_service.get_cached_prompt(
                    cache_key, model, "anthropic"
                )
                if cached_response:
                    log_service_status("ENHANCED_LLM", "info", f"🚀 [ANTHROPIC] Cache hit for {model} ({cached_response.token_count} tokens saved)")
                    return cached_response.content

            # Prepare request with caching
            request_params = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": messages,
            }
            
            # Add system prompt with caching
            if system_prompt and enable_caching:
                request_params["system"] = [{
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral", "ttl": "1h"}
                }]
            elif system_prompt:
                request_params["system"] = [{"type": "text", "text": system_prompt}]
            
            # Add tools with caching
            if tools and enable_caching:
                enhanced_tools = []
                for i, tool in enumerate(tools):
                    enhanced_tool = tool.copy()
                    # Cache the last tool definition
                    if i == len(tools) - 1:
                        enhanced_tool["cache_control"] = {"type": "ephemeral", "ttl": "1h"}
                    enhanced_tools.append(enhanced_tool)
                request_params["tools"] = enhanced_tools
            elif tools:
                request_params["tools"] = tools
            
            # Add beta header for prompt caching
            if enable_caching:
                extra_headers = {"anthropic-beta": "prompt-caching-2024-07-31"}
                request_params["extra_headers"] = extra_headers
            
            # Make API call
            response = await asyncio.to_thread(
                self.anthropic_client.messages.create,
                **request_params
            )
            
            # Extract response content
            response_text = ""
            for content in response.content:
                if hasattr(content, 'text'):
                    response_text += content.text
            
            # Log cache performance metrics
            if hasattr(response, 'usage'):
                usage = response.usage
                if hasattr(usage, 'cache_creation_input_tokens'):
                    log_service_status("ENHANCED_LLM", "info", 
                        f"🔧 [ANTHROPIC] Cache creation tokens: {usage.cache_creation_input_tokens}")
                if hasattr(usage, 'cache_read_input_tokens'):
                    log_service_status("ENHANCED_LLM", "info", 
                        f"⚡ [ANTHROPIC] Cache read tokens: {usage.cache_read_input_tokens}")
            
            # Cache the response
            if enable_caching and response_text:
                await self.cache_service.cache_prompt(
                    cache_key, response_text, model, "anthropic", 1800  # 30 min TTL
                )
                log_service_status("ENHANCED_LLM", "info", f"💾 [ANTHROPIC] Response cached for future use")
            
            return response_text
            
        except Exception as e:
            log_service_status("ENHANCED_LLM", "error", f"Anthropic API call failed: {e}")
            raise

    async def call_openai_with_caching(
        self,
        messages: List[Dict[str, Any]],
        model: str = "gpt-4",
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 1024,
        enable_caching: bool = True
    ) -> str:
        """
        Call OpenAI API with prompt caching optimization.
        
        Args:
            messages: Conversation messages
            model: OpenAI model name
            tools: Tool definitions
            max_tokens: Maximum response tokens
            enable_caching: Whether to use caching optimizations
        """
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized. Please set OPENAI_API_KEY.")
        
        try:
            # Check response cache first
            cache_key = self._generate_cache_key(messages, model)
            if enable_caching:
                cached_response = await self.cache_service.get_cached_prompt(
                    cache_key, model, "openai"
                )
                if cached_response:
                    log_service_status("ENHANCED_LLM", "info", f"🚀 [OPENAI] Cache hit for {model} ({cached_response.token_count} tokens saved)")
                    return cached_response.content

            # Prepare request
            request_params = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
            }
            
            # Add tools if provided
            if tools:
                request_params["tools"] = tools
            
            # Make API call
            response = await self.openai_client.chat.completions.create(**request_params)
            
            # Extract response content
            response_text = ""
            if response.choices:
                choice = response.choices[0]
                if choice.message and choice.message.content:
                    response_text = choice.message.content
            
            # Cache the response
            if enable_caching and response_text:
                await self.cache_service.cache_prompt(
                    cache_key, response_text, model, "openai", 1800  # 30 min TTL
                )
                log_service_status("ENHANCED_LLM", "info", f"💾 [OPENAI] Response cached for future use")
            
            return response_text
            
        except Exception as e:
            log_service_status("ENHANCED_LLM", "error", f"OpenAI API call failed: {e}")
            raise

    async def call_llm_with_fallback(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        preferred_provider: str = "ollama",
        enable_caching: bool = True
    ) -> str:
        """
        Call LLM with intelligent provider fallback and caching.
        
        Args:
            messages: Conversation messages
            system_prompt: System prompt
            tools: Tool definitions
            preferred_provider: Preferred LLM provider (ollama, anthropic, openai)
            enable_caching: Whether to use prompt caching
        """
        # Add system prompt to messages if provided
        if system_prompt:
            enhanced_messages = [{"role": "system", "content": system_prompt}] + messages
        else:
            enhanced_messages = messages
        
        # Try preferred provider first
        if preferred_provider == "anthropic" and self.anthropic_client:
            try:
                return await self.call_anthropic_with_caching(
                    messages, 
                    system_prompt=system_prompt,
                    tools=tools,
                    enable_caching=enable_caching
                )
            except Exception as e:
                log_service_status("ENHANCED_LLM", "warning", f"Anthropic fallback failed: {e}")
        
        elif preferred_provider == "openai" and self.openai_client:
            try:
                return await self.call_openai_with_caching(
                    enhanced_messages,
                    tools=tools,
                    enable_caching=enable_caching
                )
            except Exception as e:
                log_service_status("ENHANCED_LLM", "warning", f"OpenAI fallback failed: {e}")
        
        # Fallback to Ollama (always available)
        try:
            return await self.call_llm(
                enhanced_messages,
                enable_caching=enable_caching,
                cache_type="fallback"
            )
        except Exception as e:
            log_service_status("ENHANCED_LLM", "error", f"All providers failed: {e}")
            raise

    async def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics across all providers."""
        base_stats = self.cache_service.get_cache_stats()
        
        # Add provider-specific metrics
        base_stats.update({
            "providers": {
                "anthropic_available": self.anthropic_client is not None,
                "openai_available": self.openai_client is not None,
                "ollama_available": True,  # Always available through base service
            },
            "optimization_recommendations": self._get_optimization_recommendations()
        })
        
        return base_stats
    
    def _get_optimization_recommendations(self) -> List[str]:
        """Generate cache optimization recommendations."""
        recommendations = []
        stats = self.cache_service.get_cache_stats()
        
        if stats["hit_rate"] < 30:
            recommendations.append("Consider increasing cache TTL for better hit rates")
        
        if stats["memory_cache_size"] > 800:
            recommendations.append("Memory cache is near capacity, consider cleanup")
        
        if not self.anthropic_client and not self.openai_client:
            recommendations.append("Consider adding Anthropic/OpenAI API keys for advanced caching")
        
        return recommendations

    async def optimize_prompts_for_caching(
        self, 
        messages: List[Dict[str, Any]],
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Optimize prompt structure for maximum caching efficiency.
        
        Returns optimized prompt structure with cache recommendations.
        """
        optimization_report = {
            "original_structure": {
                "message_count": len(messages),
                "has_system_prompt": system_prompt is not None,
                "estimated_tokens": sum(len(str(msg.get('content', ''))) // 4 for msg in messages)
            },
            "optimizations_applied": [],
            "cache_strategy": "multi_tier",
            "estimated_cache_benefit": "medium"
        }
        
        # Extract stable content for caching
        system_content = []
        dynamic_content = []
        
        for msg in messages:
            if msg.get('role') == 'system' or (system_prompt and msg == messages[0]):
                system_content.append(msg)
                optimization_report["optimizations_applied"].append("system_prompt_caching")
            else:
                dynamic_content.append(msg)
        
        # Create optimized structure
        optimized_request = self.cache_service.enhance_prompt_with_caching(
            dynamic_content,
            system_prompt=system_prompt
        )
        
        # Calculate cache benefit
        total_tokens = optimization_report["original_structure"]["estimated_tokens"]
        if total_tokens > 1000:
            optimization_report["estimated_cache_benefit"] = "high"
        elif total_tokens > 500:
            optimization_report["estimated_cache_benefit"] = "medium"
        else:
            optimization_report["estimated_cache_benefit"] = "low"
        
        return {
            "optimized_request": optimized_request,
            "optimization_report": optimization_report
        }


# Global instance
enhanced_llm_service = EnhancedLLMService()


# Convenience functions for backwards compatibility
async def call_llm_cached(
    messages: List[Dict[str, Any]], 
    model: str = "", 
    enable_caching: bool = True
) -> str:
    """Convenience function for cached LLM calls."""
    return await enhanced_llm_service.call_llm(
        messages, model=model, enable_caching=enable_caching
    )


async def call_anthropic_cached(
    messages: List[Dict[str, Any]],
    system_prompt: Optional[str] = None,
    model: str = "claude-3-5-sonnet-20241022"
) -> str:
    """Convenience function for cached Anthropic calls."""
    return await enhanced_llm_service.call_anthropic_with_caching(
        messages, model=model, system_prompt=system_prompt
    )
