#!/usr/bin/env python3
"""
Test if LLM works for non-recall questions.
"""

import asyncio
import httpx

async def test_non_recall():
    base_url = "http://localhost:8001"
    test_user_id = "non_recall_test"
    
    async with httpx.AsyncClient() as client:
        # First establish context
        response1 = await client.post(
            f"{base_url}/chat",
            json={"user_id": test_user_id, "message": "My name is Emily."},
            timeout=30.0
        )
        print(f"Context: {response1.json()}")
        
        # Try non-recall question
        response2 = await client.post(
            f"{base_url}/chat",
            json={"user_id": test_user_id, "message": "What is 2+2?"},
            timeout=30.0
        )
        print(f"Math: {response2.json()}")
        
        # Try different non-recall question
        response3 = await client.post(
            f"{base_url}/chat",
            json={"user_id": test_user_id, "message": "Tell me a joke."},
            timeout=30.0
        )
        print(f"Joke: {response3.json()}")

if __name__ == "__main__":
    asyncio.run(test_non_recall())
