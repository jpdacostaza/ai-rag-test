"""
Memory System Configuration
===========================

Configuration classes and valves for the memory pipeline.
"""

from typing import List
from pydantic import BaseModel


class MemoryValves(BaseModel):
    """Configuration valves for the memory pipeline."""
    
    # Fix for Pydantic protected namespace warning
    model_config = {"protected_namespaces": ()}
    
    # Pipeline Requirements - which pipelines this filter connects to
    # Use ["*"] to connect to all pipelines
    pipelines: List[str] = ["*"]
    
    # Priority level determines execution order (lower = higher priority)
    priority: int = 0
    
    # API Configuration
    backend_url: str = "http://memory_api:8080"
    
    # Memory Settings
    enable_memory: bool = True
    max_memories: int = 100  # Maximum memories to retrieve per query for comprehensive context
    memory_threshold: float = 0.001  # Lower threshold to capture more relevant memories
    quality_threshold: int = 3  # Minimum quality score for memory injection
    
    # User Authentication
    require_authenticated_user: bool = True
    enforce_user_session_consistency: bool = True
    
    # API Timeouts
    api_timeout: int = 10  # seconds
    retry_attempts: int = 3
    
    # Debug Settings
    debug_mode: bool = True
    log_memory_injection: bool = True
    log_user_authentication: bool = True
    
    # Performance Settings
    batch_size: int = 50  # Number of memories to process in batches
    cache_duration: int = 300  # seconds to cache user memories
    
    # Persona Integration
    integrate_persona: bool = True  # Integrate with persona_enhanced.json configuration
    persona_priority: str = "memory_first"  # memory_first, balanced, persona_first
    
    # Model Compatibility
    model_agnostic: bool = True
    universal_memory_format: bool = True
    adaptive_prompting: bool = True
    
    # Safety and Security
    sanitize_inputs: bool = True
    validate_user_permissions: bool = True
    prevent_memory_leakage: bool = True
