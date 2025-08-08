#!/usr/bin/env python3
"""
Debug pipeline response format
"""

import requests
import json

def debug_pipeline_response():
    """Debug the full pipeline response to understand the format"""
    print("🐛 Debugging Pipeline Response Format")
    print("=" * 50)
    
    pipeline_url = "http://localhost:9099"
    
    test_message = {
        "user": {
            "id": "test_user",
            "name": "Test User",
            "role": "user"
        },
        "messages": [
            {
                "role": "user",
                "content": "Tell me about my Python memory system project."
            }
        ],
        "body": {
            "model": "test-model",
            "messages": [
                {
                    "role": "user",
                    "content": "Tell me about my Python memory system project."
                }
            ],
            "stream": False
        }
    }
    
    try:
        response = requests.post(
            f"{pipeline_url}/enhanced_memory_pipeline/filter/inlet",
            json=test_message,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📊 Response keys: {list(result.keys())}")
            
            print("\n📄 Full Response:")
            print(json.dumps(result, indent=2))
            
            return result
        else:
            print(f"❌ Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

if __name__ == "__main__":
    debug_pipeline_response()
