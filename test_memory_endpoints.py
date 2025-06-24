#!/usr/bin/env python3
"""
Quick test script to verify backend memory endpoints are working
Run this before installing the OpenWebUI pipeline to ensure connectivity
"""

import requests
import json
import time

# Configuration
BACKEND_URL = "http://localhost:8001"
API_KEY = "f2b985dd-219f-45b1-a90e-170962cc7082"
TEST_USER_ID = "test_user_pipeline"
TEST_CHAT_ID = "test_chat_pipeline"

def test_health():
    """Test backend health endpoint"""
    print("🏥 Testing backend health...")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is healthy")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend connection failed: {str(e)}")
        return False

def test_memory_storage():
    """Test storing interaction for learning"""
    print("\n🧠 Testing memory storage...")
    try:
        interaction_data = {
            "user_id": TEST_USER_ID,
            "conversation_id": TEST_CHAT_ID,
            "user_message": "My favorite programming language is Python and I work as a software engineer",
            "context": {
                "message_count": 1,
                "pipeline": "test_pipeline"
            }
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/learning/process_interaction",
            json=interaction_data,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            print("✅ Memory storage successful")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Memory storage failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Memory storage error: {str(e)}")
        return False

def test_memory_retrieval():
    """Test retrieving memories"""
    print("\n🔍 Testing memory retrieval...")
    try:
        query_data = {
            "user_id": TEST_USER_ID,
            "query": "What programming language do I like?",
            "limit": 3
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/memory/retrieve",
            json=query_data,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            memory_data = response.json()
            memories = memory_data.get("memories", [])
            print(f"✅ Memory retrieval successful")
            print(f"   Retrieved {len(memories)} memories")
            
            if memories:
                print("   Sample memory:")
                for i, memory in enumerate(memories[:1], 1):
                    content = memory.get("content", "")[:100] + "..." if len(memory.get("content", "")) > 100 else memory.get("content", "")
                    print(f"   {i}. {content}")
            return True
        else:
            print(f"❌ Memory retrieval failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Memory retrieval error: {str(e)}")
        return False

def test_pipeline_endpoints():
    """Test pipeline-specific endpoints"""
    print("\n🔧 Testing pipeline endpoints...")
    try:
        # Test pipeline list
        response = requests.get(f"{BACKEND_URL}/pipelines", timeout=5)
        if response.status_code == 200:
            pipelines = response.json().get("data", [])
            print(f"✅ Pipeline list endpoint working ({len(pipelines)} pipelines)")
        else:
            print(f"❌ Pipeline list failed: {response.status_code}")
            
        # Test specific pipeline
        response = requests.get(f"{BACKEND_URL}/pipelines/memory_pipeline", timeout=5)
        if response.status_code == 200:
            pipeline = response.json()
            print(f"✅ Memory pipeline endpoint working: {pipeline.get('name', 'Unknown')}")
            return True
        else:
            print(f"❌ Memory pipeline endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Pipeline endpoint error: {str(e)}")
        return False

def run_full_test():
    """Run complete test suite"""
    print("🧪 BACKEND MEMORY SYSTEM TEST")
    print("=" * 50)
    
    # Run tests
    health_ok = test_health()
    pipeline_ok = test_pipeline_endpoints()
    storage_ok = test_memory_storage()
    
    # Wait a moment for storage to complete
    time.sleep(2)
    
    retrieval_ok = test_memory_retrieval()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY:")
    print(f"   Backend Health: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"   Pipeline Endpoints: {'✅ PASS' if pipeline_ok else '❌ FAIL'}")
    print(f"   Memory Storage: {'✅ PASS' if storage_ok else '❌ FAIL'}")
    print(f"   Memory Retrieval: {'✅ PASS' if retrieval_ok else '❌ FAIL'}")
    
    all_passed = all([health_ok, pipeline_ok, storage_ok, retrieval_ok])
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Backend is ready for OpenWebUI pipeline integration")
        print("\n📋 NEXT STEPS:")
        print("1. Copy the pipeline code from openwebui_memory_pipeline.py")
        print("2. Install it in OpenWebUI Settings → Functions → Pipelines")
        print("3. Configure the valves with the correct backend URL and API key")
        print("4. Enable the pipeline and test memory functionality")
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("🔧 Please fix the backend issues before installing the OpenWebUI pipeline")
        print("\n🚨 TROUBLESHOOTING:")
        print("- Check if all Docker containers are running: docker ps")
        print("- Check backend logs: docker logs backend-llm-backend --tail 20")
        print("- Verify backend is accessible: curl http://localhost:8001/health")
        
    return all_passed

if __name__ == "__main__":
    run_full_test()
