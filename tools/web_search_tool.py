"""
title: Web Search Tool
author: Backend Team
version: 2.0.0
license: MIT
requirements: aiohttp
description: |-
  Enhanced multi-source web search with caching, advanced parsing, and result ranking.
  Supports DuckDuckGo with extensible architecture for additional search engines.
  Placed in /tools so OpenWebUI auto-registers it as a callable tool for models.
"""

import re
import aiohttp
import hashlib
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

PRINT_PREFIX = "[WebSearchTool]"
print(f"{PRINT_PREFIX} Enhanced Web Search Tool v2.0 Imported (tools directory).")

# In-memory cache for search results
SEARCH_CACHE = {}
CACHE_TTL_SECONDS = 300  # 5 minutes

def get_cache_key(query: str, max_results: int) -> str:
    """Generate a cache key for the query"""
    content = f"{query}:{max_results}"
    return hashlib.md5(content.encode()).hexdigest()

def get_cached_result(cache_key: str) -> Optional[str]:
    """Get cached results if not expired"""
    if cache_key in SEARCH_CACHE:
        result, timestamp = SEARCH_CACHE[cache_key]
        if datetime.now() - timestamp < timedelta(seconds=CACHE_TTL_SECONDS):
            print(f"{PRINT_PREFIX} Using cached result for query")
            return result
        else:
            # Remove expired cache entry
            del SEARCH_CACHE[cache_key]
    return None

def cache_result(cache_key: str, result: str):
    """Cache the search result"""
    SEARCH_CACHE[cache_key] = (result, datetime.now())

def calculate_relevance_score(result: Dict[str, Any], query: str) -> float:
    """Calculate relevance score for ranking"""
    score = 0.0
    query_lower = query.lower()
    title_lower = result['title'].lower()
    snippet_lower = result.get('snippet', '').lower()
    
    # Title relevance (weighted heavily)
    title_words = set(title_lower.split())
    query_words = set(query_lower.split())
    title_match = len(title_words.intersection(query_words)) / max(len(query_words), 1)
    score += title_match * 0.5
    
    # Snippet relevance
    snippet_match = len([word for word in query_words if word in snippet_lower]) / max(len(query_words), 1)
    score += snippet_match * 0.3
    
    # Date recency bonus
    if result.get('date'):
        current_year = datetime.now().year
        if str(current_year) in result['date'] or str(current_year - 1) in result['date']:
            score += 0.1
    
    # Original rank penalty
    rank_penalty = (result.get('rank', 1) - 1) * 0.05
    score = max(0, score - rank_penalty)
    
    return score

def rank_results(results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    """Rank results by relevance score"""
    # Calculate relevance scores
    for result in results:
        result['relevance_score'] = calculate_relevance_score(result, query)
    
    # Sort by relevance score (descending)
    sorted_results = sorted(results, key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    # Remove duplicates (same URL)
    seen_urls = set()
    unique_results = []
    for result in sorted_results:
        if result['url'] not in seen_urls:
            seen_urls.add(result['url'])
            unique_results.append(result)
    
    # Re-assign ranks after filtering
    for i, result in enumerate(unique_results):
        result['rank'] = i + 1
    
    return unique_results

async def _fetch(query: str, timeout: int = 15, user_agent: str = None) -> str:
    """Enhanced fetch with configurable parameters"""
    search_url = "https://html.duckduckgo.com/html/"
    params = {"q": query}
    client_timeout = aiohttp.ClientTimeout(total=timeout)
    headers = {
        "User-Agent": user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    async with aiohttp.ClientSession(timeout=client_timeout) as session:
        async with session.get(search_url, params=params, headers=headers) as resp:
            if resp.status != 200:
                raise RuntimeError(f"DuckDuckGo returned status {resp.status}")
            return await resp.text()

def _parse(html: str, max_results: int) -> List[Dict[str, Any]]:
    """Enhanced parsing with multiple snippet patterns and date extraction"""
    results: List[Dict[str, Any]] = []
    blocks = re.findall(r'<div[^>]*class="[^\"]*result[^\"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
    for i, block in enumerate(blocks[:max_results]):
        link = re.search(r'<a[^>]*class="[^\"]*result__a[^\"]*"[^>]*href="([^\"]*)"[^>]*>(.*?)</a>', block, re.DOTALL)
        if not link:
            continue
        url, title_html = link.group(1), link.group(2)
        title = re.sub(r'<[^>]+>', '', title_html).strip()
        
        # Try multiple patterns for snippets/descriptions - ENHANCED
        snippet = ""
        snippet_patterns = [
            r'<a[^>]*class="[^\"]*result__snippet[^\"]*"[^>]*>(.*?)</a>',
            r'<span[^>]*class="[^\"]*snippet[^\"]*"[^>]*>(.*?)</span>',
            r'class="[^\"]*result__snippet[^\"]*"[^>]*>(.*?)<',
            r'<div[^>]*class="[^\"]*snippet[^\"]*"[^>]*>(.*?)</div>',
            # ENHANCED: Additional patterns for better content extraction
            r'<span[^>]*class="[^\"]*result__description[^\"]*"[^>]*>(.*?)</span>',
            r'<div[^>]*class="[^\"]*result__desc[^\"]*"[^>]*>(.*?)</div>',
            r'<p[^>]*class="[^\"]*desc[^\"]*"[^>]*>(.*?)</p>',
            # Fallback: extract any substantial text between tags
            r'</a>.*?<.*?>(.*?)</.*?>',
        ]
        
        for pattern in snippet_patterns:
            snippet_match = re.search(pattern, block, re.DOTALL)
            if snippet_match:
                raw_snippet = re.sub(r'<[^>]+>', '', snippet_match.group(1)).strip()
                # Clean up common artifacts
                raw_snippet = re.sub(r'\s+', ' ', raw_snippet)
                raw_snippet = re.sub(r'^\W+|\W+$', '', raw_snippet)
                if raw_snippet and len(raw_snippet) > 15:  # Only use substantial snippets
                    snippet = raw_snippet
                    break
        
        # ENHANCED: If no snippet found, try to extract from general text content
        if not snippet or len(snippet) < 20:
            # Look for any meaningful text content in the result block
            text_content = re.sub(r'<[^>]+>', ' ', block)
            text_content = re.sub(r'\s+', ' ', text_content).strip()
            
            # Extract sentences that might be descriptions
            sentences = re.findall(r'[A-Z][^.!?]*[.!?]', text_content)
            if sentences:
                # Take the first substantial sentence as snippet
                for sentence in sentences:
                    clean_sentence = sentence.strip()
                    if len(clean_sentence) > 30 and 'http' not in clean_sentence.lower():
                        snippet = clean_sentence[:200] + ('...' if len(clean_sentence) > 200 else '')
                        break
        
        # ENHANCED: Final fallback - generate descriptive snippet from title and URL
        if not snippet or len(snippet) < 10:
            domain = re.search(r'https?://(?:www\.)?([^/]+)', url)
            domain_name = domain.group(1) if domain else 'website'
            snippet = f"Content from {domain_name} - check the full article for complete information."
        
        # Try to extract date information from the block
        date_info = ""
        date_patterns = [
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',
            r'(\d{4}-\d{2}-\d{2})',
            r'(Aug(?:ust)?\s+\d{1,2},?\s+\d{4})',
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})',
        ]
        
        for pattern in date_patterns:
            date_match = re.search(pattern, block, re.IGNORECASE)
            if date_match:
                date_info = date_match.group(1)
                break
        
        if title and url:
            results.append({
                "title": title, 
                "url": url, 
                "snippet": snippet, 
                "date": date_info,
                "rank": i + 1
            })
    return results

def _format(query: str, results: List[Dict[str, Any]], use_enhanced_format: bool = True) -> str:
    """Enhanced formatting with relevance scores and improved styling"""
    if not results:
        return f"No results found for '{query}'."
    
    if use_enhanced_format:
        out = [f"*** Enhanced Web Search Results for '{query}' ***", ""]
        for r in results:
            relevance = r.get('relevance_score', 0)
            out.append(f"**{r['rank']}. {r['title']}** SCORE: {relevance:.2f}")
            out.append(f"**URL:** {r['url']}")
            if r.get('date'):
                out.append(f"**Date:** {r['date']}")
            
            # ENHANCED: Better content indication
            if r['snippet']:
                snippet_len = len(r['snippet'])
                if snippet_len > 50:
                    out.append(f"**Content Preview:** {r['snippet']}")
                else:
                    out.append(f"**Summary:** {r['snippet']}")
            else:
                out.append("**Content:** (Visit URL for full content)")
            out.append("---")
    else:
        # Original format for backward compatibility
        out = [f"Web Search Results for '{query}':", ""]
        for r in results:
            out.append(f"**{r['rank']}. {r['title']}**")
            out.append(f"URL: {r['url']}")
            if r.get('date'):
                out.append(f"Date: {r['date']}")
            if r['snippet']:
                out.append(f"Content: {r['snippet']}")
            else:
                out.append("Content: (Visit URL for full content)")
            out.append("---")
    
    # Add metadata with enhanced guidance
    out.append(f"**Search completed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    out.append(f"**Total results:** {len(results)}")
    out.append("")
    out.append("**IMPORTANT:** These are real, current web search results. Use the titles, URLs, and available content previews to answer the user's question. For the most complete information, suggest visiting the URLs directly.")
    return "\n".join(out)

class Action:
    """Enhanced OpenWebUI Action class with caching and ranking"""
    
    class Valves(BaseModel):
        priority: int = Field(
            default=1, description="Priority level for this action"
        )
        enable_web_search: bool = Field(
            default=True, description="Enable web search functionality"
        )
        max_results_limit: int = Field(
            default=10, description="Maximum number of search results allowed"
        )
        search_timeout: int = Field(
            default=15, description="Search timeout in seconds"
        )
        user_agent: str = Field(
            default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            description="User agent string for web requests"
        )
        enable_caching: bool = Field(
            default=True, description="Enable result caching"
        )
        enable_ranking: bool = Field(
            default=True, description="Enable intelligent result ranking"
        )
        use_enhanced_format: bool = Field(
            default=True, description="Use enhanced formatting with emojis and relevance scores"
        )

    def __init__(self):
        self.valves = self.Valves()
        self.type = "action"
        
    name = "web_search"
    description = "Enhanced web search with caching, intelligent ranking, and multi-pattern content extraction. Searches DuckDuckGo for current information."
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "max_results": {
                "type": "integer", 
                "minimum": 1, 
                "maximum": 10, 
                "default": 5,
                "description": "Number of results (1-10)"
            },
        },
        "required": ["query"],
        "additionalProperties": False,
    }

    async def run(self, query: str, max_results: int = 5, __event_emitter__=None, **kwargs) -> str:
        print(f"{PRINT_PREFIX} Enhanced Action.run INVOKED! query='{query}' max_results={max_results}")
        
        if not self.valves.enable_web_search:
            print(f"{PRINT_PREFIX} Web search disabled via valves")
            return "Web search is currently disabled."
            
        # Respect the valves limit
        max_results = min(max_results, self.valves.max_results_limit)
        
        # Check cache first if enabled
        cache_key = get_cache_key(query, max_results)
        if self.valves.enable_caching:
            cached_result = get_cached_result(cache_key)
            if cached_result:
                print(f"{PRINT_PREFIX} Returning cached result")
                return cached_result
        
        if __event_emitter__:
            await __event_emitter__({"type": "status", "data": {"description": f"Searching: {query}"}})
        
        try:
            start_time = time.time()
            html = await _fetch(query, self.valves.search_timeout, self.valves.user_agent)
            results = _parse(html, max_results * 2)  # Get more results for better ranking
            
            if __event_emitter__:
                await __event_emitter__({"type": "status", "data": {"description": f"Found {len(results)} results, processing..."}})
            
            # Apply intelligent ranking if enabled
            if self.valves.enable_ranking and results:
                results = rank_results(results, query)
                results = results[:max_results]  # Limit to requested number after ranking
            
            formatted = _format(query, results, self.valves.use_enhanced_format)
            
            # Cache the result if enabled
            if self.valves.enable_caching:
                cache_result(cache_key, formatted)
            
            elapsed = time.time() - start_time
            print(f"{PRINT_PREFIX} Enhanced Action.run SUCCESS! Returning {len(formatted)} chars in {elapsed:.2f}s")
            
            if __event_emitter__:
                await __event_emitter__({"type": "status", "data": {"description": f"Search completed - {len(results)} results ranked"}})
            
            return formatted
            
        except Exception as e:
            print(f"{PRINT_PREFIX} Enhanced Action.run ERROR: {e}")
            if __event_emitter__:
                await __event_emitter__({"type": "status", "data": {"description": f"Search failed: {e}"}})
            return f"Enhanced web search error: {e}"

print(f"{PRINT_PREFIX} Enhanced Action class defined: web_search v2.0")

# Backward compatibility entry point
async def main(query: str, max_results: int = 5, **kwargs) -> str:
    action = Action()
    return await action.run(query=query, max_results=max_results, **kwargs)
