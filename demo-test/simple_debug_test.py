#!/usr/bin/env python3
"""
Simple test to trigger debug logging for memory recall.
"""

import asyncio
import httpx
import time

async def simple_debug_test():
    """Send a simple recall test to see debug logs."""
    
    base_url = "http://localhost:8001"
    test_user_id = f"debug_{int(time.time())}"
    
    # First message
    print("Sending first message...")
    async with httpx.AsyncClient() as client:
        response1 = await client.post(
            f"{base_url}/chat",
            json={"user_id": test_user_id, "message": "My name is David."},
            timeout=30.0
        )
        print(f"Response 1: {response1.json()}")
    
    # Wait and send recall
    await asyncio.sleep(2)
    print("Sending recall message...")
    async with httpx.AsyncClient() as client:
        response2 = await client.post(
            f"{base_url}/chat",
            json={"user_id": test_user_id, "message": "What is my name?"},
            timeout=30.0
        )
        print(f"Response 2: {response2.json()}")

if __name__ == "__main__":
    asyncio.run(simple_debug_test())
