#!/usr/bin/env python3

"""
Direct Database Memory Test
Tests direct storage and retrieval from ChromaDB without going through the adaptive learning system
"""

import requests
import json
import time

# Configuration
BACKEND_URL = "http://localhost:8001"
API_KEY = "f2b985dd-219f-45b1-a90e-170962cc7082"
TEST_USER_ID = "direct_test_user"

def test_direct_document_storage():
    """Test storing a document directly using the document upload endpoint"""
    print("📄 Testing direct document storage...")
    
    # Create a simple test document
    test_content = f"My name is John Doe and I am a software developer. I work at TechCorp and love Python programming. This is test data for user {TEST_USER_ID}."
    
    # Store document directly
    files = {'file': ('test_memory.txt', test_content, 'text/plain')}
    data = {
        'user_id': TEST_USER_ID,
        'name': 'Test Memory Document'
    }
    
    response = requests.post(
        f"{BACKEND_URL}/upload",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=30
    )
    
    print(f"Direct storage response: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("✅ Successfully stored document directly")
        print(f"Document ID: {result.get('doc_id', 'Unknown')}")
        return True
    else:
        print(f"❌ Failed to store document: {response.text}")
        return False

def test_direct_memory_retrieval():
    """Test retrieving the stored document"""
    print("\n🔍 Testing direct memory retrieval...")
    
    # Wait a moment for indexing
    time.sleep(3)
    
    # Retrieve memories
    query_data = {
        "user_id": TEST_USER_ID,
        "query": "What is my name and job?",
        "limit": 5
    }
    
    response = requests.post(
        f"{BACKEND_URL}/api/memory/retrieve",
        json=query_data,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        timeout=15
    )
    
    print(f"Direct retrieval response: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        memories = data.get("memories", [])
        print(f"✅ Retrieved {len(memories)} memories via direct storage")
        
        for i, memory in enumerate(memories, 1):
            content = memory.get("content", "")
            similarity = memory.get("similarity", 0)
            print(f"  {i}. Similarity: {similarity:.3f}")
            print(f"     Content: {content[:150]}{'...' if len(content) > 150 else ''}")
        
        # Check if our test content is found
        found_name = any("John Doe" in m.get("content", "") for m in memories)
        found_job = any("software developer" in m.get("content", "") for m in memories)
        
        print(f"  Found name: {'✅' if found_name else '❌'}")
        print(f"  Found job: {'✅' if found_job else '❌'}")
        
        return len(memories) > 0 and (found_name or found_job)
    else:
        print(f"❌ Failed to retrieve memories: {response.text}")
        return False

def test_learning_endpoint_directly():
    """Test the learning endpoint with minimal data"""
    print("\n🧠 Testing learning endpoint directly...")
    
    # Simple learning request
    learning_data = {
        "user_id": TEST_USER_ID,
        "conversation_id": f"direct_test_{TEST_USER_ID}",
        "user_message": "My favorite color is blue and I enjoy reading science fiction books.",
        "assistant_response": "That's interesting! Blue is a great color and science fiction offers amazing possibilities to explore.",
        "response_time": 1.5,
        "tools_used": [],
        "source": "direct_test"
    }
    
    response = requests.post(
        f"{BACKEND_URL}/api/learning/process_interaction",
        json=learning_data,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        timeout=20
    )
    
    print(f"Learning endpoint response: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("✅ Learning endpoint worked")
        print(f"Result: {result}")
        return True
    else:
        print(f"❌ Learning endpoint failed: {response.text}")
        return False

def test_chromadb_health():
    """Test if ChromaDB is healthy"""
    print("🔵 Testing ChromaDB health...")
    
    try:
        # Try to reach ChromaDB directly
        response = requests.get("http://localhost:8002/api/v1/heartbeat", timeout=10)
        if response.status_code == 200:
            print("✅ ChromaDB is healthy")
            return True
        else:
            print(f"❌ ChromaDB health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ChromaDB connection error: {e}")
        return False

def main():
    """Run all direct tests"""
    print("🚀 Starting Direct Database Memory Tests")
    print("=" * 60)
    
    # Test ChromaDB health first
    if not test_chromadb_health():
        print("❌ ChromaDB is not healthy, trying to continue anyway...")
    
    # Run tests
    tests = [
        ("Direct Document Storage", test_direct_document_storage),
        ("Direct Memory Retrieval", test_direct_memory_retrieval),
        ("Learning Endpoint Direct", test_learning_endpoint_directly)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'-' * 40}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Direct Test Results Summary:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed >= 1:  # At least one test should pass
        print("🎉 At least one storage method is working!")
        return True
    else:
        print("⚠️  All tests failed. There may be a fundamental issue.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
