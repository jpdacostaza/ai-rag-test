"""
title: Web Search Tool
author: Backend Team
version: 1.1.0
license: MIT
requirements: aiohttp
description: |-
  Real-time DuckDuckGo HTML search returning top results with titles, URLs, and snippets.
  Placed in /tools so OpenWebUI auto-registers it as a callable tool for models.
"""

import re
import aiohttp
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

PRINT_PREFIX = "[WebSearchTool]"
print(f"{PRINT_PREFIX} Imported (tools directory).")


async def _fetch(query: str) -> str:
    search_url = "https://html.duckduckgo.com/html/"
    params = {"q": query}
    timeout = aiohttp.ClientTimeout(total=15)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    }
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(search_url, params=params, headers=headers) as resp:
            if resp.status != 200:
                raise RuntimeError(f"DuckDuckGo returned status {resp.status}")
            return await resp.text()


def _parse(html: str, max_results: int) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    blocks = re.findall(r'<div[^>]*class="[^\"]*result[^\"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
    for i, block in enumerate(blocks[:max_results]):
        link = re.search(r'<a[^>]*class="[^\"]*result__a[^\"]*"[^>]*href="([^\"]*)"[^>]*>(.*?)</a>', block, re.DOTALL)
        if not link:
            continue
        url, title_html = link.group(1), link.group(2)
        title = re.sub(r'<[^>]+>', '', title_html).strip()
        
        # Try multiple patterns for snippets/descriptions
        snippet = ""
        snippet_patterns = [
            r'<a[^>]*class="[^\"]*result__snippet[^\"]*"[^>]*>(.*?)</a>',
            r'<span[^>]*class="[^\"]*snippet[^\"]*"[^>]*>(.*?)</span>',
            r'class="[^\"]*result__snippet[^\"]*"[^>]*>(.*?)<',
            r'<div[^>]*class="[^\"]*snippet[^\"]*"[^>]*>(.*?)</div>',
        ]
        
        for pattern in snippet_patterns:
            snippet_match = re.search(pattern, block, re.DOTALL)
            if snippet_match:
                snippet = re.sub(r'<[^>]+>', '', snippet_match.group(1)).strip()
                if snippet and len(snippet) > 10:  # Only use substantial snippets
                    break
        
        # Try to extract date information from the block
        date_info = ""
        date_patterns = [
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',
            r'(\d{4}-\d{2}-\d{2})',
            r'(Aug(?:ust)?\s+\d{1,2},?\s+\d{4})',
            r'(\d{1,2}/\d{1,2}/\d{4})',
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


def _format(query: str, results: List[Dict[str, Any]]) -> str:
    if not results:
        return f"No results found for '{query}'."
    out = [f"Web Search Results for '{query}':", ""]
    for r in results:
        out.append(f"**{r['rank']}. {r['title']}**")
        out.append(f"URL: {r['url']}")
        if r.get('date'):
            out.append(f"Date: {r['date']}")
        if r['snippet']:
            out.append(f"Content: {r['snippet']}")
        else:
            out.append("Content: (No preview available)")
        out.append("---")  # separator
    out.append(f"Search completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    out.append(f"Total results: {len(results)}")
    out.append("")
    out.append("IMPORTANT: Use this information to answer the user's question. These are real, current web search results.")
    return "\n".join(out)


class Action:
    """OpenWebUI Action class for web search functionality"""
    
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

    def __init__(self):
        self.valves = self.Valves()
        self.type = "action"
        
    name = "web_search"
    description = "Searches the public web (DuckDuckGo) for current info and returns summarized results."
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
        print(f"{PRINT_PREFIX} Action.run INVOKED! query='{query}' max_results={max_results}")
        
        if not self.valves.enable_web_search:
            print(f"{PRINT_PREFIX} Web search disabled via valves")
            return "Web search is currently disabled."
            
        # Respect the valves limit
        max_results = min(max_results, self.valves.max_results_limit)
        
        if __event_emitter__:
            await __event_emitter__({"type": "status", "data": {"description": f"Searching: {query}"}})
        try:
            html = await self._fetch(query)
            results = self._parse(html, max_results)
            if __event_emitter__:
                await __event_emitter__({"type": "status", "data": {"description": f"Found {len(results)} results"}})
            formatted = _format(query, results)
            print(f"{PRINT_PREFIX} Action.run SUCCESS! Returning {len(formatted)} chars")
            return formatted
        except Exception as e:
            print(f"{PRINT_PREFIX} Action.run ERROR: {e}")
            if __event_emitter__:
                await __event_emitter__({"type": "status", "data": {"description": f"Failed: {e}"}})
            return f"Web search error: {e}"

    async def _fetch(self, query: str) -> str:
        search_url = "https://html.duckduckgo.com/html/"
        params = {"q": query}
        timeout = aiohttp.ClientTimeout(total=self.valves.search_timeout)
        headers = {"User-Agent": self.valves.user_agent}
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(search_url, params=params, headers=headers) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"DuckDuckGo returned status {resp.status}")
                return await resp.text()

    def _parse(self, html: str, max_results: int) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        blocks = re.findall(r'<div[^>]*class="[^\"]*result[^\"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
        for i, block in enumerate(blocks[:max_results]):
            link = re.search(r'<a[^>]*class="[^\"]*result__a[^\"]*"[^>]*href="([^\"]*)"[^>]*>(.*?)</a>', block, re.DOTALL)
            if not link:
                continue
            url, title_html = link.group(1), link.group(2)
            title = re.sub(r'<[^>]+>', '', title_html).strip()
            snippet_match = re.search(r'<a[^>]*class="[^\"]*result__snippet[^\"]*"[^>]*>(.*?)</a>', block, re.DOTALL)
            snippet = re.sub(r'<[^>]+>', '', snippet_match.group(1)).strip() if snippet_match else ''
            if title and url:
                results.append({"title": title, "url": url, "snippet": snippet, "rank": i + 1})
        return results

print(f"{PRINT_PREFIX} Action class defined: web_search")

# Backward compatibility entry point
async def main(query: str, max_results: int = 5, **kwargs) -> str:
    action = Action()
    return await action.run(query=query, max_results=max_results, **kwargs)

