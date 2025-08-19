#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.append('/app/utilities')

# Test direct DDGS functionality
from ddgs import DDGS

async def test_ddgs_regions():
    print("Testing DDGS with different regions and search types...")
    
    queries = [
        "European news headlines today",
        "BBC news Europe",
        "euronews headlines"
    ]
    
    regions = [
        ("eu-en", "Europe English"),
        ("uk-en", "UK English"), 
        ("us-en", "US English"),
        ("wt-wt", "Worldwide"),
    ]
    
    for query in queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)
        
        for region_code, region_name in regions:
            print(f"\n--- {region_name} ({region_code}) ---")
            
            try:
                with DDGS() as ddgs:
                    # Try news search first for news queries
                    if "news" in query.lower() or "headlines" in query.lower():
                        print("Using NEWS search...")
                        results = list(ddgs.news(
                            query,
                            region=region_code,
                            safesearch="moderate",
                            max_results=2
                        ))
                    else:
                        print("Using TEXT search...")
                        results = list(ddgs.text(
                            query,
                            region=region_code,
                            safesearch="moderate",
                            max_results=2
                        ))
                    
                    for i, result in enumerate(results, 1):
                        title = result.get('title', 'No title')
                        url = result.get('href') or result.get('url', 'No URL')
                        body = result.get('body', 'No description')
                        print(f"{i}. {title}")
                        print(f"   {body[:80]}...")
                        print(f"   {url}")
                        
                    if not results:
                        print("No results found")
                        
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_ddgs_regions())
