#!/usr/bin/env python3
"""
Direct test of the fixed LLM call to check if coroutine issue is resolved.
"""
import asyncio
import os
import sys

# Add the backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_llm_call():
    """Test the LLM call directly without the web server."""
    try:
        from managers.llm_manager import call_llm

        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": "Say hello and tell me your purpose in one sentence.",
            },
        ]

        print("Testing LLM call...")
        response = await call_llm(messages)

        print(f"Response type: {type(response)}")
        print(f"Response content: {response}")

        # Check if response is a coroutine (which would be the bug)
        if hasattr(response, "__await__"):
            print("❌ ERROR: Response is still a coroutine!")
            return False
        elif isinstance(response, str):
            print("✅ SUCCESS: Response is a string as expected!")
            return True
        else:
            print(f"⚠️  WARNING: Response is unexpected type: {type(response)}")
            return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_llm_call())
    exit(0 if result else 1)
