"""
title: Enhanced Web Search Pipeline
author: OpenWebUI Assistant  
date: 2025-08-08
version: 2.0
license: MIT
description: Reliable web search pipeline using only DDGS library for zero-configuration deployment
requirements: duckduckgo-search
"""

import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


def get_last_user_message(messages: List[Dict[str, Any]]) -> str:
    """Extract the last user message from the conversation"""
    for message in reversed(messages):
        if message.get("role") == "user":
            return message.get("content", "")
    return ""


def get_last_assistant_message(messages: List[Dict[str, Any]]) -> str:
    """Extract the last assistant message from the conversation"""
    for message in reversed(messages):
        if message.get("role") == "assistant":
            return message.get("content", "")
    return ""


class Pipeline:
    class Valves(BaseModel):
        # Configuration
        auto_search_enabled: bool = True
        max_results: int = 10
        
        # Web search triggers
        explicit_search_keywords: List[str] = [
            "search for", "web search", "search the web", "look up online", 
            "find information about", "search online", "google", "bing", 
            "duckduckgo", "find recent", "search recent", "latest information"
        ]
        
        # CURRENT/RECENT INFORMATION - Only when asking for very recent/current info
        currency_keywords: List[str] = [
            "latest", "current", "today", "recent", "breaking", "now", "live",
            "updates", "2025", "this week", "this month", "happening now",
            "just announced", "recently", "new", "fresh"
        ]
        
        # MODEL UNCERTAINTY - When model admits lack of knowledge
        uncertainty_phrases: List[str] = [
            "i don't know", "i'm not sure", "i don't have", "i cannot provide",
            "i'm unable to", "no information", "not available", "unclear",
            "uncertain", "i cannot access", "cutoff date", "knowledge cutoff",
            "my training data", "as of my last update", "i need to search",
            "let me search", "i should look that up", "i'd need to check"
        ]
        
        # VERIFICATION TRIGGERS - When model suggests checking for updates
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
        """Pre-process user messages for web search triggers"""
        if not self.valves.auto_search_enabled:
            return body
            
        user_message = get_last_user_message(body["messages"])
        
        # Check if user explicitly requests web search
        if self._should_trigger_search_from_query(user_message):
            # Extract meaningful search query from user request
            search_query = self._extract_search_query(user_message)
            print(f"[WEB SEARCH] Explicit search request detected")
            print(f"[WEB SEARCH] Original: {user_message}")
            print(f"[WEB SEARCH] Extracted query: {search_query}")
            
            # Add search context to the message
            search_results = await self._search_current_news(search_query)
            
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
        """Check if query explicitly requests current information or web search"""
        query_lower = query.lower()
        
        # 1. EXPLICIT WEB SEARCH REQUEST - User directly asks for web search
        if any(keyword in query_lower for keyword in self.valves.explicit_search_keywords):
            print(f"[SEARCH] Web search triggered: Explicit user request")
            return True
            
        # 2. CURRENT/RECENT INFORMATION - Only for very recent/current queries
        has_currency_keyword = any(keyword in query_lower for keyword in self.valves.currency_keywords)
        if has_currency_keyword:
            # Additional check: Must be asking about events, news, or status
            context_keywords = ["news", "event", "status", "happening", "announce", "report", "update"]
            if any(context in query_lower for context in context_keywords):
                print(f"[SEARCH] Web search triggered: Current information request")
                return True
        
        # 3. VERIFICATION REQUEST - User wants to verify information
        if any(keyword in query_lower for keyword in self.valves.verification_keywords):
            print(f"[SEARCH] Web search triggered: Verification request")
            return True
            
        return False
    
    def _extract_search_query(self, user_message: str) -> str:
        """Extract meaningful search terms from user command"""
        import re
        
        query = user_message.lower().strip()
        
        # Step 1: Extract domain/company name from URLs if present
        url_matches = re.findall(r'https?://(?:www\.)?([^./]+)\.com/?', query)
        extracted_terms = []
        
        if url_matches:
            # Extract company name from domain
            company_name = url_matches[0].replace('-', ' ').replace('_', ' ')
            extracted_terms.append(company_name)
            print(f"[WEB SEARCH] Extracted company from URL: {company_name}")
        
        # Step 2: Remove URLs from query
        query_no_urls = re.sub(r'https?://\S+', '', query).strip()
        
        # Step 3: Remove command phrases
        command_phrases = [
            'search the web', 'web search', 'search for', 'look up online',
            'find information about', 'search online', 'google', 'bing',
            'duckduckgo', 'find recent', 'search recent', 'check'
        ]
        
        for phrase in command_phrases:
            query_no_urls = query_no_urls.replace(phrase, '').strip()
        
        # Step 4: Clean up connecting words
        connecting_words = ['to', 'and', 'where', 'what', 'how', 'why', 'when', 'who']
        words = query_no_urls.split()
        meaningful_words = [word for word in words if len(word) > 2 and word not in connecting_words]
        
        if meaningful_words:
            extracted_terms.extend(meaningful_words)
        
        # Step 5: Build final search query
        if extracted_terms:
            final_query = ' '.join(extracted_terms)
            # Add context for company searches
            if url_matches and 'work' in user_message.lower():
                final_query += ' company work careers'
            return final_query
        else:
            # Fallback: use original message minus command phrases
            return query_no_urls if query_no_urls else 'information'
    
    def _should_trigger_search_from_response(self, response: str) -> bool:
        """Check if response shows uncertainty or suggests verification"""
        response_lower = response.lower()
        
        # 1. MODEL UNCERTAINTY - Model admits it doesn't know
        if any(phrase in response_lower for phrase in self.valves.uncertainty_phrases):
            print(f"[SEARCH] Web search triggered: Model uncertainty detected")
            return True
            
        # 2. VERIFICATION SUGGESTION - Model suggests checking for updates
        if any(keyword in response_lower for keyword in self.valves.verification_keywords):
            print(f"[SEARCH] Web search triggered: Verification suggested")
            return True
            
        return False
    
    async def _search_current_news(self, query: str) -> str:
        """Enhanced web search using reliable DDGS library only"""
        # Simple DDGS-only search with multiple strategies
        try:
            from ddgs import DDGS
        except ImportError:
            try:
                from duckduckgo_search import DDGS
            except ImportError:
                return f" **Web Search Unavailable ({self.current_date}):**\n\nDDGS library not installed. Please install with: pip install ddgs"

        # Enhanced search strategies for better results
        search_strategies = [
            ("Primary search", query),
            ("News-focused search", f"news {query} 2025"),
            ("Recent search", f"recent {query}"),
            ("Current search", f"current {query} latest"),
        ]
        
        for strategy_name, search_query in search_strategies:
            try:
                print(f"[WEB SEARCH] Trying {strategy_name} with DDGS...")
                result = await self._search_with_ddgs(search_query, self.valves.max_results)
                if result and len(result.strip()) > 50:  # Ensure we got meaningful results
                    print(f"[WEB SEARCH] [OK] {strategy_name} succeeded")
                    return f" **Current Web Search Results ({self.current_date}):**\n\n{result}"
                else:
                    print(f"[WEB SEARCH] [FAIL] {strategy_name} returned insufficient data")
            except Exception as e:
                print(f"[WEB SEARCH] [FAIL] {strategy_name} failed: {e}")
                continue
        
        # If all strategies fail, provide a helpful response
        return f" **Web Search Status ({self.current_date}):**\n\nWeb search temporarily unavailable. All DDGS search strategies attempted:\n- Primary search\n- News-focused search\n- Recent search\n- Current search\n\nPlease try rephrasing your query or check back shortly."

    async def _search_with_ddgs(self, query: str, max_results: int) -> str:
        """Search using DDGS library (official OpenWebUI implementation pattern)"""
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
            
        print(f"[WEB SEARCH] Using DDGS library for: {query}")
        
        results = []
        
        # Use DDGS context manager pattern (official OpenWebUI approach)
        with DDGS() as ddgs:
            try:
                # Primary search with modern parameters
                search_results = ddgs.text(
                    keywords=query,
                    region="wt-wt",  # Worldwide
                    safesearch="moderate",
                    max_results=max_results
                )
                
                for result in search_results:
                    results.append({
                        "title": result.get("title", ""),
                        "link": result.get("href", ""),
                        "snippet": result.get("body", ""),
                        "source": "DuckDuckGo"
                    })
                    
            except Exception as ddgs_error:
                print(f"[WEB SEARCH] DDGS text search failed: {ddgs_error}")
                # Try news search as fallback within DDGS
                try:
                    news_results = ddgs.news(
                        keywords=query,
                        region="wt-wt",
                        safesearch="moderate",
                        max_results=max_results
                    )
                    
                    for result in news_results:
                        results.append({
                            "title": result.get("title", ""),
                            "link": result.get("url", ""),
                            "snippet": result.get("body", ""),
                            "source": "DuckDuckGo News"
                        })
                        
                except Exception as news_error:
                    print(f"[WEB SEARCH] DDGS news search also failed: {news_error}")
                    raise Exception(f"Both text and news search failed: {ddgs_error}")
        
        if results:
            formatted_results = []
            for i, result in enumerate(results, 1):
                title = result["title"] or "No title"
                snippet = result["snippet"] or "No description available"
                link = result["link"] or ""
                
                formatted_results.append(
                    f"{i}. **{title}**\n"
                    f"   {snippet}\n"
                    f"    {link}\n"
                )
            
            return "\n".join(formatted_results)
        else:
            raise Exception("No results returned from DDGS")
