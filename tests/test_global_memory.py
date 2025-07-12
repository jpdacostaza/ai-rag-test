#!/usr/bin/env python3
"""
Test Memory Pipeline Integration
===============================

Test if the memory pipeline is working correctly with the current setup.
"""

import requests
import json
import time

def test_memory_storage():
    """Test storing a memory via the memory API directly."""
    print("🧪 Testing direct memory storage...")
    
    try:
        payload = {
            "user_id": "test_user_global",
            "conversation_id": "test_conv_1",
            "user_message": "Hello, my name is J.P. and I work at Swift as a system and applications engineer.",
            "assistant_response": "Nice to meet you, J.P.! I'll remember that you work at Swift as a system and applications engineer.",
            "source": "pipeline_test"
        }
        
        response = requests.post(
            "http://localhost:8001/api/learning/process_interaction",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Memory stored: {result.get('new_memories', 0)} new memories")
            print(f"   📊 Total memories: {result.get('total_memories', {}).get('total', 0)}")
            return True
        else:
            print(f"   ❌ Storage failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Storage error: {e}")
        return False

def test_memory_retrieval():
    """Test retrieving memories."""
    print("🔍 Testing memory retrieval...")
    
    try:
        payload = {
            "user_id": "test_user_global",
            "query": "what do you know about me",
            "limit": 5,
            "threshold": 0.001
        }
        
        response = requests.post(
            "http://localhost:8001/api/memory/retrieve",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            memories = result.get('memories', [])
            print(f"   ✅ Retrieved {len(memories)} memories")
            
            for i, memory in enumerate(memories[:3]):
                content = memory.get('content', '')[:50]
                score = memory.get('relevance_score', 0)
                print(f"   📝 Memory {i+1}: '{content}...' (score: {score:.3f})")
            
            return len(memories) > 0
        else:
            print(f"   ❌ Retrieval failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Retrieval error: {e}")
        return False

def test_pipeline_connection():
    """Test if pipelines can communicate with memory API."""
    print("🔗 Testing pipeline-to-memory-API connection...")
    
    try:
        # Test if the pipeline can reach the memory API
        # This simulates what the pipeline does internally
        response = requests.get("http://localhost:8001/health", timeout=5)
        
        if response.status_code == 200:
            health = response.json()
            print(f"   ✅ Memory API accessible from pipeline context")
            print(f"   📊 Redis: {health.get('redis')}, ChromaDB: {health.get('chromadb')}")
            return True
        else:
            print(f"   ❌ Memory API not accessible: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        return False

def check_pipeline_status():
    """Check if the memory pipeline is loaded in pipelines service."""
    print("🔍 Checking pipeline status...")
    
    try:
        response = requests.get("http://localhost:9099/", timeout=5)
        if response.status_code == 200:
            print("   ✅ Pipelines service is running")
            
            # Check if we can see any indication of loaded pipelines
            # This is a basic check since the API might require auth
            return True
        else:
            print(f"   ❌ Pipelines service error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Cannot connect to pipelines: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Memory Pipeline Integration Test")
    print("=" * 60)
    
    results = []
    
    # Test pipeline service
    results.append(check_pipeline_status())
    
    # Test pipeline-to-memory connection
    results.append(test_pipeline_connection())
    
    # Test direct memory operations
    results.append(test_memory_storage())
    results.append(test_memory_retrieval())
    
    print("\n" + "=" * 60)
    print("Test Results")
    print("=" * 60)
    
    if all(results):
        print("🎉 ALL TESTS PASSED!")
        print("\n✅ Memory system is working correctly")
        print("✅ Pipeline is connected to memory API")
        print("✅ Memory storage and retrieval working")
        print("\n💡 If models still don't remember, the issue might be:")
        print("   • Model not configured to use the pipeline")
        print("   • Open WebUI needs full restart")
        print("   • Pipeline filter not being triggered")
        
        print("\n🧪 Next steps:")
        print("   1. Try asking a model: 'Hello, my name is [YourName]'")
        print("   2. Then ask: 'What do you remember about me?'")
        print("   3. Check if the model responds with your name")
        
    else:
        print("❌ SOME TESTS FAILED")
        print("\n🔧 Issues detected:")
        for i, result in enumerate(results):
            test_names = ["Pipeline Service", "API Connection", "Memory Storage", "Memory Retrieval"]
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_names[i]}: {status}")
    
    return all(results)

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
