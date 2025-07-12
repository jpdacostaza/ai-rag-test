#!/usr/bin/env python3
"""
Quick Web Search Test Runner
============================

A simple script to quickly test web search and anti-hallucination capabilities.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from web_search_tool import should_trigger_web_search, search_web


async def quick_test():
    """Run a quick test of the web search system."""
    print("🔍 Quick Web Search & Anti-Hallucination Test")
    print("=" * 50)
    
    # Test cases that should trigger web search
    should_trigger = [
        "Tell me about SWIFT company",
        "What is the latest news about AI?", 
        "Who is the CEO of Microsoft in 2025?",
        "swift financial services information"
    ]
    
    # Test cases that should NOT trigger web search
    should_not_trigger = [
        "What is 2+2?",
        "Write a poem about cats",
        "Hello, how are you?",
        "Explain machine learning"
    ]
    
    print("\n✅ Should TRIGGER web search:")
    for query in should_trigger:
        result = should_trigger_web_search(query, "")
        status = "✓" if result else "✗"
        print(f"  {status} {query}")
    
    print("\n❌ Should NOT trigger web search:")
    for query in should_not_trigger:
        result = should_trigger_web_search(query, "")
        status = "✓" if not result else "✗"
        print(f"  {status} {query}")
    
    print("\n🌐 Testing actual web search:")
    try:
        result = await search_web("SWIFT financial company", max_results=1)
        if result.get("status") == "success":
            print("  ✓ Web search is working!")
            print(f"    Query: {result.get('query')}")
            print(f"    Results: {len(result.get('results', []))}")
        else:
            print(f"  ⚠️ Web search returned: {result.get('status')}")
    except Exception as e:
        print(f"  ❌ Web search error: {e}")
    
    print("\n🎉 Quick test completed!")


if __name__ == "__main__":
    asyncio.run(quick_test())
