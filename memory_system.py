"""
Memory System Compatibility Module
=================================

This module provides backward compatibility for direct imports of memory_system.
Redirects to the actual implementation in pipelines/memory_system/.

This file provides the same interface as memory_system/__init__.py but as a 
single module file for environments that prefer direct module imports.
"""

# Import from the actual memory system implementation
try:
    from pipelines.memory_system import *
    from pipelines.memory_system.processor import MemoryProcessor
    from pipelines.memory_system.config import MemoryConfig
    
    # Make commonly used classes available at module level
    __all__ = [
        'MemoryProcessor',
        'MemoryConfig'
    ]
    
except ImportError as e:
    # Fallback if pipelines.memory_system is not available
    import logging
    logging.warning(f"Memory system implementation not available: {e}")
    
    # Provide stub classes for compatibility
    class MemoryProcessor:
        def __init__(self, *args, **kwargs):
            logging.warning("MemoryProcessor stub - real implementation not available")
            
        def process(self, *args, **kwargs):
            logging.warning("MemoryProcessor.process stub called")
            return None
    
    class MemoryConfig:
        def __init__(self, *args, **kwargs):
            logging.warning("MemoryConfig stub - real implementation not available")
    
    __all__ = [
        'MemoryProcessor',
        'MemoryConfig'
    ]
