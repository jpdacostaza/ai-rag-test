#!/usr/bin/env python3
"""
Debug why web search content isn't being detected
"""

import sys
import asyncio
sys.path.insert(0, '.')
sys.path.insert(0, 'pipelines')

async def debug_content():
    from enhanced_memory_pipeline import Pipeline
    
    pipeline = Pipeline()
    
    test_body = {
        "messages": [
            {"role": "user", "content": "search the web for current weather in the netherlands"}
        ]
    }
    
    user_data = {"id": "test-user-123", "name": "Test User"}
    
    print("=== DEBUGGING CONTENT DETECTION ===")
    result = await pipeline.inlet(body=test_body.copy(), __user__=user_data)
    
    print(f"\nOriginal messages: {len(test_body['messages'])}")
    print(f"Result messages: {len(result['messages'])}")
    print()
    
    for i, msg in enumerate(result["messages"]):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        print(f"Message {i}: {role}")
        print(f"  Length: {len(content)} characters")
        print(f"  Content preview: {content[:200]}...")
        print(f"  Contains 'web search': {'web search' in content.lower()}")
        print(f"  Contains 'results': {'results' in content.lower()}")
        print(f"  Contains 'memory': {'memory' in content.lower()}")
        print(f"  Contains 'conversation': {'conversation' in content.lower()}")
        print()

if __name__ == "__main__":
    asyncio.run(debug_content())
