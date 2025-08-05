"""
⚠️  DEPRECATED: This configuration file has been replaced by config_unified.py
==============================================================================

This file is kept for backward compatibility but should not be modified.
All new configuration should be done through config_unified.py.

Migration date: 2025-07-13T11:24:41.509693
Replacement: config_unified.py

To complete the migration:
1. Verify all imports have been updated to use config_unified
2. Test the application thoroughly
3. Remove this file when confident the migration is complete
"""

# Original configuration content follows:
# (kept for reference during migration period)

"""
Centralized Configuration Management
===================================

This module provides a centralized way to manage all configuration values,
eliminating hardcoded URLs, secrets, and other configuration throughout the codebase.
"""

import os
import re
from typing import Optional, Dict, Any, List
from pathlib import Path
import json

class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""
    pass

class SecurityConfig:
    """Security-related configuration."""
    
    @property
    def jwt_secret(self) -> str:
        secret = os.getenv("JWT_SECRET")
        if not secret:
            raise ConfigurationError("JWT_SECRET environment variable is required")
        if len(secret) < 32:
            raise ConfigurationError("JWT_SECRET must be at least 32 characters")
        return secret
    
    @property
    def api_key(self) -> str:
        key = os.getenv("API_KEY")
        if not key:
            raise ConfigurationError("API_KEY environment variable is required")
        return key
    
    @property
    def enable_debug(self) -> bool:
        return os.getenv("ENABLE_DEBUG", "false").lower() == "true"
    
    @property
    def enable_rate_limiting(self) -> bool:
        return os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true"
    
    @property
    def max_requests_per_minute(self) -> int:
        return int(os.getenv("MAX_REQUESTS_PER_MINUTE", "60"))

class ServiceConfig:
    """Service endpoint configuration."""
    
    @property
    def openwebui_url(self) -> str:
        return os.getenv("OPENWEBUI_URL", "http://openwebui:8080")
    
    @property
    def memory_api_url(self) -> str:
        return os.getenv("MEMORY_API_URL", "http://memory-api:5001")
    
    @property
    def redis_url(self) -> str:
        return os.getenv("REDIS_URL", "redis://redis:6379")
    
    @property
    def chromadb_url(self) -> str:
        return os.getenv("CHROMADB_URL", "http://chroma:8000")
    
    @property
    def ollama_url(self) -> str:
        return os.getenv("OLLAMA_URL", "http://ollama:11434")
    
    @property
    def backend_host(self) -> str:
        return os.getenv("BACKEND_HOST", "0.0.0.0")
    
    @property
    def backend_port(self) -> int:
        return int(os.getenv("BACKEND_PORT", "3000"))

class DatabaseConfig:
    """Database configuration."""
    
    @property
    def redis_host(self) -> str:
        return os.getenv("REDIS_HOST", "redis")
    
    @property
    def redis_port(self) -> int:
        return int(os.getenv("REDIS_PORT", "6379"))
    
    @property
    def redis_password(self) -> Optional[str]:
        return os.getenv("REDIS_PASSWORD")
    
    @property
    def redis_db(self) -> int:
        return int(os.getenv("REDIS_DB", "0"))
    
    @property
    def chromadb_host(self) -> str:
        return os.getenv("CHROMADB_HOST", "chromadb")
    
    @property
    def chromadb_port(self) -> int:
        return int(os.getenv("CHROMADB_PORT", "8000"))

class MemoryConfig:
    """Memory system configuration."""
    
    @property
    def enable_memory(self) -> bool:
        return os.getenv("ENABLE_MEMORY", "true").lower() == "true"
    
    @property
    def similarity_threshold(self) -> float:
        return float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))
    
    @property
    def max_memories(self) -> int:
        return int(os.getenv("MAX_MEMORIES", "10"))
    
    @property
    def cache_ttl(self) -> int:
        return int(os.getenv("CACHE_TTL", "3600"))

class ValidationConfig:
    """Input validation configuration."""
    
    @property
    def max_message_length(self) -> int:
        return int(os.getenv("MAX_MESSAGE_LENGTH", "10000"))
    
    @property
    def max_query_length(self) -> int:
        return int(os.getenv("MAX_QUERY_LENGTH", "1000"))
    
    @property
    def allowed_user_id_patterns(self) -> List[str]:
        """Patterns for valid user IDs."""
        return [
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',  # UUID
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',  # Email
            r'^[a-zA-Z0-9][a-zA-Z0-9._-]{2,}[a-zA-Z0-9]$'  # Username
        ]
    
    def validate_user_id(self, user_id: str) -> bool:
        """Validate user ID against allowed patterns."""
        if not user_id or len(user_id.strip()) < 3:
            return False
        
        # Check for invalid patterns
        invalid_patterns = ["undefined", "null", "none", "", "anonymous", "guest", "openwebui_default_user"]
        if user_id.lower() in invalid_patterns:
            return False
        
        # Check against allowed patterns
        for pattern in self.allowed_user_id_patterns:
            if re.match(pattern, user_id, re.IGNORECASE):
                return True
        
        return False
    
    def validate_email(self, email: str) -> bool:
        """Validate email format."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))

class AppConfig:
    """Main application configuration."""
    
    def __init__(self):
        self.security = SecurityConfig()
        self.services = ServiceConfig()
        self.database = DatabaseConfig()
        self.memory = MemoryConfig()
        self.validation = ValidationConfig()
        
        # Load environment file if it exists
        self._load_env_file()
    
    def _load_env_file(self):
        """Load environment variables from .env file."""
        env_file = Path(".env")
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, _, value = line.partition('=')
                        if key and value:
                            os.environ.setdefault(key.strip(), value.strip())
    
    def validate_configuration(self) -> List[str]:
        """Validate all configuration and return list of errors."""
        errors = []
        
        try:
            # Test security configuration
            _ = self.security.jwt_secret
            _ = self.security.api_key
        except ConfigurationError as e:
            errors.append(f"Security configuration error: {e}")
        
        # Validate service URLs
        service_urls = [
            ("OPENWEBUI_URL", self.services.openwebui_url),
            ("MEMORY_API_URL", self.services.memory_api_url),
            ("REDIS_URL", self.services.redis_url),
            ("CHROMADB_URL", self.services.chromadb_url),
            ("OLLAMA_URL", self.services.ollama_url)
        ]
        
        for name, url in service_urls:
            if not self._is_valid_url(url):
                errors.append(f"Invalid {name}: {url}")
        
        return errors
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format."""
        url_pattern = r'^https?://[a-zA-Z0-9.-]+(?::\d+)?(?:/.*)?$'
        return bool(re.match(url_pattern, url))
    
    def get_database_url(self, db_type: str) -> str:
        """Get database URL for specific database type."""
        if db_type.lower() == "redis":
            if self.database.redis_password:
                return f"redis://:{self.database.redis_password}@{self.database.redis_host}:{self.database.redis_port}/{self.database.redis_db}"
            else:
                return f"redis://{self.database.redis_host}:{self.database.redis_port}/{self.database.redis_db}"
        elif db_type.lower() == "chromadb":
            return f"http://{self.database.chromadb_host}:{self.database.chromadb_port}"
        else:
            raise ValueError(f"Unknown database type: {db_type}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (excluding sensitive data)."""
        return {
            "services": {
                "openwebui_url": self.services.openwebui_url,
                "memory_api_url": self.services.memory_api_url,
                "ollama_url": self.services.ollama_url,
                "backend_host": self.services.backend_host,
                "backend_port": self.services.backend_port
            },
            "memory": {
                "enable_memory": self.memory.enable_memory,
                "similarity_threshold": self.memory.similarity_threshold,
                "max_memories": self.memory.max_memories,
                "cache_ttl": self.memory.cache_ttl
            },
            "security": {
                "enable_debug": self.security.enable_debug,
                "enable_rate_limiting": self.security.enable_rate_limiting,
                "max_requests_per_minute": self.security.max_requests_per_minute
            }
        }

# Global configuration instance
config = AppConfig()

def get_config() -> AppConfig:
    """Get the global configuration instance."""
    return config

def validate_startup_config() -> None:
    """Validate configuration at startup and raise errors if invalid."""
    errors = config.validate_configuration()
    if errors:
        error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
        raise ConfigurationError(error_msg)
