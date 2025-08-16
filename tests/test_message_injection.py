#!/usr/bin/env python3

import sys, os
sys.path.append('/app/backend/functions/filters')
from auto_web_search_filter import AutoWebSearchFilter
import asyncio

async def test_injection():
    # Create filter and test message injection
    filter_instance = AutoWebSearchFilter()

    # Simulate complete message flow
    test_body = {
        'messages': [
            {'role': 'user', 'content': 'search the web for current weather in Amsterdam'}
        ]
    }

    result = await filter_instance.inlet(test_body)

    print('=== FINAL MESSAGES TO MODEL ===')
    for i, msg in enumerate(result['messages']):
        print(f'Message {i+1} ({msg["role"]}):')
        content = msg['content']
        if len(content) > 500:
            print(content[:500] + '...')
        else:
            print(content)
        print('---')

if __name__ == "__main__":
    asyncio.run(test_injection())
