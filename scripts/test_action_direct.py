"""
Test script to verify Action execution with direct logging
"""

import asyncio
import sys
import os
sys.path.append(os.getcwd())

async def test_action():
    from tools.web_search_tool import Action
    
    print("=== Testing Action directly ===")
    action = Action()
    result = await action.run(query="latest AI news today", max_results=3)
    print(f"Result length: {len(result)}")
    print(f"First 200 chars: {result[:200]}")
    print("=== Action test complete ===")

if __name__ == '__main__':
    asyncio.run(test_action())
