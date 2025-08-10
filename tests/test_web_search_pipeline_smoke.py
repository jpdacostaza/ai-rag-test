import asyncio
import pytest

from pipelines.enhanced_web_search_pipeline import Pipeline


@pytest.mark.asyncio
async def test_inlet_explicit_search_injects_block():
    pipe = Pipeline()
    await pipe.on_startup()
    body = {"messages": [{"role": "user", "content": "search the web for latest AI developments"}]}
    body = await pipe.inlet(body)
    user_msg = body["messages"][0]["content"].lower()
    # Accept any of the possible search result markers
    assert ("web search results" in user_msg or "web search status" in user_msg or "web search unavailable" in user_msg)
    await pipe.on_shutdown()


@pytest.mark.asyncio
async def test_outlet_uncertainty_triggers_search_when_not_already_done():
    pipe = Pipeline()
    await pipe.on_startup()
    # User message that should NOT explicitly trigger search (no explicit keyword, no context word)
    body = {"messages": [{"role": "user", "content": "Tell me about AI breakthroughs"}]}
    body = await pipe.inlet(body)
    user_msg_after_inlet = body["messages"][0]["content"].lower()
    # Should not yet have injected results
    assert "web search results" not in user_msg_after_inlet

    # Add uncertain assistant reply
    body["messages"].append({"role": "assistant", "content": "I don't have the most recent info yet."})
    body = await pipe.outlet(body)
    assistant_msg = body["messages"][-1]["content"].lower()
    assert ("current information update" in assistant_msg and (
        "web search results" in assistant_msg or "web search status" in assistant_msg or "web search unavailable" in assistant_msg
    ))
    await pipe.on_shutdown()
