"""
Configuration and environment variables for the FastAPI backend.
"""

import os
import logging
import platform
import sys
import time
from human_logging import log_service_status

# Application startup time
_APP_START_TIME = time.time()

# Model configuration
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "llama3.2:3b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
USE_OLLAMA = os.getenv("USE_OLLAMA", "true").lower() == "true"

# OpenAI API configuration
OPENAI_API_BASE_URL = os.getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_MAX_TOKENS = int(os.getenv("OPENAI_API_MAX_TOKENS", "4096"))
OPENAI_API_TIMEOUT = int(os.getenv("OPENAI_API_TIMEOUT", "180"))

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
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8002"))  # Fixed: ChromaDB runs on port 8002 in docker-compose
USE_HTTP_CHROMA = os.getenv("USE_HTTP_CHROMA", "true").lower() == "true"

# Embedding configuration
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/e5-small-v2")  # Default: Use e5-small-v2 from HuggingFace
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "huggingface")  # Options: "huggingface", "ollama"
SENTENCE_TRANSFORMERS_HOME = os.getenv("SENTENCE_TRANSFORMERS_HOME", "./storage/models")
AUTO_PULL_MODELS = os.getenv("AUTO_PULL_MODELS", "true").lower() == "true"  # Automatically pull missing models

# Cache configuration
CACHE_TTL = int(os.getenv("CACHE_TTL", "600"))  # 10 minutes default
MODEL_CACHE_TTL = int(os.getenv("MODEL_CACHE_TTL", "300"))  # 5 minutes default

# Session management
SESSION_CLEANUP_INTERVAL = int(os.getenv("SESSION_CLEANUP_INTERVAL", "3600"))  # 1 hour default

# Connection pool settings
CONNECTION_POOL_SIZE = int(os.getenv("CONNECTION_POOL_SIZE", "10"))
MAX_KEEPALIVE_CONNECTIONS = int(os.getenv("MAX_KEEPALIVE_CONNECTIONS", "5"))


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
    """Load persona configuration from config/persona.json."""
    try:
        import json

        with open("config/persona.json", "r", encoding="utf-8") as f:
            persona = json.load(f)
            return persona.get("system_prompt", "You are a helpful AI assistant with access to tools and memory.")
    except Exception as e:
        # Log the error for debugging purposes
        from human_logging import log_service_status

        log_service_status("CONFIG", "warning", f"Failed to load config/persona.json: {e}")
        return "You are a helpful AI assistant with access to tools and memory."


# Default system prompt
DEFAULT_SYSTEM_PROMPT = load_persona()
