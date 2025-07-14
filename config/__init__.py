"""
Configuration module for the FastAPI backend.
"""

# Import pipeline configuration for pipelines service
try:
    from .pipeline_config import API_KEY, PIPELINES_DIR, LOG_LEVELS
except ImportError:
    # Fallback values if pipeline_config is not available
    import os
    import logging
    API_KEY = os.getenv("PIPELINES_API_KEY", "0p3n-w3bu!")
    PIPELINES_DIR = os.getenv("PIPELINES_DIR", "./pipelines")
    LOG_LEVELS = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }

__all__ = ["API_KEY", "PIPELINES_DIR", "LOG_LEVELS"]
