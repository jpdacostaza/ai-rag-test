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
    Get backend configuration for pipeline usage
    Simplified version for pipeline container with zero-config persistence
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
        }
    }