"""
Unified Prompt Management System
===============================

Centralized management for all prompt handling across the application.
Consolidates functionality from multiple files into a single, maintainable system.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass
import logging

if TYPE_CHECKING:
    from services.chat_service import ChatContext
    # from services.user_profile_manager import user_profile_manager  # Optional import

logger = logging.getLogger(__name__)


@dataclass
class PromptConfig:
    """Configuration for prompt management."""
    use_model_optimization: bool = True
    model_context_limit: int = 2048
    optimization_mode: str = "optimized"


class PromptManager:
    """
    Unified manager for all prompt operations.
    
    This class consolidates all prompt functionality that was previously
    scattered across multiple files, providing a single source of truth for:
    - Loading prompts from configuration files
    - Managing different prompt types (unified, base, new user, small model)
    - Building context with appropriate prompts
    - Caching for performance optimization
    """
    
    def __init__(self, debug: bool = True):
        """Initialize the PromptManager with optional debug logging."""
        self.debug = debug
        self.config = PromptConfig()
        self._prompt_cache: Dict[str, str] = {}
        self._load_environment_config()
    
    def _load_environment_config(self):
        """Load configuration from environment variables."""
        self.config.use_model_optimization = os.getenv(
            "USE_MODEL_OPTIMIZATION", 
            str(self.config.use_model_optimization)
        ).lower() == "true"
        
        self.config.model_context_limit = int(os.getenv(
            "MODEL_CONTEXT_LIMIT", 
            str(self.config.model_context_limit)
        ))
        
        self.config.optimization_mode = os.getenv(
            "OPTIMIZATION_MODE", 
            self.config.optimization_mode
        )
    
    def log(self, message: str, level: str = "INFO"):
        """Log messages with consistent formatting."""
        if self.debug:
            print(f"[PROMPT MANAGER {level}] {message}")
            # Also use standard logging for Docker visibility
            if level == "ERROR":
                logger.error(f"[PROMPT MANAGER] {message}")
            elif level == "WARN":
                logger.warning(f"[PROMPT MANAGER] {message}")
            else:
                logger.info(f"[PROMPT MANAGER] {message}")
    
    def get_default_prompt(self) -> str:
        """
        Get prompt from unified_prompt.json - no fallbacks, single source of truth.
        """
        return self.get_unified_prompt()
    
    def get_unified_prompt(self) -> str:
        """
        Get the unified prompt that works for all model sizes and scenarios.
        
        This replaces get_unified_persona_prompt() from processor.py
        """
        cache_key = "unified_prompt"
        if cache_key in self._prompt_cache:
            self.log(f"Using cached unified prompt ({len(self._prompt_cache[cache_key])} chars)", "INFO")
            return self._prompt_cache[cache_key]
        
        try:
            # Use only the single unified prompt configuration file
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'unified_prompt.json')
            
            self.log(f"Loading unified prompt from: {config_path}", "INFO")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                prompt_data = json.load(f)
                unified_prompt = prompt_data.get("system_prompt", "")
                version = prompt_data.get("version", "unknown")
                
                if unified_prompt:
                    self.log(f"Unified prompt loaded successfully!", "INFO")
                    self.log(f"   Version: {version}", "INFO")
                    self.log(f"   Character count: {len(unified_prompt)}", "INFO")
                    self.log(f"   Estimated tokens: {len(unified_prompt) // 4}", "INFO")
                    self.log(f"   Context usage (2K): {(len(unified_prompt) // 4) / 2048 * 100:.1f}%", "INFO")
                    self.log(f"   File path: {config_path}", "INFO")
                    
                    # Check for key features
                    features = []
                    if 'real-time' in unified_prompt.lower():
                        features.append("Real-time Access")
                    if 'memory' in unified_prompt.lower():
                        features.append("Memory System")
                    if 'web search' in unified_prompt.lower():
                        features.append("Web Search")
                    if 'weather' in unified_prompt.lower():
                        features.append("Weather Tools")
                    if 'function' in unified_prompt.lower():
                        features.append("Function Calling")
                    
                    if features:
                        self.log(f"   Features enabled: {', '.join(features)}", "INFO")
                    
                    self._prompt_cache[cache_key] = unified_prompt
                    return unified_prompt
            
            # No fallback prompts - require configuration files
            error_msg = "Could not load unified prompt from configuration file. Please ensure unified_prompt.json exists."
            self.log(error_msg, "ERROR")
            raise ValueError(error_msg)
            
        except Exception as e:
            self.log(f"Error loading unified prompt: {e}", "ERROR")
            raise ValueError(f"Could not load unified prompt: {e}")
    
    def get_base_prompt(self) -> str:
        """
        Get the base prompt - now always returns unified prompt for consistency.
        """
        # For consistency, always use unified prompt
        return self.get_unified_prompt()

    def get_new_user_prompt(self) -> str:
        """
        Get the new user prompt - now always uses unified prompt for consistency.
        """
        # For consistency, always use unified prompt
        return self.get_unified_prompt()

    def get_model_prompt(self) -> str:
        """
        Get model optimized prompt - now always uses unified prompt for consistency.
        """
        # For consistency, always use unified prompt
        return self.get_unified_prompt()

    def get_4b_model_prompt(self) -> str:
        """
        Backward compatibility - Get optimized prompt for 4B language models.
        """
        # For consistency, always use unified prompt
        return self.get_unified_prompt()

    def load_from_config(self, config_path: str) -> str:
        """
        Load prompt from a specific configuration file.
        
        Args:
            config_path: Path to the prompt configuration file
            
        Returns:
            The system prompt from the configuration file
        """
        try:
            if Path(config_path).exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    prompt_data = json.load(f)
                    prompt = prompt_data.get("system_prompt", "")
                    if prompt:
                        self.log(f"Loaded prompt from {config_path} ({len(prompt)} chars)")
                        return prompt
            
            self.log(f"Configuration file not found: {config_path}", "WARN")
            return ""
            
        except Exception as e:
            self.log(f"Error loading prompt from {config_path}: {e}", "ERROR")
            return ""

    def build_context_with_prompt(self, context: 'ChatContext') -> Tuple[str, List[Dict[str, Any]]]:
        """
        Build LLM context with unified prompt and user information.
        
        Simplified version that always uses unified_prompt.json as single source of truth.
        
        Args:
            context: ChatContext object with user information
            
        Returns:
            Tuple of (system_prompt, messages_list)
        """
        try:
            self.log("Building context with unified prompt", "INFO")
            
            # Always use unified prompt as single source of truth
            system_prompt = self.get_unified_prompt()
            self.log("Using unified prompt for context building", "INFO")
            
            self.log(f"Selected prompt length: {len(system_prompt)} chars (~{len(system_prompt)//4} tokens)", "INFO")
            
            # Add user profile information if available
            if hasattr(context, 'user_id') and context.user_id:
                try:
                    # Import here to avoid circular imports - check if module exists
                    try:
                        from services.user_profile_manager import user_profile_manager
                        user_context = user_profile_manager.build_context_for_llm(context.user_id)
                        if user_context:
                            system_prompt += f"\n\nUser Profile Information: {user_context}"
                            self.log(f"Added user context for {context.user_id}")
                    except ImportError:
                        self.log("User profile manager not available", "WARN")
                except Exception as e:
                    self.log(f"Error loading user context: {e}", "WARN")
            
            # Build conversation context
            full_context = ""
            
            # Add memories if available
            if hasattr(context, 'memories') and context.memories:
                memory_text = "\n".join([str(m) for m in context.memories])
                full_context += f"Relevant memories:\n{memory_text}\n\n"
                self.log(f"Added {len(context.memories)} memories to context", "INFO")
            
            # Add recent conversation history if available
            if hasattr(context, 'history') and context.history:
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
                    self.log(f"Added conversation history ({len(context.history)} entries)", "INFO")
            
            # Build messages
            messages = [{"role": "system", "content": system_prompt}]
            
            if full_context:
                messages.append({"role": "system", "content": full_context})
                self.log(f"Added context message ({len(full_context)} chars)", "INFO")
            
            if hasattr(context, 'message') and context.message:
                messages.append({"role": "user", "content": context.message})
                self.log(f"Added user message: {context.message[:100]}{'...' if len(context.message) > 100 else ''}", "INFO")
            
            total_context_size = sum(len(msg.get("content", "")) for msg in messages)
            self.log(f"Total context built: {len(messages)} messages, {total_context_size} chars (~{total_context_size//4} tokens)", "INFO")
            
            return system_prompt, messages
            
        except Exception as e:
            self.log(f"Error building context with prompt: {e}", "ERROR")
            # Re-raise the error instead of using fallback
            raise

    def clear_cache(self):
        """Clear the prompt cache to force reloading from files."""
        self._prompt_cache.clear()
        self.log("Prompt cache cleared")

    def get_cache_status(self) -> Dict[str, int]:
        """Get information about cached prompts."""
        return {key: len(value) for key, value in self._prompt_cache.items()}
    
    # Backward compatibility methods for old persona system
    def build_context_with_persona(self, context: 'ChatContext', persona_type: str = "unified") -> Tuple[str, List[Dict[str, Any]]]:
        """Backward compatibility method - now always uses unified prompt."""
        self.log(f"Legacy persona method called with type '{persona_type}' - using unified prompt", "WARN")
        return self.build_context_with_prompt(context)


# Global instance for easy access
prompt_manager = PromptManager()


# Backwards compatibility functions for existing code
def get_unified_persona_prompt() -> str:
    """Backwards compatibility wrapper."""
    return prompt_manager.get_unified_prompt()


def get_base_persona_prompt() -> str:
    """Backwards compatibility wrapper."""
    return prompt_manager.get_base_prompt()


def get_new_user_persona_prompt() -> str:
    """Backwards compatibility wrapper."""
    return prompt_manager.get_new_user_prompt()


def get_small_model_persona() -> str:
    """Backwards compatibility wrapper - now returns 4B model prompt."""
    return prompt_manager.get_4b_model_prompt()


def get_model_persona() -> str:
    """New function for model prompt."""
    return prompt_manager.get_model_prompt()

def get_4b_model_persona() -> str:
    """Backward compatibility function for 4B model prompt."""
    return prompt_manager.get_4b_model_prompt()


# Create singleton instance
prompt_manager = PromptManager()

# Legacy constant for backwards compatibility - lazy load to avoid circular imports
def get_default_system_prompt():
    """Get default system prompt with lazy loading."""
    try:
        return prompt_manager.get_default_prompt()
    except Exception:
        return "Using fallback prompt - check unified_prompt.json"

DEFAULT_SYSTEM_PROMPT = get_default_system_prompt

# Backwards compatibility for the old module name
persona_manager = prompt_manager
PersonaManager = PromptManager
PersonaConfig = PromptConfig
