"""
Tools Package
============

This package contains various tools for the AI RAG backend system.
"""

# Import main tools for package-level access
try:
    from .web_search_tool import WebSearchTool
    from .web_search import search_web, web_search
    
    __all__ = ['WebSearchTool', 'search_web', 'web_search']
    
except ImportError:
    # If imports fail, create empty list
    __all__ = []
