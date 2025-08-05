"""
Unified Configuration Management for OpenWebUI Enhanced Memory System
====================================================================

This module consolidates all configuration across the backend, replacing:
- config.py (main backend config)
- config_minimal.py (pipeline config)
- core/config.py (centralized config)
- pipelines/config.py (pipeline specific)

Usage:
    from config.config_unified import Config
    
    # Get singleton instance
    config = Config.get_instance()
    
    # Access configuration sections
    model_settings = config.model
    memory_settings = config.memory
    database_settings = config.database
"""

import os
import json
import logging
import platform
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field
from enum import Enum

# Application startup time
_APP_START_TIME = time.time()

class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

class ModelProvider(Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    HUGGINGFACE = "huggingface"

class EmbeddingProvider(Enum):
    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"
    SENTENCE_TRANSFORMERS = "sentence_transformers"

@dataclass
class ModelConfig:
    """Model and LLM configuration."""
    # Primary model settings
    default_model: str = "qwen3:4b"  # Upgraded to Qwen3 4B parameter model
    provider: ModelProvider = ModelProvider.OLLAMA
    
    # Ollama settings
    ollama_base_url: str = "http://ollama:11434"
    use_ollama: bool = True
    
    # OpenAI settings
    openai_api_base_url: str = "https://api.openai.com/v1"
    openai_api_key: Optional[str] = None
    openai_max_tokens: int = 8192
    openai_timeout: int = 180
    
    # Context and performance
    default_context_length: int = 8192
    memory_context_length: int = 16384
    llm_timeout: int = 30
    
    # Model caching
    model_cache_ttl: int = 300
    auto_pull_models: bool = True
    
    def __post_init__(self):
        # Load from environment
        self.default_model = os.getenv("DEFAULT_MODEL", self.default_model)
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", self.ollama_base_url)
        self.use_ollama = os.getenv("USE_OLLAMA", str(self.use_ollama)).lower() == "true"
        
        self.openai_api_base_url = os.getenv("OPENAI_API_BASE_URL", self.openai_api_base_url)
        self.openai_api_key = os.getenv("OPENAI_API_KEY", self.openai_api_key)
        self.openai_max_tokens = int(os.getenv("OPENAI_API_MAX_TOKENS", str(self.openai_max_tokens)))
        self.openai_timeout = int(os.getenv("OPENAI_API_TIMEOUT", str(self.openai_timeout)))
        
        self.default_context_length = int(os.getenv("DEFAULT_CONTEXT_LENGTH", str(self.default_context_length)))
        self.memory_context_length = int(os.getenv("MEMORY_CONTEXT_LENGTH", str(self.memory_context_length)))
        self.llm_timeout = int(os.getenv("LLM_TIMEOUT", str(self.llm_timeout)))
        
        self.model_cache_ttl = int(os.getenv("MODEL_CACHE_TTL", str(self.model_cache_ttl)))
        self.auto_pull_models = os.getenv("AUTO_PULL_MODELS", str(self.auto_pull_models)).lower() == "true"

@dataclass
class MemoryConfig:
    """Memory system configuration."""
    # Memory API settings
    api_url: str = "http://backend-memory-api:8080"
    api_port: int = 8080
    timeout: float = 10.0
    
    # Memory behavior - OPTIMIZED for better retention
    max_memories: int = 5
    max_documents: int = 50
    retrieval_threshold: float = 0.0001  # Lowered for more inclusive retrieval
    auto_store_enabled: bool = True
    auto_store_threshold: int = 3
    hybrid_search: bool = True
    
    # Cross-session persistence
    enable_cross_session: bool = True
    persistent_user_memory: bool = True
    
    # System prompt
    system_prompt: str = (
        "You are an AI assistant with access to conversation memory and context. "
        "When relevant information from memory is available, acknowledge and use it naturally in your responses. "
        "If you have stored information about the user (name, workplace, preferences, etc.), reference it appropriately. "
        "Always validate that you're incorporating memory context when it's relevant to the conversation."
    )
    
    # Pipeline settings
    max_context_length: int = 4000
    persona_optimization: bool = True
    model_size_threshold: int = 4000000000  # 4B parameters
    
    def __post_init__(self):
        # Load from environment
        self.api_url = os.getenv("MEMORY_API_URL", self.api_url)
        self.api_port = int(os.getenv("MEMORY_API_PORT", str(self.api_port)))
        self.timeout = float(os.getenv("MEMORY_TIMEOUT", str(self.timeout)))
        
        self.max_memories = int(os.getenv("MAX_MEMORIES", str(self.max_memories)))
        self.max_documents = int(os.getenv("MEMORY_MAX_DOCUMENTS", str(self.max_documents)))
        self.retrieval_threshold = float(os.getenv("MEMORY_RETRIEVAL_THRESHOLD", str(self.retrieval_threshold)))
        self.auto_store_enabled = os.getenv("MEMORY_AUTO_STORE", str(self.auto_store_enabled)).lower() == "true"
        self.auto_store_threshold = int(os.getenv("MEMORY_AUTO_STORE_THRESHOLD", str(self.auto_store_threshold)))
        self.hybrid_search = os.getenv("MEMORY_HYBRID_SEARCH", str(self.hybrid_search)).lower() == "true"
        
        self.enable_cross_session = os.getenv("ENABLE_CROSS_SESSION_MEMORY", str(self.enable_cross_session)).lower() == "true"
        self.persistent_user_memory = os.getenv("PERSISTENT_USER_MEMORY", str(self.persistent_user_memory)).lower() == "true"
        
        self.system_prompt = os.getenv("MEMORY_SYSTEM_PROMPT", self.system_prompt)

@dataclass
class DatabaseConfig:
    """Database configuration for Redis, ChromaDB, etc."""
    # Redis settings
    redis_host: str = "backend-redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # ChromaDB settings
    chroma_host: str = "backend-chroma"
    chroma_port: int = 8000
    use_http_chroma: bool = True
    
    # Embedding settings - ARM64 optimized for Orange Pi 5 Plus
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"  # 45MB, 2.5x faster than nomic-embed-text
    embedding_provider: EmbeddingProvider = EmbeddingProvider.HUGGINGFACE  # Direct HuggingFace for speed
    sentence_transformers_home: str = "./storage/sentence_transformers"
    
    def __post_init__(self):
        # Load from environment
        self.redis_host = os.getenv("REDIS_HOST", self.redis_host)
        self.redis_port = int(os.getenv("REDIS_PORT", str(self.redis_port)))
        self.redis_db = int(os.getenv("REDIS_DB", str(self.redis_db)))
        
        # Handle Redis password: convert empty string to None (Redis auth issue)
        redis_password_env = os.getenv("REDIS_PASSWORD", self.redis_password)
        self.redis_password = None if redis_password_env == "" else redis_password_env
        
        self.chroma_host = os.getenv("CHROMA_HOST", self.chroma_host)
        self.chroma_port = int(os.getenv("CHROMA_PORT", str(self.chroma_port)))
        self.use_http_chroma = os.getenv("USE_HTTP_CHROMA", str(self.use_http_chroma)).lower() == "true"
        
        self.embedding_model = os.getenv("EMBEDDING_MODEL", self.embedding_model)
        embedding_provider_str = os.getenv("EMBEDDING_PROVIDER", self.embedding_provider.value)
        self.embedding_provider = EmbeddingProvider(embedding_provider_str)
        self.sentence_transformers_home = os.getenv("SENTENCE_TRANSFORMERS_HOME", self.sentence_transformers_home)

@dataclass
class ServiceConfig:
    """Service endpoints and networking configuration."""
    # Backend API
    backend_host: str = "0.0.0.0"
    backend_port: int = 3000
    backend_url: str = "http://backend:3000"
    
    # Memory API
    memory_api_host: str = "0.0.0.0"
    memory_api_port: int = 5001
    memory_api_url: str = "http://memory-api:5001"
    
    # OpenWebUI
    openwebui_url: str = "http://openwebui:8080"
    pipelines_url: str = "http://pipelines:9099"
    
    # External services
    web_search_timeout: int = 10
    api_timeout: int = 30
    
    def __post_init__(self):
        # Load from environment
        self.backend_host = os.getenv("BACKEND_HOST", self.backend_host)
        self.backend_port = int(os.getenv("BACKEND_PORT", str(self.backend_port)))
        self.backend_url = os.getenv("BACKEND_URL", self.backend_url)
        
        self.memory_api_host = os.getenv("MEMORY_API_HOST", self.memory_api_host)
        self.memory_api_port = int(os.getenv("MEMORY_API_PORT", str(self.memory_api_port)))
        self.memory_api_url = os.getenv("MEMORY_API_URL", self.memory_api_url)
        
        self.openwebui_url = os.getenv("OPENWEBUI_URL", self.openwebui_url)
        self.pipelines_url = os.getenv("PIPELINES_URL", self.pipelines_url)
        
        self.web_search_timeout = int(os.getenv("WEB_SEARCH_TIMEOUT", str(self.web_search_timeout)))
        self.api_timeout = int(os.getenv("API_TIMEOUT", str(self.api_timeout)))

@dataclass
class SecurityConfig:
    """Security and authentication configuration."""
    # API Security
    api_key: Optional[str] = None
    jwt_secret: Optional[str] = None
    enable_debug: bool = False
    enable_rate_limiting: bool = True
    max_requests_per_minute: int = 60
    
    # CORS settings
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    cors_methods: List[str] = field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE"])
    cors_headers: List[str] = field(default_factory=lambda: ["*"])
    
    def __post_init__(self):
        # Load from environment
        self.api_key = os.getenv("API_KEY", self.api_key)
        self.jwt_secret = os.getenv("JWT_SECRET", self.jwt_secret)
        self.enable_debug = os.getenv("ENABLE_DEBUG", str(self.enable_debug)).lower() == "true"
        self.enable_rate_limiting = os.getenv("ENABLE_RATE_LIMITING", str(self.enable_rate_limiting)).lower() == "true"
        self.max_requests_per_minute = int(os.getenv("MAX_REQUESTS_PER_MINUTE", str(self.max_requests_per_minute)))
        
        # Parse CORS settings from environment
        cors_origins_env = os.getenv("CORS_ORIGINS")
        if cors_origins_env:
            self.cors_origins = [origin.strip() for origin in cors_origins_env.split(",")]

@dataclass
class PersonaConfig:
    """Persona and system prompt configuration."""
    # Persona settings
    use_small_model_persona: bool = True
    small_model_context_limit: int = 2048
    persona_optimization_mode: str = "auto"
    
    # System prompts
    default_system_prompt: str = "You are a helpful AI assistant."
    
    def __post_init__(self):
        # Load from environment
        self.use_small_model_persona = os.getenv("USE_SMALL_MODEL_PERSONA", str(self.use_small_model_persona)).lower() == "true"
        self.small_model_context_limit = int(os.getenv("SMALL_MODEL_CONTEXT_LIMIT", str(self.small_model_context_limit)))
        self.persona_optimization_mode = os.getenv("PERSONA_OPTIMIZATION_MODE", self.persona_optimization_mode)
        
        # Load system prompt from file or environment
        self.default_system_prompt = self._load_system_prompt()
    
    def _load_system_prompt(self) -> str:
        """Load system prompt from config file or environment."""
        # Try environment first
        env_prompt = os.getenv("DEFAULT_SYSTEM_PROMPT")
        if env_prompt:
            return env_prompt
        
        # Try loading from persona files - Orange Pi optimized (only keep essential ones)
        persona_files = [
            "config/persona_unified_small.json",    # Primary: Orange Pi <7B models, anti-fabrication
            "config/persona_new_user.json"          # Fallback: new user handling
        ]
        
        for persona_file in persona_files:
            try:
                if Path(persona_file).exists():
                    with open(persona_file, "r", encoding="utf-8") as f:
                        persona_data = json.load(f)
                        return persona_data.get("system_prompt", self.default_system_prompt)
            except Exception:
                continue
        
        return self.default_system_prompt

@dataclass
class LoggingConfig:
    """Logging configuration."""
    # Logging settings
    log_level: LogLevel = LogLevel.INFO
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: Optional[str] = None
    console_logging: bool = True
    file_logging: bool = False
    
    # Log files
    logs_dir: str = "./storage/logs"
    max_log_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    
    # Zero-conf settings for Orange Pi
    orange_pi_mode: bool = True
    lightweight_logging: bool = True
    
    def __post_init__(self):
        # Load from environment
        log_level_str = os.getenv("LOG_LEVEL", self.log_level.value)
        try:
            self.log_level = LogLevel(log_level_str.lower())
        except ValueError:
            self.log_level = LogLevel.INFO
        
        self.log_format = os.getenv("LOG_FORMAT", self.log_format)
        self.log_file = os.getenv("LOG_FILE", self.log_file)
        self.console_logging = os.getenv("CONSOLE_LOGGING", str(self.console_logging)).lower() == "true"
        self.file_logging = os.getenv("FILE_LOGGING", str(self.file_logging)).lower() == "true"
        
        self.logs_dir = os.getenv("LOGS_DIR", self.logs_dir)
        self.max_log_size = int(os.getenv("MAX_LOG_SIZE", str(self.max_log_size)))
        self.backup_count = int(os.getenv("LOG_BACKUP_COUNT", str(self.backup_count)))
        
        # Orange Pi optimizations
        self.orange_pi_mode = os.getenv("ORANGE_PI_MODE", str(self.orange_pi_mode)).lower() == "true"
        self.lightweight_logging = os.getenv("LIGHTWEIGHT_LOGGING", str(self.lightweight_logging)).lower() == "true"
        
        # Create logs directory if it doesn't exist
        if self.file_logging:
            Path(self.logs_dir).mkdir(parents=True, exist_ok=True)

class Config:
    """Unified configuration manager (Singleton)."""
    
    _instance: Optional['Config'] = None
    _initialized: bool = False
    
    def __init__(self):
        if Config._initialized:
            return
        
        # Initialize all configuration sections
        self.model = ModelConfig()
        self.memory = MemoryConfig()
        self.database = DatabaseConfig()
        self.service = ServiceConfig()
        self.security = SecurityConfig()
        self.persona = PersonaConfig()
        self.logging = LoggingConfig()
        
        # Create aliases for backward compatibility
        self.api = self.service  # API config is the same as service config
        
        # App metadata
        self.app_start_time = _APP_START_TIME
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        
        Config._initialized = True
    
    @classmethod
    def get_instance(cls) -> 'Config':
        """Get singleton instance of Config."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def get_app_start_time(self) -> float:
        """Get application start time."""
        return self.app_start_time
    
    def log_system_info(self) -> Dict[str, Any]:
        """Get system information for logging."""
        return {
            "python_version": sys.version,
            "platform": platform.platform(),
            "environment": self.environment,
            "debug_mode": self.debug,
            "model_provider": self.model.provider.value,
            "memory_enabled": True,
            "start_time": self.app_start_time
        }
    
    def log_environment_variables(self) -> Dict[str, str]:
        """Get relevant environment variables for logging (sanitized)."""
        sensitive_keys = ["API_KEY", "JWT_SECRET", "PASSWORD", "TOKEN"]
        env_vars = {}
        
        for key, value in os.environ.items():
            if any(sensitive in key.upper() for sensitive in sensitive_keys):
                env_vars[key] = "***REDACTED***"
            elif key.startswith(("DEFAULT_", "OLLAMA_", "REDIS_", "CHROMA_", "MEMORY_", "OPENAI_")):
                env_vars[key] = value
        
        return env_vars
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "model": self.model.__dict__,
            "memory": self.memory.__dict__,
            "database": self.database.__dict__,
            "service": self.service.__dict__,
            "security": {k: v for k, v in self.security.__dict__.items() if "secret" not in k.lower()},
            "persona": self.persona.__dict__,
            "environment": self.environment,
            "debug": self.debug
        }

# Legacy compatibility functions and variables
def get_config() -> Dict[str, Any]:
    """Legacy compatibility function for pipelines."""
    config = Config.get_instance()
    return {
        'backend_url': config.service.backend_url,
        'redis_host': config.database.redis_host,
        'redis_port': config.database.redis_port,
        'chroma_host': config.database.chroma_host,
        'chroma_port': config.database.chroma_port,
        'memory_api_url': config.memory.api_url,
        'authentication': {
            'enabled': True,
            'token_required': False
        },
        'memory_settings': {
            'max_context_length': config.memory.max_context_length,
            'persona_optimization': config.memory.persona_optimization,
            'model_size_threshold': config.memory.model_size_threshold
        }
    }

def get_app_start_time() -> float:
    """Legacy compatibility function."""
    return Config.get_instance().get_app_start_time()

def log_system_info():
    """Legacy compatibility function."""
    return Config.get_instance().log_system_info()

def log_environment_variables():
    """Legacy compatibility function."""
    return Config.get_instance().log_environment_variables()

# Create singleton instance
_config = Config.get_instance()

# Legacy compatibility exports
DEFAULT_MODEL = _config.model.default_model
OLLAMA_BASE_URL = _config.model.ollama_base_url
USE_OLLAMA = _config.model.use_ollama
DEFAULT_SYSTEM_PROMPT = _config.persona.default_system_prompt

# OpenAI settings
OPENAI_API_BASE_URL = _config.model.openai_api_base_url
OPENAI_API_KEY = _config.model.openai_api_key
OPENAI_API_MAX_TOKENS = _config.model.openai_max_tokens
OPENAI_API_TIMEOUT = _config.model.openai_timeout

# Context settings
DEFAULT_CONTEXT_LENGTH = _config.model.default_context_length
MEMORY_CONTEXT_LENGTH = _config.model.memory_context_length

# Memory settings
MEMORY_RETRIEVAL_THRESHOLD = _config.memory.retrieval_threshold
MEMORY_MAX_DOCUMENTS = _config.memory.max_documents
MEMORY_HYBRID_SEARCH = _config.memory.hybrid_search
ENABLE_CROSS_SESSION_MEMORY = _config.memory.enable_cross_session
PERSISTENT_USER_MEMORY = _config.memory.persistent_user_memory
MEMORY_SYSTEM_PROMPT = _config.memory.system_prompt

# Timeout settings
LLM_TIMEOUT = _config.model.llm_timeout
API_TIMEOUT = _config.service.api_timeout
WEB_SEARCH_TIMEOUT = _config.service.web_search_timeout
CONNECTION_TIMEOUT = 5  # Default connection timeout
READ_TIMEOUT = 30  # Default read timeout  
WRITE_TIMEOUT = 30  # Default write timeout
CONNECTION_POOL_SIZE = 10  # Default connection pool size
MAX_KEEPALIVE_CONNECTIONS = 5  # Default max keepalive connections

# Database settings
REDIS_HOST = _config.database.redis_host
REDIS_PORT = _config.database.redis_port
REDIS_DB = _config.database.redis_db
CHROMA_HOST = _config.database.chroma_host
CHROMA_PORT = _config.database.chroma_port
USE_HTTP_CHROMA = _config.database.use_http_chroma

# Embedding settings
EMBEDDING_MODEL = _config.database.embedding_model
EMBEDDING_PROVIDER = _config.database.embedding_provider.value
SENTENCE_TRANSFORMERS_HOME = _config.database.sentence_transformers_home
AUTO_PULL_MODELS = _config.model.auto_pull_models

# Model caching
MODEL_CACHE_TTL = _config.model.model_cache_ttl

# Persona settings
USE_SMALL_MODEL_PERSONA = _config.persona.use_small_model_persona
SMALL_MODEL_CONTEXT_LIMIT = _config.persona.small_model_context_limit
PERSONA_OPTIMIZATION_MODE = _config.persona.persona_optimization_mode

# Memory API settings
MEMORY_API_URL = _config.memory.api_url
MEMORY_API_PORT = _config.memory.api_port
MEMORY_API_BASE_URL = f"{_config.memory.api_url}:{_config.memory.api_port}"

# Security settings
API_KEY = _config.security.api_key
JWT_SECRET = _config.security.jwt_secret
