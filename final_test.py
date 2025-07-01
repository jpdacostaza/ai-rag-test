#!/usr/bin/env python3
"""Simple final test to confirm everything works"""
import requests

try:
    # Test 1: API Health
    response = requests.get("http://localhost:8001/", timeout=5)
    if response.status_code == 200:
        print("✅ API Health: WORKING")
    else:
        print(f"❌ API Health: {response.status_code}")
        exit(1)
    
    # Test 2: Remember Function
    response = requests.post(
        "http://localhost:8001/api/memory/remember",
        json={"user_id": "final_cleanup_test", "content": "Cleanup verification completed"},
        timeout=5
    )
    if response.status_code == 200:
        print("✅ Remember Function: WORKING")
    else:
        print(f"❌ Remember Function: {response.status_code}")
        exit(1)
    
    print("🎉 ALL SYSTEMS OPERATIONAL AFTER CLEANUP!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
