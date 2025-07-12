#!/usr/bin/env python3
"""
Test web search without authentication dependency
"""

import sys
import asyncio
sys.path.insert(0, '.')
sys.path.insert(0, 'pipelines')

print("=== TESTING WEB SEARCH WITHOUT AUTH DEPENDENCY ===")
print()

try:
    from enhanced_memory_pipeline import Pipeline
    
    # Create pipeline instance
    pipeline = Pipeline()
    
    # Disable memory to test just web search
    pipeline.valves.enable_memory = False
    
    # Test body - simple web search request
    test_body = {
        "messages": [
            {
                "role": "user", 
                "content": "search the web for current weather in the netherlands"
            }
        ],
        "model": "llama3.2:3b"
    }
    
    print("Testing web search with memory disabled...")
    print("This should work even without authentication")
    print()
    
    async def test_web_search_only():
        try:
            # Call inlet without user authentication
            result = await pipeline.inlet(body=test_body.copy())
            
            print("✅ Pipeline inlet completed")
            print(f"Original messages: {len(test_body['messages'])}")
            print(f"Result messages: {len(result['messages'])}")
            
            # Check for web search results
            web_search_found = False
            for msg in result["messages"]:
                if msg.get("role") == "system":
                    content = msg.get("content", "")
                    if "web search results" in content.lower():
                        print(f"✅ WEB SEARCH RESULTS FOUND!")
                        print(f"System message length: {len(content)} chars")
                        web_search_found = True
                        break
                    else:
                        print(f"System message (no web search): {content[:100]}...")
            
            if not web_search_found:
                print(f"❌ No web search results found")
                # Show all messages for debugging
                for i, msg in enumerate(result["messages"]):
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")[:100]
                    print(f"  Message {i}: {role} - {content}...")
            
            return web_search_found
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # Run the test
    success = asyncio.run(test_web_search_only())
    
    if success:
        print(f"\n🎉 SUCCESS: Web search works independently!")
        print(f"This means the issue was the auth dependency")
    else:
        print(f"\n❌ FAILED: Web search still not working")
        print(f"Need to investigate further")
        
except Exception as e:
    print(f"❌ Setup error: {e}")
    import traceback
    traceback.print_exc()
