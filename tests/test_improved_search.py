#!/usr/bin/env python3
import asyncio
import sys
sys.path.append('/app/utilities')
from enhanced_web_search import search_web

async def test():
    result = await search_web('European news headlines today', max_results=3)
    print('Improved Search Results:')
    print('='*50)
    for i, item in enumerate(result.get('results', []), 1):
        title = item.get('title', 'No title')
        snippet = item.get('snippet', 'No snippet')
        link = item.get('link', 'No link')
        print(f'{i}. {title}')
        print(f'   {snippet}')
        print(f'   {link}')
        print()

asyncio.run(test())
