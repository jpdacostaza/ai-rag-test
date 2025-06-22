#!/usr/bin/env python3
"""
Test fresh user vs existing user comparison.
"""

import asyncio
import httpx
import time

async def test_fresh_vs_existing():
    base_url = "http://localhost:8001"
    
    async with httpx.AsyncClient() as client:
        # Test fresh user
        fresh_user = f"fresh_{int(time.time())}"
        response1 = await client.post(
            f"{base_url}/chat",
            json={"user_id": fresh_user, "message": "Hello, how are you?"},
            timeout=30.0
        )
        print(f"Fresh user first message: {response1.json()}")
        
        # Test fresh user second message (this should work)
        response2 = await client.post(
            f"{base_url}/chat",
            json={"user_id": fresh_user, "message": "Tell me a joke."},
            timeout=30.0
        )
        print(f"Fresh user second message: {response2.json()}")

if __name__ == "__main__":
    asyncio.run(test_fresh_vs_existing())
