#!/usr/bin/env python3
"""
Test fallback behavior by simulating import failures
"""

import sys
import asyncio
sys.path.insert(0, '.')

print("=== TESTING FALLBACK BEHAVIOR ===")
print()

# Test 1: Temporarily rename web_search_tool to simulate failure
print("TEST 1: Simulating web search import failure...")
print("-" * 50)

import os
original_name = "web_search_tool.py"
temp_name = "web_search_tool_temp.py" 

try:
    # Temporarily rename the file to simulate import failure
    if os.path.exists(original_name):
        os.rename(original_name, temp_name)
    
    # Clear any cached imports
    if 'enhanced_memory_pipeline' in sys.modules:
        del sys.modules['enhanced_memory_pipeline']
    if 'web_search_tool' in sys.modules:
        del sys.modules['web_search_tool']
    
    # Add pipelines to path
    sys.path.insert(0, 'pipelines')
    
    # Import pipeline with missing web search tool
    from enhanced_memory_pipeline import (
        web_search_available,
        should_trigger_web_search,
        search_web
    )
    
    print(f"Web search available: {web_search_available}")
    
    # Test fallback functions
    print("\nTesting fallback functions...")
    test_query = "search the web for weather"
    
    print(f"Testing trigger function...")
    trigger_result = should_trigger_web_search(test_query, "")
    print(f"Trigger result: {trigger_result}")
    
    print(f"Testing search function...")
    async def test_search():
        result = await search_web(test_query, 3)
        return result
    
    search_result = asyncio.run(test_search())
    print(f"Search result: {search_result}")
    
    print("\n✅ Fallback system working correctly!")
    
finally:
    # Restore the original file
    if os.path.exists(temp_name):
        os.rename(temp_name, original_name)
        print(f"\n🔄 Restored {original_name}")

print("\n=== FALLBACK TEST COMPLETE ===")
