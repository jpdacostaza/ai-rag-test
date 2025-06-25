"""
Web Search Tool for AI Assistant
Provides fallback web search functionality when the model doesn't know an answer.
Uses DuckDuckGo as primary search engine with optional SerpAPI backup.
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import quote_plus
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class WebSearchTool:
    """Web search tool with multiple search engine backends"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=10)
            headers = {"User-Agent": self.user_agent}
            self.session = aiohttp.ClientSession(timeout=timeout, headers=headers)
        return self.session
    
    async def search_duckduckgo(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search using DuckDuckGo Instant Answer API
        Returns structured search results
        """
        try:
            session = await self._get_session()
            
            # Clean and encode query
            clean_query = re.sub(r'[^\w\s-]', '', query).strip()
            encoded_query = quote_plus(clean_query)
            
            # DuckDuckGo Instant Answer API
            url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    results = []
                    
                    # Extract instant answer if available
                    if data.get('Abstract'):
                        results.append({
                            'title': data.get('AbstractText', '')[:100] + "...",
                            'snippet': data.get('Abstract', ''),
                            'url': data.get('AbstractURL', ''),
                            'source': 'DuckDuckGo Instant Answer'
                        })
                    
                    # Extract related topics
                    for topic in data.get('RelatedTopics', [])[:max_results-len(results)]:
                        if isinstance(topic, dict) and topic.get('Text'):
                            results.append({
                                'title': topic.get('Text', '')[:100] + "...",
                                'snippet': topic.get('Text', ''),
                                'url': topic.get('FirstURL', ''),
                                'source': 'DuckDuckGo Related'
                            })
                    
                    # If no results, try web search fallback
                    if not results:
                        return await self._fallback_web_search(clean_query, max_results)
                    
                    return results[:max_results]
                else:
                    logger.warning(f"DuckDuckGo API returned status {response.status}")
                    return await self._fallback_web_search(clean_query, max_results)
                    
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {str(e)}")
            return await self._fallback_web_search(clean_query, max_results)
    
    async def _fallback_web_search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Fallback web search using HTML scraping approach
        """
        try:
            session = await self._get_session()
            encoded_query = quote_plus(query)
            
            # Use DuckDuckGo HTML search as fallback
            search_url = f"https://duckduckgo.com/html/?q={encoded_query}"
            
            async with session.get(search_url) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_search_results(html, max_results)
                else:
                    logger.error(f"Fallback search failed with status {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Fallback web search failed: {str(e)}")
            return []
    
    def _parse_search_results(self, html: str, max_results: int) -> List[Dict[str, Any]]:
        """Parse HTML search results (simplified parsing)"""
        results = []
        try:
            # Very basic HTML parsing - in production, consider using BeautifulSoup
            # This is a simplified approach to avoid additional dependencies
            
            # Look for result patterns in DuckDuckGo HTML
            import re
            
            # Extract titles and snippets using regex patterns
            title_pattern = r'<a[^>]*class="result__a"[^>]*>([^<]+)</a>'
            snippet_pattern = r'<a[^>]*class="result__snippet"[^>]*>([^<]+)</a>'
            url_pattern = r'<a[^>]*class="result__a"[^>]*href="([^"]+)"'
            
            titles = re.findall(title_pattern, html)
            snippets = re.findall(snippet_pattern, html)
            urls = re.findall(url_pattern, html)
            
            for i in range(min(len(titles), max_results)):
                result = {
                    'title': titles[i] if i < len(titles) else 'Search Result',
                    'snippet': snippets[i] if i < len(snippets) else 'No description available',
                    'url': urls[i] if i < len(urls) else '',
                    'source': 'DuckDuckGo Web Search'
                }
                results.append(result)
                
        except Exception as e:
            logger.error(f"Failed to parse search results: {str(e)}")
            
        return results
    
    async def search(self, query: str, max_results: int = 3) -> Dict[str, Any]:
        """
        Main search interface
        Returns formatted search results with metadata
        """
        try:
            start_time = datetime.now()
            
            # Perform search
            results = await self.search_duckduckgo(query, max_results)
            
            end_time = datetime.now()
            search_duration = (end_time - start_time).total_seconds()
            
            # Format response
            response = {
                'query': query,
                'results_count': len(results),
                'search_duration_seconds': round(search_duration, 3),
                'timestamp': end_time.isoformat(),
                'results': results
            }
            
            if results:
                logger.info(f"Web search successful: '{query}' returned {len(results)} results in {search_duration:.3f}s")
            else:
                logger.warning(f"Web search returned no results for query: '{query}'")
                
            return response
            
        except Exception as e:
            logger.error(f"Web search failed for query '{query}': {str(e)}")
            return {
                'query': query,
                'results_count': 0,
                'search_duration_seconds': 0,
                'timestamp': datetime.now().isoformat(),
                'results': [],
                'error': str(e)
            }
    
    def format_search_results_for_chat(self, search_data: Dict[str, Any]) -> str:
        """
        Format search results for inclusion in chat response
        """
        if not search_data.get('results'):
            return f"I searched the web for '{search_data.get('query', '')}' but couldn't find current information. The query may be too specific or the information might not be readily available online."
        
        formatted_text = f"I found some recent information about '{search_data['query']}':\n\n"
        
        for i, result in enumerate(search_data['results'][:3], 1):
            formatted_text += f"{i}. **{result['title']}**\n"
            if result['snippet']:
                formatted_text += f"   {result['snippet']}\n"
            if result['url']:
                formatted_text += f"   Source: {result['url']}\n"
            formatted_text += "\n"
        
        if search_data['results_count'] > 3:
            formatted_text += f"*(Found {search_data['results_count']} total results)*\n"
        
        return formatted_text.strip()
    
    async def close(self):
        """Clean up resources"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def should_search_web(self, user_message: str, model_response: str = "") -> bool:
        """
        Determine if web search is needed based on user query and model uncertainty
        Enhanced logic to properly handle different query types
        """
        user_lower = user_message.lower()
        response_lower = model_response.lower()
        
        # First, check if this is a casual greeting or simple conversation
        casual_greetings = [
            "hello", "hi", "hey", "how are you", "good morning", "good evening",
            "good afternoon", "what's up", "howdy", "greetings", "thanks", "thank you"
        ]
        
        # Check if it's a tool-specific query that should NOT trigger web search
        tool_specific_keywords = [
            "calculate", "convert", "weather in", "time in", "current time",
            "square root", "multiply", "divide", "add", "subtract",
            "celsius to", "fahrenheit to", "km to miles", "miles to km"
        ]
        
        # Enhanced news detection - these SHOULD trigger web search
        news_keywords = [
            "news about", "latest news", "breaking news", "current news",
            "what's happening", "recent developments", "today's news",
            "news today", "news update", "news on", "climate change news"
        ]
        
        # Check message characteristics
        is_casual_greeting = any(
            greeting in user_lower 
            for greeting in casual_greetings
        ) and len(user_message.split()) < 10
        
        is_tool_query = any(
            keyword in user_lower 
            for keyword in tool_specific_keywords
        )
        
        is_news_query = any(
            keyword in user_lower 
            for keyword in news_keywords
        )
        
        # If it's a casual greeting or tool query, don't trigger web search
        if is_casual_greeting or (is_tool_query and not is_news_query):
            logger.info(f"Skipping web search - Casual: {is_casual_greeting}, Tool: {is_tool_query}")
            return False
        
        # Keywords that suggest current/recent information needs
        current_info_keywords = [
            'current', 'recent', 'latest', 'today', 'now', 'this year', '2025',
            'breaking', 'update', 'what happened', 'what\'s happening'
        ]
        
        # Keywords that suggest factual lookup needs
        factual_keywords = [
            'who is', 'what is', 'when did', 'where is', 'how many',
            'population of', 'capital of', 'president of', 'ceo of',
            'founder of'
        ]
        
        # Model uncertainty indicators
        uncertainty_phrases = [
            "i don't know", "i'm not sure", "i don't have", "i cannot provide",
            "i don't have access", "i'm not aware", "i don't have current",
            "i don't have recent", "my knowledge", "as of my last update"
        ]
        
        # Check for different trigger conditions
        needs_current_info = any(keyword in user_lower for keyword in current_info_keywords)
        needs_factual_info = any(keyword in user_lower for keyword in factual_keywords)
        model_uncertain = any(phrase in response_lower for phrase in uncertainty_phrases)
        
        # News queries have highest priority
        if is_news_query:
            logger.info(f"Web search triggered - News query detected: {user_message[:50]}...")
            return True
        
        # Check other conditions
        should_search = needs_current_info or needs_factual_info or model_uncertain
        
        if should_search:
            logger.info(f"Web search triggered - Current: {needs_current_info}, Factual: {needs_factual_info}, Uncertain: {model_uncertain}")
        
        return should_search

# Global instance
web_search_tool = WebSearchTool()

async def search_web(query: str, max_results: int = 3) -> Dict[str, Any]:
    """Convenience function for web search"""
    return await web_search_tool.search(query, max_results)

def format_web_results_for_chat(search_data: Dict[str, Any]) -> str:
    """Convenience function for formatting search results"""
    return web_search_tool.format_search_results_for_chat(search_data)

def should_trigger_web_search(user_message: str, model_response: str = "") -> bool:
    """Convenience function for search detection"""
    return web_search_tool.should_search_web(user_message, model_response)
