"""
Enhanced Web Search Tool for OpenWebUI
====================================
Simple, reliable web search using only ddgs library.
Based on official OpenWebUI web search implementations.
Zero-configuration deployment with persistent setup.

Environment overrides (zero-conf friendly):
    WEB_SEARCH_CACHE_TTL            -> int seconds (default 300)
    WEB_SEARCH_DEFAULT_MAX_RESULTS  -> int (default 5)
    REDIS_URL / REDIS_HOST / REDIS_PORT as already supported
"""

import asyncio
import json
import time
import os
import hashlib
import warnings
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from collections import OrderedDict

try:
    from ddgs import DDGS  # Single supported package
    DDGS_AVAILABLE = True
    print("[WEB SEARCH] ddgs package loaded")
except ImportError:
    DDGS_AVAILABLE = False
    print("[WEB SEARCH] ddgs package missing. Install with: pip install ddgs")


class WebSearchTool:
    """Reliable web search tool using only ddgs library with structured output and caching.

    Instance attributes `cache_ttl` and `default_max_results` are resolved from environment
    on construction so container rebuilds pick up changes without code modifications.
    """

    DEFAULT_CACHE_TTL = 300  # 5 minutes
    DEFAULT_MAX_RESULTS = 5
    # In-memory bounded LRU cache (key -> (timestamp, data))
    _CACHE: "OrderedDict[str, Tuple[float, Dict[str, Any]]]" = OrderedDict()
    DEFAULT_MAX_CACHE_ENTRIES = 256

    def _init_redis(self):
        """Initialize Redis client if configuration present (optional)."""
        try:
            import redis  # type: ignore
        except Exception:
            self._redis = None
            return
        redis_url = os.getenv("REDIS_URL")
        host = os.getenv("REDIS_HOST", "redis")
        port = int(os.getenv("REDIS_PORT", "6379"))
        try:
            if redis_url:
                self._redis = redis.from_url(redis_url, socket_timeout=0.5)
            else:
                self._redis = redis.Redis(host=host, port=port, socket_timeout=0.5)
            # Ping quickly to verify
            self._redis.ping()
        except Exception:
            self._redis = None

    def __init__(self):
        self.current_year = datetime.now().year
        self.current_date = datetime.now().strftime("%B %d, %Y")
        self._redis = None
        # Resolve environment overrides with safe parsing
        self.cache_ttl = self._parse_int_env("WEB_SEARCH_CACHE_TTL", self.DEFAULT_CACHE_TTL, minimum=30)
        self.default_max_results = self._parse_int_env(
            "WEB_SEARCH_DEFAULT_MAX_RESULTS", self.DEFAULT_MAX_RESULTS, minimum=1, maximum=25
        )
        self._init_redis()
        self.max_cache_entries = self._parse_int_env(
            "WEB_SEARCH_MAX_CACHE_ENTRIES", self.DEFAULT_MAX_CACHE_ENTRIES, minimum=32, maximum=4096
        )

    @staticmethod
    def _parse_int_env(name: str, default: int, minimum: Optional[int] = None, maximum: Optional[int] = None) -> int:
        raw = os.getenv(name)
        if not raw:
            return default
        try:
            value = int(raw)
            if minimum is not None and value < minimum:
                return minimum
            if maximum is not None and value > maximum:
                return maximum
            return value
        except ValueError:
            return default

    # -------------------- Public API -------------------- #
    async def search_current_news(self, query: str, max_results: Optional[int] = None) -> Dict[str, Any]:
        """Perform a multi-strategy search and return structured results.

        Returns dict:
            {
              'query': str,
              'timestamp': iso str,
              'results': [ {title, snippet, link, source} ],
              'summary': formatted string or error message,
              'cached': bool,
              'strategies_attempted': [...],
            }
        """
        # Metrics import (local to avoid hard dependency during module import)
        try:
            from utilities.web_search_metrics import (
                WEB_SEARCH_QUERIES, WEB_SEARCH_CACHE_HITS, WEB_SEARCH_CACHE_MISSES,
                WEB_SEARCH_REDIS_HITS, WEB_SEARCH_REDIS_MISSES,
                WEB_SEARCH_RESULTS_ITEMS, WEB_SEARCH_DURATION)
        except Exception:  # Metrics optional
            WEB_SEARCH_QUERIES = WEB_SEARCH_CACHE_HITS = WEB_SEARCH_CACHE_MISSES = None
            WEB_SEARCH_REDIS_HITS = WEB_SEARCH_REDIS_MISSES = None
            WEB_SEARCH_RESULTS_ITEMS = WEB_SEARCH_DURATION = None

        start_time = time.time()
        if WEB_SEARCH_QUERIES: WEB_SEARCH_QUERIES.inc()
        now_ts = start_time
        norm_query = (query or "").strip().lower()
        cache_key = self._make_cache_key(norm_query, max_results)

        # Determine effective max_results
        if max_results is None or max_results <= 0:
            max_results = self.default_max_results

        # Cache lookup
        cached = self._CACHE.get(cache_key)
        if cached and (now_ts - cached[0]) < self.cache_ttl:
            data = cached[1]
            data["cached"] = True
            if WEB_SEARCH_CACHE_HITS: WEB_SEARCH_CACHE_HITS.inc()
            # Move to end (most recently used)
            try:
                self._CACHE.move_to_end(cache_key)
            except Exception:
                pass
            return data
        else:
            if WEB_SEARCH_CACHE_MISSES: WEB_SEARCH_CACHE_MISSES.inc()

        # Redis lookup
        if self._redis:
            try:
                raw = self._redis.get(cache_key)
                if raw:
                    data = json.loads(raw)
                    data["cached"] = True
                    self._CACHE[cache_key] = (now_ts, data)  # warm local
                    if WEB_SEARCH_REDIS_HITS: WEB_SEARCH_REDIS_HITS.inc()
                    return data
            except Exception:
                if WEB_SEARCH_REDIS_MISSES: WEB_SEARCH_REDIS_MISSES.inc()

        if not DDGS_AVAILABLE:
            result = self._empty_result(query, f"Web search unavailable. DDGS library not installed. Install with: pip install ddgs")
            self._store_cache(cache_key, result)
            return result

        strategies = [
            ("primary", lambda q: q),
            ("news", lambda q: f"news {q} {self.current_year}"),
            ("recent", lambda q: f"recent {q}"),
            ("current", lambda q: f"current {q} latest"),
        ]

        aggregated: List[Dict[str, str]] = []
        attempted: List[str] = []
        for name, mod in strategies:
            search_query = mod(query)
            attempted.append(name)
            try:
                print(f"[WEB SEARCH] Trying {name} strategy -> {search_query}")
                results = await self._search_with_ddgs(search_query, max_results)
                if results:
                    aggregated.extend(results)
                    # Break early if we have sufficient content
                    if len(aggregated) >= max_results:
                        break
            except Exception as e:
                print(f"[WEB SEARCH] Strategy {name} failed: {e}")
                continue

        if aggregated:
            formatted = format_search_results({"results": aggregated})
            result_dict = {
                "query": query,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "results": aggregated[:max_results],
                "summary": f"Current Web Search Results ({self.current_date}):\n\n{formatted}",
                "cached": False,
                "strategies_attempted": attempted,
            }
            if WEB_SEARCH_RESULTS_ITEMS: WEB_SEARCH_RESULTS_ITEMS.observe(len(result_dict["results"]))
        else:
            result_dict = self._empty_result(
                query,
                "Web search temporarily unavailable. Strategies attempted: " + ", ".join(attempted)
            )
        # Persist cache + latency metric
        self._store_cache(cache_key, result_dict)
        if WEB_SEARCH_DURATION: WEB_SEARCH_DURATION.observe(time.time() - start_time)
        return result_dict

    # -------------------- Internal helpers -------------------- #
    def _store_cache(self, key: str, value: Dict[str, Any]):
        # Insert / update and enforce LRU bound
        self._CACHE[key] = (time.time(), value)
        try:
            self._CACHE.move_to_end(key)
        except Exception:
            pass
        # Evict oldest if over capacity
        while len(self._CACHE) > self.max_cache_entries:
            try:
                self._CACHE.popitem(last=False)
                # Metric: count eviction
                try:
                    from utilities.web_search_metrics import WEB_SEARCH_CACHE_EVICTIONS
                    if WEB_SEARCH_CACHE_EVICTIONS:
                        WEB_SEARCH_CACHE_EVICTIONS.inc()
                except Exception:
                    pass
            except Exception:
                break
        # Gauge: current cache size
        try:
            from utilities.web_search_metrics import WEB_SEARCH_CACHE_SIZE
            if WEB_SEARCH_CACHE_SIZE:
                WEB_SEARCH_CACHE_SIZE.set(len(self._CACHE))
        except Exception:
            pass
        if self._redis:
            try:
                self._redis.setex(key, self.cache_ttl, json.dumps(value))
            except Exception:
                pass

    def _make_cache_key(self, norm_query: str, max_results: int) -> str:
        h = hashlib.sha256(f"{norm_query}|{max_results}".encode()).hexdigest()[:16]
        return f"websearch:{h}"

    def _empty_result(self, query: str, message: str) -> Dict[str, Any]:
        return {
            "query": query,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "results": [],
            "summary": message,
            "cached": False,
            "strategies_attempted": [],
        }

    async def _search_with_ddgs(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Low-level DDGS search returning list of result dicts."""
        try:
            print(f"[WEB SEARCH] Using DDGS for: {query}")
            results: List[Dict[str, str]] = []
            with DDGS() as ddgs:
                try:
                    search_results = ddgs.text(
                        query,
                        region="wt-wt",
                        safesearch="moderate",
                        max_results=max_results,
                    )
                    for r in search_results:
                        results.append({
                            "title": r.get("title", ""),
                            "link": r.get("href", ""),
                            "snippet": r.get("body", ""),
                            "source": "DuckDuckGo",
                        })
                except Exception as ddgs_error:
                    print(f"[WEB SEARCH] Text search failed: {ddgs_error}")
                    try:
                        news_results = ddgs.news(
                            query,
                            region="wt-wt",
                            safesearch="moderate",
                            max_results=max_results,
                        )
                        for r in news_results:
                            results.append({
                                "title": r.get("title", ""),
                                "link": r.get("url", ""),
                                "snippet": r.get("body", ""),
                                "source": "DuckDuckGo News",
                            })
                    except Exception as news_error:
                        print(f"[WEB SEARCH] News search failed: {news_error}")
                        raise
            return results
        except Exception as e:
            print(f"[WEB SEARCH] DDGS search fatal error: {e}")
            raise


def format_search_results(result_dict: Dict[str, Any], limit: int = 5) -> str:
    """Format structured results dict into human-readable bullet list."""
    results = (result_dict or {}).get("results", [])[:limit]
    if not results:
        return (result_dict or {}).get("summary", "No results.")
    lines = []
    for i, r in enumerate(results, 1):
        title = r.get("title") or "No title"
        snippet = r.get("snippet") or "No description available"
        link = r.get("link") or ""
        lines.append(f"{i}. **{title}**\n   {snippet}\n   {link}")
    return "\n".join(lines)


# Public async function (structured)
async def search_web(query: str, max_results: Optional[int] = None) -> Dict[str, Any]:
    tool = WebSearchTool()
    return await tool.search_current_news(query, max_results)


def should_trigger_web_search(query: str, model_response: Optional[str] = None) -> Tuple[bool, str]:
    """Determine if a query should trigger web search (basic heuristic).

    Returns (should_trigger, reason).
    If smart trigger module is available, defer to it for richer logic.
    """
    try:
        # Prefer smart trigger if importable
        from utilities.smart_web_search_trigger import should_trigger_web_search_smart
        if model_response is None:
            model_response = ""
        smart_should, smart_reason = should_trigger_web_search_smart(query, model_response)
        return smart_should, smart_reason
    except Exception:
        search_indicators = [
            "search for", "find information about", "what's the latest on",
            "current news about", "recent developments", "look up",
            "search the web", "find online", "web search", "latest news",
            "recent news", "current events", "what happened", "news about"
        ]
        q_lower = (query or "").lower()
        triggered = any(indicator in q_lower for indicator in search_indicators)
        return triggered, "Keyword trigger" if triggered else "No trigger"


# Export the main tool class
__all__ = ["WebSearchTool", "search_web", "should_trigger_web_search", "format_search_results"]
