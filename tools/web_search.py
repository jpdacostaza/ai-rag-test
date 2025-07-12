"""
title: Web Search Tool
author: open-webui
author_url: https://github.com/open-webui
funding_url: https://github.com/open-webui
version: 2.0.0
license: MIT
requirements: httpx
"""

import httpx
import json
from datetime import datetime
from urllib.parse import quote_plus
from typing import Optional


class Tools:
    def __init__(self):
        pass

    async def search_web(
        self,
        query: str,
        max_results: int = 5
    ) -> str:
        """
        Search the web for current information. Provides real-time data from July 12, 2025.
        
        Args:
            query: The search query to look up current information
            max_results: Maximum number of results to return (default: 5)
            
        Returns:
            Current search results with sources and real-time data
        """
        
        current_date = datetime.now().strftime("%B %d, %Y")
        current_year = datetime.now().year
        
        # Force real-time search with current date
        search_query = f"{query} {current_year} July 2025"
        
        try:
            # Primary method: SearXNG with forced current results
            try:
                search_url = "https://searx.be/search"
                params = {
                    'q': search_query,
                    'format': 'json',
                    'engines': 'google,bing',
                    'categories': 'general',
                    'time_range': 'day'
                }
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                
                async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
                    response = await client.get(search_url, params=params)
                    if response.status_code == 200:
                        data = response.json()
                        results = []
                        
                        for item in data.get('results', []):
                            if len(results) >= max_results:
                                break
                                
                            title = item.get('title', '')
                            content = item.get('content', '')
                            url = item.get('url', '')
                            
                            if title and len(title) > 10:
                                results.append({
                                    'title': title[:120] + '...' if len(title) > 120 else title,
                                    'content': content[:300] + '...' if len(content) > 300 else content,
                                    'url': url
                                })
                        
                        if results:
                            formatted_results = f"🌐 **REAL-TIME WEB SEARCH RESULTS for '{query}'**\n"
                            formatted_results += f"*🕐 Search performed on {current_date} at {datetime.now().strftime('%H:%M:%S')}*\n\n"
                            
                            for i, result in enumerate(results, 1):
