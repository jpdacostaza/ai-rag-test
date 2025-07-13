"""
⚠️  DEPRECATED: This configuration file has been replaced by config_unified.py
==============================================================================

This file is kept for backward compatibility but should not be modified.
All new configuration should be done through config_unified.py.

Migration date: 2025-07-13T11:24:41.509170
Replacement: config_unified.py

To complete the migration:
1. Verify all imports have been updated to use config_unified
2. Test the application thoroughly
3. Remove this file when confident the migration is complete
"""

# Original configuration content follows:
# (kept for reference during migration period)

"""
Minimal configuration for pipelines container.
"""

import os

# Model configuration
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "llama3.2:3b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
USE_OLLAMA = os.getenv("USE_OLLAMA", "true").lower() == "true"

# Memory/RAG settings
DEFAULT_CONTEXT_LENGTH = int(os.getenv("DEFAULT_CONTEXT_LENGTH", "8192"))
MEMORY_CONTEXT_LENGTH = int(os.getenv("MEMORY_CONTEXT_LENGTH", "16384"))
MEMORY_RETRIEVAL_THRESHOLD = float(os.getenv("MEMORY_RETRIEVAL_THRESHOLD", "0.0005"))
MEMORY_MAX_DOCUMENTS = int(os.getenv("MEMORY_MAX_DOCUMENTS", "50"))
MEMORY_HYBRID_SEARCH = os.getenv("MEMORY_HYBRID_SEARCH", "true").lower() == "true"
ENABLE_CROSS_SESSION_MEMORY = os.getenv("ENABLE_CROSS_SESSION_MEMORY", "true").lower() == "true"
PERSISTENT_USER_MEMORY = os.getenv("PERSISTENT_USER_MEMORY", "true").lower() == "true"
MEMORY_SYSTEM_PROMPT = os.getenv("MEMORY_SYSTEM_PROMPT", 
    "You are an AI assistant with access to conversation memory and context.")

# Performance settings
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "30"))
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))
WEB_SEARCH_TIMEOUT = int(os.getenv("WEB_SEARCH_TIMEOUT", "10"))

# Persona settings
USE_SMALL_MODEL_PERSONA = os.getenv("USE_SMALL_MODEL_PERSONA", "true").lower()
SMALL_MODEL_CONTEXT_LIMIT = int(os.getenv("SMALL_MODEL_CONTEXT_LIMIT", "2048"))
PERSONA_OPTIMIZATION_MODE = os.getenv("PERSONA_OPTIMIZATION_MODE", "auto")

# Database configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
USE_HTTP_CHROMA = os.getenv("USE_HTTP_CHROMA", "true").lower() == "true"

# Memory API configuration
MEMORY_API_URL = os.getenv("MEMORY_API_URL", "http://backend-memory-api")
MEMORY_API_PORT = int(os.getenv("MEMORY_API_PORT", "8080"))
MEMORY_API_BASE_URL = f"{MEMORY_API_URL}:{MEMORY_API_PORT}"

# Embedding configuration
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "ollama")

# Default system prompt
DEFAULT_SYSTEM_PROMPT = "You are a helpful AI assistant with access to tools and memory."

def get_config():
    """
    Get configuration dictionary for pipeline access.
    Returns a dictionary with all relevant configuration values.
    """
    return {
        # Model configuration
        "DEFAULT_MODEL": DEFAULT_MODEL,
        "OLLAMA_BASE_URL": OLLAMA_BASE_URL,
        "USE_OLLAMA": USE_OLLAMA,
        
        # Memory/RAG settings
        "DEFAULT_CONTEXT_LENGTH": DEFAULT_CONTEXT_LENGTH,
        "MEMORY_CONTEXT_LENGTH": MEMORY_CONTEXT_LENGTH,
        "MEMORY_RETRIEVAL_THRESHOLD": MEMORY_RETRIEVAL_THRESHOLD,
        "MEMORY_MAX_DOCUMENTS": MEMORY_MAX_DOCUMENTS,
        "MEMORY_HYBRID_SEARCH": MEMORY_HYBRID_SEARCH,
        "ENABLE_CROSS_SESSION_MEMORY": ENABLE_CROSS_SESSION_MEMORY,
        "PERSISTENT_USER_MEMORY": PERSISTENT_USER_MEMORY,
        "MEMORY_SYSTEM_PROMPT": MEMORY_SYSTEM_PROMPT,
        
        # Performance settings
        "LLM_TIMEOUT": LLM_TIMEOUT,
        "API_TIMEOUT": API_TIMEOUT,
        "WEB_SEARCH_TIMEOUT": WEB_SEARCH_TIMEOUT,
        
        # Persona settings
        "USE_SMALL_MODEL_PERSONA": USE_SMALL_MODEL_PERSONA,
        "SMALL_MODEL_CONTEXT_LIMIT": SMALL_MODEL_CONTEXT_LIMIT,
        "PERSONA_OPTIMIZATION_MODE": PERSONA_OPTIMIZATION_MODE,
        
        # Database settings
        "REDIS_HOST": REDIS_HOST,
        "REDIS_PORT": REDIS_PORT,
        "REDIS_DB": REDIS_DB,
        "CHROMA_HOST": CHROMA_HOST,
        "CHROMA_PORT": CHROMA_PORT,
        "USE_HTTP_CHROMA": USE_HTTP_CHROMA,
        
        # Memory API settings
        "MEMORY_API_URL": MEMORY_API_URL,
        "MEMORY_API_PORT": MEMORY_API_PORT,
        "MEMORY_API_BASE_URL": MEMORY_API_BASE_URL,
        
        # Embedding settings
        "EMBEDDING_MODEL": EMBEDDING_MODEL,
        "EMBEDDING_PROVIDER": EMBEDDING_PROVIDER,
        
        # System settings
        "DEFAULT_SYSTEM_PROMPT": DEFAULT_SYSTEM_PROMPT,
    }

# Legacy variables for pipeline compatibility
API_KEY = os.getenv("PIPELINES_API_KEY", "0p3n-w3bu!")
PIPELINES_DIR = os.getenv("PIPELINES_DIR", "./pipelines")
