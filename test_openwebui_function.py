import asyncio
import aiohttp
import json

async def test_openwebui_function_call():
    """Test if OpenWebUI can call our Action directly"""
    url = "http://localhost:8080/api/v1/functions/id/web_search_tool/run"
    headers = {"Content-Type": "application/json"}
    data = {
        "query": "current date time today",
        "max_results": 3
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as resp:
                print(f"Status: {resp.status}")
                result = await resp.text()
                print(f"Response:\n{result}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_openwebui_function_call())
