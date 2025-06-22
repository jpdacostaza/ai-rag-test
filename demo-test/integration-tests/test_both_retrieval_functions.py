#!/usr/bin/env python3

import requests
import time

# Test both retrieval functions with enhanced logging
def test_search_endpoint():
    """Test the /upload/search endpoint (uses database.py retrieve_user_memory)"""
    print("🧪 Testing search endpoint...")
    
    url = "http://localhost:8001/upload/search"
    
    # Test data
    test_data = {
        "query": "test document",
        "user_id": "test-user-123", 
        "limit": 5
    }
    
    try:
        response = requests.post(url, data=test_data, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_chat_endpoint():
    """Test chat endpoint which should use database_manager.py retrieve_user_memory"""
    print("\n🧪 Testing chat endpoint...")
    
    url = "http://localhost:8001/api/chat"
    
    # Test data
    test_data = {
        "model": "qwen2.5:0.5b",
        "messages": [
            {
                "role": "user", 
                "content": "Tell me about my uploaded documents"
            }
        ],
        "user_id": "test-user-123",
        "stream": False
    }
    
    try:
        response = requests.post(url, json=test_data, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    print("🔍 Testing both retrieval functions with enhanced logging...")
    print("=" * 60)
    
    # Give the backend a moment to start up
    time.sleep(2)
    
    # Test search endpoint (database.py)
    search_result = test_search_endpoint()
    
    # Test chat endpoint (database_manager.py) 
    chat_result = test_chat_endpoint()
    
    print("\n" + "=" * 60)
    print("🔍 Test Summary:")
    print(f"Search endpoint results: {search_result.get('results_count', 0) if search_result else 'Failed'}")
    print(f"Chat endpoint worked: {'Yes' if chat_result else 'No'}")
    
    print("\nCheck backend logs for detailed debug output!")

if __name__ == "__main__":
    main()
