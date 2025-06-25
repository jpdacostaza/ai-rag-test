#!/usr/bin/env python3
"""
Live Web Search Integration Test
Tests the web search functionality with real queries in a live environment.
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:9099"

def live_web_search_test():
    """Perform live web search integration tests"""
    
    print("🚀 Live Web Search Integration Test")
    print("=" * 60)
    print(f"Testing against: {BASE_URL}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test scenarios that should trigger web search
    test_queries = [
        {
            "message": "What are the latest developments in AI technology today?",
            "description": "Current AI developments query",
            "expected_web_search": True
        },
        {
            "message": "Who is the current president of France?",
            "description": "Current factual information",
            "expected_web_search": True
        },
        {
            "message": "What's happening in the news about climate change today?",
            "description": "Current news query",
            "expected_web_search": True
        },
        {
            "message": "Hello, how are you doing?",
            "description": "Casual greeting",
            "expected_web_search": False
        },
        {
            "message": "Calculate the square root of 144",
            "description": "Math calculation",
            "expected_web_search": False
        }
    ]
    
    results = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📋 Test {i}/5: {query['description']}")
        print(f"Query: '{query['message']}'")
        print(f"Expected web search: {'Yes' if query['expected_web_search'] else 'No'}")
        
        try:
            # Prepare request
            request_data = {
                "user_id": f"live_test_user_{i}",
                "message": query["message"],
                "model": "llama3.2:3b"
            }
            
            # Send request
            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/chat",
                json=request_data,
                timeout=60
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")
                
                # Analyze response for web search indicators
                web_search_indicators = [
                    "i found", "recent information", "search results", 
                    "source:", "web search", "duckduckgo", "latest", 
                    "according to", "current information"
                ]
                
                found_indicators = [
                    indicator for indicator in web_search_indicators 
                    if indicator in response_text.lower()
                ]
                
                has_web_search = len(found_indicators) > 0
                
                # Display results
                print(f"⏱️  Response time: {duration:.1f}s")
                print(f"📝 Response length: {len(response_text)} chars")
                print(f"🔍 Web search detected: {'Yes' if has_web_search else 'No'}")
                
                if found_indicators:
                    print(f"📊 Web indicators found: {found_indicators[:3]}")
                
                # Check if expectation matches result
                if has_web_search == query["expected_web_search"]:
                    print("✅ Result matches expectation")
                    test_result = "PASS"
                else:
                    print("⚠️  Result doesn't match expectation")
                    test_result = "UNEXPECTED"
                
                # Show response preview
                preview = response_text[:200] + "..." if len(response_text) > 200 else response_text
                print(f"💬 Response preview: {preview}")
                
                results.append({
                    "test": i,
                    "query": query["message"],
                    "duration": duration,
                    "has_web_search": has_web_search,
                    "expected": query["expected_web_search"],
                    "result": test_result,
                    "response_length": len(response_text)
                })
                
            else:
                print(f"❌ Request failed: {response.status_code}")
                print(f"Error: {response.text}")
                results.append({
                    "test": i,
                    "query": query["message"],
                    "result": "ERROR",
                    "error": response.status_code
                })
                
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            results.append({
                "test": i,
                "query": query["message"],
                "result": "EXCEPTION",
                "error": str(e)
            })
        
        # Brief pause between tests
        if i < len(test_queries):
            print("⏳ Waiting 3 seconds before next test...")
            time.sleep(3)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed_tests = [r for r in results if r.get("result") == "PASS"]
    unexpected_tests = [r for r in results if r.get("result") == "UNEXPECTED"]
    error_tests = [r for r in results if r.get("result") in ["ERROR", "EXCEPTION"]]
    
    print(f"✅ Passed: {len(passed_tests)}/{len(results)}")
    print(f"⚠️  Unexpected: {len(unexpected_tests)}/{len(results)}")
    print(f"❌ Errors: {len(error_tests)}/{len(results)}")
    
    if len(passed_tests) >= len(results) * 0.8:  # 80% success rate
        print("\n🎉 LIVE TEST: SUCCESS")
        print("✅ Web search integration is working correctly!")
    elif len(passed_tests) >= len(results) * 0.6:  # 60% success rate
        print("\n⚠️  LIVE TEST: PARTIAL SUCCESS")
        print("🔍 Some issues detected, but core functionality working")
    else:
        print("\n❌ LIVE TEST: NEEDS ATTENTION")
        print("🔧 Significant issues detected with web search integration")
    
    # Save detailed results
    with open("live_web_search_test_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "test_results": results,
            "summary": {
                "total_tests": len(results),
                "passed": len(passed_tests),
                "unexpected": len(unexpected_tests),
                "errors": len(error_tests),
                "success_rate": len(passed_tests) / len(results) * 100
            }
        }, f, indent=2)
    
    print(f"\n📁 Detailed results saved to: live_web_search_test_results.json")
    
    return len(passed_tests) >= len(results) * 0.8

if __name__ == "__main__":
    try:
        success = live_web_search_test()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        exit(130)
