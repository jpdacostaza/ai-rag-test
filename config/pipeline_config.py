import os
import logging

####################################
# Load .env file
####################################
try:
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv("./.env"))
except ImportError:
    print("dotenv not installed, skipping...")

# Define log levels dictionary
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

# Required by OpenWebUI Pipelines
API_KEY = os.getenv("PIPELINES_API_KEY", "0p3n-w3bu!")
PIPELINES_DIR = os.getenv("PIPELINES_DIR", "./pipelines")

def get_config():
    """
    Get backend configuration for pipeline usage - RAG Architecture
    Enhanced configuration for RAG dual-database system with zero-config persistence
    """
    return {
        'backend_url': os.getenv('BACKEND_URL', 'http://backend-memory-api:8003'),
        'redis_host': os.getenv('REDIS_HOST', 'backend-redis'),
        'redis_port': int(os.getenv('REDIS_PORT', '6379')),
        'chroma_host': os.getenv('CHROMA_HOST', 'backend-chroma'),  
        'chroma_port': int(os.getenv('CHROMA_PORT', '8000')),
        'memory_api_url': os.getenv('MEMORY_API_URL', 'http://backend-memory-api:8003'),
        'authentication': {
            'enabled': True,
            'token_required': False
        },
        'memory_settings': {
            'max_context_length': 4000,
            'persona_optimization': True,
            'model_size_threshold': 4000000000  # 4B parameters
        },
        'database_config': {
            'redis_url': f"redis://{os.getenv('REDIS_HOST', 'backend-redis')}:{os.getenv('REDIS_PORT', '6379')}",
            'chroma_url': f"http://{os.getenv('CHROMA_HOST', 'backend-chroma')}:{os.getenv('CHROMA_PORT', '8000')}"
        },
        # RAG System Configuration
        'rag_config': {
            'system_version': '2.0.0',
            'architecture': 'dual_database',
            'enable_rag_architecture': True,
            'enable_dual_database': True,
            'enable_explicit_memory': True,
            'enable_importance_classification': True,
            'enable_semantic_search': True,
            'storage_strategies': {
                'redis_only': {
                    'importance_range': (0.0, 0.4),
                    'ttl': 3600,
                    'description': 'Short-term memory in Redis only'
                },
                'dual_storage': {
                    'importance_range': (0.5, 0.7),
                    'ttl': 43200,
                    'description': 'Medium-term memory in both Redis and ChromaDB'
                },
                'chroma_priority': {
                    'importance_range': (0.8, 1.0),
                    'ttl': 86400,
                    'description': 'Long-term memory prioritizing ChromaDB'
                }
            },
            'importance_thresholds': {
                'short_term': 0.2,  # Lowered for better memory capture
                'long_term': 0.5    # Lowered for more long-term storage
            },
            'explicit_memory_triggers': [
                'remember', 'don\'t forget', 'please remember',
                'keep in mind', 'note that', 'make sure to remember',
                'store this', 'save this information', 'memorize'
            ]
        }
    }