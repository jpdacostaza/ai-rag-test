#!/usr/bin/env python3
"""
Quick RAG Test
==============
Simple test to check RAG functionality.
"""

import requests
import time

BASE_URL = "http://localhost:8001"
API_KEY = "f2b985dd-219f-45b1-a90e-170962cc7082"

def quick_rag_test():
    """Quick RAG test."""
    print("🔍 Quick RAG Test")
    
    # 1. Upload document
    print("📤 Uploading document...")
    test_content = "DataViz Pro memory optimization: use chunked processing and lazy loading for better performance with large datasets."
    
    files = {'file': ('quick_test.txt', test_content, 'text/plain')}
    data = {'user_id': 'quick_test'}
    
    try:
        upload_resp = requests.post(
            f"{BASE_URL}/upload/document",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=15
        )
        print(f"Upload: {upload_resp.status_code}")
        
        if upload_resp.status_code == 200:
            print("✅ Upload successful")
            time.sleep(2)
            
            # 2. Search documents
            print("🔍 Searching...")
            search_resp = requests.post(
                f"{BASE_URL}/upload/search",
                data={'query': 'DataViz memory', 'user_id': 'quick_test', 'limit': 3},
                headers={"Authorization": f"Bearer {API_KEY}"},
                timeout=10
            )
            print(f"Search: {search_resp.status_code}")
            if search_resp.status_code == 200:
                results = search_resp.json()
                print(f"Found: {results.get('results_count', 0)} results")
                if results.get('results_count', 0) > 0:
                    print("🎯 RAG WORKING!")
                else:
                    print("⚠️ No results found")
            
        else:
            print(f"❌ Upload failed: {upload_resp.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    quick_rag_test()
