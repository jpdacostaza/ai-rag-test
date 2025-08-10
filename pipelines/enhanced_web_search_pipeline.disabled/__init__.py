"""Enhanced Web Search Pipeline package.

Provides Pipeline class for web search augmentation. Converted from single
module to package so imports like `from pipelines.enhanced_web_search_pipeline import Pipeline`
work even when a directory of supplemental assets (e.g., valves.json) exists.

Legacy notice: the former standalone `pipelines/enhanced_web_search_pipeline.py` file
has been removed in favor of this package module to eliminate duplication and
ensure zero‑configuration persistence across container rebuilds. All imports
should target this package path going forward.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

def get_last_user_message(messages: List[Dict[str, Any]]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            return message.get("content", "")
    return ""

def get_last_assistant_message(messages: List[Dict[str, Any]]) -> str:
    for message in reversed(messages):
        if message.get("role") == "assistant":
            return message.get("content", "")
    return ""

class Pipeline:
    class Valves(BaseModel):
        auto_search_enabled: bool = True
        max_results: int = 10
        explicit_search_keywords: List[str] = [
            "search for", "web search", "search the web", "look up online",
            "find information about", "search online", "google", "bing",
            "duckduckgo", "find recent", "search recent", "latest information"
        ]
        currency_keywords: List[str] = [
            "latest", "current", "today", "recent", "breaking", "now", "live",
            "updates", "2025", "this week", "this month", "happening now",
            "just announced", "recently", "new", "fresh"
        ]
        uncertainty_phrases: List[str] = [
            "i don't know", "i'm not sure", "i don't have", "i cannot provide",
            "i'm unable to", "no information", "not available", "unclear",
            "uncertain", "i cannot access", "cutoff date", "knowledge cutoff",
            "my training data", "as of my last update", "i need to search",
            "let me search", "i should look that up", "i'd need to check"
        ]
        verification_keywords: List[str] = [
            "verify", "confirm", "double-check", "make sure", "check if",
            "is this still", "has this changed", "is this current", "update on",
            "still accurate", "still valid", "still true", "up to date"
        ]
    def __init__(self):
        self.type = "filter"
        self.name = "Enhanced Web Search"
        self.valves = self.Valves()
        self.current_year = datetime.now().year
        self.current_date = datetime.now().strftime("%B %d, %Y")
    async def on_startup(self):
        print(f"Enhanced Web Search Pipeline started - {self.current_date}")
    async def on_shutdown(self):
        print("Enhanced Web Search Pipeline stopped")
    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        if not self.valves.auto_search_enabled:
            return body
        user_message = get_last_user_message(body["messages"])
        if self._should_trigger_search_from_query(user_message):
            search_query = self._extract_search_query(user_message)
            print("[WEB SEARCH] Explicit search request detected")
            print(f"[WEB SEARCH] Original: {user_message}")
            print(f"[WEB SEARCH] Extracted query: {search_query}")
            search_results = await self._search_current_news(search_query)
            enhanced_message = (
                f"{user_message}\n\n--- WEB SEARCH RESULTS ---\n{search_results}\n--- END SEARCH RESULTS ---\n\n" \
                "Please use the above current information to provide an accurate and up-to-date response."
            )
            for message in reversed(body["messages"]):
                if message["role"] == "user":
                    message["content"] = enhanced_message
                    break
        return body
    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        if not self.valves.auto_search_enabled:
            return body
        messages = body.get("messages", [])
        if len(messages) < 2:
            return body
        user_message = get_last_user_message(messages)
        assistant_message = get_last_assistant_message(messages)
        if (self._should_trigger_search_from_response(assistant_message)
                and "WEB SEARCH RESULTS" not in user_message):
            search_results = await self._search_current_news(user_message)
            enhanced_response = (
                f"{assistant_message}\n\n**Current Information Update:**\n{search_results}\n\n" \
                "Based on the latest information above, here's what I can tell you:"
            )
            for message in reversed(messages):
                if message["role"] == "assistant":
                    message["content"] = enhanced_response
                    break
        return body
    def _should_trigger_search_from_query(self, query: str) -> bool:
        q = query.lower()
        if any(k in q for k in self.valves.explicit_search_keywords):
            print("[SEARCH] Web search triggered: Explicit user request")
            return True
        if any(k in q for k in self.valves.currency_keywords):
            context = ["news", "event", "status", "happening", "announce", "report", "update"]
            if any(c in q for c in context):
                print("[SEARCH] Web search triggered: Current information request")
                return True
        if any(k in q for k in self.valves.verification_keywords):
            print("[SEARCH] Web search triggered: Verification request")
            return True
        return False
    def _extract_search_query(self, user_message: str) -> str:
        import re
        query = user_message.lower().strip()
        url_matches = re.findall(r'https?://(?:www\.)?([^./]+)\.com/?', query)
        extracted_terms: List[str] = []
        if url_matches:
            company_name = url_matches[0].replace('-', ' ').replace('_', ' ')
            extracted_terms.append(company_name)
            print(f"[WEB SEARCH] Extracted company from URL: {company_name}")
        query_no_urls = re.sub(r'https?://\S+', '', query).strip()
        command_phrases = [
            'search the web', 'web search', 'search for', 'look up online',
            'find information about', 'search online', 'google', 'bing',
            'duckduckgo', 'find recent', 'search recent', 'check'
        ]
        for phrase in command_phrases:
            query_no_urls = query_no_urls.replace(phrase, '').strip()
        connecting = ['to', 'and', 'where', 'what', 'how', 'why', 'when', 'who']
        words = query_no_urls.split()
        # Keep words longer than 2 chars OR important short tech tokens (e.g., 'ai')
        short_whitelist = {"ai", "uk", "us", "eu", "it", "vr"}
        meaningful = [w for w in words if (len(w) > 2 or w in short_whitelist) and w not in connecting]
        if meaningful:
            extracted_terms.extend(meaningful)
        if extracted_terms:
            final_query = ' '.join(extracted_terms)
            if url_matches and 'work' in user_message.lower():
                final_query += ' company work careers'
            return final_query
        return query_no_urls if query_no_urls else 'information'
    def _should_trigger_search_from_response(self, response: str) -> bool:
        r = response.lower()
        if any(p in r for p in self.valves.uncertainty_phrases):
            print("[SEARCH] Web search triggered: Model uncertainty detected")
            return True
        if any(k in r for k in self.valves.verification_keywords):
            print("[SEARCH] Web search triggered: Verification suggested")
            return True
        return False
    async def _search_current_news(self, query: str) -> str:
        # Delegate to shared enhanced_web_search implementation to avoid duplication
        try:
            from utilities.enhanced_web_search import search_web
            data = await search_web(query, max_results=self.valves.max_results)
            if data.get('results'):
                return f" **Current Web Search Results ({self.current_date}):**\n\n{data.get('summary','')}"
            return (f" **Web Search Status ({self.current_date}):**\n\nWeb search temporarily unavailable. "
                    f"Strategies attempted: {', '.join(data.get('strategies_attempted', []))}")
        except Exception as e:
            return (f" **Web Search Unavailable ({self.current_date}):**\n\n"
                    f"Runtime search failure: {e}")
    async def _search_with_ddgs(self, query: str, max_results: int) -> str:
        # Backwards compatibility: delegate to shared tool
        try:
            from utilities.enhanced_web_search import search_web, format_search_results
            data = await search_web(query, max_results=max_results)
            return format_search_results(data, limit=max_results)
        except Exception:
            return ""
__all__ = ["Pipeline"]
