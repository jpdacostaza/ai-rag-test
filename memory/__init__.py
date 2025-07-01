"""
Memory System Module

This module contains all memory-related functionality including:
- API endpoints for memory operations
- Memory functions for OpenWebUI
- Utility functions for memory management
"""

from .api.main import app as memory_api_app

__version__ = "2.0.0"
__all__ = ["memory_api_app"]
