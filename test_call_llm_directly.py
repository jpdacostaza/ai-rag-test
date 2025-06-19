#!/usr/bin/env python3
"""
Quick test to verify call_llm function works correctly
"""
import asyncio
import os
import sys

from managers.llm_manager import call_llm

# Add the current directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


async def test_call_llm():
    """Test the call_llm function directly."""
    try:
        messages = [
            {
                "role": "user",
                "content": "Hello! Say 'test successful' if you can respond.",
            }
        ]
        print("🧪 Testing call_llm function directly...")
        result = await call_llm(messages)
        print(f"✅ Success! Result type: {type(result)}")
        print(f"✅ Result content: {result}")
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"❌ Error type: {type(e)}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = asyncio.run(test_call_llm())
    if result and not str(result).startswith("<coroutine"):
        print("🎉 call_llm function works correctly!")
    else:
        print("💥 call_llm function has issues!")
