"""
Enhanced Memory System Module
=============================

This module contains all memory-related functionality including:
- API endpoints for memory operations  
- Memory functions for OpenWebUI
- Utility functions for memory management
- Separated core memory logic
"""

from .api.enhanced_memory_api import app as memory_api_app
from .core import MemoryClient, MemoryConfig, MemoryQuery, MemoryRecord, MemoryResponse, IMemoryProvider
from .service import MemoryService
from .providers import MemoryProviderFactory

__version__ = "2.0.0"
__all__ = [
    "memory_api_app",
    'MemoryService',
    'MemoryClient', 
    'MemoryConfig',
    'MemoryQuery',
    'MemoryRecord',
    'MemoryResponse',
    'IMemoryProvider',
    'MemoryProviderFactory'
]
