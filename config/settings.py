"""
Centralized Configuration Management
===================================

This module provides centralized configuration management using Pydantic BaseSettings,
replacing scattered config imports with unified, environment-aware configuration.
"""

import os
from typing import Optional, Dict, Any, List
try:
    from pydantic_settings import BaseSettings
    from pydantic import Field, validator
except ImportError:
    from pydantic import BaseSettings, Field, validator
from pathlib import Path


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    # Redis settings
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    redis_db: int = Field(default=0, description="Redis database number")
    redis_max_connections: int = Field(default=100, description="Maximum Redis connections")
    
    # ChromaDB settings
    chroma_host: str = Field(default="localhost", description="ChromaDB host")
    chroma_port: int = Field(default=8000, description="ChromaDB port")
    chroma_collection_name: str = Field(default="llm_memory", description="ChromaDB collection name")
    
    # Vector embedding settings
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", description="Embedding model name")
    embedding_device: str = Field(default="cpu", description="Embedding device (cpu/gpu)")
    
    model_config = {"env_prefix": "DB_", "case_sensitive": False}


class LLMSettings(BaseSettings):
    """LLM configuration settings."""
    
    # Ollama settings
    use_ollama: bool = Field(default=True, description="Use Ollama as primary LLM")
    ollama_url: str = Field(default="http://localhost:11434", description="Ollama base URL")
    ollama_model: str = Field(default="llama3.2:3b", description="Default Ollama model")
    ollama_timeout: int = Field(default=300, description="Ollama request timeout")
    
    # OpenAI settings (fallback)
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    openai_model: str = Field(default="gpt-3.5-turbo", description="Default OpenAI model")
    openai_max_tokens: int = Field(default=2000, description="OpenAI max tokens")
    
    # System prompt
    default_system_prompt: str = Field(
        default="You are a helpful assistant. Provide clear, accurate, and concise responses.",
        description="Default system prompt"
    )
    
    model_config = {"env_prefix": "LLM_", "case_sensitive": False}


class APISettings(BaseSettings):
    """API configuration settings."""
    
    # Server settings
    host: str = Field(default="0.0.0.0", description="API host")
    port: int = Field(default=8000, description="API port")
    debug: bool = Field(default=False, description="Enable debug mode")
    reload: bool = Field(default=False, description="Enable auto-reload")
    
    # CORS settings
    cors_origins: List[str] = Field(default=["*"], description="CORS allowed origins")
    cors_methods: List[str] = Field(default=["*"], description="CORS allowed methods")
    cors_headers: List[str] = Field(default=["*"], description="CORS allowed headers")
    
    # Request settings
    max_request_size: int = Field(default=10 * 1024 * 1024, description="Maximum request size")  # 10MB
    request_timeout: int = Field(default=300, description="Request timeout in seconds")  # 5 minutes
    
    @validator('cors_origins', 'cors_methods', 'cors_headers', pre=True)
    def parse_cors_list(cls, v):
        """Parse comma-separated CORS values."""
        if isinstance(v, str):
            return [item.strip() for item in v.split(',')]
        return v
    
    model_config = {"env_prefix": "API_", "case_sensitive": False}


class CacheSettings(BaseSettings):
    """Cache configuration settings."""
    
    # Cache settings
    enable_cache: bool = Field(default=True, description="Enable caching")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")  # 1 hour
    cache_max_size: int = Field(default=1000, description="Maximum cache size")
    cache_cleanup_interval: int = Field(default=300, description="Cache cleanup interval in seconds")
    
    # Cache strategies
    cache_chat_responses: bool = Field(default=True, description="Cache chat responses")
    cache_embeddings: bool = Field(default=True, description="Cache embeddings")
    cache_web_search: bool = Field(default=True, description="Cache web search results")
    
    class Config:
        env_prefix = "CACHE_"
        case_sensitive = False


class MemorySettings(BaseSettings):
    """Memory system configuration settings."""
    
    # Memory storage settings
    enable_memory: bool = Field(default=True, description="Enable memory system")
    memory_threshold: float = Field(default=0.8, description="Memory relevance threshold")
    max_memories_per_user: int = Field(default=1000, description="Maximum memories per user")
    memory_cleanup_days: int = Field(default=30, description="Memory cleanup interval in days")
    
    # Auto-memory settings
    auto_store_personal_info: bool = Field(default=True, env="AUTO_STORE_PERSONAL_INFO")
    auto_store_preferences: bool = Field(default=True, env="AUTO_STORE_PREFERENCES")
    auto_store_important_conversations: bool = Field(default=True, env="AUTO_STORE_IMPORTANT")
    
    class Config:
        env_prefix = "MEMORY_"
        case_sensitive = False


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""
    
    # Logging levels
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", env="LOG_FORMAT")
    
    # Log destinations
    log_to_file: bool = Field(default=True, env="LOG_TO_FILE")
    log_file_path: str = Field(default="logs/app.log", env="LOG_FILE_PATH")
    log_max_size: int = Field(default=10 * 1024 * 1024, env="LOG_MAX_SIZE")  # 10MB
    log_backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")
    
    # Structured logging
    enable_structured_logging: bool = Field(default=False, env="ENABLE_STRUCTURED_LOGGING")
    log_correlation_ids: bool = Field(default=True, env="LOG_CORRELATION_IDS")
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Invalid log level: {v}. Must be one of {valid_levels}')
        return v.upper()
    
    class Config:
        env_prefix = "LOG_"
        case_sensitive = False


class SecuritySettings(BaseSettings):
    """Security configuration settings."""
    
    # Authentication
    enable_auth: bool = Field(default=False, env="ENABLE_AUTH")
    secret_key: Optional[str] = Field(default=None, env="SECRET_KEY")
    token_expiry_hours: int = Field(default=24, env="TOKEN_EXPIRY_HOURS")
    
    # Rate limiting
    enable_rate_limiting: bool = Field(default=True, env="ENABLE_RATE_LIMITING")
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW")  # seconds
    
    # OpenWebUI integration
    openwebui_auth_required: bool = Field(default=True, env="OPENWEBUI_AUTH_REQUIRED")
    validate_user_ids: bool = Field(default=True, env="VALIDATE_USER_IDS")
    
    class Config:
        env_prefix = "SECURITY_"
        case_sensitive = False


class AppSettings(BaseSettings):
    """Main application configuration."""
    
    # App metadata
    app_name: str = Field(default="LLM Backend API", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    app_description: str = Field(default="FastAPI LLM Backend with RAG capabilities", env="APP_DESCRIPTION")
    
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # File paths
    data_dir: Path = Field(default=Path("data"), env="DATA_DIR")
    logs_dir: Path = Field(default=Path("logs"), env="LOGS_DIR")
    config_dir: Path = Field(default=Path("config"), env="CONFIG_DIR")
    
    # Component settings
    database: DatabaseSettings = DatabaseSettings()
    llm: LLMSettings = LLMSettings()
    api: APISettings = APISettings()
    cache: CacheSettings = CacheSettings()
    memory: MemorySettings = MemorySettings()
    logging: LoggingSettings = LoggingSettings()
    security: SecuritySettings = SecuritySettings()
    
    @validator('data_dir', 'logs_dir', 'config_dir')
    def ensure_directories_exist(cls, v):
        """Ensure directories exist."""
        if isinstance(v, str):
            v = Path(v)
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    @validator('environment')
    def validate_environment(cls, v):
        """Validate environment."""
        valid_envs = ['development', 'testing', 'staging', 'production']
        if v.lower() not in valid_envs:
            raise ValueError(f'Invalid environment: {v}. Must be one of {valid_envs}')
        return v.lower()
    
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == 'production'
    
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == 'development'
    
    def get_redis_url(self) -> str:
        """Get Redis connection URL."""
        auth = f":{self.database.redis_password}@" if self.database.redis_password else ""
        return f"redis://{auth}{self.database.redis_host}:{self.database.redis_port}/{self.database.redis_db}"
    
    def get_chroma_url(self) -> str:
        """Get ChromaDB connection URL."""
        return f"http://{self.database.chroma_host}:{self.database.chroma_port}"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from legacy config


# Global settings instance
settings = AppSettings()


def get_settings() -> AppSettings:
    """Get the global settings instance."""
    return settings


def reload_settings() -> AppSettings:
    """Reload settings from environment."""
    global settings
    settings = AppSettings()
    return settings


# Legacy compatibility functions for gradual migration
def get_app_start_time():
    """Legacy compatibility for app start time."""
    import time
    return time.time()


def get_default_system_prompt():
    """Legacy compatibility for default system prompt."""
    return settings.llm.default_system_prompt


# Legacy constants for compatibility
DEFAULT_SYSTEM_PROMPT = settings.llm.default_system_prompt
DEFAULT_MODEL = settings.llm.ollama_model
OLLAMA_BASE_URL = settings.llm.ollama_url
