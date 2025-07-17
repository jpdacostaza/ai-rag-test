"""
Configuration and environment variables for the FastAPI backend.
"""

import os
import logging
import platform
import sys
import time
from core.logging_config import log_service_status

# Application startup time
_APP_START_TIME = time.time()

# Model configuration - Using local Ollama models only (free)
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "llama3.2:3b")  # Free local model
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
USE_OLLAMA = os.getenv("USE_OLLAMA", "true").lower() == "true"  # Default to local Ollama

# OpenAI API configuration - Enhanced for memory/RAG testing
OPENAI_API_BASE_URL = os.getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_MAX_TOKENS = int(os.getenv("OPENAI_API_MAX_TOKENS", "8192"))  # Increased for better context handling
OPENAI_API_TIMEOUT = int(os.getenv("OPENAI_API_TIMEOUT", "180"))

# RAG Dual-Database Memory System Configuration
DEFAULT_CONTEXT_LENGTH = int(os.getenv("DEFAULT_CONTEXT_LENGTH", "8192"))  # Minimum for good RAG performance
MEMORY_CONTEXT_LENGTH = int(os.getenv("MEMORY_CONTEXT_LENGTH", "16384"))  # For memory-heavy operations

# RAG Memory System Settings - Dual Database (Redis + ChromaDB)
MEMORY_RETRIEVAL_THRESHOLD = float(os.getenv("MEMORY_RETRIEVAL_THRESHOLD", "0.0005"))  # Even lower for better recall
MEMORY_MAX_DOCUMENTS = int(os.getenv("MEMORY_MAX_DOCUMENTS", "50"))  # Increased from 30 to 50
MEMORY_HYBRID_SEARCH = os.getenv("MEMORY_HYBRID_SEARCH", "true").lower() == "true"
ENABLE_CROSS_SESSION_MEMORY = os.getenv("ENABLE_CROSS_SESSION_MEMORY", "true").lower() == "true"
PERSISTENT_USER_MEMORY = os.getenv("PERSISTENT_USER_MEMORY", "true").lower() == "true"

# RAG System Features
ENABLE_RAG_ARCHITECTURE = os.getenv("ENABLE_RAG_ARCHITECTURE", "true").lower() == "true"
ENABLE_DUAL_DATABASE = os.getenv("ENABLE_DUAL_DATABASE", "true").lower() == "true"
ENABLE_EXPLICIT_MEMORY = os.getenv("ENABLE_EXPLICIT_MEMORY", "true").lower() == "true"
ENABLE_IMPORTANCE_CLASSIFICATION = os.getenv("ENABLE_IMPORTANCE_CLASSIFICATION", "true").lower() == "true"
ENABLE_SEMANTIC_SEARCH = os.getenv("ENABLE_SEMANTIC_SEARCH", "true").lower() == "true"

# RAG Database Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
CHROMA_HOST = os.getenv("CHROMA_HOST", "chroma")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))

# RAG Memory API Configuration
MEMORY_API_HOST = os.getenv("MEMORY_API_HOST", "0.0.0.0")
MEMORY_API_PORT = int(os.getenv("MEMORY_API_PORT", "5001"))
MEMORY_API_VERSION = os.getenv("MEMORY_API_VERSION", "2.0.0")
MEMORY_API_TITLE = os.getenv("MEMORY_API_TITLE", "Enhanced Memory API with RAG")

# RAG Importance Classification
SHORT_TERM_IMPORTANCE_THRESHOLD = float(os.getenv("SHORT_TERM_IMPORTANCE_THRESHOLD", "0.4"))
LONG_TERM_IMPORTANCE_THRESHOLD = float(os.getenv("LONG_TERM_IMPORTANCE_THRESHOLD", "0.7"))

# RAG TTL Settings
SHORT_TERM_TTL = int(os.getenv("SHORT_TERM_TTL", "3600"))      # 1 hour
MEDIUM_TERM_TTL = int(os.getenv("MEDIUM_TERM_TTL", "43200"))   # 12 hours
LONG_TERM_TTL = int(os.getenv("LONG_TERM_TTL", "86400"))       # 24 hours

# RAG-Enhanced System Prompt for Memory Context
MEMORY_SYSTEM_PROMPT = os.getenv("MEMORY_SYSTEM_PROMPT", 
    "You are an AI assistant with access to a RAG dual-database memory system (Redis + ChromaDB). "
    "When relevant information from memory is available, acknowledge and use it naturally in your responses. "
    "If you have stored information about the user (name, workplace, preferences, etc.), reference it appropriately. "
    "Always validate that you're incorporating memory context when it's relevant to the conversation. "
    "For explicit memory commands like 'remember this', process and store the information with appropriate importance levels. "
    "Use semantic search to find relevant memories and provide context-aware responses based on stored information."
)

# LLM timeout settings
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "30"))  # Reduced from 180 to 30 seconds

# Performance timeout configurations (Added to fix high latency)
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))  # API request timeout
WEB_SEARCH_TIMEOUT = int(os.getenv("WEB_SEARCH_TIMEOUT", "10"))  # Web search timeout
CONNECTION_TIMEOUT = int(os.getenv("CONNECTION_TIMEOUT", "5"))  # Connection timeout
READ_TIMEOUT = int(os.getenv("READ_TIMEOUT", "25"))  # Read timeout
WRITE_TIMEOUT = int(os.getenv("WRITE_TIMEOUT", "5"))  # Write timeout

# Database configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))  # Fixed: ChromaDB runs on port 8000 in docker-compose
USE_HTTP_CHROMA = os.getenv("USE_HTTP_CHROMA", "true").lower() == "true"

# Memory API configuration
MEMORY_API_URL = os.getenv("MEMORY_API_URL", "http://backend-memory-api")
MEMORY_API_PORT = int(os.getenv("MEMORY_API_PORT", "8080"))
MEMORY_API_BASE_URL = f"{MEMORY_API_URL}:{MEMORY_API_PORT}"

# Embedding configuration - Optimized for memory/RAG performance
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")  # Community recommended: Better for RAG
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "ollama")  # Use ollama for nomic-embed-text
SENTENCE_TRANSFORMERS_HOME = os.getenv("SENTENCE_TRANSFORMERS_HOME", "./storage/models")
AUTO_PULL_MODELS = os.getenv("AUTO_PULL_MODELS", "true").lower() == "true"  # Automatically pull missing models

# RAG/Memory optimization settings - Optimized for cross-session memory
RAG_CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "1000"))  # Smaller chunks for better matching
RAG_CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "100"))  # Smaller overlap
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "30"))  # Increased from 20 to 30 for more results
RAG_MINIMUM_SCORE = float(os.getenv("RAG_MINIMUM_SCORE", "0.0005"))  # Even lower threshold
RAG_HYBRID_SEARCH = os.getenv("RAG_HYBRID_SEARCH", "true").lower() == "true"  # Enable hybrid search

# Cache configuration
CACHE_TTL = int(os.getenv("CACHE_TTL", "600"))  # 10 minutes default
MODEL_CACHE_TTL = int(os.getenv("MODEL_CACHE_TTL", "300"))  # 5 minutes default

# Session management
SESSION_CLEANUP_INTERVAL = int(os.getenv("SESSION_CLEANUP_INTERVAL", "3600"))  # 1 hour default

# Connection pool settings
CONNECTION_POOL_SIZE = int(os.getenv("CONNECTION_POOL_SIZE", "10"))
MAX_KEEPALIVE_CONNECTIONS = int(os.getenv("MAX_KEEPALIVE_CONNECTIONS", "5"))

# Persona optimization settings for different model sizes
USE_SMALL_MODEL_PERSONA = os.getenv("USE_SMALL_MODEL_PERSONA", "true").lower()  # auto, true, false
SMALL_MODEL_CONTEXT_LIMIT = int(os.getenv("SMALL_MODEL_CONTEXT_LIMIT", "2048"))  # Context limit for small models
PERSONA_OPTIMIZATION_MODE = os.getenv("PERSONA_OPTIMIZATION_MODE", "auto")  # auto, small, full


def get_app_start_time():
    """Get the application startup time."""
    return _APP_START_TIME


def log_system_info():
    """Log system information for startup diagnostics."""
    try:
        log_service_status("SYSTEM", "info", f"Python version: {sys.version.split()[0]}")
        log_service_status("SYSTEM", "info", f"Platform: {platform.system()} {platform.release()}")
        log_service_status("SYSTEM", "info", f"Working directory: {os.getcwd()}")
    except Exception as e:
        log_service_status("SYSTEM", "warning", f"Failed to log system info: {e}")


def log_environment_variables():
    """Log relevant environment variables for startup diagnostics."""
    try:
        env_vars_to_log = [
            "REDIS_HOST",
            "REDIS_PORT",
            "CHROMA_HOST",
            "CHROMA_PORT",
            "DEFAULT_MODEL",
            "EMBEDDING_MODEL",
            "EMBEDDING_PROVIDER",
            "SENTENCE_TRANSFORMERS_HOME",
            "OLLAMA_BASE_URL",
            "USE_OLLAMA",
            "USE_HTTP_CHROMA",
            "OPENAI_API_BASE_URL",
            "LLM_TIMEOUT",
        ]

        log_service_status("STARTUP", "info", "Environment configuration:")
        for var in env_vars_to_log:
            value = os.getenv(var, "Not set")
            # Mask sensitive values
            if "KEY" in var or "SECRET" in var:
                value = "***" if value != "Not set" else "Not set"
            log_service_status("CONFIG", "info", f"{var}={value}")
    except Exception as e:
        log_service_status("CONFIG", "warning", f"Failed to log environment: {e}")


# Persona configuration
def load_persona():
    """Load persona configuration from config/persona_enhanced.json."""
    try:
        import json

        with open("config/persona_enhanced.json", "r", encoding="utf-8") as f:
            persona = json.load(f)
            return persona.get("system_prompt", "You are a helpful AI assistant with access to tools and memory.")
    except Exception as e:
        # Log the error for debugging purposes
        from core.logging_config import log_service_status

        log_service_status("CONFIG", "warning", f"Failed to load config/persona_enhanced.json: {e}")
        return "You are a helpful AI assistant with access to tools and memory."


# Default system prompt
DEFAULT_SYSTEM_PROMPT = load_persona()

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
