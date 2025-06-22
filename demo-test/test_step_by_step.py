#!/usr/bin/env python3

import requests
import json

def test_step_by_step():
    """Test the search step by step via API to isolate the issue"""
    print("🔍 Step-by-step API test to isolate the NumPy array error...")
    
    BASE_URL = "http://localhost:8001"
    
    # Step 1: Check health
    print("\nStep 1: Check backend health...")
    try:
        health_response = requests.get(f"{BASE_URL}/health", timeout=10)
        if health_response.status_code == 200:
            health = health_response.json()
            print(f"✅ Health: {health.get('summary')}")
            print(f"   ChromaDB: {'✅' if health.get('databases', {}).get('chromadb', {}).get('available') else '❌'}")
            print(f"   Embeddings: {'✅' if health.get('databases', {}).get('embeddings', {}).get('available') else '❌'}")
        else:
            print(f"❌ Health check failed: {health_response.status_code}")
            return
    except Exception as e:
        print(f"❌ Could not connect to backend: {e}")
        return
    
    # Step 2: Upload a test document first to ensure there's data to search
    print("\nStep 2: Upload test document...")
    try:
        test_content = "This is a test document about machine learning and artificial intelligence"
        files = {'file': ('test.txt', test_content, 'text/plain')}
        data = {'user_id': 'step-test-user'}
        
        upload_response = requests.post(f"{BASE_URL}/upload/document", files=files, data=data, timeout=30)
        if upload_response.status_code == 200:
            upload_result = upload_response.json()
            print(f"✅ Upload successful: {upload_result.get('chunks_created', 0)} chunks created")
        else:
            print(f"❌ Upload failed: {upload_response.status_code} - {upload_response.text}")
            return
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return
    
    # Step 3: Wait a moment for processing
    import time
    print("\nStep 3: Waiting for document processing...")
    time.sleep(3)
    
    # Step 4: Try a search
    print("\nStep 4: Testing search (this should trigger the NumPy error)...")
    try:
        search_data = {
            "query": "machine learning",
            "user_id": "step-test-user",
            "limit": 5
        }
        
        search_response = requests.post(f"{BASE_URL}/upload/search", data=search_data, timeout=30)
        if search_response.status_code == 200:
            search_result = search_response.json()
            print(f"✅ Search completed: {search_result.get('results_count', 0)} results")
            if search_result.get('results_count', 0) > 0:
                print("🎉 SUCCESS: Found results! The NumPy error has been fixed!")
                for i, result in enumerate(search_result.get('results', [])[:2]):
                    print(f"  Result {i+1}: {result.get('content', '')[:50]}...")
                    print(f"    Similarity: {result.get('similarity', 0):.4f}")
            else:
                print("⚠️  Still getting 0 results - NumPy error may still be occurring")
        else:
            print(f"❌ Search failed: {search_response.status_code} - {search_response.text}")
    except Exception as e:
        print(f"❌ Search error: {e}")

if __name__ == "__main__":
    test_step_by_step()
