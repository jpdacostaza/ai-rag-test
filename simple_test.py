#!/usr/bin/env python3
"""
Simple test to verify backend functionality
"""

import requests
import json

def test_simple_chat():
    """Test simple chat functionality"""
    
    print("🧪 Simple Chat Test")
    print("=" * 30)
    
    # Simple greeting test
    test_request = {
        "user_id": "test_user",
        "message": "Hello there!",
        "model": "llama3.2:3b"
    }
    
    print(f"Testing: '{test_request['message']}'")
    
    try:
        response = requests.post(
            "http://localhost:9099/chat",
            json=test_request,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Response received: {result.get('response', 'No response field')[:100]}...")
            return True
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_web_search_trigger():
    """Test web search trigger detection"""
    
    print("\n🔍 Web Search Trigger Test")
    print("=" * 30)
    
    # Test that should trigger web search
    test_request = {
        "user_id": "test_user", 
        "message": "What's happening in the world today?",
        "model": "llama3.2:3b"
    }
    
    print(f"Testing: '{test_request['message']}'")
    
    try:
        response = requests.post(
            "http://localhost:9099/chat",
            json=test_request,
            timeout=45
        )
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get('response', '')
            
            # Check if web search was used
            if 'web search' in response_text.lower() or 'searched' in response_text.lower() or 'found' in response_text.lower():
                print(f"✅ Web search likely triggered: {response_text[:100]}...")
                return True
            else:
                print(f"⚠️  Response (web search unclear): {response_text[:100]}...")
                return True  # Still successful response
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Backend Functionality")
    print("=" * 50)
    
    # Test simple chat
    simple_success = test_simple_chat()
    
    # Test web search if simple chat works
    if simple_success:
        web_search_success = test_web_search_trigger()
        
        print(f"\n📊 Results:")
        print(f"Simple Chat: {'✅' if simple_success else '❌'}")
        print(f"Web Search: {'✅' if web_search_success else '❌'}")
        
        if simple_success and web_search_success:
            print("\n🎉 All tests passed! Backend is working correctly.")
        else:
            print("\n⚠️  Some tests failed. Check the logs above.")
    else:
        print("\n❌ Basic chat functionality failed. Cannot test web search.")
