#!/usr/bin/env python3
"""
Test the web search function directly via OpenWebUI API
"""
import requests
import json

# Test the backend web search endpoint first
try:
    print("Testing backend /tools/web_search endpoint...")
    response = requests.post(
        'http://localhost:3000/tools/web_search',
        json={'query': 'current date time', 'max_results': 3},
        timeout=30
    )
    print(f"Backend Status: {response.status_code}")
    print(f"Backend Response: {response.text[:500]}...")
except Exception as e:
    print(f"Backend test failed: {e}")

print("\n" + "="*50 + "\n")

# Test OpenWebUI function execution (requires auth)
print("To test OpenWebUI function directly, you'll need to:")
print("1. Get your API key from User Settings > API Keys")
print("2. Run this curl command:")
print("""
curl -X POST http://localhost:8080/api/v1/functions/web_search_tool/run \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"query": "current date time", "max_results": 3}'
""")
