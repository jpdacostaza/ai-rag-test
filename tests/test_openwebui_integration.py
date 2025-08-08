#!/usr/bin/env python3
"""
Test OpenWebUI Memory Function Integration
=========================================

This script tests the integration between OpenWebUI and our memory system
to ensure the function loading and API communication work correctly.
"""

import asyncio
import json
import requests
import time
from typing import Dict, Any

# Test configuration
OPENWEBUI_URL = "http://localhost:8080"
MEMORY_API_URL = "http://localhost:5001"
TEST_USER_ID = "openwebui_integration_test"
TEST_SESSION_ID = "test_session_1"

def test_memory_api_direct():
    """Test memory API directly"""
    print("🔍 Testing Memory API Direct Access...")
    
    # Test storage
    store_payload = {
        "user_id": TEST_USER_ID,
        "content": "I am testing the OpenWebUI memory integration system",
        "context": "integration_test"
    }
    
    try:
        response = requests.post(
            f"{MEMORY_API_URL}/api/memory/store",
            json=store_payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Memory stored successfully: {result['memory_id']}")
            return result['memory_id']
        else:
            print(f"❌ Memory storage failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Memory API connection failed: {e}")
        return None

def test_memory_retrieval(memory_id):
    """Test memory retrieval"""
    print("🔍 Testing Memory Retrieval...")
    
    retrieve_payload = {
        "user_id": TEST_USER_ID,
        "query": "OpenWebUI integration",
        "limit": 5
    }
    
    try:
        response = requests.post(
            f"{MEMORY_API_URL}/api/memory/retrieve",
            json=retrieve_payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            memories = result.get('memories', [])
            
            if memories:
                print(f"✅ Retrieved {len(memories)} memories")
                for i, memory in enumerate(memories):
                    print(f"   Memory {i+1}: {memory['content'][:50]}...")
                return True
            else:
                print("❌ No memories retrieved")
                return False
        else:
            print(f"❌ Memory retrieval failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Memory retrieval failed: {e}")
        return False

def test_openwebui_function_loading():
    """Test if OpenWebUI has loaded our function"""
    print("🔍 Testing OpenWebUI Function Loading...")
    
    try:
        # Check if OpenWebUI is accessible
        response = requests.get(f"{OPENWEBUI_URL}/api/v1/functions", timeout=10)
        
        if response.status_code == 200:
            functions = response.json()
            print(f"✅ OpenWebUI API accessible, found {len(functions)} functions")
            
            # Look for our memory function
            memory_functions = [f for f in functions if 'memory' in f.get('id', '').lower()]
            
            if memory_functions:
                print(f"✅ Found {len(memory_functions)} memory-related functions")
                for func in memory_functions:
                    print(f"   Function: {func.get('id', 'unknown')}")
                return True
            else:
                print("⚠️  No memory functions found in OpenWebUI")
                return False
        else:
            print(f"❌ OpenWebUI API not accessible: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ OpenWebUI connection failed: {e}")
        return False

def test_openwebui_health():
    """Test OpenWebUI health"""
    print("🔍 Testing OpenWebUI Health...")
    
    try:
        response = requests.get(f"{OPENWEBUI_URL}/api/v1/auths", timeout=10)
        
        if response.status_code in [200, 401]:  # 401 is expected if not authenticated
            print("✅ OpenWebUI is running and accessible")
            return True
        else:
            print(f"❌ OpenWebUI health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ OpenWebUI health check failed: {e}")
        return False

def main():
    """Main test execution"""
    print("🚀 Starting OpenWebUI Memory Integration Tests")
    print("=" * 60)
    
    # Test results
    results = {}
    
    # Test 1: Memory API Direct Access
    print("\n📋 Test 1: Memory API Direct Access")
    memory_id = test_memory_api_direct()
    results['memory_api_store'] = memory_id is not None
    
    # Test 2: Memory Retrieval
    if memory_id:
        print("\n📋 Test 2: Memory Retrieval")
        results['memory_api_retrieve'] = test_memory_retrieval(memory_id)
    else:
        results['memory_api_retrieve'] = False
    
    # Test 3: OpenWebUI Health
    print("\n📋 Test 3: OpenWebUI Health Check")
    results['openwebui_health'] = test_openwebui_health()
    
    # Test 4: OpenWebUI Function Loading
    print("\n📋 Test 4: OpenWebUI Function Loading")
    results['openwebui_functions'] = test_openwebui_function_loading()
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 Integration Test Summary")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASSED" if passed_test else "❌ FAILED"
        print(f"{test_name:<25}: {status}")
    
    print(f"\nOverall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        print("\n✅ Your memory system is ready for OpenWebUI!")
        print("✅ You can now test the memory function through the OpenWebUI interface")
        print("✅ The system should remember previous conversations and context")
    else:
        print("⚠️  Some integration tests failed")
        print("🔧 Please check the failed components and ensure all services are running")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
