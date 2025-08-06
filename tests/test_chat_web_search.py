#!/usr/bin/env python3
"""
Test Chat with Web Search
"""

import requests
import json

def test_chat_with_web_search():
    print("🧪 Testing Chat with Web Search Integration")
    print("=" * 60)
    
    # Test chat with explicit web search request
    chat_payload = {
        "model": "qwen2.5:3b",
        "messages": [
            {
                "role": "user", 
                "content": "Search the web for information about Swift company. What is it exactly? I need current information."
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
            
            print("✅ Chat response received")
            print("📝 Response:")
            print("-" * 40)
            print(assistant_message)
            print("-" * 40)
            
            # Check if web search was used
            web_search_indicators = [
                'search', 'found', 'according to', 'based on current information',
                'real-time', 'web search', 'online', 'sources', 'website'
            ]
            
            if any(indicator in assistant_message.lower() for indicator in web_search_indicators):
                print("\n✅ Chat appears to be using web search!")
            else:
                print("\n⚠️  Chat may still be using cached/training data")
                
        else:
            print(f"❌ Chat failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_chat_with_web_search()
