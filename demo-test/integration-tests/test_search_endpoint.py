#!/usr/bin/env python3

import requests
import json

def test_search_endpoint():
    """Test the search endpoint to trigger the numpy error."""
    
    url = "http://localhost:8001/upload/search"
    data = {
        "query": "test numpy array", 
        "user_id": "test-user",
        "limit": 5
    }
    
    print(f"Testing search endpoint with form data: {data}")
    
    try:
        response = requests.post(url, data=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"Results: {len(response_data.get('results', []))} documents found")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_search_endpoint()
