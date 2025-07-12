#!/usr/bin/env python3
"""
Test improved authentication with user ID fallback
"""

import sys
import asyncio
sys.path.insert(0, '.')
sys.path.insert(0, 'pipelines')

print("=== TESTING IMPROVED AUTHENTICATION ===")
print()

async def test_with_user_id():
    """Test with a user ID present"""
    from enhanced_memory_pipeline import Pipeline
    
    pipeline = Pipeline()
    
    # Test with user ID that's not UUID format
    test_body = {
        "messages": [
            {"role": "user", "content": "search the web for current weather in the netherlands"}
        ],
        "model": "llama3.2:3b"
    }
    
    user_data = {"id": "test-user-123", "name": "Test User"}
    
    print("Testing with non-UUID user ID...")
    result = await pipeline.inlet(body=test_body.copy(), __user__=user_data)
    
    print(f"✅ Pipeline completed")
    print(f"Messages: {len(result['messages'])}")
    
    # Check for both web search and memory injection
    web_search_found = False
    memory_context_found = False
    
    for msg in result["messages"]:
        if msg.get("role") == "system":
            content = msg.get("content", "")
            if "web search results" in content.lower():
                web_search_found = True
                print(f"✅ Web search results found")
            if "memory" in content.lower() or "previous conversations" in content.lower():
                memory_context_found = True
                print(f"✅ Memory context found")
    
    return web_search_found, memory_context_found

async def test_without_user_id():
    """Test without any user ID - should use anonymous fallback"""
    from enhanced_memory_pipeline import Pipeline
    
    pipeline = Pipeline()
    
    test_body = {
        "messages": [
            {"role": "user", "content": "search the web for current weather in the netherlands"}
        ],
        "model": "llama3.2:3b"
    }
    
    print("\nTesting without user ID (anonymous fallback)...")
    result = await pipeline.inlet(body=test_body.copy())
    
    print(f"✅ Pipeline completed")
    print(f"Messages: {len(result['messages'])}")
    
    # Check for both web search and memory injection
    web_search_found = False
    memory_context_found = False
    
    for msg in result["messages"]:
        if msg.get("role") == "system":
            content = msg.get("content", "")
            if "web search results" in content.lower():
                web_search_found = True
                print(f"✅ Web search results found")
            if "memory" in content.lower() or "previous conversations" in content.lower():
                memory_context_found = True
                print(f"✅ Memory context found")
    
    return web_search_found, memory_context_found

async def main():
    try:
        print("TEST 1: With User ID")
        print("-" * 30)
        web1, mem1 = await test_with_user_id()
        
        print("\nTEST 2: Without User ID (Anonymous)")
        print("-" * 30)
        web2, mem2 = await test_without_user_id()
        
        print("\n" + "=" * 50)
        print("SUMMARY")
        print("=" * 50)
        print(f"With User ID:")
        print(f"  Web Search: {'✅' if web1 else '❌'}")
        print(f"  Memory: {'✅' if mem1 else '❌'}")
        print(f"Without User ID:")
        print(f"  Web Search: {'✅' if web2 else '❌'}")
        print(f"  Memory: {'✅' if mem2 else '❌'}")
        
        if web1 and web2:
            print(f"\n🎉 WEB SEARCH: Working in both scenarios!")
        elif web1 or web2:
            print(f"\n⚠️ WEB SEARCH: Partially working")
        else:
            print(f"\n❌ WEB SEARCH: Not working")
            
        if mem1 and mem2:
            print(f"🎉 MEMORY: Working in both scenarios!")
        elif mem1 or mem2:
            print(f"⚠️ MEMORY: Partially working")
        else:
            print(f"❌ MEMORY: Not working")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
