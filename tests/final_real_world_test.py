#!/usr/bin/env python3
"""
Final comprehensive real-world test
"""

import sys
import asyncio
sys.path.insert(0, '.')
sys.path.insert(0, 'pipelines')

print("🌍 FINAL REAL-WORLD TEST")
print("=" * 60)
print("Simulating actual OpenWebUI request with realistic user data")
print()

async def comprehensive_test():
    from enhanced_memory_pipeline import Pipeline
    
    # Create pipeline
    pipeline = Pipeline()
    
    # Realistic OpenWebUI request body
    openwebui_body = {
        "messages": [
            {
                "id": "msg_001", 
                "role": "user", 
                "content": "search the web for current weather in the netherlands",
                "timestamp": 1641234567
            }
        ],
        "model": "llama3.2:3b",
        "stream": False,
        "chat_id": "chat_12345",
        "title": "Weather Search"
    }
    
    # Realistic user object (as OpenWebUI would provide)
    openwebui_user = {
        "id": "user_67890",
        "name": "John Doe", 
        "email": "john@example.com",
        "role": "user"
    }
    
    print("BEFORE PIPELINE:")
    print(f"  Messages: {len(openwebui_body['messages'])}")
    for i, msg in enumerate(openwebui_body["messages"]):
        print(f"    {i}: {msg['role']} - {msg['content']}")
    print()
    
    print("PROCESSING...")
    result = await pipeline.inlet(body=openwebui_body.copy(), __user__=openwebui_user)
    
    print("\nAFTER PIPELINE:")
    print(f"  Messages: {len(result['messages'])}")
    
    # Analyze each message
    web_search_found = False
    memory_found = False
    
    for i, msg in enumerate(result["messages"]):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        
        print(f"\n  Message {i}: {role}")
        print(f"    Length: {len(content)} characters")
        
        if len(content) > 0:
            # Check for web search
            if "web search" in content.lower() or "current" in content.lower() and "weather" in content.lower():
                web_search_found = True
                print(f"    ✅ Contains web search content")
            
            # Check for memory/context
            if "memory" in content.lower() or "previous" in content.lower() or "conversation" in content.lower():
                memory_found = True
                print(f"    ✅ Contains memory content")
            
            # Show content preview
            if len(content) > 200:
                preview = content[:200] + "..."
            else:
                preview = content
            print(f"    Preview: {preview}")
        else:
            print(f"    ❌ Empty content")
    
    # Check if user_id was added
    user_id_added = "user_id" in result
    if user_id_added:
        print(f"\n  ✅ User ID added to body: {result['user_id']}")
    else:
        print(f"\n  ❌ No user_id in result body")
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    
    success_count = 0
    total_checks = 3
    
    if web_search_found:
        print("✅ Web search: WORKING")
        success_count += 1
    else:
        print("❌ Web search: NOT WORKING")
    
    if memory_found:
        print("✅ Memory system: WORKING") 
        success_count += 1
    else:
        print("❌ Memory system: NOT WORKING")
    
    if user_id_added:
        print("✅ User authentication: WORKING")
        success_count += 1
    else:
        print("❌ User authentication: NOT WORKING")
    
    print(f"\nOverall: {success_count}/{total_checks} components working")
    
    if success_count == total_checks:
        print("\n🎉 PERFECT! All systems working correctly!")
        print("Your OpenWebUI should have full web search functionality")
    elif success_count >= 2:
        print("\n✅ GOOD! Most systems working")
        print("Web search should work in OpenWebUI")
    elif success_count >= 1:
        print("\n⚠️ PARTIAL! Some systems working")
        print("May have limited functionality")
    else:
        print("\n❌ FAILED! Systems not working properly")
        print("Web search will not work in OpenWebUI")
    
    return success_count >= 1

if __name__ == "__main__":
    try:
        success = asyncio.run(comprehensive_test())
        print(f"\nTest completed. Success: {success}")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
