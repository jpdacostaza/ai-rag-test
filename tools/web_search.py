"""
Web Search Module for Backend Import
===================================

This module provides the web search functionality that the backend expects.
It re-exports the main web search tool functions for backend compatibility.
"""

# Import the main web search tool functions
try:
    from .web_search_tool import Action as WebSearchAction
    
    # Create WebSearchTool wrapper class
    class WebSearchTool:
        def __init__(self):
            self._action = WebSearchAction()
            self.valves = getattr(self._action, 'valves', None)
        
        async def search_web(self, query: str, max_results: int = 5):
            """Perform web search using Action class"""
            try:
                # The Action class has a web_search method that takes a body parameter
                body = {"query": query, "max_results": max_results}
                result = await self._action.web_search(body)
                return result
            except Exception as e:
                return {"error": f"Search failed: {str(e)}", "query": query}
    
    # Create module-level search function
    async def search_web(query: str, max_results: int = 5):
        """Module-level search function"""
        tool = WebSearchTool()
        return await tool.search_web(query, max_results)
    
    # Create the Tools class that the backend expects
    class Tools:
        """Tools class for backend compatibility"""
        
        def __init__(self):
            self.web_search_tool = WebSearchTool()
        
        async def search_web(self, query: str, num_results: int = 5):
            """Perform web search"""
            return await self.web_search_tool.search_web(query, num_results)
        
        async def web_search(self, query: str, num_results: int = 5):
            """Alias for search_web"""
            return await self.search_web(query, num_results)
    
    # Re-export for backend compatibility
    __all__ = ['Tools', 'WebSearchTool', 'search_web', 'web_search', 'search']
    
    # Create aliases for different import patterns
    web_search = search_web
    search = search_web
    
    def get_web_search_tool():
        """Factory function to get web search tool instance"""
        return WebSearchTool()
    
    # Module-level search function for direct import
    async def perform_web_search(query: str, num_results: int = 5):
        """Perform web search with default settings"""
        tool = WebSearchTool()
        return await tool.search_web(query, num_results)
    
except ImportError as e:
    # Fallback if web_search_tool is not available
    print(f"[WARNING] Web search tool not available: {e}")
    
    # Create stub Tools class
    class Tools:
        """Stub Tools class when web search is not available"""
        
        def __init__(self):
            pass
        
        async def search_web(self, *args, **kwargs):
            return {"error": "Web search not available"}
        
        async def web_search(self, *args, **kwargs):
            return {"error": "Web search not available"}
    
    # Create stub functions
    def search_web(*args, **kwargs):
        return {"error": "Web search not available"}
    
    def web_search(*args, **kwargs):
        return {"error": "Web search not available"}
    
    def search(*args, **kwargs):
        return {"error": "Web search not available"}
    
    class WebSearchTool:
        def __init__(self):
            pass
        
        async def search_web(self, *args, **kwargs):
            return {"error": "Web search not available"}
    
    def get_web_search_tool():
        return WebSearchTool()
    
    async def perform_web_search(*args, **kwargs):
        return {"error": "Web search not available"}
    
    __all__ = ['Tools', 'WebSearchTool', 'search_web', 'web_search', 'search']
