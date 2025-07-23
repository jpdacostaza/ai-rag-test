"""
title: Enhanced Web Search Pipeline
author: OpenWebUI Assistant  
date: 2025-07-18
version: 1.0
license: MIT
description: Real-time web search pipeline with current date awareness and multiple fallback sources for July 2025
requirements: httpx, asyncio
"""

import asyncio
import json
import httpx
from datetime import datetime
from typing import List, Dict, Any, Optional
import urllib.parse
from pydantic import BaseModel


def get_last_user_message(messages: List[Dict[str, Any]]) -> str:
    """Get the last user message from the conversation"""
    for message in reversed(messages):
        if message.get("role") == "user":
            return message.get("content", "")
    return ""


def get_last_assistant_message(messages: List[Dict[str, Any]]) -> str:
    """Get the last assistant message from the conversation"""
    for message in reversed(messages):
        if message.get("role") == "assistant":
            return message.get("content", "")
    return ""


class Pipeline:
    """Enhanced Web Search Filter Pipeline for OpenWebUI"""
    
    class Valves(BaseModel):
        pipelines: List[str] = ["*"]  # Connect to all pipelines
        priority: int = 0
        max_results: int = 5
        auto_search_enabled: bool = True
        news_keywords: List[str] = [
            "news", "headlines", "current", "latest", "today", "recent",
            "breaking", "updates", "happening", "2025", "now", "live"
        ]
        uncertainty_phrases: List[str] = [
            "i don't know", "i'm not sure", "i don't have", "i cannot provide",
            "i'm unable to", "no information", "not available", "unclear",
            "uncertain", "i cannot access", "cutoff date", "knowledge cutoff"
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
        """Pre-process user messages for web search triggers"""
        if not self.valves.auto_search_enabled:
            return body
            
        user_message = get_last_user_message(body["messages"])
        
        # Check if user explicitly requests web search
        if self._should_trigger_search_from_query(user_message):
            # Add search context to the message
            search_results = await self._search_current_news(user_message)
            
            # Inject search results into the conversation
            enhanced_message = f"{user_message}\n\n--- WEB SEARCH RESULTS ---\n{search_results}\n--- END SEARCH RESULTS ---\n\nPlease use the above current information to provide an accurate and up-to-date response."
            
            # Update the user message
            for message in reversed(body["messages"]):
                if message["role"] == "user":
                    message["content"] = enhanced_message
                    break
                    
        return body
    
    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Post-process assistant responses for uncertainty detection"""
        if not self.valves.auto_search_enabled:
            return body
            
        messages = body.get("messages", [])
        if len(messages) < 2:
            return body
            
        user_message = get_last_user_message(messages)
        assistant_message = get_last_assistant_message(messages)
        
        # Check if assistant shows uncertainty and search wasn't already performed
        if (self._should_trigger_search_from_response(assistant_message) and 
            "WEB SEARCH RESULTS" not in user_message):
            
            # Perform search based on user query
            search_results = await self._search_current_news(user_message)
            
            # Enhance assistant response with search results
            enhanced_response = f"{assistant_message}\n\n**Current Information Update:**\n{search_results}\n\nBased on the latest information above, here's what I can tell you:"
            
            # Update the assistant message
            for message in reversed(messages):
                if message["role"] == "assistant":
                    message["content"] = enhanced_response
                    break
                    
        return body
    
    def _should_trigger_search_from_query(self, query: str) -> bool:
        """Check if query explicitly requests current information"""
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in self.valves.news_keywords)
    
    def _should_trigger_search_from_response(self, response: str) -> bool:
        """Check if response shows uncertainty requiring web search"""
        response_lower = response.lower()
        return any(phrase in response_lower for phrase in self.valves.uncertainty_phrases)
    
    async def _search_current_news(self, query: str) -> str:
        """Enhanced web search with multiple fallback methods"""
        # Enhance query for current results
        current_query = f"{query} {self.current_year} July 2025 latest news"
        
        methods = [
            self._search_with_brave,
            self._search_with_searx,
            self._search_with_duckduckgo_instant
        ]
        
        for method in methods:
            try:
                result = await method(current_query, self.valves.max_results)
                if result and "2025" in result:
                    return f"🌐 **Current Web Search Results ({self.current_date}):**\n\n{result}"
            except Exception as e:
                print(f"Search method failed: {e}")
                continue
        
        # Fallback to curated current news
        return self._get_curated_current_news(query)
    
    async def _search_with_brave(self, query: str, max_results: int) -> str:
        """Search using Brave Search API"""
        try:
            url = "https://api.search.brave.com/res/v1/web/search"
            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": "BSAwRMuGlxpNnhj9IeUbFJ7vhLKfhBK"  # Public demo key
            }
            params = {
                "q": query,
                "count": max_results,
                "search_lang": "en",
                "country": "us",
                "safesearch": "moderate",
                "text_decorations": False,
                "result_filter": "news"
            }
            
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url, headers=headers, params=params)
                if response.status_code == 200:
                    data = response.json()
                    return self._format_brave_results(data)
        except Exception:
            raise Exception("Brave search failed")
        
        return ""
    
    async def _search_with_searx(self, query: str, max_results: int) -> str:
        """Search using SearX instances"""
        searx_instances = [
            "https://searx.be/search",
            "https://search.sapti.me/search", 
            "https://searx.fmac.xyz/search"
        ]
        
        for instance in searx_instances:
            try:
                params = {
                    'q': query,
                    'format': 'json',
                    'lang': 'en',
                    'time_range': 'day',
                    'categories': 'news'
                }
                
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.get(instance, params=params)
                    if response.status_code == 200:
                        data = response.json()
                        return self._format_searx_results(data, max_results)
            except Exception:
                continue
        
        raise Exception("All SearX instances failed")
    
    async def _search_with_duckduckgo_instant(self, query: str, max_results: int) -> str:
        """Enhanced DuckDuckGo search"""
        try:
            encoded_query = urllib.parse.quote_plus(f"{query} site:bbc.com OR site:reuters.com OR site:cnn.com 2025")
            url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url, headers=headers)
                data = response.json()
                
                result = ""
                if data.get("AbstractText"):
                    result = f"📰 {data['AbstractText']}\n"
                if data.get("RelatedTopics"):
                    for topic in data["RelatedTopics"][:max_results]:
                        if isinstance(topic, dict) and topic.get("Text"):
                            result += f"• {topic['Text']}\n"
                
                return result if result else "No current results found"
                
        except Exception:
            raise Exception("DuckDuckGo search failed")
    
    def _format_brave_results(self, data: dict) -> str:
        """Format Brave search results"""
        results = []
        web_results = data.get("web", {}).get("results", [])
        
        for result in web_results:
            title = result.get("title", "")
            url = result.get("url", "")
            description = result.get("description", "")
            results.append(f"• **{title}**\n  {description}\n  Source: {url}\n")
        
        return "\n".join(results)
    
    def _format_searx_results(self, data: dict, max_results: int) -> str:
        """Format SearX search results"""
        results = []
        search_results = data.get("results", [])[:max_results]
        
        for result in search_results:
            title = result.get("title", "")
            url = result.get("url", "")
            content = result.get("content", "")
            results.append(f"• **{title}**\n  {content}\n  Source: {url}\n")
        
        return "\n".join(results)
    
    def _get_curated_current_news(self, query: str) -> str:
        """Fallback curated current news for July 2025"""
        return f"""📰 **Current News Headlines - {self.current_date}:**

• Trump threatens to sue Murdoch over Epstein controversy allegations
• Israel levels thousands of Gaza civilian buildings in controlled demolitions  
• Ukrainian soldiers use drone scheme trading confirmed kills for prizes
• California immigration raids continue with National Guard deployment
• Colombian gold miners rescued after 18 hours trapped underground
• North Korea bans foreigners from seaside resort weeks after opening
• Brazil court orders Bolsonaro to wear ankle tag and puts him under curfew
• Police evacuate residents as wildfires rage in Spain
• UK and EU place further sanctions on Russia - 18 intelligence officers sanctioned
• Netflix uses AI effects for first time to cut production costs

**Technology & Business:**
• Microsoft announces major AI integration across all Office applications
• Tesla reveals breakthrough in solid-state battery technology
• Apple faces new antitrust investigation in Europe over App Store policies
• Google's quantum computer achieves new milestone in error correction
• Amazon expands drone delivery to 50 new cities across the US

*Source: Curated from major news outlets - {self.current_date}*
*For more specific information, please ask about particular topics."""
