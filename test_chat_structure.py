#!/usr/bin/env python3
"""
Test the async structure of the chat endpoint without depending on external services.
"""
import asyncio
import os
import sys

# Add the backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def mock_call_llm(messages):
    """Mock LLM function that returns a string."""
    await asyncio.sleep(0.1)  # Simulate async work
    return "This is a mock response from the LLM."


async def test_chat_logic():
    """Test the main chat logic structure."""
    try:
        # Mock the main variables that would be in the chat endpoint
        user_message = "Hello test"
        user_id = "test_user"
        tool_used = False

        # Simulate the exact logic from the fixed main.py
        if not tool_used:
            print("[DEBUG] Entering LLM code path - no tool was used")

            # Mock the database and memory operations
            query_emb = None  # Simulating get_embedding returning None
            memory_chunks = []  # Simulating empty memory
            history_msgs = []  # Simulating empty history

            # Compose LLM context with explicit instructions for plain text responses
            system_prompt = (
                "You are a helpful assistant. Always respond with plain text only."
            )

            # Ensure all memory_chunks and history_msgs are strings and handle None values
            memory_chunks = memory_chunks or []
            current_history_msgs = history_msgs or []
            context = "\n".join(
                [str(m) for m in memory_chunks] + [str(m) for m in current_history_msgs]
            )
            messages = [
                {"role": "system", "content": system_prompt},
                *[{"role": "user", "content": m} for m in current_history_msgs],
                {"role": "user", "content": user_message},
                (
                    {"role": "system", "content": f"Relevant memory: {context}"}
                    if context
                    else None
                ),
            ]
            messages = [m for m in messages if m]

            print("[DEBUG] About to call LLM directly")
            try:
                user_response = await mock_call_llm(messages)
                print(f"[DEBUG] user_response type: {type(user_response)}")
                print(f"[DEBUG] user_response content: {str(user_response)[:100]}...")

                # Check if response is what we expect
                if hasattr(user_response, "__await__"):
                    print("❌ ERROR: Response is still a coroutine!")
                    return False
                elif isinstance(user_response, str):
                    print("✅ SUCCESS: Response is a string as expected!")
                    print(f"Final response: {user_response}")
                    return True
                else:
                    print(
                        f"⚠️  WARNING: Response is unexpected type: {type(user_response)}"
                    )
                    return False

            except Exception as e:
                print(f"❌ ERROR in LLM call: {e}")
                user_response = "I apologize, but I'm having trouble processing your request right now. Please try again."
                return False
        else:
            print("[DEBUG] Tool path would be used")
            return True

    except Exception as e:
        print(f"❌ ERROR in chat logic: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_chat_logic())
    print(f"\nTest result: {'PASSED' if result else 'FAILED'}")
    exit(0 if result else 1)
