#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.append('/app/utilities')
from enhanced_web_search import search_web

async def test_search():
    print("Testing web search for European news...")
    
    # Try more specific European news query
    result = await search_web('Europe news headlines August 2025 today', max_results=5)
    print(f"Query: {result.get('query')}")
    print(f"Results found: {len(result.get('results', []))}")
    print("="*50)
    
    for i, item in enumerate(result.get('results', []), 1):
        title = item.get('title', 'No title')
        snippet = item.get('snippet', 'No snippet')
        link = item.get('link', 'No link')
        print(f"{i}. {title}")
        print(f"   {snippet}")
        print(f"   {link}")
        print()

if __name__ == "__main__":
    asyncio.run(test_search())
