"""
RAG DUAL-DATABASE MEMORY SYSTEM CONFIGURATION
============================================

This configuration file documents the complete RAG memory system
architecture implemented on 2025-07-17.

System Architecture: RAG (Retrieval-Augmented Generation) Dual-Database
Database Strategy: Redis (short-term) + ChromaDB (long-term)
Storage Distribution: Importance-based routing with semantic search
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Union

@dataclass
class RAGDatabaseConfig:
    """RAG dual-database configuration"""
    
    # Redis Configuration (Short-term memory)
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_decode_responses: bool = True
    redis_socket_timeout: int = 5
    
    # ChromaDB Configuration (Long-term memory)
    chroma_host: str = "chroma"
    chroma_port: int = 8000
    chroma_collection_name: str = "rag_memories"
    chroma_embedding_function: str = "all-MiniLM-L6-v2"
    
    # RAG Storage Strategy - LOWERED for better memory retention
    short_term_importance_threshold: float = 0.2
    long_term_importance_threshold: float = 0.5
    
    # TTL Settings
    short_term_ttl: int = 3600      # 1 hour
    medium_term_ttl: int = 43200    # 12 hours
    long_term_ttl: int = 86400      # 24 hours
    
    def __post_init__(self):
        """Load from environment variables"""
        self.redis_host = os.getenv("REDIS_HOST", self.redis_host)
        self.redis_port = int(os.getenv("REDIS_PORT", str(self.redis_port)))
        self.chroma_host = os.getenv("CHROMA_HOST", self.chroma_host)
        self.chroma_port = int(os.getenv("CHROMA_PORT", str(self.chroma_port)))

@dataclass
class MemoryClassificationConfig:
    """Memory importance classification configuration"""
    
    # High importance keywords (0.9)
    high_importance_keywords: List[str] = None
    
    # Medium importance keywords (0.7)
    medium_importance_keywords: List[str] = None
    
    # Explicit memory triggers
    explicit_memory_triggers: List[str] = None
    
    # Context-based importance mapping
    context_importance_mapping: Dict[str, float] = None
    
    def __post_init__(self):
        if self.high_importance_keywords is None:
            self.high_importance_keywords = [
                "name", "email", "phone", "address", "password", 
                "allergy", "allergic", "medical", "emergency", 
                "deadline", "appointment", "meeting", "birthday",
                "anniversary", "account", "login", "credential"
            ]
        
        if self.medium_importance_keywords is None:
            self.medium_importance_keywords = [
                "prefer", "like", "dislike", "favorite", "setting",
                "configuration", "project", "work", "colleague",
                "friend", "family"
            ]
        
        if self.explicit_memory_triggers is None:
            self.explicit_memory_triggers = [
                "remember", "don't forget", "please remember",
                "keep in mind", "note that", "make sure to remember",
                "store this", "save this information", "memorize"
            ]
        
        if self.context_importance_mapping is None:
            self.context_importance_mapping = {
                "profile": 0.9,
                "personal": 0.9,
                "health": 0.9,
                "security": 0.9,
                "important": 0.9,
                "preference": 0.7,
                "setting": 0.7,
                "work": 0.7,
                "project": 0.7,
                "temporary": 0.3,
                "session": 0.3,
                "ui": 0.3,
                "interaction": 0.3
            }

@dataclass
class RAGAPIConfig:
    """RAG Memory API configuration"""
    
    # API Server Settings
    api_host: str = "0.0.0.0"
    api_port: int = 5001
    api_version: str = "2.0.0"
    api_title: str = "Enhanced Memory API with RAG"
    api_description: str = "Dual-database memory system with Redis + ChromaDB"
    
    # Request/Response Settings
    default_limit: int = 10
    max_limit: int = 100
    request_timeout: int = 10
    
    # Performance Settings
    max_context_length: int = 4000
    enable_caching: bool = True
    cache_ttl: int = 300  # 5 minutes
    
    def __post_init__(self):
        """Load from environment variables"""
        self.api_host = os.getenv("MEMORY_API_HOST", self.api_host)
        self.api_port = int(os.getenv("MEMORY_API_PORT", str(self.api_port)))

@dataclass
class RAGPersonaConfig:
    """RAG-enhanced persona configuration"""
    
    # Persona Files - Simplified to use unified prompt only
    unified_prompt_path: str = "config/unified_prompt.json"  # Single unified persona for all scenarios
    
    # Memory Integration
    memory_acknowledgment_required: bool = True
    memory_acknowledgment_priority: str = "absolute_first"
    
    # Model Optimization
    model_size_threshold: int = 4000000000  # 4B parameters
    use_small_model_persona: bool = True
    
    # RAG Features
    enable_memory_first_responses: bool = True
    enable_semantic_search: bool = True
    enable_explicit_memory_processing: bool = True
    enable_importance_classification: bool = True
    
    def __post_init__(self):
        """Load from environment variables"""
        self.memory_acknowledgment_required = os.getenv(
            "MEMORY_ACKNOWLEDGMENT_REQUIRED", 
            str(self.memory_acknowledgment_required)
        ).lower() == "true"
        
        self.enable_memory_first_responses = os.getenv(
            "ENABLE_MEMORY_FIRST_RESPONSES",
            str(self.enable_memory_first_responses)
        ).lower() == "true"

@dataclass
class RAGSystemConfig:
    """Complete RAG system configuration"""
    
    # Component configurations
    database: RAGDatabaseConfig = None
    classification: MemoryClassificationConfig = None
    api: RAGAPIConfig = None
    persona: RAGPersonaConfig = None
    
    # System Settings
    debug_mode: bool = False
    log_level: str = "INFO"
    environment: str = "production"
    
    # Performance Monitoring
    enable_metrics: bool = True
    metrics_endpoint: str = "/metrics"
    health_check_interval: int = 30
    
    def __post_init__(self):
        """Initialize component configurations"""
        if self.database is None:
            self.database = RAGDatabaseConfig()
        
        if self.classification is None:
            self.classification = MemoryClassificationConfig()
        
        if self.api is None:
            self.api = RAGAPIConfig()
        
        if self.persona is None:
            self.persona = RAGPersonaConfig()
        
        # Load from environment
        self.debug_mode = os.getenv("DEBUG_MODE", str(self.debug_mode)).lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", self.log_level)
        self.environment = os.getenv("ENVIRONMENT", self.environment)

# Global configuration instance
rag_config = RAGSystemConfig()

# Storage Strategy Configuration
STORAGE_STRATEGIES = {
    "redis_only": {
        "description": "Short-term memory in Redis only",
        "importance_range": (0.0, 0.4),
        "databases": ["redis"],
        "ttl": rag_config.database.short_term_ttl,
        "use_cases": ["temporary interactions", "ui state", "session data"]
    },
    "dual_storage": {
        "description": "Medium-term memory in both Redis and ChromaDB",
        "importance_range": (0.5, 0.7),
        "databases": ["redis", "chromadb"],
        "ttl": rag_config.database.medium_term_ttl,
        "use_cases": ["preferences", "work info", "project data"]
    },
    "chroma_priority": {
        "description": "Long-term memory prioritizing ChromaDB with Redis cache",
        "importance_range": (0.8, 1.0),
        "databases": ["chromadb", "redis"],
        "ttl": rag_config.database.long_term_ttl,
        "use_cases": ["personal info", "explicit memories", "critical data"]
    }
}

# API Endpoints Configuration
API_ENDPOINTS = {
    "health": {
        "path": "/health",
        "method": "GET",
        "description": "System health check with database status"
    },
    "store_memory": {
        "path": "/api/memory/store",
        "method": "POST",
        "description": "Store memory with importance-based routing"
    },
    "store_explicit": {
        "path": "/api/memory/store_explicit",
        "method": "POST",
        "description": "Process explicit memory commands"
    },
    "retrieve_memories": {
        "path": "/api/memory/retrieve",
        "method": "POST",
        "description": "Retrieve memories using RAG strategy"
    },
    "semantic_search": {
        "path": "/api/memory/search/{user_id}",
        "method": "GET",
        "description": "Perform semantic search across memories"
    },
    "memory_stats": {
        "path": "/api/memory/stats/{user_id}",
        "method": "GET",
        "description": "Get comprehensive memory statistics"
    }
}

# Docker Service Configuration
DOCKER_SERVICES = {
    "memory-api": {
        "image": "backend-memory-api",
        "port": 5001,
        "environment": {
            "REDIS_HOST": "redis",
            "CHROMA_HOST": "chroma",
            "MEMORY_API_PORT": "5001"
        },
        "depends_on": ["redis", "chroma"]
    },
    "redis": {
        "image": "redis:7-alpine",
        "port": 6379,
        "healthcheck": {
            "test": ["CMD", "redis-cli", "ping"],
            "interval": "10s",
            "timeout": "5s",
            "retries": 5
        }
    },
    "chroma": {
        "image": "chromadb/chroma:latest",
        "port": 8000,
        "environment": {
            "CHROMA_SERVER_HOST": "0.0.0.0",
            "CHROMA_SERVER_PORT": "8000"
        }
    }
}

# Performance Expectations
PERFORMANCE_TARGETS = {
    "redis_retrieval": {
        "target": "5ms",
        "description": "Ultra-fast Redis memory retrieval"
    },
    "chromadb_search": {
        "target": "100ms",
        "description": "Semantic search with embeddings"
    },
    "dual_database_query": {
        "target": "50ms",
        "description": "Combined Redis + ChromaDB queries"
    },
    "explicit_memory_processing": {
        "target": "200ms",
        "description": "Content extraction and classification"
    }
}

# Feature Flags
FEATURE_FLAGS = {
    "enable_rag_architecture": True,
    "enable_dual_database": True,
    "enable_explicit_memory": True,
    "enable_importance_classification": True,
    "enable_semantic_search": True,
    "enable_memory_statistics": True,
    "enable_network_resilience": True,
    "enable_performance_monitoring": True
}

# System Status
SYSTEM_STATUS = {
    "version": "2.0.0",
    "architecture": "RAG Dual-Database",
    "deployment_date": "2025-07-17",
    "status": "production_ready",
    "databases": ["Redis", "ChromaDB"],
    "features": [
        "importance_based_routing",
        "explicit_memory_processing",
        "semantic_search",
        "dual_database_storage",
        "network_resilience",
        "comprehensive_statistics"
    ]
}

def get_system_info() -> Dict:
    """Get comprehensive system information"""
    return {
        "config": {
            "database": rag_config.database.__dict__,
            "classification": rag_config.classification.__dict__,
            "api": rag_config.api.__dict__,
            "persona": rag_config.persona.__dict__
        },
        "storage_strategies": STORAGE_STRATEGIES,
        "api_endpoints": API_ENDPOINTS,
        "docker_services": DOCKER_SERVICES,
        "performance_targets": PERFORMANCE_TARGETS,
        "feature_flags": FEATURE_FLAGS,
        "system_status": SYSTEM_STATUS
    }

def validate_configuration() -> bool:
    """Validate RAG system configuration"""
    try:
        # Check database configuration
        assert rag_config.database.redis_host, "Redis host not configured"
        assert rag_config.database.chroma_host, "ChromaDB host not configured"
        
        # Check classification configuration
        assert rag_config.classification.explicit_memory_triggers, "Explicit memory triggers not configured"
        assert rag_config.classification.context_importance_mapping, "Context importance mapping not configured"
        
        # Check API configuration
        assert rag_config.api.api_port > 0, "API port not configured"
        assert rag_config.api.api_version, "API version not configured"
        
        # Check persona configuration
        assert rag_config.persona.unified_prompt_path, "Unified prompt path not configured"
        
        return True
        
    except AssertionError as e:
        print(f"Configuration validation failed: {e}")
        return False

if __name__ == "__main__":
    print("RAG Dual-Database Memory System Configuration")
    print("=" * 50)
    
    if validate_configuration():
        print("[OK] Configuration validation passed")
        
        system_info = get_system_info()
        print(f"[OK] System version: {system_info['system_status']['version']}")
        print(f"[OK] Architecture: {system_info['system_status']['architecture']}")
        print(f"[OK] Status: {system_info['system_status']['status']}")
        print(f"[OK] Databases: {', '.join(system_info['system_status']['databases'])}")
        print(f"[OK] Features: {len(system_info['system_status']['features'])} enabled")
        
    else:
        print("[FAIL] Configuration validation failed")
