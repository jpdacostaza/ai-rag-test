"""
Tools Package
============

This package contains various tools for the AI RAG backend system.
"""

# Import main tools for package-level access
try:
    from utilities.enhanced_web_search import search_web as web_search
    from functions.tools.weather_tool import Tools as WeatherTools
    
    __all__ = ['web_search', 'WeatherTools']
    
except ImportError:
    # If imports fail, create empty list
    __all__ = []
