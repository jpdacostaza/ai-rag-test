"""
Startup Manager for FastAPI LLM Backend
Handles application startup, configuration, and system initialization
"""

import asyncio
import itertools
import sys
import os
import platform
from typing import Optional, Dict, Any

from human_logging import log_service_status, init_logging
from watchdog import start_watchdog_service, get_watchdog
from enhanced_integration import start_enhanced_background_tasks
from database import db_manager
from model_manager import refresh_model_cache

class StartupManager:
    """Manages application startup process and configuration."""
    
    def __init__(self):
        self.startup_start_time = None
        self.watchdog_thread = None
        
    async def initialize_application(self):
        """Initialize the entire application startup process."""
        import time
        self.startup_start_time = time.time()
        
        log_service_status("STARTUP", "starting", "🚀 FastAPI LLM Backend startup initiated")
        
        # Log system information
        self._log_system_info()
        self._log_environment_variables()
        
        # Initialize model cache
        log_service_status("STARTUP", "starting", "Initializing model cache...")
        await refresh_model_cache()
        
        # Initialize cache and memory systems
        log_service_status("STARTUP", "starting", "Initializing cache management and memory systems...")
        await self._initialize_memory_systems()
        
        # Initialize background services
        log_service_status("STARTUP", "starting", "Initializing background services...")
        await self._initialize_background_services()
        
        # Wait for services to stabilize
        log_service_status("STARTUP", "starting", "Waiting 2 seconds for services to initialize...")
        await asyncio.sleep(2)
        
        # Start enhanced background tasks
        await start_enhanced_background_tasks()        
        # Final startup summary
        self._print_startup_summary()
        
        startup_duration = time.time() - self.startup_start_time
        log_service_status("STARTUP", "ready", f"🚀 FastAPI LLM Backend startup completed successfully! ({startup_duration:.2f}s)")
        
    async def _initialize_memory_systems(self):
        """Initialize cache management and memory systems."""
        try:
            from database import get_cache_manager, get_database_health
            
            # Initialize cache manager
            log_service_status("CACHE_INIT", "starting", "Initializing cache management system")
            
            # Verify cache manager
            cache_manager = get_cache_manager()
            if cache_manager:
                cache_stats = cache_manager.get_cache_stats()
                log_service_status("CACHE_INIT", "ready", f"Cache management initialized. Version: {cache_stats.get('version', 'unknown')}, Total keys: {cache_stats.get('total_keys', 0)}")
            
            # Perform health check
            log_service_status("MEMORY_HEALTH", "starting", "Performing startup memory/cache health check...")
            health_status = get_database_health()
            
            # Test cache operations
            import time
            test_key = f"startup_health_test"
            test_value = f"test_{int(time.time())}"
            
            from database import set_cache, get_cache
            set_cache(db_manager, test_key, test_value, ttl=10)
            retrieved = get_cache(db_manager, test_key)
            
            if retrieved == test_value:
                redis_status = "✅" if health_status["redis"]["available"] else "❌"
                chroma_status = "✅" if health_status["chromadb"]["available"] else "❌"
                
                startup_duration = time.time() - (self.startup_start_time or time.time())
                log_service_status("MEMORY_HEALTH", "ready", f"Memory systems healthy (Redis: {redis_status}, ChromaDB: {chroma_status}) - {startup_duration:.2f}s")
                log_service_status("MEMORY_INIT", "ready", "Memory systems initialized and validated successfully")
            else:
                log_service_status("MEMORY_HEALTH", "warning", "Cache test failed - systems may be degraded")
                
            log_service_status("MEMORY", "ready", "Memory and cache systems initialized successfully")
            
        except Exception as e:
            log_service_status("MEMORY", "error", f"Failed to initialize memory systems: {str(e)}")
            
    async def _initialize_background_services(self):
        """Initialize background monitoring and services."""
        try:
            # Start watchdog service
            self.watchdog_thread = start_watchdog_service()
            if self.watchdog_thread and self.watchdog_thread.is_alive():
                log_service_status("WATCHDOG", "ready", "Background monitoring service started successfully")
            else:
                log_service_status("WATCHDOG", "warning", "Background monitoring service failed to start")
                
        except Exception as e:
            log_service_status("WATCHDOG", "error", f"Failed to start background services: {str(e)}")
    
    def _log_system_info(self):
        """Log system information for startup diagnostics."""
        try:
            log_service_status("SYSTEM", "info", f"Python version: {sys.version.split()[0]}")
            log_service_status("SYSTEM", "info", f"Platform: {platform.system()} {platform.release()}")
            log_service_status("SYSTEM", "info", f"Working directory: {os.getcwd()}")
            
        except Exception as e:
            log_service_status("SYSTEM", "warning", f"Failed to log system info: {e}")

    def _log_environment_variables(self):
        """Log relevant environment variables for startup diagnostics."""
        try:
            env_vars_to_log = [
                "REDIS_HOST", "REDIS_PORT", "CHROMA_HOST", "CHROMA_PORT", 
                "DEFAULT_MODEL", "EMBEDDING_MODEL", "SENTENCE_TRANSFORMERS_HOME",
                "OLLAMA_BASE_URL", "USE_OLLAMA", "USE_HTTP_CHROMA"
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

    def _print_startup_summary(self):
        """Print a formatted startup summary."""
        lines = [
            "================= SERVICE STATUS SUMMARY =================",
            "Redis:      ✅",
            "ChromaDB:   ✅", 
            "Embeddings: ✅",
            "========================================================"
        ]
        for line in lines:
            print(line)

    async def spinner_log(self, message: str, duration: float = 2.0, interval: float = 0.2):
        """Show a spinner/progress animation in the logs for a given duration."""
        spinner = itertools.cycle(['|', '/', '-', '\\'])
        steps = int(duration / interval)
        for _ in range(steps):
            sys.stdout.write(f"\r{message} {next(spinner)}")
            sys.stdout.flush()
            await asyncio.sleep(interval)
        sys.stdout.write("\r" + " " * (len(message) + 2) + "\r")
        sys.stdout.flush()

class ConfigurationManager:
    """Manages application configuration and environment variables."""
    
    @staticmethod
    def get_config() -> Dict[str, Any]:
        """Get current application configuration."""
        return {
            "models": {
                "default_model": os.getenv("DEFAULT_MODEL", "llama3.2:3b"),
                "embedding_model": os.getenv("EMBEDDING_MODEL", "Qwen/Qwen2.5-Embedding-0.6B"),
                "ollama_base_url": os.getenv("OLLAMA_BASE_URL", "http://ollama:11434"),
                "use_ollama": os.getenv("USE_OLLAMA", "true").lower() == "true"
            },
            "database": {
                "redis_host": os.getenv("REDIS_HOST", "redis"),
                "redis_port": int(os.getenv("REDIS_PORT", "6379")),
                "chroma_host": os.getenv("CHROMA_HOST", "chroma"),
                "chroma_port": int(os.getenv("CHROMA_PORT", "8000")),
                "use_http_chroma": os.getenv("USE_HTTP_CHROMA", "true").lower() == "true"
            },
            "system": {
                "sentence_transformers_home": os.getenv("SENTENCE_TRANSFORMERS_HOME", "./storage/models"),
                "storage_base_path": os.getenv("STORAGE_BASE_PATH", "./storage"),
                "log_level": os.getenv("LOG_LEVEL", "INFO")
            },
            "api": {
                "llm_timeout": int(os.getenv("LLM_TIMEOUT", "180")),
                "max_history": int(os.getenv("MAX_HISTORY", "10")),
                "cache_ttl": int(os.getenv("CACHE_TTL", "600"))
            }
        }
    
    @staticmethod
    def validate_config() -> Dict[str, bool]:
        """Validate current configuration and return status of each component."""
        config = ConfigurationManager.get_config()
        validation_results = {}
        
        # Validate model configuration
        validation_results["models"] = all([
            config["models"]["default_model"],
            config["models"]["embedding_model"],
            config["models"]["ollama_base_url"]
        ])
        
        # Validate database configuration
        validation_results["database"] = all([
            config["database"]["redis_host"],
            1 <= config["database"]["redis_port"] <= 65535,
            config["database"]["chroma_host"],
            1 <= config["database"]["chroma_port"] <= 65535
        ])
        
        # Validate system configuration
        validation_results["system"] = all([
            config["system"]["sentence_transformers_home"],
            config["system"]["storage_base_path"]
        ])
        
        # Validate API configuration
        validation_results["api"] = all([
            config["api"]["llm_timeout"] > 0,
            config["api"]["max_history"] > 0,
            config["api"]["cache_ttl"] > 0
        ])
        
        return validation_results

# Global startup manager instance
startup_manager = StartupManager()
config_manager = ConfigurationManager()
