#!/usr/bin/env python3
"""
End-to-end test for web search integration in the chat endpoint.
"""

import json
import asyncio
import httpx

async def test_chat_with_web_search():
    """Test the chat endpoint with queries that should trigger web search"""
    
    print("🚀 Testing Chat Endpoint with Web Search Integration")
    print("=" * 60)
    
    # Test cases for web search triggers
    test_cases = [
        {
            "name": "Uncertainty Query",
            "message": "Who is the current CEO of Microsoft?",
            "user_id": "test_web_search_user",
            "expected_trigger": True
        },
        {
            "name": "Current Events",
            "message": "What's happening in the news today?",
            "user_id": "test_web_search_user",
            "expected_trigger": True
        },
        {
            "name": "Factual Query",
            "message": "What is the population of Tokyo in 2025?",
            "user_id": "test_web_search_user",
            "expected_trigger": True
        },
        {
            "name": "Casual Conversation",
            "message": "How are you doing today?",
            "user_id": "test_web_search_user",
            "expected_trigger": False
        }
    ]
    
    backend_url = "http://localhost:9099"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📋 Test {i}: {test_case['name']}")
            print(f"Query: '{test_case['message']}'")
            
            try:
                response = await client.post(
                    f"{backend_url}/chat",
                    json={
                        "message": test_case["message"],
                        "user_id": test_case["user_id"]
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get("response", "")
                    
                    print(f"✅ Response received ({len(response_text)} chars)")
                    
                    # Check if response contains web search indicators
                    web_search_indicators = [
                        "I found some recent information",
                        "Source:",
                        "*(Found",
                        "web results"
                    ]
                    
                    has_web_search = any(indicator in response_text for indicator in web_search_indicators)
                    
                    if test_case["expected_trigger"]:
                        if has_web_search:
                            print(f"🔍 ✅ Web search was triggered as expected")
                        else:
                            print(f"⚠️  Web search not detected in response")
                    else:
                        if not has_web_search:
                            print(f"✅ Web search correctly not triggered")
                        else:
                            print(f"⚠️  Unexpected web search in response")
                    
                    # Show response preview
                    preview = response_text[:200] + "..." if len(response_text) > 200 else response_text
                    print(f"Response preview: {preview}")
                    
                else:
                    print(f"❌ Request failed with status {response.status_code}")
                    print(f"Error: {response.text}")
                    
            except Exception as e:
                print(f"❌ Test failed: {e}")
    
    print(f"\n🏁 Chat endpoint web search integration tests completed")

if __name__ == "__main__":
    asyncio.run(test_chat_with_web_search())
