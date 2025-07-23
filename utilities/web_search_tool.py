"""
Web search tool.
DEPRECATED: This module has been replaced by enhanced web search solutions.

Current web search options:
1. RECOMMENDED: Enhanced Web Search Pipeline (pipelines/pipeline_web_search/enhanced_web_search_pipeline.py)
   - OpenWebUI native integration with automatic triggering
   - Zero-configuration setup
   - Real-time uncertainty detection
   - Multiple search engine fallbacks

2. FALLBACK: Enhanced Web Search Tool (utilities/enhanced_web_search.py)
   - Standalone tool for direct API usage
   - Manual triggering required
   - Same search capabilities as pipeline

Migration Guide:
- For OpenWebUI: Enable Enhanced Web Search Pipeline in admin settings
- For direct API: Import from utilities.enhanced_web_search
- Legacy compatibility: This module redirects to appropriate solutions
"""

import logging
from typing import Dict, Any

# Legacy compatibility - redirect to pipeline
logger = logging.getLogger(__name__)

def should_trigger_web_search(query: str, response: str) -> bool:
    """
    DEPRECATED: Use Enhanced Web Search Pipeline instead.
    
    This function is maintained for backward compatibility only.
    The Enhanced Web Search Pipeline provides automatic triggering.
    """
    logger.warning("web_search_tool.should_trigger_web_search is deprecated. Use Enhanced Web Search Pipeline instead.")
    
    # Legacy trigger logic for compatibility
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
    
    query_lower = query.lower()
    
    # Exclude simple math and basic calculations
    if any(math_pattern in query_lower for math_pattern in [
        "what is", "what's", "calculate", "compute"
    ]) and any(math_op in query_lower for math_op in [
        "+", "-", "*", "/", "plus", "minus", "times", "divided", "=", "equals"
    ]):
        return False
    
    # Exclude creative and general requests
    creative_patterns = [
        "write a", "create a", "make a", "generate a", "compose a",
        "poem", "story", "song", "joke", "recipe for"
    ]
    if any(pattern in query_lower for pattern in creative_patterns):
        return False
    
    # Check if query contains time-sensitive or current information requests
    current_info_keywords = [
        "current", "latest", "recent", "today", "now", "2024", "2025",
        "news", "price", "stock", "weather", "breaking", "update"
    ]
    
    # Check for company/organization specific queries (more precise)
    company_keywords = [
        "company", "organization", "business", "corporation", "swift.com",
        "website", "headquarters", "ceo", "founded", "established"
    ]
    
    # More precise "what is" and "who is" for entities (not math)
    entity_patterns = [
        "what is " + word for word in ["swift", "microsoft", "apple", "google", "amazon", "meta", "tesla"]
    ] + [
        "who is the ceo", "who is the founder", "what does", "where is"
    ]
    
    # Check for factual/specific information requests
    factual_keywords = [
        "when was", "how many", "where is", "what happened", 
        "statistics", "data", "facts", "information about"
    ]
    
    # Check for technology/product queries
    tech_keywords = [
        "features", "capabilities", "specifications", "release", "version",
        "launch", "announcement", "product"
    ]
    
    # Trigger for time-sensitive queries
    if any(keyword in query_lower for keyword in current_info_keywords):
        return True
    
    # Trigger for company queries
    if any(keyword in query_lower for keyword in company_keywords):
        return True
    
    # Trigger for entity-specific "what is" queries
    if any(pattern in query_lower for pattern in entity_patterns):
        return True
    
    # Trigger for factual queries
    if any(keyword in query_lower for keyword in factual_keywords):
        return True
    
    # Trigger for tech queries
    if any(keyword in query_lower for keyword in tech_keywords):
        return True
    
    # Special trigger for Swift company queries
    if "swift" in query_lower and ("work" in query_lower or "job" in query_lower or "company" in query_lower or "financial" in query_lower or "services" in query_lower):
        return True
    
    return False


async def search_web(query: str, max_results: int = 3) -> Dict[str, Any]:
    """
    DEPRECATED: Use Enhanced Web Search Pipeline or Enhanced Web Search Tool instead.
    
    This function provides legacy compatibility with redirection options:
    1. For OpenWebUI: Use Enhanced Web Search Pipeline (recommended)
    2. For direct API: Use utilities.enhanced_web_search.search_web()
    """
    from datetime import datetime
    
    logger.warning("web_search_tool.search_web is deprecated. Use Enhanced Web Search Pipeline or utilities.enhanced_web_search instead.")
    
    current_date = datetime.now().strftime("%B %d, %Y")
    current_year = datetime.now().year
    
    logging.info(f"[WEB_SEARCH] Legacy search called for: {query} - redirecting to enhanced solutions")
    
    # Try to import and use enhanced web search as fallback
    try:
        from utilities.enhanced_web_search import search_web as enhanced_search
        logger.info("Redirecting to enhanced_web_search.search_web()")
        result = await enhanced_search(query, max_results)
        
        # Convert to legacy format
        return {
            "query": query,
            "results": [
                {
                    "title": f"Enhanced Web Search Results - {current_date}",
                    "snippet": result,
                    "url": "utilities/enhanced_web_search.py"
                }
            ],
            "total_results": 1,
            "search_time": 0.0,
            "status": "redirected_to_enhanced",
            "message": f"Redirected to Enhanced Web Search Tool - {current_date}"
        }
    except Exception as e:
        logger.error(f"Enhanced web search fallback failed: {e}")
        
        # Return a notice about the available options
        return {
            "query": query,
            "results": [
                {
                    "title": f"Web Search Options Available - {current_date}",
                    "snippet": f"""Multiple web search solutions are available:

1. RECOMMENDED: Enhanced Web Search Pipeline
   • Location: pipelines/pipeline_web_search/enhanced_web_search_pipeline.py
   • Features: Automatic triggering, OpenWebUI integration, zero-config
   • Setup: Enable in OpenWebUI admin settings

2. DIRECT API: Enhanced Web Search Tool  
   • Location: utilities/enhanced_web_search.py
   • Features: Same search capabilities, manual triggering
   • Usage: from utilities.enhanced_web_search import search_web

Your query: "{query}" - use either solution above for current {current_year} results.

Error with fallback: {str(e)}""",
                    "url": "utilities/enhanced_web_search.py"
                }
            ],
            "total_results": 1,
            "search_time": 0.0,
            "status": "deprecated_with_options",
            "message": f"Web search options available - {current_date}"
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
