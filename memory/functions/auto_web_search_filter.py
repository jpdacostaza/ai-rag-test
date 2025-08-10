"""
Auto Web Search Filter
Automatically performs a web search and injects results into the conversation context
when the model fails to call the web_search Action.

Purpose:
Fallback path for small / non-tool-calling local models (e.g. qwen2.5:3b) so that
queries requiring current information still get fresh data.

Strategy:
- Runs in inlet stage.
- If last user message contains trigger phrases and no prior injected results,
  first tries to call the real Action, then falls back to direct search if needed.
- Appends synthetic system message with results before model reply.

Enhanced Features:
- Prefers calling real Action to maintain single code path
- Forced invocation for explicit web search requests
- Improved query extraction and result formatting
"""

import re
import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

PRINT_PREFIX = "[AutoWebSearchFilter]"
print(f"{PRINT_PREFIX} Imported.")

class Filter:
    class Valves(BaseModel):
        priority: int = Field(default=2, description="Priority for auto web search filter (higher runs earlier)")
        enable_auto_search: bool = Field(default=True, description="Enable automatic fallback web search")
        max_results: int = Field(default=5, ge=1, le=10, description="Results to inject (1-10)")
        trigger_keywords: List[str] = Field(
            default=[
                "current", "today", "latest", "news", "headline", "weather", "temperature",
                "date", "time", "update", "trending", "market", "stock", "price", "search the web",
                "web search", "lookup", "recent", "what is happening", "check online"
            ],
            description="Keywords that trigger auto web search"
        )
        force_keywords: List[str] = Field(
            default=[
                "search the web", "web search", "lookup online", "check online", "find online",
                "search for", "look up current", "get latest"
            ],
            description="Keywords that force web search regardless of cooldown"
        )
        cooldown_seconds: int = Field(default=30, description="Minimum seconds before re-searching same hash")
        min_chars: int = Field(default=12, description="Minimum user message length to consider")
        use_real_action: bool = Field(default=True, description="Try to call real Action first before fallback")

    def __init__(self):
        self.valves = self.Valves()
        self.type = "filter"
        self.name = "Auto Web Search Fallback"
        self.version = "2.0"
        self._recent_hashes: Dict[str, datetime] = {}

    async def inlet(self, body: dict, __user__=None) -> dict:
        if not self.valves.enable_auto_search:
            return body

        messages: List[Dict[str, Any]] = body.get("messages", [])
        if not messages:
            return body

        last = messages[-1]
        if last.get("role") != "user":
            return body

        content: str = last.get("content", "").strip()
        if len(content) < self.valves.min_chars:
            return body

        # Avoid duplicate injection
        if any("WEB_SEARCH_RESULTS" in m.get("content", "") for m in messages):
            return body

        # Check triggers
        lowered = content.lower()
        is_forced = any(kw in lowered for kw in self.valves.force_keywords)
        is_triggered = is_forced or any(kw in lowered for kw in self.valves.trigger_keywords)
        
        if not is_triggered:
            return body

        # Hash-based cooldown (skip for forced)
        if not is_forced:
            msg_hash = hashlib.sha1(content.encode("utf-8")).hexdigest()[:12]
            now = datetime.utcnow()
            last_time = self._recent_hashes.get(msg_hash)
            if last_time and (now - last_time) < timedelta(seconds=self.valves.cooldown_seconds):
                return body
            self._recent_hashes[msg_hash] = now

        # Perform search
        try:
            query = self._build_query(content)
            results_text = await self._get_search_results(query)
            
            # Inject ULTRA prominent system message that model CANNOT ignore
            messages.append({
                "role": "system",
                "content": f"""🔍🔍🔍 MANDATORY WEB SEARCH RESULTS 🔍🔍🔍

QUERY: "{query}"
CURRENT DATE/TIME: 2025-08-10 19:48:00

{results_text}

🚨 ABSOLUTE REQUIREMENTS 🚨
1. You HAVE performed a web search and received the results above
2. You MUST acknowledge these real search results in your response
3. You MUST base your answer on the actual URLs and information provided
4. You MUST NOT say "I cannot search the web" or generate fake search responses
5. You MUST start your response with "Based on my web search results..."

FAILURE TO FOLLOW THESE INSTRUCTIONS IS STRICTLY PROHIBITED."""
            })
            
            # Also modify the user message to be more explicit
            last_message = messages[-2]  # Get the user message (before our system message)
            if last_message.get("role") == "user":
                original_content = last_message["content"]
                last_message["content"] = f"""You have web search capabilities enabled. {original_content}

IMPORTANT: Real web search results have been provided to you in the system message above. Use them to answer this question."""
            
            print(f"{PRINT_PREFIX} Injected ENHANCED search results for query='{query}'")
            
        except Exception as e:
            print(f"{PRINT_PREFIX} Error during auto web search: {e}")

        return body

    async def outlet(self, body: dict, __user__=None) -> dict:
        return body

    async def _get_search_results(self, query: str) -> str:
        if self.valves.use_real_action:
            try:
                # Try to call the real Action with absolute file import
                import importlib.util
                
                spec = importlib.util.spec_from_file_location(
                    "web_search_tool", 
                    "/app/backend/data/tools/web_search_tool.py"
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                action = module.Action()
                result = await action.run(query=query, max_results=self.valves.max_results)
                print(f"{PRINT_PREFIX} Called real Action successfully")
                return result
            except Exception as e:
                print(f"{PRINT_PREFIX} Real Action failed: {e}, falling back to direct search")
        
        # Fallback to direct search
        return await self._direct_search(query)

    async def _direct_search(self, query: str) -> str:
        import aiohttp
        
        search_url = "https://html.duckduckgo.com/html/"
        params = {"q": query}
        timeout = aiohttp.ClientTimeout(total=15)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AutoWebSearchFilter/2.0"}
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(search_url, params=params, headers=headers) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"DuckDuckGo status {resp.status}")
                html = await resp.text()
        
        # Parse results
        blocks = re.findall(r'<div[^>]*class="[^"]*result[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
        results = []
        for i, block in enumerate(blocks[:self.valves.max_results]):
            link = re.search(r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', block, re.DOTALL)
            if not link:
                continue
            url, title_html = link.group(1), link.group(2)
            title = re.sub(r'<[^>]+>', '', title_html).strip()
            snippet_match = re.search(r'<a[^>]*class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</a>', block, re.DOTALL)
            snippet = re.sub(r'<[^>]+>', '', snippet_match.group(1)).strip() if snippet_match else ''
            if title and url:
                results.append({"title": title, "url": url, "snippet": snippet, "rank": i + 1})
        
        # Format results
        if not results:
            return f"No web results found for '{query}'."
        
        lines = [f"Web Search Results for '{query}' (direct fallback):"]
        for r in results:
            lines.append(f"{r['rank']}. {r['title']}")
            lines.append(f"URL: {r['url']}")
            if r['snippet']:
                lines.append(f"Summary: {r['snippet']}")
            lines.append("")
        lines.append(f"Search completed at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
        return "\n".join(lines)

    def _build_query(self, content: str) -> str:
        # Extract meaningful query from user message
        cleaned = re.sub(r"\b(please|can you|could you|search|find|look up|web search for|check|get)\b", "", content, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        
        # If too short after cleaning, use original
        if len(cleaned) < 5:
            cleaned = content
            
        # Remove question marks and common filler
        cleaned = re.sub(r"[?!]+$", "", cleaned)
        cleaned = re.sub(r"\b(the|a|an|what|when|where|how|why)\b", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        
        return cleaned or content

print(f"{PRINT_PREFIX} Enhanced Filter class defined: Auto Web Search Fallback v2.0")
