#!/usr/bin/env python3
"""
Test with very specific non-tool questions to isolate the issue.
"""

import asyncio
import httpx

async def test_specific_questions():
    base_url = "http://localhost:8001"
    test_user_id = "specific_test"
    
    async with httpx.AsyncClient() as client:
        # First establish context
        response1 = await client.post(
            f"{base_url}/chat",
            json={"user_id": test_user_id, "message": "My favorite color is blue."},
            timeout=30.0
        )
        print(f"Context: {response1.json()}")
        
        # Try very specific recall that shouldn't match any tool
        response2 = await client.post(
            f"{base_url}/chat",
            json={"user_id": test_user_id, "message": "Can you remind me about my favorite color?"},
            timeout=30.0
        )
        print(f"Recall: {response2.json()}")

if __name__ == "__main__":
    asyncio.run(test_specific_questions())
