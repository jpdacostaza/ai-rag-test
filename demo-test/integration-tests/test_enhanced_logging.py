#!/usr/bin/env python3
"""
Test search with enhanced logging to debug the 0 results issue
"""

import requests
import time

BASE_URL = "http://localhost:8001"
API_KEY = "f2b985dd-219f-45b1-a90e-170962cc7082"

def test_search_with_logging():
    print("🔍 Testing search with enhanced memory logging...")
    
    # Wait for backend to restart
    time.sleep(15)
    
    # Upload a test document
    print("📤 Uploading test document...")
    test_content = "Python machine learning with scikit-learn and pandas for data analysis"
    
    files = {'file': ('ml_test.txt', test_content, 'text/plain')}
    data = {'user_id': 'debug_user'}
    
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
        print("🔍 Testing search...")
        search_payload = {
            'query': 'machine learning data analysis',
            'user_id': 'debug_user',
            'limit': 3
        }
        
        search_response = requests.post(
            f"{BASE_URL}/upload/search",
            data=search_payload,
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=15
        )
        
        if search_response.status_code == 200:
            results = search_response.json()
            print(f"📊 Search results: {results}")
        else:
            print(f"❌ Search failed: {search_response.status_code}")
            
    else:
        print(f"❌ Upload failed: {upload_response.status_code}")

if __name__ == "__main__":
    test_search_with_logging()
