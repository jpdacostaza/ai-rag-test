#!/usr/bin/env python3
"""
Direct debug of the numpy array issue
"""

import requests
import time

BASE_URL = "http://localhost:8001"
API_KEY = "f2b985dd-219f-45b1-a90e-170962cc7082"

def debug_numpy_issue():
    print("🐛 Debugging the numpy array issue...")
    
    # Upload a simple document
    test_content = "Simple test for debugging numpy array comparison issue"
    
    files = {'file': ('debug_numpy.txt', test_content, 'text/plain')}
    data = {'user_id': 'numpy_debug_user'}
    
    print("📤 Uploading document...")
    upload_response = requests.post(
        f"{BASE_URL}/upload/document",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=20
    )
    
    if upload_response.status_code == 200:
        print("✅ Upload successful")
        time.sleep(2)
        
        print("🔍 Attempting search to trigger numpy error...")
        search_payload = {
            'query': 'simple test',
            'user_id': 'numpy_debug_user', 
            'limit': 1
        }
        
        search_response = requests.post(
            f"{BASE_URL}/upload/search",
            data=search_payload,
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=15
        )
        
        print(f"📊 Search response: {search_response.json()}")
        
        # Now check logs immediately
        print("\n📋 Checking backend logs for the error...")
        import subprocess
        try:
            result = subprocess.run(
                ["docker", "logs", "backend-llm-backend", "--tail", "10"],
                capture_output=True,
                text=True,
                timeout=5,
                encoding='utf-8',
                errors='ignore'  # Ignore encoding errors
            )
            
            if result.returncode == 0:
                logs = result.stdout
                print("Backend logs:")
                print(logs)
                
                if "truth value of an array" in logs:
                    print("🎯 Found the numpy array error!")
                else:
                    print("🤔 No numpy array error visible in recent logs")
            else:
                print(f"❌ Failed to get logs: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Error getting logs: {e}")
            
    else:
        print(f"❌ Upload failed: {upload_response.status_code}")

if __name__ == "__main__":
    debug_numpy_issue()
