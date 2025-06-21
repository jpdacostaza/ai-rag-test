#!/usr/bin/env python3
"""
Simple RAG Investigation
========================
Directly test document upload and search functionality.
"""

import requests
import time

BASE_URL = "http://localhost:8001"
API_KEY = "f2b985dd-219f-45b1-a90e-170962cc7082"

def test_upload():
    """Test document upload."""
    print("🔍 Testing Document Upload...")
    
    # Create test document
    test_content = "DataViz Pro is a Python tool for data visualization using matplotlib and pandas. Memory tips: use chunked processing and lazy loading for better performance."
    
    # Prepare upload request
    files = {'file': ('dataviz_test.txt', test_content, 'text/plain')}
    data = {'user_id': 'test_user_rag', 'description': 'Test document for RAG'}
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    try:
        response = requests.post(
            f"{BASE_URL}/upload/document",
            files=files,
            data=data,
            headers=headers,
            timeout=30
        )
        
        print(f"📤 Upload Status: {response.status_code}")
        print(f"📝 Upload Response: {response.text}")
        
        if response.status_code == 200:
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ Upload Error: {e}")
        return False

def test_search():
    """Test document search."""
    print("\n🔍 Testing Document Search...")
    
    search_data = {
        'query': 'DataViz Pro memory tips',
        'user_id': 'test_user_rag',
        'limit': 5
    }
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    try:
        response = requests.post(
            f"{BASE_URL}/upload/search",
            data=search_data,
            headers=headers,
            timeout=20
        )
        
        print(f"🔍 Search Status: {response.status_code}")
        print(f"📝 Search Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"📊 Found {len(results)} results")
            for i, result in enumerate(results):
                print(f"   {i+1}. {result}")
            return len(results) > 0
        else:
            return False
            
    except Exception as e:
        print(f"❌ Search Error: {e}")
        return False

def test_rag_integration():
    """Test RAG integration with chat."""
    print("\n🔍 Testing RAG Integration...")
    
    # Test with a question that should use the uploaded document
    payload = {
        "model": "llama3.2:3b",
        "messages": [
            {"role": "user", "content": "Based on the uploaded documents, what are the memory optimization tips for DataViz Pro?"}
        ],
        "max_tokens": 150,
        "temperature": 0.3
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        print(f"💬 Chat Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            content = data['choices'][0]['message']['content']
            print(f"📝 Chat Response: {content}")
            
            # Check if response contains document-specific information
            keywords = ['chunked', 'lazy loading', 'dataviz', 'matplotlib', 'pandas']
            found_keywords = [kw for kw in keywords if kw.lower() in content.lower()]
            
            if found_keywords:
                print(f"✅ RAG SUCCESS: Found keywords: {found_keywords}")
                return True
            else:
                print(f"⚠️ RAG UNCLEAR: No specific keywords found")
                return False
        else:
            print(f"📝 Chat Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Chat Error: {e}")
        return False

def check_services():
    """Check if required services are running."""
    print("🔍 Checking Services...")
    
    # Check backend health
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"🎯 Backend Health: {response.status_code}")
    except Exception as e:
        print(f"❌ Backend Error: {e}")
    
    # Check ChromaDB specifically
    try:
        response = requests.get(f"{BASE_URL}/health/chromadb", timeout=10)
        print(f"🗄️ ChromaDB Health: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ ChromaDB Error: {e}")

def main():
    """Run RAG investigation."""
    print("🚀 Starting RAG Investigation")
    print("=" * 50)
    
    # Check services first
    check_services()
    
    # Test upload
    upload_success = test_upload()
    if not upload_success:
        print("❌ Upload failed, skipping other tests")
        return
    
    # Wait for processing
    print("\n⏳ Waiting for document processing...")
    time.sleep(5)
    
    # Test search
    search_success = test_search()
    
    # Test RAG integration
    rag_success = test_rag_integration()
    
    print("\n" + "=" * 50)
    print("📋 RAG Investigation Summary:")
    print(f"   📤 Upload: {'✅ SUCCESS' if upload_success else '❌ FAILED'}")
    print(f"   🔍 Search: {'✅ SUCCESS' if search_success else '❌ FAILED'}")
    print(f"   💬 RAG: {'✅ SUCCESS' if rag_success else '❌ NEEDS WORK'}")

if __name__ == "__main__":
    main()
