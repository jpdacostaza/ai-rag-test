#!/usr/bin/env python3
"""
Debug web search issue step by step
"""

import sys
import asyncio
sys.path.insert(0, '.')
sys.path.insert(0, 'pipelines')

print("=== DEBUGGING WEB SEARCH STEP BY STEP ===")
print()

try:
    from enhanced_memory_pipeline import Pipeline, web_search_available, should_trigger_web_search
    
    print(f"1. Web search available globally: {web_search_available}")
    
    # Test trigger function directly
    test_query = "search the web for current weather in the netherlands"
    trigger_result = should_trigger_web_search(test_query, "")
    print(f"2. Direct trigger test: {trigger_result}")
    
    # Create pipeline and test with memory enabled
    pipeline = Pipeline()
    print(f"3. Pipeline created with memory enabled: {pipeline.valves.enable_memory}")
    
    test_body = {
        "messages": [
            {"role": "user", "content": test_query}
        ],
        "model": "llama3.2:3b"
    }
    
    async def test_with_memory_enabled():
        print(f"\n--- Testing with memory ENABLED ---")
        result = await pipeline.inlet(body=test_body.copy())
        return check_web_search_results(result, "Memory enabled")
    
    async def test_with_memory_disabled():
        print(f"\n--- Testing with memory DISABLED ---")
        pipeline.valves.enable_memory = False
        result = await pipeline.inlet(body=test_body.copy())
        return check_web_search_results(result, "Memory disabled")
    
    def check_web_search_results(result, test_name):
        print(f"{test_name} - Messages: {len(result['messages'])}")
        for i, msg in enumerate(result["messages"]):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            print(f"  {i}: {role} - {len(content)} chars")
            if "web search" in content.lower():
                print(f"    ✅ Contains web search results!")
                return True
            elif role == "system":
                print(f"    Content preview: {content[:150]}...")
        return False
    
    # Run both tests
    result1 = asyncio.run(test_with_memory_enabled())
    result2 = asyncio.run(test_with_memory_disabled())
    
    print(f"\n=== RESULTS ===")
    print(f"Memory enabled: {'✅ Web search worked' if result1 else '❌ No web search'}")
    print(f"Memory disabled: {'✅ Web search worked' if result2 else '❌ No web search'}")
    
    if not result1 and not result2:
        print(f"\n❌ Web search not working in either case!")
        print(f"The issue is in the pipeline logic itself")
    elif result1 and not result2:
        print(f"\n⚠️ Web search only works with memory enabled")
        print(f"Need to fix the early return logic")
    elif result2 and not result1:
        print(f"\n⚠️ Web search only works with memory disabled")
        print(f"Authentication is blocking web search")
    else:
        print(f"\n✅ Web search works in both cases!")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
