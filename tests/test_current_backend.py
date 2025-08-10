#!/usr/bin/env python3
import asyncio
import aiohttp
import json

async def test_backend():
    url = "http://localhost:3000/tools/web_search"
    data = {"query": "current time Amsterdam today"}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data) as resp:
            print(f"Status: {resp.status}")
            result = await resp.text()
            print(f"Result:\n{result}")

if __name__ == "__main__":
    asyncio.run(test_backend())
