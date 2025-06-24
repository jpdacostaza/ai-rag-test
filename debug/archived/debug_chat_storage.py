#!/usr/bin/env python3
"""
Debug script to check what's being stored in chat history and why responses might be empty.
"""

import json
import asyncio
import httpx
import time

async def debug_chat_storage():
    """Debug chat storage to understand why responses are empty."""
    
    print("=" * 60)
    print("DEBUGGING CHAT STORAGE")
    print("=" * 60)
    
    base_url = "http://localhost:8001"
    test_user_id = f"debug_user_{int(time.time())}"
    
    try:
        # Send a simple chat message
        print(f"\n1. Sending test message to user: {test_user_id}")
        
        test_message = "Hello, my name is Bob."
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/chat",
                json={"user_id": test_user_id, "message": test_message},
                timeout=30.0
            )
            
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                response_data = response.json()
                print(f"   Response: {response_data}")
                ai_response = response_data.get("response", "")
                print(f"   AI Response: '{ai_response}'")
                print(f"   AI Response Type: {type(ai_response)}")
                print(f"   AI Response Length: {len(ai_response)}")
                print(f"   AI Response is empty: {not ai_response or ai_response.strip() == ''}")
            else:
                print(f"   Error: {response.text}")
                return
        
        # Wait a moment for storage to complete
        await asyncio.sleep(2)
        
        # Check what was stored in Redis
        print(f"\n2. Checking Redis storage...")
        import subprocess
        result = subprocess.run(
            ["docker", "exec", "backend-redis", "redis-cli", "LRANGE", f"chat_history:{test_user_id}", "0", "-1"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"   Redis output: {result.stdout}")
            if result.stdout.strip():
                stored_entries = result.stdout.strip().split('\n')
                for i, entry in enumerate(stored_entries):
                    try:
                        parsed = json.loads(entry)
                        print(f"   Entry {i}: {parsed}")
                        print(f"     Message: '{parsed.get('message', '')}'")
                        print(f"     Response: '{parsed.get('response', '')}'")
                        print(f"     Response empty: {not parsed.get('response', '') or parsed.get('response', '').strip() == ''}")
                    except json.JSONDecodeError:
                        print(f"   Entry {i}: Failed to parse JSON: {entry}")
            else:
                print("   No entries found in Redis")
        else:
            print(f"   Redis check failed: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Debug failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_chat_storage())
