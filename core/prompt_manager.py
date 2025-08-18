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
    use_4b_model_optimization: bool = True
    model_context_limit: int = 4096
    optimization_mode: str = "4b_optimized"
    default_system_prompt: str = "You are a helpful AI assistant."


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
        self.config.use_4b_model_optimization = os.getenv(
            "USE_4B_MODEL_OPTIMIZATION", 
            str(self.config.use_4b_model_optimization)
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
        Get the default system prompt with environment override support.
        
        This replaces the DEFAULT_SYSTEM_PROMPT functionality from config_unified.py
        """
        cache_key = "default_prompt"
        if cache_key in self._prompt_cache:
            return self._prompt_cache[cache_key]
        
        # Try environment first
        env_prompt = os.getenv("DEFAULT_SYSTEM_PROMPT")
        if env_prompt:
            self.log(f"Using DEFAULT_SYSTEM_PROMPT from environment ({len(env_prompt)} chars)")
            self._prompt_cache[cache_key] = env_prompt
            return env_prompt
        
        # Use single unified prompt file optimized for 7B models
        prompt_file = "config/unified_prompt.json"
        
        try:
            if Path(prompt_file).exists():
                with open(prompt_file, "r", encoding="utf-8") as f:
                    prompt_data = json.load(f)
                    prompt = prompt_data.get("system_prompt", self.config.default_system_prompt)
                    self.log(f"Loaded default prompt from {prompt_file} ({len(prompt)} chars)")
                    self._prompt_cache[cache_key] = prompt
                    return prompt
        except Exception as e:
            self.log(f"Error loading default prompt from {prompt_file}: {e}", "ERROR")
        
        # No fallback - require configuration files
        raise ValueError(f"Could not load default prompt from any source. Please ensure {prompt_file} exists.")
    
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
        Get the enhanced prompt from the configuration file.
        
        This replaces get_base_persona_prompt() from processor.py
        """
        cache_key = "base_prompt"
        if cache_key in self._prompt_cache:
            return self._prompt_cache[cache_key]
        
        try:
            # Primary: Try to load unified small prompt (Orange Pi optimized)
            prompt_path = "/op./storage/openwebui/config/persona_unified_small.json"
            try:
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    prompt_data = json.load(f)
                    enhanced_prompt = prompt_data.get("system_prompt", "")
                    if enhanced_prompt:
                        self.log(f"Loaded unified small prompt ({len(enhanced_prompt)} chars) from {prompt_path}")
                        self._prompt_cache[cache_key] = enhanced_prompt
                        return enhanced_prompt
            except Exception as e:
                self.log(f"Could not load unified small prompt: {e}, trying alternative paths", "WARN")
            
            # Try alternative prompt paths
            alternative_paths = [
                "config/persona_new_user.json",
                "/op./storage/openwebui/config/persona_new_user.json",
                "./config/persona_new_user.json"
            ]
            
            for path in alternative_paths:
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        prompt_data = json.load(f)
                        enhanced_prompt = prompt_data.get("system_prompt", "")
                        if enhanced_prompt:
                            self.log(f"Loaded prompt from alternative path: {path}")
                            self._prompt_cache[cache_key] = enhanced_prompt
                            return enhanced_prompt
                except Exception:
                    continue
            
            # No fallback prompts - require configuration files
            raise ValueError("Could not load base prompt from any configured path. Please ensure prompt configuration files exist.")
            
        except Exception as e:
            self.log(f"Error loading prompt: {e}", "ERROR")
            raise ValueError(f"Could not load base prompt: {e}")

    def get_new_user_prompt(self) -> str:
        """
        Get the new user prompt without aggressive memory instructions.
        
        This replaces get_new_user_persona_prompt() from processor.py
        """
        cache_key = "new_user_prompt"
        if cache_key in self._prompt_cache:
            return self._prompt_cache[cache_key]
        
        try:
            # Try to load new user prompt file first
            prompt_path = "/op./storage/openwebui/config/persona_new_user.json"
            try:
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    prompt_data = json.load(f)
                    new_user_prompt = prompt_data.get("system_prompt", "")
                    if new_user_prompt:
                        self.log(f"Loaded new user prompt ({len(new_user_prompt)} chars) from {prompt_path}")
                        self._prompt_cache[cache_key] = new_user_prompt
                        return new_user_prompt
            except Exception as e:
                self.log(f"Could not load new user prompt file: {e}", "WARN")
            
            # No fallback prompts - require configuration files  
            raise ValueError("Could not load new user prompt from any configured path. Please ensure persona_new_user.json exists.")
            
        except Exception as e:
            self.log(f"Error loading new user prompt: {e}", "ERROR")
            raise ValueError(f"Could not load new user prompt: {e}")

    def get_4b_model_prompt(self) -> str:
        """
        Get optimized prompt for 4B language models.
        
        This replaces get_small_model_persona() from processor.py
        """
        cache_key = "4b_model_prompt"
        if cache_key in self._prompt_cache:
            return self._prompt_cache[cache_key]
        
        try:
            # Try to load 4B model optimized prompt
            prompt_paths = [
                "config/persona_4b_model.json",
                "/op./storage/openwebui/config/persona_4b_model.json",
                "./config/persona_4b_model.json"
            ]
            
            for path in prompt_paths:
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        prompt_data = json.load(f)
                        model_prompt = prompt_data.get("system_prompt", "")
                        if model_prompt:
                            self.log(f"Loaded 4B model prompt from: {path}")
                            self._prompt_cache[cache_key] = model_prompt
                            return model_prompt
                except Exception:
                    continue
            
            # No fallback prompts - require configuration files
            raise ValueError("Could not load 4B model prompt from any configured path. Please ensure persona_4b_model.json exists.")
            
        except Exception as e:
            self.log(f"Error loading 4B model prompt: {e}", "ERROR")
            raise ValueError(f"Could not load 4B model prompt: {e}")

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

    def build_context_with_persona(self, context: 'ChatContext', persona_type: str = "unified") -> Tuple[str, List[Dict[str, Any]]]:
        """
        Build LLM context with appropriate prompt and user information.
        
        This replaces the _build_llm_context functionality from chat_service.py
        
        Args:
            context: ChatContext object with user information
            persona_type: Type of prompt to use ("unified", "base", "new_user", "4b_model", "default")
            
        Returns:
            Tuple of (system_prompt, messages_list)
        """
        try:
            self.log(f"Building context with persona type: {persona_type}", "INFO")
            
            # Select appropriate prompt based on type
            if persona_type == "unified":
                system_prompt = self.get_unified_prompt()
                self.log("Using unified prompt for context building", "INFO")
            elif persona_type == "base":
                system_prompt = self.get_base_prompt()
                self.log("Using base prompt for context building", "INFO")
            elif persona_type == "new_user":
                system_prompt = self.get_new_user_prompt()
                self.log("Using new user prompt for context building", "INFO")
            elif persona_type == "4b_model":
                system_prompt = self.get_4b_model_prompt()
                self.log("Using 4B model prompt for context building", "INFO")
            elif persona_type == "default":
                system_prompt = self.get_default_prompt()
                self.log("Using default prompt for context building", "INFO")
            else:
                self.log(f"Unknown persona type '{persona_type}', using unified", "WARN")
                system_prompt = self.get_unified_prompt()
            
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


def get_4b_model_persona() -> str:
    """New function for 4B model prompt."""
    return prompt_manager.get_4b_model_prompt()


# Legacy constant for backwards compatibility
DEFAULT_SYSTEM_PROMPT = prompt_manager.get_default_prompt()

# Backwards compatibility for the old module name
persona_manager = prompt_manager
PersonaManager = PromptManager
PersonaConfig = PromptConfig
