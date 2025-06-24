#!/usr/bin/env python3
"""
Quick test to check current backend state.
"""

import asyncio
import httpx

async def quick_test():
    base_url = "http://localhost:8001"
    
    async with httpx.AsyncClient() as client:
        # Test with a new user (no history)
        response1 = await client.post(
            f"{base_url}/chat",
            json={"user_id": "fresh_user", "message": "Hello!"},
            timeout=30.0
        )
        print(f"Fresh user: {response1.json()}")

if __name__ == "__main__":
    asyncio.run(quick_test())
