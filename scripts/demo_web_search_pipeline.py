import asyncio
import os, sys

# Ensure project root (directory containing 'pipelines') is on sys.path when running directly
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from pipelines.enhanced_web_search_pipeline import Pipeline

ASYNC_QUERY = "search the web for latest AI developments"


async def run_demo():
    pipe = Pipeline()
    await pipe.on_startup()

    # Simulate initial user message (inlet stage)
    body = {"messages": [{"role": "user", "content": ASYNC_QUERY}]}
    body = await pipe.inlet(body)

    # Simulate model uncertain response to trigger outlet enhancement
    body["messages"].append({
        "role": "assistant",
        "content": "I don't have the most recent info yet."  # triggers uncertainty path
    })
    body = await pipe.outlet(body)

    final_assistant = body["messages"][-1]["content"]
    user_after_inlet = body["messages"][0]["content"]
    print("===== USER MESSAGE AFTER INLET (TRUNCATED) =====")
    print(user_after_inlet[:600])
    print("\n===== ASSISTANT MESSAGE AFTER OUTLET =====")
    print(final_assistant[:600])
    any_block = any("Current Web Search Results" in m["content"] or "WEB SEARCH RESULTS" in m["content"] for m in body["messages"])
    print("\nContains search results block anywhere:", any_block)
    await pipe.on_shutdown()


if __name__ == "__main__":
    asyncio.run(run_demo())
