#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.append('/app/utilities')
from enhanced_web_search import search_web

async def test_different_searches():
    print("Testing different web search strategies...")
    
    searches = [
        "European news today",
        "BBC news Europe",
        "Reuters Europe news", 
        "DW news Europe today",
        "euronews headlines",
        "CNN Europe news today"
    ]
    
    for search_query in searches:
        print(f"\n{'='*60}")
        print(f"Testing: {search_query}")
        print('='*60)
        
        try:
            result = await search_web(search_query, max_results=3)
            results = result.get('results', [])
            
            if not results:
                print("No results found")
                continue
                
            for i, item in enumerate(results, 1):
                title = item.get('title', 'No title')
                snippet = item.get('snippet', 'No snippet')
                link = item.get('link', 'No link')
                print(f"{i}. {title}")
                print(f"   {snippet[:100]}...")
                print(f"   {link}")
                print()
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_different_searches())
