"""
Pipeline Configuration for OpenWebUI
Provides configuration settings for enhanced memory pipeline with Docker service endpoints
"""

def get_config():
    """
    Get pipeline configuration with corrected Docker service names
    """
    return {
        'backend_url': 'http://backend-memory-api:8080',
        'redis_host': 'backend-redis',
        'redis_port': 6379,
        'chroma_host': 'backend-chroma',
        'chroma_port': 8000,
        'memory_api_url': 'http://backend-memory-api:8080',
        'authentication': {
            'enabled': True,
            'token_required': False
        },
        'memory_settings': {
            'max_context_length': 4000,
            'persona_optimization': True,
            'model_size_threshold': 4000000000  # 4B parameters
        }
    }

# Configuration dictionary for backward compatibility
CONFIG = get_config()

# Direct access variables
BACKEND_URL = 'http://backend-memory-api:8080'
REDIS_HOST = 'backend-redis'
REDIS_PORT = 6379
CHROMA_HOST = 'backend-chroma'
CHROMA_PORT = 8000
MEMORY_API_URL = 'http://backend-memory-api:8080'