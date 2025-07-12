"""
Simplified web search tool for OpenWebUI pipelines.
Self-contained version with minimal dependencies.
"""

import asyncio
import httpx
import json
import re
from typing import Dict, Any, List, Optional
from urllib.parse import quote_plus


def should_trigger_web_search(query: str, response: str = "") -> bool:
    """
    Determine if a web search should be triggered based on the query.
    
    Args:
        query: The user's query
        response: The LLM's initial response (optional)
        
    Returns:
        bool: True if web search should be triggered
    """
    if not query or len(query.strip()) < 3:
        return False
    
    query_lower = query.lower()
    
    # Explicit search triggers
    explicit_triggers = [
        "search the web", "google this", "look up", "find online", 
        "search for", "web search", "google", "bing", "search"
    ]
    
    for trigger in explicit_triggers:
        if trigger in query_lower:
            return True
    
    # Current information triggers
    current_info_triggers = [
        "current", "latest", "recent", "today", "now", "new", 
        "price", "weather", "news", "stock", "update"
    ]
    
    for trigger in current_info_triggers:
        if trigger in query_lower:
            return True
    
    # Company/specific information triggers
    if any(word in query_lower for word in ["company", "website", "contact", "address", "phone"]):
        return True
    
    return False


async def search_web(query: str, max_results: int = 3) -> Dict[str, Any]:
    """
    Perform a web search using DuckDuckGo.
    
    Args:
        query: Search query
        max_results: Maximum number of results to return
        
    Returns:
        Dict containing search results
    """
    try:
        print(f"[PIPELINE WEB SEARCH] Searching for: {query}")
        
        # Use DuckDuckGo instant answer API
        search_url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&no_html=1&skip_disambig=1"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(search_url)
            data = response.json()
            
            results = []
            
            # Extract abstract if available
            if data.get("Abstract"):
                results.append({
                    "title": data.get("AbstractText", "Information"),
                    "content": data.get("Abstract"),
                    "url": data.get("AbstractURL", ""),
                    "source": "DuckDuckGo"
                })
            
            # Extract related topics
            if data.get("RelatedTopics"):
                for topic in data.get("RelatedTopics", [])[:max_results-len(results)]:
                    if isinstance(topic, dict) and topic.get("Text"):
                        results.append({
                            "title": topic.get("Text", "")[:100] + "..." if len(topic.get("Text", "")) > 100 else topic.get("Text", ""),
                            "content": topic.get("Text", ""),
                            "url": topic.get("FirstURL", ""),
                            "source": "DuckDuckGo"
                        })
            
            # If no results, try definition
            if not results and data.get("Definition"):
                results.append({
                    "title": "Definition",
                    "content": data.get("Definition"),
                    "url": data.get("DefinitionURL", ""),
                    "source": "DuckDuckGo"
                })
            
            print(f"[PIPELINE WEB SEARCH] Found {len(results)} results")
            
            return {
                "query": query,
                "results": results,
                "status": "success" if results else "no_results"
            }
            
    except Exception as e:
        print(f"[PIPELINE WEB SEARCH ERROR] {e}")
        return {
            "query": query,
            "results": [],
            "status": "error",
            "error": str(e)
        }


def format_web_results_for_chat(search_results: Dict[str, Any]) -> str:
    """
    Format web search results for inclusion in chat context.
    
    Args:
        search_results: Results from search_web function
        
    Returns:
        Formatted string for chat context
    """
    if not search_results.get("results"):
        return ""
    
    formatted = "\n\n🌐 Current Web Information:\n"
    
    for i, result in enumerate(search_results["results"], 1):
        title = result.get("title", "")
        content = result.get("content", "")
        url = result.get("url", "")
        
        # Truncate content if too long
        if len(content) > 300:
            content = content[:300] + "..."
        
        formatted += f"\n{i}. {title}\n"
        formatted += f"   {content}\n"
        if url:
            formatted += f"   Source: {url}\n"
    
    formatted += "\nPlease use this current information to answer the user's question."
    
    return formatted


# Test function for debugging
async def test_search():
    """Test the web search functionality."""
    query = "current weather in Paris"
    results = await search_web(query)
    print(json.dumps(results, indent=2))
    print("\nFormatted for chat:")
    print(format_web_results_for_chat(results))


if __name__ == "__main__":
    asyncio.run(test_search())
