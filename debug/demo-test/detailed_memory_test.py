#!/usr/bin/env python3
"""
Detailed memory recall test to understand exactly where the issue lies.
"""

import json
import asyncio
import httpx
import time
import subprocess

async def detailed_memory_test():
    """Test memory recall step by step with detailed debugging."""
    
    print("=" * 60)
    print("DETAILED MEMORY RECALL TEST")
    print("=" * 60)
    
    base_url = "http://localhost:8001"
    test_user_id = f"memory_test_{int(time.time())}"
    
    try:
        # Step 1: Store initial context
        print(f"\n1. Storing initial context for user: {test_user_id}")
        
        first_message = "My name is Charlie and I work as a data scientist."
        response1 = await send_chat_message(base_url, test_user_id, first_message)
        print(f"   Message: {first_message}")
        print(f"   Response: {response1}")
        
        # Step 2: Check what was stored
        await asyncio.sleep(1)
        print(f"\n2. Checking stored chat history in Redis...")
        await check_redis_storage(test_user_id)
        
        # Step 3: Recall test
        print(f"\n3. Testing memory recall...")
        recall_message = "What is my name?"
        response2 = await send_chat_message(base_url, test_user_id, recall_message)
        print(f"   Recall message: {recall_message}")
        print(f"   Recall response: {response2}")
        
        # Check if name was recalled
        name_recalled = "Charlie" in response2
        print(f"   ✅ Name recalled: {name_recalled}")
        
        # Step 4: Check what was stored after recall
        await asyncio.sleep(1)
        print(f"\n4. Checking chat history after recall...")
        await check_redis_storage(test_user_id)
        
        # Step 5: Test job recall
        print(f"\n5. Testing job recall...")
        job_message = "What do I do for work?"
        response3 = await send_chat_message(base_url, test_user_id, job_message)
        print(f"   Job message: {job_message}")
        print(f"   Job response: {response3}")
        
        # Check if job was recalled
        job_recalled = "data scientist" in response3.lower()
        print(f"   ✅ Job recalled: {job_recalled}")
        
        # Step 6: Final chat history check
        await asyncio.sleep(1)
        print(f"\n6. Final chat history check...")
        await check_redis_storage(test_user_id)
        
        print(f"\n" + "=" * 60)
        print("DETAILED TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Name recall: {name_recalled}")
        print(f"✅ Job recall: {job_recalled}")
        
        if name_recalled and job_recalled:
            print("🎉 MEMORY RECALL IS WORKING!")
        else:
            print("⚠️  Memory recall needs investigation")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

async def send_chat_message(base_url: str, user_id: str, message: str) -> str:
    """Send a chat message and return the response."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/chat",
            json={"user_id": user_id, "message": message},
            timeout=30.0
        )
        if response.status_code == 200:
            return response.json()["response"]
        else:
            raise Exception(f"Chat request failed: {response.status_code} - {response.text}")

async def check_redis_storage(user_id: str):
    """Check what's stored in Redis for the user."""
    result = subprocess.run(
        ["docker", "exec", "backend-redis", "redis-cli", "LRANGE", f"chat_history:{user_id}", "0", "-1"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"   Redis entries for {user_id}:")
        if result.stdout.strip():
            entries = result.stdout.strip().split('\n')
            for i, entry in enumerate(entries):
                try:
                    parsed = json.loads(entry)
                    message = parsed.get('message', '')[:50] + "..." if len(parsed.get('message', '')) > 50 else parsed.get('message', '')
                    response = parsed.get('response', '')[:50] + "..." if len(parsed.get('response', '')) > 50 else parsed.get('response', '')
                    print(f"     Entry {i}: M:'{message}' R:'{response}'")
                except json.JSONDecodeError:
                    print(f"     Entry {i}: Failed to parse: {entry[:100]}...")
        else:
            print(f"     No entries found")
    else:
        print(f"     Redis check failed: {result.stderr}")

if __name__ == "__main__":
    asyncio.run(detailed_memory_test())
