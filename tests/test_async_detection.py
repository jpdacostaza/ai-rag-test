#!/usr/bin/env python3
"""
Test asyncio detection in error handler
"""

import asyncio
from utilities.simple_error_handling import handle_errors

@handle_errors("test_async", default_value="ERROR")
async def test_async_function():
    print("This is an async function")
    await asyncio.sleep(0.1)
    return "SUCCESS"

@handle_errors("test_sync", default_value="ERROR")
def test_sync_function():
    print("This is a sync function")
    return "SUCCESS"

async def main():
    print("Testing async function detection...")
    
    print(f"test_async_function is coroutine: {asyncio.iscoroutinefunction(test_async_function)}")
    print(f"test_sync_function is coroutine: {asyncio.iscoroutinefunction(test_sync_function)}")
    
    # Test calling the functions
    print("Calling async function...")
    try:
        result = await test_async_function()
        print(f"Async result: {result}")
    except Exception as e:
        print(f"Async error: {e}")
        import traceback
        traceback.print_exc()
    
    print("Calling sync function...")
    try:
        result = test_sync_function()
        print(f"Sync result: {result}")
    except Exception as e:
        print(f"Sync error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
