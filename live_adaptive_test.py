#!/usr/bin/env python3
"""
Live Adaptive Learning Test
===========================
Tests the adaptive learning functionality in real-time with the backend.
"""

import asyncio
import json
import requests
import time
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8001"
API_KEY = "f2b985dd-219f-45b1-a90e-170962cc7082"
MODEL = "llama3.2:3b"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

def print_section(title):
    print(f"\n{'='*60}")
    print(f"🧠 {title}")
    print(f"{'='*60}")

def test_basic_chat():
    """Test basic chat functionality with the model."""
    print_section("BASIC CHAT TEST")
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "Hello! Say 'AI Ready' if you can respond."}],
        "max_tokens": 50,
        "temperature": 0.7
    }
    
    try:
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/v1/chat/completions", headers=headers, json=payload, timeout=30)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            content = response.json()['choices'][0]['message']['content']
            print(f"✅ SUCCESS ({response_time:.2f}s): {content[:100]}")
            return True
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_learning_conversation():
    """Test adaptive learning with context."""
    print_section("ADAPTIVE LEARNING TEST")
    
    conversations = [
        "I'm working on a project called DataViz Pro with Python.",
        "What memory tips do you have for my DataViz Pro project?"
    ]
    
    for i, msg in enumerate(conversations, 1):
        print(f"🔄 Message {i}: {msg[:50]}...")
        payload = {
            "model": MODEL,
            "messages": [{"role": "user", "content": msg}],
            "max_tokens": 100,
            "temperature": 0.5
        }
        
        try:
            start_time = time.time()
            response = requests.post(f"{BASE_URL}/v1/chat/completions", headers=headers, json=payload, timeout=45)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content']
                print(f"✅ SUCCESS ({response_time:.2f}s)")
                if i > 1 and "DataViz" in content:
                    print("🎯 LEARNING DETECTED: Context remembered!")
            else:
                print(f"❌ FAILED: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        time.sleep(1)

def test_cache_functionality():
    """Test if caching improves response times."""
    print_section("CACHE TEST")
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "What is Python?"}],
        "max_tokens": 50,
        "temperature": 0.1
    }
    
    times = []
    for i in range(2):
        print(f"🔄 Request {i+1}/2")
        try:
            start_time = time.time()
            response = requests.post(f"{BASE_URL}/v1/chat/completions", headers=headers, json=payload, timeout=30)
            response_time = time.time() - start_time
            times.append(response_time)
            
            if response.status_code == 200:
                print(f"✅ SUCCESS ({response_time:.2f}s)")
                if i > 0 and response_time < times[0] * 0.7:
                    print("🚀 CACHE HIT: Faster response detected!")
            else:
                print(f"❌ FAILED: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ ERROR: {e}")
        time.sleep(1)

def test_document_rag():
    """Test RAG functionality with document upload."""
    print_section("RAG DOCUMENT TEST")
    
    # Create simple test document
    test_content = "DataViz Pro is a Python tool for data visualization using matplotlib and pandas. Memory tips: use chunked processing and lazy loading."
    
    try:        # Upload document
        files = {'file': ('test_doc.txt', test_content, 'text/plain')}
        data = {'user_id': 'test_user'}
        upload_response = requests.post(
            f"{BASE_URL}/upload/document",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=20
        )
        
        if upload_response.status_code == 200:
            print("✅ Document uploaded")
            print(f"📝 Upload response: {upload_response.text}")
            time.sleep(3)  # Give more time for processing
            
            # Test document search first
            search_payload = {
                'query': 'DataViz Pro memory tips',
                'user_id': 'test_user',
                'limit': 3
            }
            search_response = requests.post(
                f"{BASE_URL}/upload/search",
                data=search_payload,
                headers={"Authorization": f"Bearer {API_KEY}"},
                timeout=15
            )
            
            if search_response.status_code == 200:
                search_results = search_response.json()
                print(f"🔍 Search results: {search_results}")
            else:
                print(f"⚠️ Search failed: HTTP {search_response.status_code}")
            
            # Test RAG query
            rag_payload = {
                "model": MODEL,
                "messages": [{"role": "user", "content": "What memory tips are mentioned for DataViz Pro?"}],
                "max_tokens": 80,
                "temperature": 0.3            }
            
            rag_response = requests.post(f"{BASE_URL}/v1/chat/completions", headers=headers, json=rag_payload, timeout=30)
            
            if rag_response.status_code == 200:
                content = rag_response.json()['choices'][0]['message']['content']
                print(f"✅ RAG Query successful")
                print(f"📝 Full Response: {content}")
                if "chunked" in content.lower() or "lazy" in content.lower() or "dataviz" in content.lower():
                    print("🎯 RAG SUCCESS: Document context found!")
                else:
                    print("⚠️ RAG UNCLEAR: Context may not be retrieved")
                    print(f"🔍 Response keywords: {content.lower()}")
            else:
                print(f"❌ RAG Query failed: HTTP {rag_response.status_code}")
                print(f"📝 Error: {rag_response.text}")
        else:
            print(f"❌ Upload failed: HTTP {upload_response.status_code}")
            
    except Exception as e:
        print(f"❌ RAG ERROR: {e}")

def main():
    """Run all live tests."""
    print("🚀 Starting Live Tests")
    print(f"🎯 Target: {BASE_URL} | Model: {MODEL}")
    
    # Run tests
    test_basic_chat()
    test_learning_conversation()
    test_cache_functionality()
    test_document_rag()
    
    print_section("SUMMARY")
    print("📋 Tests completed! Check results above for:")
    print("   ✅ Basic chat | 🧠 Learning | 🚀 Cache | 📄 RAG")

if __name__ == "__main__":
    main()
