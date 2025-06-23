#!/usr/bin/env python3
"""
Semantic Search Deep Investigation
================================
Investigates why semantic search returns 0 results despite successful document uploads.
Focuses on similarity thresholds, embedding distances, and ChromaDB query parameters.
"""

import requests
import json
import time
import numpy as np
from datetime import datetime

BASE_URL = "http://localhost:8001"
API_KEY = "f2b985dd-219f-45b1-a90e-170962cc7082"

headers = {
    "Content-Type": "application/json", 
    "Authorization": f"Bearer {API_KEY}"
}

def print_header(title):
    print(f"\n{'='*70}")
    print(f"🔍 {title}")
    print(f"{'='*70}")

def test_document_upload_and_search():
    """Test document upload and detailed search analysis."""
    print_header("SEMANTIC SEARCH DEEP DIVE")
    
    # Create test documents with varying similarity
    test_docs = [
        {
            "filename": "high_similarity.txt",
            "content": "Python data visualization with matplotlib and pandas. Use chunked processing for memory optimization.",
            "user_id": "search_test_user"
        },
        {
            "filename": "medium_similarity.txt", 
            "content": "Data analysis techniques in Python programming language. Memory management best practices.",
            "user_id": "search_test_user"
        },
        {
            "filename": "low_similarity.txt",
            "content": "Machine learning algorithms and neural network architectures for deep learning applications.",
            "user_id": "search_test_user"
        }
    ]
    
    # Test queries with different similarity levels
    test_queries = [
        "Python data visualization memory optimization",
        "matplotlib pandas chunked processing", 
        "data analysis programming",
        "neural networks deep learning",
        "completely unrelated query about cooking recipes"
    ]
    
    print("📤 Uploading test documents...")
    uploaded_docs = []
    
    for doc in test_docs:
        try:
            files = {'file': (doc['filename'], doc['content'], 'text/plain')}
            data = {'user_id': doc['user_id']}
            
            upload_response = requests.post(
                f"{BASE_URL}/upload/document",
                files=files,
                data=data,
                headers={"Authorization": f"Bearer {API_KEY}"},
                timeout=20
            )
            
            if upload_response.status_code == 200:
                result = upload_response.json()
                print(f"✅ Uploaded {doc['filename']}: {result['data']['chunks_processed']} chunks")
                uploaded_docs.append(doc)
            else:
                print(f"❌ Failed to upload {doc['filename']}: {upload_response.status_code}")
                
        except Exception as e:
            print(f"❌ Error uploading {doc['filename']}: {e}")
    
    if not uploaded_docs:
        print("❌ No documents uploaded successfully. Cannot continue test.")
        return
    
    # Wait for processing
    print("\n⏳ Waiting 5 seconds for document processing...")
    time.sleep(5)
    
    print_header("SEARCH ANALYSIS")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Query {i}: '{query}'")
        
        try:
            # Test search endpoint
            search_payload = {
                'query': query,
                'user_id': 'search_test_user',
                'limit': 5
            }
            
            search_response = requests.post(
                f"{BASE_URL}/upload/search",
                data=search_payload,
                headers={"Authorization": f"Bearer {API_KEY}"},
                timeout=15
            )
            
            if search_response.status_code == 200:
                search_results = search_response.json()
                print(f"📊 Search Results: {search_results}")
                
                if search_results.get('results_count', 0) > 0:
                    print("🎯 SUCCESS: Found relevant documents!")
                    for j, result in enumerate(search_results.get('results', []), 1):
                        print(f"   Result {j}: {result}")
                else:
                    print("⚠️ WARNING: No results found despite document uploads")
                    
            else:
                print(f"❌ Search failed: HTTP {search_response.status_code}")
                print(f"   Response: {search_response.text}")
                
        except Exception as e:
            print(f"❌ Search error: {e}")
    
    print_header("CHROMADB DIRECT INSPECTION")
    return test_chromadb_direct_access()

def test_chromadb_direct_access():
    """Test direct ChromaDB access to understand data storage."""
    try:
        # Check ChromaDB health
        chroma_response = requests.get("http://localhost:8002/api/v1/heartbeat", timeout=10)
        if chroma_response.status_code == 200:
            print("✅ ChromaDB is accessible")
        else:
            print(f"⚠️ ChromaDB health check failed: {chroma_response.status_code}")
            
        # Try to get collection info
        collections_response = requests.get("http://localhost:8002/api/v1/collections", timeout=10)
        if collections_response.status_code == 200:
            collections = collections_response.json()
            print(f"📂 Collections found: {json.dumps(collections, indent=2)}")
        else:
            print(f"⚠️ Failed to get collections: {collections_response.status_code}")
            
    except Exception as e:
        print(f"❌ ChromaDB direct access error: {e}")

def test_embedding_generation():
    """Test embedding generation directly."""
    print_header("EMBEDDING GENERATION TEST")
    
    test_texts = [
        "Python data visualization",
        "matplotlib pandas",
        "neural networks",
        "cooking recipes"
    ]
    
    for text in test_texts:
        try:
            # We can't directly access the embedding endpoint, but we can test via document upload
            # and observe the backend logs for embedding generation
            print(f"🧠 Testing embedding for: '{text}'")
            
            # Upload a tiny document to trigger embedding generation
            files = {'file': (f"test_{hash(text)}.txt", text, 'text/plain')}
            data = {'user_id': 'embedding_test_user'}
            
            upload_response = requests.post(
                f"{BASE_URL}/upload/document",
                files=files,
                data=data,
                headers={"Authorization": f"Bearer {API_KEY}"},
                timeout=15
            )
            
            if upload_response.status_code == 200:
                result = upload_response.json()
                print(f"✅ Embedding generated (via upload): {result['data']['chunks_processed']} chunks")
            else:
                print(f"❌ Embedding generation failed: {upload_response.status_code}")
                
        except Exception as e:
            print(f"❌ Embedding test error: {e}")
        
        time.sleep(1)  # Rate limiting

def analyze_backend_logs():
    """Analyze backend logs for embedding and search issues."""
    print_header("BACKEND LOG ANALYSIS")
    
    try:
        import subprocess
        result = subprocess.run(
            ["docker", "logs", "backend-llm-backend", "--tail", "50"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            logs = result.stdout
            print("📋 Recent backend logs:")
            print(logs)
            
            # Look for specific patterns
            if "embedding" in logs.lower():
                print("🧠 Found embedding-related logs")
            if "search" in logs.lower():
                print("🔍 Found search-related logs")
            if "error" in logs.lower():
                print("⚠️ Found error logs")
            if "similarity" in logs.lower():
                print("📊 Found similarity-related logs")
                
        else:
            print(f"❌ Failed to get logs: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Log analysis error: {e}")

def main():
    """Run comprehensive semantic search investigation."""
    print("🚀 Starting Semantic Search Deep Investigation")
    print(f"🎯 Target: {BASE_URL}")
    print(f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Wait for backend to be ready
    print("\n⏳ Waiting for backend to be fully ready...")
    time.sleep(10)
    
    # Check backend health
    try:
        health_response = requests.get(f"{BASE_URL}/health", timeout=10)
        if health_response.status_code == 200:
            print("✅ Backend is healthy")
        else:
            print(f"⚠️ Backend health check failed: {health_response.status_code}")
            return
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        return
    
    # Run investigations
    test_document_upload_and_search()
    test_embedding_generation()
    analyze_backend_logs()
    
    print_header("INVESTIGATION SUMMARY")
    print("📋 Check the output above for:")
    print("   🔍 Search result patterns")
    print("   🧠 Embedding generation status")
    print("   📊 ChromaDB data storage")
    print("   ⚠️ Error patterns in logs")
    print("\n💡 Next steps: Analyze similarity thresholds and query parameters")

if __name__ == "__main__":
    main()
