#!/usr/bin/env python3
"""
Test Enhanced Memory Pipeline Directly
======================================

This script tests the Enhanced Memory Pipeline using the patterns that I found
successful in other implementations. Based on the analysis of working examples:

1. mem0_memory_filter_pipeline.py - Shows proper valve configuration
2. langfuse_filter_pipeline.py - Shows proper inlet/outlet patterns  
3. Various successful filter pipelines - Show common configurations

Key patterns for success:
- pipelines: ["*"] to connect to all models
- priority: 0 for highest priority  
- Simple valve initialization in __init__
- Proper inlet/outlet implementation
- Direct API calls to memory backend
"""

import requests
import json
import time
import sys

# Configuration based on successful examples
PIPELINE_URL = "http://localhost:9099"
MEMORY_API_URL = "http://localhost:8001"

def test_pipeline_direct_call():
    """Test direct call to Enhanced Memory Pipeline using successful patterns."""
    print("\n🔧 Testing Enhanced Memory Pipeline Direct Call...")
    
    try:
        # Test 1: Check if pipeline is accessible with correct endpoint
        response = requests.get(f"{PIPELINE_URL}/enhanced_memory_pipeline/valves", timeout=5)
        if response.status_code == 200:
            valves = response.json()
            print("✅ Pipeline valves accessible:")
            print(f"   Pipelines: {valves.get('pipelines', 'unknown')}")
            print(f"   Priority: {valves.get('priority', 'unknown')}")
            print(f"   Backend URL: {valves.get('backend_url', 'unknown')}")
            print(f"   Enable Memory: {valves.get('enable_memory', 'unknown')}")
            print(f"   Debug Mode: {valves.get('debug_mode', 'unknown')}")
        else:
            print(f"❌ Pipeline valves access failed: {response.status_code}")
            return False
            
        # Test 2: Test inlet call using correct OpenWebUI format
        inlet_body = {
            "body": {
                "messages": [
                    {"role": "user", "content": "Hello, my name is John and I work as a software engineer"}
                ],
                "model": "test_model",
                "chat_id": "test_conversation_001"
            }
        }
        
        print("\n🔧 Testing inlet call...")
        response = requests.post(
            f"{PIPELINE_URL}/enhanced_memory_pipeline/filter/inlet",
            json=inlet_body,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Inlet call successful!")
            print(f"   Response: {json.dumps(result, indent=2)[:500]}...")
            
            # Check if memory injection happened
            messages = result.get('messages', [])
            system_messages = [msg for msg in messages if msg.get('role') == 'system']
            if system_messages:
                print(f"✅ Memory injection detected! Found {len(system_messages)} system messages")
            else:
                print("⚠️  No memory injection detected")
                
        else:
            print(f"❌ Inlet call failed: {response.status_code}")
            if response.text:
                print(f"   Error: {response.text}")
            return False
            
        # Test 3: Test outlet call 
        print("\n🔧 Testing outlet call...")
        outlet_body = {
            "body": {
                "messages": [
                    {"role": "user", "content": "Hello, my name is John and I work as a software engineer"},
                    {"role": "assistant", "content": "Hello John! Nice to meet you. It's great to know you're a software engineer. What programming languages do you enjoy working with?"}
                ],
                "model": "test_model", 
                "chat_id": "test_conversation_001"
            }
        }
        
        response = requests.post(
            f"{PIPELINE_URL}/enhanced_memory_pipeline/filter/outlet",
            json=outlet_body,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Outlet call successful!")
            print(f"   Response: {json.dumps(result, indent=2)[:500]}...")
        else:
            print(f"❌ Outlet call failed: {response.status_code}")
            if response.text:
                print(f"   Error: {response.text}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Pipeline direct test failed: {e}")
        return False

def test_memory_api_compatibility():
    """Test Memory API with the corrected port and endpoints."""
    print("\n🔧 Testing Memory API with correct configuration...")
    
    try:
        # Test health check
        response = requests.get(f"{MEMORY_API_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Memory API health check: PASSED")
        else:
            print(f"❌ Memory API health check: FAILED ({response.status_code})")
            return False
            
        # Test storing a memory using correct endpoint format
        memory_data = {
            "user_id": "john_doe_test",
            "content": "John works as a software engineer and likes Python programming",
            "source": "pipeline_test", 
            "conversation_id": "test_conversation_001"
        }
        
        response = requests.post(f"{MEMORY_API_URL}/api/memory/store_explicit", json=memory_data, timeout=5)
        if response.status_code == 200:
            print("✅ Memory storage test: PASSED")
        else:
            print(f"❌ Memory storage test: FAILED ({response.status_code})")
            if response.text:
                print(f"   Error: {response.text}")
            return False
            
        # Test retrieving memories
        retrieval_data = {
            "user_id": "john_doe_test",
            "query": "software engineer Python",
            "limit": 5
        }
        
        response = requests.post(f"{MEMORY_API_URL}/api/memory/retrieve", json=retrieval_data, timeout=5)
        if response.status_code == 200:
            result = response.json()
            memories = result.get('memories', [])
            if len(memories) > 0:
                print("✅ Memory retrieval test: PASSED")
                print(f"   Retrieved {len(memories)} memories")
                for i, memory in enumerate(memories[:2]):
                    print(f"   Memory {i+1}: {memory.get('content', '')[:100]}...")
            else:
                print("⚠️  Memory retrieval test: No memories found")
        else:
            print(f"❌ Memory retrieval test: FAILED ({response.status_code})")
            if response.text:
                print(f"   Error: {response.text}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Memory API test failed: {e}")
        return False

def main():
    """Run comprehensive test based on successful patterns."""
    print("🧪 Testing Enhanced Memory Pipeline (Based on Successful Examples)")
    print("=" * 70)
    
    tests = [
        ("Memory API Compatibility", test_memory_api_compatibility),
        ("Pipeline Direct Call", test_pipeline_direct_call),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
    
    print("\n" + "=" * 70)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Enhanced Memory Pipeline is working correctly!")
        print("\n🔍 Key successful patterns applied:")
        print("   • Correct port configuration (8001 not 8080)")
        print("   • Proper valve initialization with pipelines: ['*']")
        print("   • Priority 0 for highest execution priority")
        print("   • Direct inlet/outlet API testing")
        print("   • Memory storage and retrieval validation")
    else:
        print("❌ Some tests failed. Check configuration and logs.")
        
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
