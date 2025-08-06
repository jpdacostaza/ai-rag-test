#!/usr/bin/env python3
"""
Test Web Search Functionality
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.web_search import Tools

async def test_web_search():
    print("🧪 Testing Web Search Functionality")
    print("=" * 50)
    
    tools = Tools()
    
    # Test search for Swift company
    test_query = "Swift company"
    print(f"🔍 Testing search for: {test_query}")
    
    try:
        result = await tools.search_web(test_query, max_results=3)
        print("\n📝 Search Result:")
        print(result)
        
        # Check if it's a fallback message
        if "Live web search temporarily unavailable" in result:
            print("\n⚠️  Web search is using fallback mode - no real web data")
        elif "Real-time information" in result and "Note:" in result:
            print("\n⚠️  Web search returned generic fallback response")
        else:
            print("\n✅ Web search appears to be working")
            
    except Exception as e:
        print(f"\n❌ Web search failed: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Web Search Test Complete")

if __name__ == "__main__":
    asyncio.run(test_web_search())
