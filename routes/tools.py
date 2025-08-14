"""
Tools router for exposing tool functionality to OpenWebUI.
Provides endpoints for web search and other tools.
Note: KNMI API endpoints removed - weather tool now uses web search directly.
"""

import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any

from core.unified_logging import log_service_status
from utilities.simple_error_handling import handle_api_errors

tools_router = APIRouter(prefix="/tools", tags=["tools"])

# Import web search tool
try:
    from utilities.enhanced_web_search import search_web
    WEB_SEARCH_AVAILABLE = True
    log_service_status("TOOLS", "info", "Zero-conf web search available")
except ImportError as e:
    WEB_SEARCH_AVAILABLE = False
    log_service_status("TOOLS", "warning", f"Web search tool not available: {e}")


@tools_router.get("/")
async def list_tools():
    """List available tools."""
    tools = []
    
    if WEB_SEARCH_AVAILABLE:
        tools.append({
            "name": "web_search", 
            "description": "Search the web for current information",
            "enabled": True
        })
    
    # Note: Weather tool now uses web search directly via OpenWebUI actions
    tools.append({
        "name": "netherlands_weather",
        "description": "Netherlands weather via web search (handled by weather tool)",
        "enabled": True,
        "type": "action"
    })
    
    return {"tools": tools}


@tools_router.post("/web_search")
@handle_api_errors("web_search")
async def web_search_endpoint(request: Dict[str, Any] = Body(...)):
    """
    Web search endpoint for OpenWebUI.
    
    Args:
        request: Request body containing:
            - query: Search query string
            - max_results: Maximum number of results (optional, default: 5)
    
    Returns:
        Search results with sources and timestamps
    """
    if not WEB_SEARCH_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Web search functionality is not available"
        )
    
    query = request.get("query")
    if not query:
        raise HTTPException(
            status_code=400,
            detail="Missing required parameter: query"
        )
    
    max_results = request.get("max_results", 5)
    
    try:
        log_service_status("TOOLS", "info", f"Web search requested: '{query}' (max_results={max_results})")
        
        # Call the zero-conf web search
        search_results = await search_web(query, max_results=max_results)
        
        log_service_status("TOOLS", "ready", f"Web search completed for query: '{query}'")
        
        return {
            "success": True,
            "query": query,
            "results": search_results.get("results", []),
            "summary": search_results.get("summary", ""),
            "strategies_attempted": search_results.get("strategies_attempted", []),
            "max_results": max_results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        log_service_status("TOOLS", "error", f"Web search failed for query '{query}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Web search failed: {str(e)}"
        )
