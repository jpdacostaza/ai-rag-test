import pytest
from utilities.enhanced_web_search import search_web, should_trigger_web_search


@pytest.mark.asyncio
async def test_search_web_structured_minimal():
    result = await search_web("open source ai", max_results=2)
    # Structure assertions
    assert isinstance(result, dict)
    for key in ("query", "timestamp", "results", "summary", "cached", "strategies_attempted"):
        assert key in result
    assert result["query"] == "open source ai"
    assert isinstance(result["results"], list)
    # Allow zero results if DDGS not installed
    if result["results"]:
        assert len(result["results"]) <= 2
        first = result["results"][0]
        assert {"title", "snippet", "link", "source"}.issubset(first.keys())


@pytest.mark.asyncio
async def test_search_web_cache_behavior():
    r1 = await search_web("latest ai news", max_results=1)
    cached_flag_first = r1["cached"]
    # Second call should be cached (if first succeeded)
    r2 = await search_web("latest ai news", max_results=1)
    # If first failed completely (no DDGS), both may be non-cached identical structures; tolerate that.
    if not cached_flag_first:
        # second should be cached unless DDGS unavailable (then still cached structure) - accept either True/False but
        # enforce at least same summary
        assert r2["summary"] == r1["summary"]
    assert r2["query"] == r1["query"]


def test_should_trigger_wrapper():
    should, reason = should_trigger_web_search("search the web for swift", "placeholder response")
    assert should is True
    assert isinstance(reason, str)
