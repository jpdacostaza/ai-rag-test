#!/usr/bin/env python3
"""
Test Chat with Uncertainty Triggers
"""

import requests
import json

def test_uncertainty_triggers():
    print("🧪 Testing Uncertainty Trigger for Web Search")
    print("=" * 60)
    
    # Test cases with uncertainty phrases that should trigger web search
    test_cases = [
        {
            "name": "Explicit Uncertainty",
            "query": "What is Swift company? I'm not sure about this."
        },
        {
            "name": "Knowledge Limitation",
            "query": "Tell me about Swift company - I don't have current information."
        },
        {
            "name": "Explicit Web Search Request",
            "query": "Please search the web for Swift company information."
        },
        {
            "name": "Current Information Request",
            "query": "What's the latest news about Swift company today?"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print(f"Query: {test_case['query']}")
        print("-" * 50)
        
        chat_payload = {
            "model": "qwen2.5:3b",
            "messages": [
                {
                    "role": "user", 
                    "content": test_case['query']
                }
            ],
            "stream": False
        }
        
        try:
            response = requests.post(
                "http://localhost:3000/v1/chat/completions",
                json=chat_payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                assistant_message = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                
                print("📝 Response:")
                print(assistant_message[:300] + "..." if len(assistant_message) > 300 else assistant_message)
                
                # Check for web search indicators
                web_indicators = [
                    "web search", "search results", "current information", 
                    "latest", "according to", "based on", "sources",
                    "real-time", "july 2025", "august 2025"
                ]
                
                if any(indicator in assistant_message.lower() for indicator in web_indicators):
                    print("✅ Web search was triggered!")
                else:
                    print("❌ No web search detected")
                    
            else:
                print(f"❌ Request failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
        
        print("-" * 50)
    
    print("\n🏁 Uncertainty Trigger Test Complete")

if __name__ == "__main__":
    test_uncertainty_triggers()
