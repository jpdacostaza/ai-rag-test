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