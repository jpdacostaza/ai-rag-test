#!/usr/bin/env python3
"""
Quick Web Search Integration Test
"""

import requests
import json
import time

def test_web_search_integration():
    """Test web search integration quickly"""
    
    print("🔍 Quick Web Search Integration Test")
    print("=" * 50)
    
    # Test query that should trigger web search
    test_request = {
        "user_id": "debug_user",
        "message": "What are the latest developments in artificial intelligence today?",
        "model": "llama3.2:3b"
    }
    
    print(f"Testing query: '{test_request['message']}'")
    
    try:
        start_time = time.time()
        response = requests.post(
            "http://localhost:9099/chat",
            json=test_request,
            timeout=60
        )
        duration = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get("response", "")
            
            print(f"\n✅ Response received in {duration:.1f}s")
            print(f"📝 Response length: {len(response_text)} chars")
            print(f"📄 Response content:\n{response_text}\n")
            
            # Check for web search indicators
            web_indicators = [
                "i found", "recent information", "search", "source:", 
                "web", "latest", "duckduckgo", "results"
            ]
            
            found_indicators = [ind for ind in web_indicators if ind in response_text.lower()]
            
            if found_indicators:
                print(f"🔍 Web search indicators found: {found_indicators}")
                print("✅ Web search integration appears to be working!")
            else:
                print("⚠️  No clear web search indicators found")
                print("🔍 This could mean:")
                print("   - Web search didn't trigger")
                print("   - Web search failed")
                print("   - Model provided answer without web search")
                
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"📄 Error response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

def test_uncertainty_detection():
    """Test uncertainty detection"""
    print("\n🤔 Testing Uncertainty Detection")
    print("=" * 50)
    
    # Import the web search functions to test directly
    try:
        from web_search_tool import should_trigger_web_search
        
        test_cases = [
            ("What's the latest news?", "", True),
            ("I don't know about that", "", True),
            ("Hello how are you?", "I'm doing well", False),
            ("Who is the current president?", "I'm not sure", True),
        ]
        
        for query, response, expected in test_cases:
            result = should_trigger_web_search(query, response)
            status = "✅" if result == expected else "❌"
            print(f"{status} Query: '{query}' -> {result} (expected {expected})")
            
    except ImportError as e:
        print(f"❌ Cannot import web search functions: {e}")

if __name__ == "__main__":
    test_web_search_integration()
    test_uncertainty_detection()
