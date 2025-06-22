#!/usr/bin/env python3
"""
Quick test to verify the NumPy array fix for ChromaDB search
"""

import requests
import time

BASE_URL = "http://localhost:8001"
API_KEY = "f2b985dd-219f-45b1-a90e-170962cc7082"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

def test_search_fix():
    print("🧪 Testing ChromaDB search after NumPy fix...")
    
    # Wait for backend to be ready
    time.sleep(15)
    
    # Upload a test document
    test_content = "Test document for ChromaDB using Qwen3-Embedding-0.6B model. This contains important information about data processing."
    
    try:
        # Upload document
        files = {'file': ('test_search_fix.txt', test_content, 'text/plain')}
        data = {'user_id': 'test_search_user'}
        upload_response = requests.post(
            f"{BASE_URL}/upload/document",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=20
        )
        
        if upload_response.status_code == 200:
            print("✅ Document uploaded successfully")
            time.sleep(3)  # Wait for processing
            
            # Test search
            search_payload = {
                'query': 'data processing information',
                'user_id': 'test_search_user',
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
                
                if search_results and len(search_results) > 0:
                    print("🎯 SUCCESS: Search returned results! NumPy fix worked!")
                    return True
                else:
                    print("⚠️ Search returned no results")
                    return False
            else:
                print(f"❌ Search failed: HTTP {search_response.status_code}")
                print(f"Response: {search_response.text}")
                return False
        else:
            print(f"❌ Upload failed: HTTP {upload_response.status_code}")
            print(f"Response: {upload_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    test_search_fix()
