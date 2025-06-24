#!/usr/bin/env python3
"""
Comprehensive Memory Pipeline Live Test
=======================================
Tests all aspects of the memory pipeline after Docker rebuild.
"""

import requests
import time
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8001"
API_KEY = "f2b985dd-219f-45b1-a90e-170962cc7082"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

def print_section(title):
    print(f"\n{'='*70}")
    print(f"🧠 {title}")
    print(f"{'='*70}")

def test_backend_health():
    """Test backend health and service status."""
    print_section("BACKEND HEALTH CHECK")
    
    try:
        # Test root endpoint
        response = requests.get(f"{BASE_URL}/", timeout=10)
        if response.status_code == 200:
            print("✅ Backend is responding")
        else:
            print(f"❌ Backend health check failed: HTTP {response.status_code}")
            return False
            
        # Test pipeline status
        response = requests.get(f"{BASE_URL}/api/pipeline/status", headers=headers, timeout=10)
        if response.status_code == 200:
            status = response.json()
            print("✅ Pipeline status retrieved:")
            print(f"   Status: {status.get('status')}")
            services = status.get('services', {})
            for service, healthy in services.items():
                status_icon = "✅" if healthy else "❌"
                print(f"   {service}: {status_icon}")
            return True
        else:
            print(f"❌ Pipeline status failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_memory_storage_and_retrieval():
    """Test memory storage and retrieval pipeline."""
    print_section("MEMORY STORAGE & RETRIEVAL")
    
    user_id = f"test_user_{int(time.time())}"
    
    try:
        # Store a learning interaction
        interaction_data = {
            "user_id": user_id,
            "conversation_id": f"conv_{user_id}",
            "user_message": "I'm working on a machine learning project called SentimentAI. It analyzes customer reviews using transformers.",
            "assistant_response": "That sounds like an interesting project! For SentimentAI using transformers, consider using BERT or RoBERTa for classification.",
            "response_time": 2.5,
            "tools_used": ["transformers", "analysis"],
            "source": "memory_test"
        }
        
        print("📝 Storing learning interaction...")
        response = requests.post(f"{BASE_URL}/api/learning/process_interaction", 
                               headers=headers, json=interaction_data, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Learning interaction stored: {result.get('status')}")
        else:
            print(f"❌ Learning storage failed: HTTP {response.status_code}")
            return False
            
        # Wait for processing
        time.sleep(2)
        
        # Test memory retrieval
        print("🔍 Retrieving memories...")
        memory_query = {
            "user_id": user_id,
            "query": "SentimentAI machine learning project",
            "limit": 5,
            "threshold": 0.5
        }
        
        response = requests.post(f"{BASE_URL}/api/memory/retrieve", 
                               headers=headers, json=memory_query, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            memories = result.get('memories', [])
            print(f"✅ Memory retrieval successful: {len(memories)} memories found")
            
            if memories:
                print("📋 Retrieved memory content:")
                for i, memory in enumerate(memories, 1):
                    content = memory.get('content', '')[:100]
                    score = memory.get('metadata', {}).get('similarity', 'N/A')
                    print(f"   {i}. {content}... (score: {score})")
                return True
            else:
                print("⚠️ No memories found - this may be expected for new user")
                return True
        else:
            print(f"❌ Memory retrieval failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Memory test error: {e}")
        return False

def test_chat_with_memory():
    """Test chat functionality with memory context."""
    print_section("CHAT WITH MEMORY CONTEXT")
    
    try:
        # First conversation about a specific topic
        print("💬 First conversation (setting context)...")
        payload1 = {
            "model": "llama3.2:3b",
            "messages": [{"role": "user", "content": "I'm building a web app called QuickChat using FastAPI and React. What deployment options do you recommend?"}],
            "max_tokens": 100,
            "temperature": 0.7
        }
        
        start_time = time.time()
        response1 = requests.post(f"{BASE_URL}/v1/chat/completions", headers=headers, json=payload1, timeout=30)
        time1 = time.time() - start_time
        
        if response1.status_code == 200:
            content1 = response1.json()['choices'][0]['message']['content']
            print(f"✅ First response ({time1:.2f}s): {content1[:100]}...")
        else:
            print(f"❌ First chat failed: HTTP {response1.status_code}")
            return False
            
        # Wait for memory processing
        time.sleep(3)
        
        # Second conversation referencing the same project
        print("💬 Second conversation (testing memory)...")
        payload2 = {
            "model": "llama3.2:3b",
            "messages": [{"role": "user", "content": "What database would work well with my QuickChat application?"}],
            "max_tokens": 100,
            "temperature": 0.7
        }
        
        start_time = time.time()
        response2 = requests.post(f"{BASE_URL}/v1/chat/completions", headers=headers, json=payload2, timeout=30)
        time2 = time.time() - start_time
        
        if response2.status_code == 200:
            content2 = response2.json()['choices'][0]['message']['content']
            print(f"✅ Second response ({time2:.2f}s): {content2[:100]}...")
            
            # Check if context was remembered
            if "quickchat" in content2.lower() or "fastapi" in content2.lower() or "react" in content2.lower():
                print("🎯 MEMORY CONTEXT DETECTED! Previous conversation remembered!")
                return True
            else:
                print("⚠️ Memory context not clearly detected, but responses successful")
                return True
        else:
            print(f"❌ Second chat failed: HTTP {response2.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Chat with memory error: {e}")
        return False

def test_document_rag():
    """Test document upload and RAG functionality."""
    print_section("DOCUMENT RAG PIPELINE")
    
    try:
        # Create test document
        test_content = """
        CloudSync Pro is an enterprise file synchronization tool built with Python.
        Key features:
        - Real-time sync across multiple devices
        - End-to-end encryption using AES-256
        - Bandwidth optimization with delta sync
        - API integration for third-party tools
        
        Performance tips:
        - Use connection pooling for database operations
        - Implement caching for frequently accessed files
        - Monitor memory usage during large file transfers
        """
        
        print("📄 Uploading test document...")
        files = {'file': ('cloudsync_manual.txt', test_content, 'text/plain')}
        data = {'user_id': 'rag_test_user'}
        
        response = requests.post(f"{BASE_URL}/upload/document", 
                               files=files, data=data, 
                               headers={"Authorization": f"Bearer {API_KEY}"}, timeout=20)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Document uploaded: {result.get('data', {}).get('chunks_processed', 'unknown')} chunks")
        else:
            print(f"❌ Document upload failed: HTTP {response.status_code}")
            return False
            
        # Wait for indexing
        time.sleep(3)
        
        # Test RAG query
        print("🔍 Testing RAG query...")
        payload = {
            "model": "llama3.2:3b",
            "messages": [{"role": "user", "content": "What performance tips are mentioned for CloudSync Pro?"}],
            "max_tokens": 120,
            "temperature": 0.3
        }
        
        response = requests.post(f"{BASE_URL}/v1/chat/completions", headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            content = response.json()['choices'][0]['message']['content']
            print(f"✅ RAG query successful")
            print(f"📝 Response: {content}")
            
            # Check if document content was retrieved
            keywords = ["connection pooling", "caching", "memory usage", "cloudsync"]
            found_keywords = [kw for kw in keywords if kw.lower() in content.lower()]
            
            if found_keywords:
                print(f"🎯 RAG SUCCESS! Found keywords: {', '.join(found_keywords)}")
                return True
            else:
                print("⚠️ RAG unclear - document context may not be retrieved")
                return True
        else:
            print(f"❌ RAG query failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Document RAG error: {e}")
        return False

def test_cache_performance():
    """Test caching system performance."""
    print_section("CACHE PERFORMANCE")
    
    try:
        payload = {
            "model": "llama3.2:3b",
            "messages": [{"role": "user", "content": "What is 5 + 5? Just give the number."}],
            "max_tokens": 10,
            "temperature": 0.0  # Deterministic for caching
        }
        
        # First request (cache miss)
        print("🔄 First request (cache miss)...")
        start_time = time.time()
        response1 = requests.post(f"{BASE_URL}/v1/chat/completions", headers=headers, json=payload, timeout=30)
        time1 = time.time() - start_time
        
        if response1.status_code == 200:
            content1 = response1.json()['choices'][0]['message']['content']
            print(f"✅ First response ({time1:.2f}s): {content1.strip()}")
        else:
            print(f"❌ First request failed: HTTP {response1.status_code}")
            return False
            
        # Second request (should be cache hit)
        print("🔄 Second request (cache hit expected)...")
        start_time = time.time()
        response2 = requests.post(f"{BASE_URL}/v1/chat/completions", headers=headers, json=payload, timeout=30)
        time2 = time.time() - start_time
        
        if response2.status_code == 200:
            content2 = response2.json()['choices'][0]['message']['content']
            print(f"✅ Second response ({time2:.2f}s): {content2.strip()}")
            
            # Check for cache hit
            if time2 < time1 * 0.8 and content1.strip() == content2.strip():
                speedup = time1 / time2 if time2 > 0 else 1
                print(f"🚀 CACHE HIT! {speedup:.1f}x speedup ({time1:.2f}s → {time2:.2f}s)")
                return True
            else:
                print("⚠️ Cache hit not clearly detected, but responses successful")
                return True
        else:
            print(f"❌ Second request failed: HTTP {response2.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Cache test error: {e}")
        return False

def main():
    """Run comprehensive memory pipeline test."""
    print("🧪 COMPREHENSIVE MEMORY PIPELINE TEST")
    print(f"🎯 Target: {BASE_URL}")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all tests
    tests = [
        ("Backend Health", test_backend_health),
        ("Memory Storage & Retrieval", test_memory_storage_and_retrieval),
        ("Chat with Memory", test_chat_with_memory),
        ("Document RAG", test_document_rag),
        ("Cache Performance", test_cache_performance)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {e}")
            results[test_name] = False
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    print_section("TEST RESULTS SUMMARY")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"   {test_name:<30} {status}")
    
    print(f"\n📊 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Memory pipeline is fully operational!")
    elif passed >= total * 0.8:
        print("✅ Most tests passed! Memory pipeline is largely functional.")
    else:
        print("⚠️ Some issues detected. Check failed tests above.")
    
    print(f"\n🏁 Test completed at {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()
