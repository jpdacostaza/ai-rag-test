"""
Test Suite for Configuration System
===================================

Comprehensive tests for the Pydantic-based configuration system including
environment variable handling, validation, and settings management.
"""

import pytest
import os
from unittest.mock import patch, Mock
from pydantic import ValidationError

from config.settings import (
    DatabaseSettings,
    LLMSettings,
    APISettings,
    CacheSettings,
    MemorySettings,
    LoggingSettings,
    SecuritySettings,
    AppSettings
)


@pytest.mark.unit
@pytest.mark.configuration
class TestDatabaseSettings:
    """Test suite for DatabaseSettings."""
    
    def test_database_settings_defaults(self):
        """Test default database settings."""
        settings = DatabaseSettings()
        
        assert settings.host == "localhost"
        assert settings.port == 5432
        assert settings.database == "optbackend"
        assert settings.user == "postgres"
        assert settings.password == "password"
        assert settings.max_connections == 20
        assert settings.min_connections == 5
    
    def test_database_settings_from_env(self):
        """Test database settings from environment variables."""
        env_vars = {
            "DB_HOST": "db.example.com",
            "DB_PORT": "3306",
            "DB_DATABASE": "production_db",
            "DB_USER": "admin",
            "DB_PASSWORD": "secret123",
            "DB_MAX_CONNECTIONS": "50",
            "DB_MIN_CONNECTIONS": "10"
        }
        
        with patch.dict(os.environ, env_vars):
            settings = DatabaseSettings()
            
            assert settings.host == "db.example.com"
            assert settings.port == 3306
            assert settings.database == "production_db"
            assert settings.user == "admin"
            assert settings.password == "secret123"
            assert settings.max_connections == 50
            assert settings.min_connections == 10
    
    def test_database_url_generation(self):
        """Test database URL generation."""
        settings = DatabaseSettings(
            host="localhost",
            port=5432,
            database="testdb",
            user="testuser",
            password="testpass"
        )
        
        expected_url = "postgresql://testuser:testpass@localhost:5432/testdb"
        assert settings.get_database_url() == expected_url
    
    def test_database_url_with_special_chars(self):
        """Test database URL generation with special characters in password."""
        settings = DatabaseSettings(
            user="test@user",
            password="pass@word#123"
        )
        
        url = settings.get_database_url()
        # URL should be properly encoded
        assert "test%40user" in url
        assert "pass%40word%23123" in url
    
    def test_database_settings_validation(self):
        """Test database settings validation."""
        # Test invalid port
        with pytest.raises(ValidationError):
            DatabaseSettings(port=-1)
        
        with pytest.raises(ValidationError):
            DatabaseSettings(port=70000)
        
        # Test invalid connection counts
        with pytest.raises(ValidationError):
            DatabaseSettings(max_connections=0)
        
        with pytest.raises(ValidationError):
            DatabaseSettings(min_connections=-1)


@pytest.mark.unit
@pytest.mark.configuration
class TestLLMSettings:
    """Test suite for LLMSettings."""
    
    def test_llm_settings_defaults(self):
        """Test default LLM settings."""
        settings = LLMSettings()
        
        assert settings.model == "gpt-4"
        assert settings.temperature == 0.7
        assert settings.max_tokens == 4000
        assert settings.api_base == "https://api.openai.com/v1"
        assert settings.timeout == 30.0
        assert settings.max_retries == 3
    
    def test_llm_settings_from_env(self):
        """Test LLM settings from environment variables."""
        env_vars = {
            "LLM_MODEL": "gpt-3.5-turbo",
            "LLM_TEMPERATURE": "0.9",
            "LLM_MAX_TOKENS": "2000",
            "LLM_API_BASE": "https://custom.openai.com/v1",
            "LLM_API_KEY": "sk-test123",
            "LLM_TIMEOUT": "60.0",
            "LLM_MAX_RETRIES": "5"
        }
        
        with patch.dict(os.environ, env_vars):
            settings = LLMSettings()
            
            assert settings.model == "gpt-3.5-turbo"
            assert settings.temperature == 0.9
            assert settings.max_tokens == 2000
            assert settings.api_base == "https://custom.openai.com/v1"
            assert settings.api_key == "sk-test123"
            assert settings.timeout == 60.0
            assert settings.max_retries == 5
    
    def test_llm_settings_validation(self):
        """Test LLM settings validation."""
        # Test invalid temperature
        with pytest.raises(ValidationError):
            LLMSettings(temperature=-0.1)
        
        with pytest.raises(ValidationError):
            LLMSettings(temperature=2.1)
        
        # Test invalid max_tokens
        with pytest.raises(ValidationError):
            LLMSettings(max_tokens=0)
        
        # Test invalid timeout
        with pytest.raises(ValidationError):
            LLMSettings(timeout=0)
        
        # Test invalid max_retries
        with pytest.raises(ValidationError):
            LLMSettings(max_retries=-1)


@pytest.mark.unit
@pytest.mark.configuration
class TestAPISettings:
    """Test suite for APISettings."""
    
    def test_api_settings_defaults(self):
        """Test default API settings."""
        settings = APISettings()
        
        assert settings.host == "0.0.0.0"
        assert settings.port == 8000
        assert settings.cors_origins == ["*"]
        assert settings.max_request_size == 10 * 1024 * 1024  # 10MB
        assert settings.rate_limit == 100
        assert settings.debug is False
    
    def test_api_settings_from_env(self):
        """Test API settings from environment variables."""
        env_vars = {
            "API_HOST": "127.0.0.1",
            "API_PORT": "3000",
            "API_CORS_ORIGINS": "http://localhost:3000,https://example.com",
            "API_MAX_REQUEST_SIZE": "20971520",  # 20MB
            "API_RATE_LIMIT": "200",
            "API_DEBUG": "true"
        }
        
        with patch.dict(os.environ, env_vars):
            settings = APISettings()
            
            assert settings.host == "127.0.0.1"
            assert settings.port == 3000
            assert settings.cors_origins == ["http://localhost:3000", "https://example.com"]
            assert settings.max_request_size == 20971520
            assert settings.rate_limit == 200
            assert settings.debug is True
    
    def test_api_settings_validation(self):
        """Test API settings validation."""
        # Test invalid port
        with pytest.raises(ValidationError):
            APISettings(port=0)
        
        with pytest.raises(ValidationError):
            APISettings(port=70000)
        
        # Test invalid max_request_size
        with pytest.raises(ValidationError):
            APISettings(max_request_size=0)
        
        # Test invalid rate_limit
        with pytest.raises(ValidationError):
            APISettings(rate_limit=0)


@pytest.mark.unit
@pytest.mark.configuration
class TestCacheSettings:
    """Test suite for CacheSettings."""
    
    def test_cache_settings_defaults(self):
        """Test default cache settings."""
        settings = CacheSettings()
        
        assert settings.redis_host == "localhost"
        assert settings.redis_port == 6379
        assert settings.redis_db == 0
        assert settings.ttl == 3600
        assert settings.max_connections == 10
    
    def test_cache_settings_from_env(self):
        """Test cache settings from environment variables."""
        env_vars = {
            "REDIS_HOST": "redis.example.com",
            "REDIS_PORT": "6380",
            "REDIS_DB": "1",
            "REDIS_PASSWORD": "redis123",
            "CACHE_TTL": "7200",
            "REDIS_MAX_CONNECTIONS": "20"
        }
        
        with patch.dict(os.environ, env_vars):
            settings = CacheSettings()
            
            assert settings.redis_host == "redis.example.com"
            assert settings.redis_port == 6380
            assert settings.redis_db == 1
            assert settings.redis_password == "redis123"
            assert settings.ttl == 7200
            assert settings.max_connections == 20
    
    def test_cache_redis_url_generation(self):
        """Test Redis URL generation."""
        settings = CacheSettings(
            redis_host="localhost",
            redis_port=6379,
            redis_db=0,
            redis_password="secret"
        )
        
        expected_url = "redis://:secret@localhost:6379/0"
        assert settings.get_redis_url() == expected_url
    
    def test_cache_redis_url_without_password(self):
        """Test Redis URL generation without password."""
        settings = CacheSettings(
            redis_host="localhost",
            redis_port=6379,
            redis_db=0
        )
        
        expected_url = "redis://localhost:6379/0"
        assert settings.get_redis_url() == expected_url


@pytest.mark.unit
@pytest.mark.configuration
class TestAppSettings:
    """Test suite for AppSettings (main configuration)."""
    
    def test_app_settings_initialization(self):
        """Test AppSettings initialization with all subsettings."""
        settings = AppSettings()
        
        assert isinstance(settings.database, DatabaseSettings)
        assert isinstance(settings.llm, LLMSettings)
        assert isinstance(settings.api, APISettings)
        assert isinstance(settings.cache, CacheSettings)
        assert isinstance(settings.memory, MemorySettings)
        assert isinstance(settings.logging, LoggingSettings)
        assert isinstance(settings.security, SecuritySettings)
    
    def test_app_settings_from_env(self):
        """Test AppSettings with environment variables."""
        env_vars = {
            "DB_HOST": "prod-db.com",
            "LLM_MODEL": "gpt-4-turbo",
            "API_PORT": "9000",
            "REDIS_HOST": "prod-redis.com",
            "APP_NAME": "Production API",
            "ENVIRONMENT": "production"
        }
        
        with patch.dict(os.environ, env_vars):
            settings = AppSettings()
            
            assert settings.database.host == "prod-db.com"
            assert settings.llm.model == "gpt-4-turbo"
            assert settings.api.port == 9000
            assert settings.cache.redis_host == "prod-redis.com"
            assert settings.app_name == "Production API"
            assert settings.environment == "production"
    
    def test_app_settings_debug_mode(self):
        """Test debug mode settings."""
        # Test debug mode from environment
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            settings = AppSettings()
            assert settings.environment == "development"
        
        # Test production mode
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            settings = AppSettings()
            assert settings.environment == "production"
    
    def test_app_settings_secrets_masking(self):
        """Test that sensitive settings are properly masked."""
        env_vars = {
            "DB_PASSWORD": "secret_db_password",
            "LLM_API_KEY": "sk-secret_api_key",
            "JWT_SECRET_KEY": "secret_jwt_key"
        }
        
        with patch.dict(os.environ, env_vars):
            settings = AppSettings()
            
            # Secrets should be set but not exposed in string representation
            settings_str = str(settings)
            assert "secret_db_password" not in settings_str
            assert "sk-secret_api_key" not in settings_str
            assert "secret_jwt_key" not in settings_str
    
    def test_app_settings_validation_cascade(self):
        """Test that validation errors cascade from subsettings."""
        env_vars = {
            "DB_PORT": "invalid_port",
            "LLM_TEMPERATURE": "5.0",  # Too high
        }
        
        with patch.dict(os.environ, env_vars):
            with pytest.raises(ValidationError):
                AppSettings()


@pytest.mark.unit
@pytest.mark.configuration
class TestSecuritySettings:
    """Test suite for SecuritySettings."""
    
    def test_security_settings_defaults(self):
        """Test default security settings."""
        settings = SecuritySettings()
        
        assert len(settings.jwt_secret_key) == 32  # Default generated secret
        assert settings.jwt_algorithm == "HS256"
        assert settings.jwt_expire_minutes == 1440  # 24 hours
        assert settings.allowed_hosts == ["*"]
        assert settings.cors_allow_credentials is True
    
    def test_security_settings_from_env(self):
        """Test security settings from environment variables."""
        env_vars = {
            "JWT_SECRET_KEY": "custom_secret_key_123",
            "JWT_ALGORITHM": "HS512",
            "JWT_EXPIRE_MINUTES": "720",  # 12 hours
            "ALLOWED_HOSTS": "localhost,127.0.0.1,example.com",
            "CORS_ALLOW_CREDENTIALS": "false"
        }
        
        with patch.dict(os.environ, env_vars):
            settings = SecuritySettings()
            
            assert settings.jwt_secret_key == "custom_secret_key_123"
            assert settings.jwt_algorithm == "HS512"
            assert settings.jwt_expire_minutes == 720
            assert settings.allowed_hosts == ["localhost", "127.0.0.1", "example.com"]
            assert settings.cors_allow_credentials is False


@pytest.mark.integration
@pytest.mark.configuration
class TestConfigurationIntegration:
    """Integration tests for the configuration system."""
    
    def test_settings_loading_performance(self):
        """Test that settings load quickly."""
        import time
        
        start_time = time.time()
        
        # Load settings multiple times
        for _ in range(10):
            settings = AppSettings()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should load quickly
        assert duration < 1.0, f"Settings loading too slow: {duration}s"
    
    def test_settings_singleton_pattern(self):
        """Test that settings can be used as singleton."""
        settings1 = AppSettings()
        settings2 = AppSettings()
        
        # Should have same configuration
        assert settings1.database.host == settings2.database.host
        assert settings1.llm.model == settings2.llm.model
        assert settings1.api.port == settings2.api.port
    
    def test_environment_isolation(self):
        """Test that environment changes affect new instances."""
        # Initial settings
        settings1 = AppSettings()
        original_port = settings1.api.port
        
        # Change environment and create new settings
        with patch.dict(os.environ, {"API_PORT": "9999"}):
            settings2 = AppSettings()
            assert settings2.api.port == 9999
        
        # Original should remain unchanged if it's a new instance
        settings3 = AppSettings()
        assert settings3.api.port == original_port
    
    @pytest.mark.parametrize("env_name,setting_path,test_value", [
        ("DB_HOST", "database.host", "test-db.com"),
        ("LLM_MODEL", "llm.model", "custom-model"),
        ("API_PORT", "api.port", "8080"),
        ("REDIS_HOST", "cache.redis_host", "test-redis.com"),
    ])
    def test_environment_variable_mapping(self, env_name, setting_path, test_value):
        """Test that environment variables map correctly to settings."""
        with patch.dict(os.environ, {env_name: str(test_value)}):
            settings = AppSettings()
            
            # Navigate to the setting using the path
            current = settings
            for part in setting_path.split('.'):
                current = getattr(current, part)
            
            # Convert to same type for comparison
            if isinstance(current, int):
                test_value = int(test_value)
            
            assert current == test_value
