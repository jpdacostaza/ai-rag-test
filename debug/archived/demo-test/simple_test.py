#!/usr/bin/env python3
"""
Simple test script to check if the memory recall is working.
This runs a basic test to see if the backend is responsive.
"""

import requests
import json
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL = "http://localhost:8000"

def quick_test():
    """Quick test to see if the backend is working."""
    
    try:
        # Test 1: Health check
        logging.info("=== Testing Backend Health ===")
        response = requests.get(f"{BASE_URL}/health/simple", timeout=5)
        
        if response.status_code == 200:
            logging.info("✅ Backend is responding!")
            result = response.json()
            logging.info(f"Backend uptime: {result.get('uptime_seconds', 0):.1f} seconds")
        else:
            logging.error(f"❌ Health check failed: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        logging.error("❌ Cannot connect to backend - is it running on port 8000?")
        return False
    except Exception as e:
        logging.error(f"❌ Health check failed: {e}")
        return False
    
    try:
        # Test 2: Simple chat test
        logging.info("=== Testing Simple Chat ===")
        chat_response = requests.post(f"{BASE_URL}/chat", json={
            "user_id": "test_user_quick",
            "message": "Hello, can you hear me?"
        }, timeout=30)
        
        if chat_response.status_code == 200:
            result = chat_response.json()
            response_text = result.get('response', '')
            if len(response_text) > 5:
                logging.info(f"✅ Chat working! Response: {response_text[:100]}...")
                return True
            else:
                logging.error(f"❌ Chat returned empty response: '{response_text}'")
                return False
        else:
            logging.error(f"❌ Chat failed: {chat_response.status_code} - {chat_response.text}")
            return False
            
    except requests.exceptions.Timeout:
        logging.error("❌ Chat request timed out - backend may be hanging")
        return False
    except Exception as e:
        logging.error(f"❌ Chat test failed: {e}")
        return False

def main():
    """Run the quick test."""
    logging.info("🚀 Running quick backend test...")
    
    if quick_test():
        logging.info("🎉 Backend is working! You can now run the full memory test.")
    else:
        logging.info("❌ Backend has issues. Check the logs above.")

if __name__ == "__main__":
    main()
