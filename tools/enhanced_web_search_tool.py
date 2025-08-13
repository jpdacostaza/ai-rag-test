"""
Enhanced Multi-Source Web Search Tool
Supports multiple search engines, caching, and advanced content extraction
Version: 2.0.0
"""

import re
import aiohttp
import asyncio
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from dataclasses import dataclass
import urllib.parse

PRINT_PREFIX = "[EnhancedWebSearch]"
print(f"{PRINT_PREFIX} Enhanced Multi-Source Search Tool Loaded.")

# In-memory cache for search results
SEARCH_CACHE = {}
CACHE_TTL_SECONDS = 300  # 5 minutes

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    date: str
    source: str
    rank: int
    relevance_score: float = 0.0

class SearchEngine:
    """Base class for search engine implementations"""
    
    async def search(self, query: str, max_results: int) -> List[SearchResult]:
        raise NotImplementedError

class DuckDuckGoEngine(SearchEngine):
    """Enhanced DuckDuckGo search engine"""
    
    def __init__(self, timeout: int = 15, user_agent: str = None):
        self.timeout = timeout
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    async def search(self, query: str, max_results: int) -> List[SearchResult]:
        try:
            html = await self._fetch(query)
            return self._parse(html, max_results)
        except Exception as e:
            print(f"{PRINT_PREFIX} DuckDuckGo search error: {e}")
            return []
    
    async def _fetch(self, query: str) -> str:
        search_url = "https://html.duckduckgo.com/html/"
        params = {"q": query}
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        headers = {"User-Agent": self.user_agent}
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(search_url, params=params, headers=headers) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"DuckDuckGo returned status {resp.status}")
                return await resp.text()
    
    def _parse(self, html: str, max_results: int) -> List[SearchResult]:
        results: List[SearchResult] = []
        blocks = re.findall(r'<div[^>]*class="[^\"]*result[^\"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
        
        for i, block in enumerate(blocks[:max_results]):
            link = re.search(r'<a[^>]*class="[^\"]*result__a[^\"]*"[^>]*href="([^\"]*)"[^>]*>(.*?)</a>', block, re.DOTALL)
            if not link:
                continue
            
            url, title_html = link.group(1), link.group(2)
            title = re.sub(r'<[^>]+>', '', title_html).strip()
            
            # Enhanced snippet extraction with multiple patterns
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
                    if snippet and len(snippet) > 10:
                        break
            
            # Enhanced date extraction
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
                results.append(SearchResult(
                    title=title,
                    url=url,
                    snippet=snippet,
                    date=date_info,
                    source="DuckDuckGo",
                    rank=i + 1
                ))
        
        return results

class BingEngine(SearchEngine):
    """Bing search engine (placeholder for future implementation)"""
    
    async def search(self, query: str, max_results: int) -> List[SearchResult]:
        # Placeholder - would require Bing API key
        print(f"{PRINT_PREFIX} Bing search not implemented yet")
        return []

class GoogleEngine(SearchEngine):
    """Google search engine (placeholder for future implementation)"""
    
    async def search(self, query: str, max_results: int) -> List[SearchResult]:
        # Placeholder - would require Google API key
        print(f"{PRINT_PREFIX} Google search not implemented yet")
        return []

class SearchCache:
    """In-memory cache for search results"""
    
    @staticmethod
    def get_cache_key(query: str, max_results: int, sources: List[str]) -> str:
        """Generate a cache key for the query"""
        content = f"{query}:{max_results}:{','.join(sorted(sources))}"
        return hashlib.md5(content.encode()).hexdigest()
    
    @staticmethod
    def get(cache_key: str) -> Optional[Tuple[List[SearchResult], datetime]]:
        """Get cached results if not expired"""
        if cache_key in SEARCH_CACHE:
            results, timestamp = SEARCH_CACHE[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=CACHE_TTL_SECONDS):
                return results, timestamp
            else:
                # Remove expired cache entry
                del SEARCH_CACHE[cache_key]
        return None
    
    @staticmethod
    def set(cache_key: str, results: List[SearchResult]):
        """Cache the search results"""
        SEARCH_CACHE[cache_key] = (results, datetime.now())

class ResultRanker:
    """Advanced result ranking and filtering"""
    
    @staticmethod
    def calculate_relevance_score(result: SearchResult, query: str) -> float:
        """Calculate relevance score based on various factors"""
        score = 0.0
        query_lower = query.lower()
        title_lower = result.title.lower()
        snippet_lower = result.snippet.lower()
        
        # Title relevance (weighted heavily)
        title_words = set(title_lower.split())
        query_words = set(query_lower.split())
        title_match = len(title_words.intersection(query_words)) / max(len(query_words), 1)
        score += title_match * 0.5
        
        # Snippet relevance
        snippet_match = len([word for word in query_words if word in snippet_lower]) / max(len(query_words), 1)
        score += snippet_match * 0.3
        
        # Date recency bonus (if date is available)
        if result.date:
            try:
                # Try to parse common date formats and give bonus for recent dates
                current_year = datetime.now().year
                if str(current_year) in result.date or str(current_year - 1) in result.date:
                    score += 0.1
            except:
                pass
        
        # Source ranking bonus
        source_scores = {
            "DuckDuckGo": 1.0,
            "Google": 1.1,
            "Bing": 0.9
        }
        score *= source_scores.get(result.source, 1.0)
        
        # Original rank penalty (lower rank = higher penalty)
        rank_penalty = (result.rank - 1) * 0.05
        score = max(0, score - rank_penalty)
        
        return score
    
    @staticmethod
    def rank_and_filter(results: List[SearchResult], query: str, max_results: int) -> List[SearchResult]:
        """Rank results by relevance and filter to max_results"""
        # Calculate relevance scores
        for result in results:
            result.relevance_score = ResultRanker.calculate_relevance_score(result, query)
        
        # Sort by relevance score (descending)
        sorted_results = sorted(results, key=lambda x: x.relevance_score, reverse=True)
        
        # Remove duplicates (same URL)
        seen_urls = set()
        unique_results = []
        for result in sorted_results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)
        
        return unique_results[:max_results]

class EnhancedSearchTool:
    """Main enhanced search tool with multi-source support"""
    
    def __init__(self):
        self.engines = {
            "duckduckgo": DuckDuckGoEngine(),
            "bing": BingEngine(),
            "google": GoogleEngine()
        }
        self.cache = SearchCache()
        self.ranker = ResultRanker()
    
    async def search(
        self, 
        query: str, 
        max_results: int = 5,
        sources: List[str] = None,
        use_cache: bool = True
    ) -> List[SearchResult]:
        """
        Perform multi-source search with caching and ranking
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            sources: List of search engines to use (default: ["duckduckgo"])
            use_cache: Whether to use cached results
        
        Returns:
            List of ranked SearchResult objects
        """
        if sources is None:
            sources = ["duckduckgo"]  # Default to DuckDuckGo for now
        
        # Check cache first
        cache_key = self.cache.get_cache_key(query, max_results, sources)
        if use_cache:
            cached = self.cache.get(cache_key)
            if cached:
                print(f"{PRINT_PREFIX} Using cached results for: {query}")
                return cached[0][:max_results]
        
        # Perform searches across multiple sources
        all_results = []
        search_tasks = []
        
        for source in sources:
            if source in self.engines:
                task = self.engines[source].search(query, max_results * 2)  # Get more results for better ranking
                search_tasks.append((source, task))
        
        # Execute searches concurrently
        for source, task in search_tasks:
            try:
                results = await task
                all_results.extend(results)
                print(f"{PRINT_PREFIX} {source}: {len(results)} results")
            except Exception as e:
                print(f"{PRINT_PREFIX} Error from {source}: {e}")
        
        # Rank and filter results
        final_results = self.ranker.rank_and_filter(all_results, query, max_results)
        
        # Cache the results
        if use_cache:
            self.cache.set(cache_key, final_results)
        
        print(f"{PRINT_PREFIX} Returning {len(final_results)} ranked results")
        return final_results
    
    def format_results(self, query: str, results: List[SearchResult]) -> str:
        """Format search results for display"""
        if not results:
            return f"No results found for '{query}'."
        
        out = [f"🔍 **Enhanced Web Search Results for '{query}'**", ""]
        
        for result in results:
            # Enhanced formatting with relevance score and source
            out.append(f"**{result.rank}. {result.title}** ⭐ {result.relevance_score:.2f}")
            out.append(f"🔗 **URL:** {result.url}")
            out.append(f"📡 **Source:** {result.source}")
            
            if result.date:
                out.append(f"📅 **Date:** {result.date}")
            
            if result.snippet:
                out.append(f"📄 **Content:** {result.snippet}")
            else:
                out.append("📄 **Content:** (No preview available)")
            
            out.append("---")
        
        # Add metadata
        out.append(f"🕒 **Search completed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        out.append(f"📊 **Total results:** {len(results)}")
        out.append(f"🚀 **Cache status:** {'Cached' if any('cached' in str(r) for r in results) else 'Fresh'}")
        out.append("")
        out.append("**IMPORTANT:** Use this information to answer the user's question. These are real, current web search results.")
        
        return "\n".join(out)

# Global enhanced search tool instance
enhanced_search_tool = EnhancedSearchTool()

print(f"{PRINT_PREFIX} Enhanced Multi-Source Search Tool Ready!")
