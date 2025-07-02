"""
Web search tool.
Provides web search functionality using utilities.ai_tools.
"""

import logging
from typing import Dict, Any
from utilities.ai_tools import web_search as ai_tools_web_search


def should_trigger_web_search(query: str, response: str) -> bool:
    """
    Determine if a web search should be triggered based on the query and response.
    
    Args:
        query: The user's query
        response: The LLM's initial response
        
    Returns:
        bool: True if web search should be triggered
    """
    # Check if the response indicates uncertainty or lack of information
    uncertainty_phrases = [
        "i don't know",
        "i'm not sure",
        "i don't have",
        "i cannot provide",
        "i'm unable to",
        "no information",
        "not available",
        "unclear",
        "uncertain"
    ]
    
    response_lower = response.lower()
    if any(phrase in response_lower for phrase in uncertainty_phrases):
        return True
    
    # Check if query contains time-sensitive or current information requests
    current_info_keywords = [
        "current", "latest", "recent", "today", "now", "2024", "2023",
        "news", "price", "stock", "weather", "breaking"
    ]
    
    query_lower = query.lower()
    if any(keyword in query_lower for keyword in current_info_keywords):
        return True
    
    return False


async def search_web(query: str, max_results: int = 3) -> Dict[str, Any]:
    """
    Perform web search for the given query.
    
    Args:
        query: The search query
        max_results: Maximum number of results to return
        
    Returns:
        Dict containing search results
    """
    logging.info(f"[WEB_SEARCH] Performing web search for: {query}")
    
    try:
        # Use real web search from utilities.ai_tools
        result = ai_tools_web_search(query, num_results=max_results)
        
        # Format the result into our expected structure
        search_results = {
            "query": query,
            "results": [],
            "total_results": 0,
            "search_time": 0.0,
            "status": "success",
            "message": "Search completed successfully"
        }
        
        # Check if we got a valid result string
        if result and isinstance(result, str):
            # Parse the result and add to our structure
            # This is a simple implementation - in a real system you'd want 
            # to parse structured data rather than text
            search_results["results"] = [
                {
                    "title": "Search Result",
                    "snippet": result,
                    "url": "#"
                }
            ]
            search_results["total_results"] = 1
        else:
            search_results["status"] = "no_results"
            search_results["message"] = "No search results found"
            
        return search_results
    
    except Exception as e:
        logging.error(f"[WEB_SEARCH] Error performing search: {str(e)}")
        return {
            "query": query,
            "results": [],
            "total_results": 0,
            "search_time": 0.0,
            "status": "error",
            "message": f"Search error: {str(e)}"
        }


def format_web_results_for_chat(search_results: Dict[str, Any]) -> str:
    """
    Format web search results for inclusion in chat response.
    
    Args:
        search_results: Search results from search_web()
        
    Returns:
        str: Formatted string for chat inclusion
    """
    if not search_results.get("results"):
        return "\n[Note: Web search yielded no results]"
    
    formatted = "\n\n## Web Search Results:\n"
    
    for i, result in enumerate(search_results["results"][:3], 1):
        title = result.get("title", "No Title")
        snippet = result.get("snippet", "No description available")
        url = result.get("url", "#")
        
        formatted += f"\n{i}. **{title}**\n"
        formatted += f"   {snippet}\n"
        formatted += f"   Source: {url}\n"
    
    return formatted
