"""
Enhanced Web Search Tool for OpenWebUI
====================================
Simple, reliable web search using only DDGS library.
Based on official OpenWebUI web search implementations.
Zero-configuration deployment with persistent setup.
"""

import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    # Try modern ddgs package first (recommended)
    from ddgs import DDGS
    DDGS_AVAILABLE = True
    print("[WEB SEARCH] Using modern ddgs package")
except ImportError:
    try:
        # Fallback to legacy duckduckgo-search
        from duckduckgo_search import DDGS
        DDGS_AVAILABLE = True
        print("[WEB SEARCH] Using legacy duckduckgo-search package (consider upgrading to ddgs)")
    except ImportError:
        DDGS_AVAILABLE = False
        print("[WEB SEARCH] Warning: Neither ddgs nor duckduckgo-search available. Install with: pip install ddgs")


class WebSearchTool:
    """Reliable web search tool using only DDGS library"""
    
    def __init__(self):
        self.current_year = datetime.now().year
        self.current_date = datetime.now().strftime("%B %d, %Y")
        
    async def search_current_news(self, query: str, max_results: int = 5) -> str:
        """
        Search for current news using DDGS with multiple search strategies
        """
        if not DDGS_AVAILABLE:
            return f" Web Search Status ({self.current_date}):\n\nWeb search unavailable. DDGS library not installed.\nPlease install with: pip install ddgs"
        
        # Enhanced search strategies for better results
        search_strategies = [
            ("Primary search", lambda q: q),
            ("News-focused search", lambda q: f"news {q} 2025"),
            ("Recent search", lambda q: f"recent {q}"),
            ("Current search", lambda q: f"current {q} latest"),
        ]
        
        for strategy_name, query_modifier in search_strategies:
            try:
                search_query = query_modifier(query)
                print(f"[WEB SEARCH] Trying {strategy_name} with DDGS...")
                result = await self._search_with_ddgs(search_query, max_results)
                if result and len(result.strip()) > 50:  # Ensure we got meaningful results
                    print(f"[WEB SEARCH] [OK] {strategy_name} succeeded")
                    return f" Current Web Search Results ({self.current_date}):\n\n{result}"
                else:
                    print(f"[WEB SEARCH] [FAIL] {strategy_name} returned insufficient data")
            except Exception as e:
                print(f"[WEB SEARCH] [FAIL] {strategy_name} failed: {e}")
                continue
        
        # If all strategies fail, provide a helpful response
        return f" Web Search Status ({self.current_date}):\n\nWeb search temporarily unavailable. All DDGS search strategies attempted:\n- Primary search\n- News-focused search\n- Recent search\n- Current search\n\nPlease try rephrasing your query or check back shortly."
    
    async def _search_with_ddgs(self, query: str, max_results: int) -> str:
        """Search using DDGS library (official OpenWebUI implementation pattern)"""
        try:
            print(f"[WEB SEARCH] Using DDGS library for: {query}")
            
            results = []
            
            # Use DDGS context manager pattern (official OpenWebUI approach)
            with DDGS() as ddgs:
                try:
                    # Primary search with modern parameters (query as first positional argument)
                    search_results = ddgs.text(
                        query,  # Query as positional argument
                        region="wt-wt",  # Worldwide
                        safesearch="moderate",
                        max_results=max_results
                    )
                    
                    for result in search_results:
                        results.append({
                            "title": result.get("title", ""),
                            "link": result.get("href", ""),
                            "snippet": result.get("body", ""),
                            "source": "DuckDuckGo"
                        })
                        
                except Exception as ddgs_error:
                    print(f"[WEB SEARCH] DDGS text search failed: {ddgs_error}")
                    # Try news search as fallback
                    try:
                        news_results = ddgs.news(
                            query,  # Query as positional argument
                            region="wt-wt",
                            safesearch="moderate",
                            max_results=max_results
                        )
                        
                        for result in news_results:
                            results.append({
                                "title": result.get("title", ""),
                                "link": result.get("url", ""),
                                "snippet": result.get("body", ""),
                                "source": "DuckDuckGo News"
                            })
                            
                    except Exception as news_error:
                        print(f"[WEB SEARCH] DDGS news search also failed: {news_error}")
                        raise Exception(f"Both text and news search failed: {ddgs_error}")
            
            if results:
                formatted_results = []
                for i, result in enumerate(results, 1):
                    title = result["title"] or "No title"
                    snippet = result["snippet"] or "No description available"
                    link = result["link"] or ""
                    
                    formatted_results.append(
                        f"{i}. **{title}**\n"
                        f"   {snippet}\n"
                        f"    {link}\n"
                    )
                
                return "\n".join(formatted_results)
            else:
                raise Exception("No results returned from DDGS")
                
        except Exception as e:
            print(f"[WEB SEARCH] DDGS search failed: {e}")
            raise Exception(f"DDGS search failed: {str(e)}")


# For backwards compatibility - keep the original function signatures
async def search_web(query: str, max_results: int = 5) -> str:
    """Legacy function for backwards compatibility"""
    tool = WebSearchTool()
    return await tool.search_current_news(query, max_results)


def should_trigger_web_search(query: str) -> bool:
    """Determine if a query should trigger web search"""
    search_indicators = [
        "search for", "find information about", "what's the latest on",
        "current news about", "recent developments", "look up",
        "search the web", "find online", "web search", "latest news",
        "recent news", "current events", "what happened", "news about"
    ]
    
    return any(indicator in query.lower() for indicator in search_indicators)


# Export the main tool class
__all__ = ["WebSearchTool", "search_web", "should_trigger_web_search"]
