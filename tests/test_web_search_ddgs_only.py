import asyncio

async def _run():
    from utilities.enhanced_web_search import search_web
    result = await search_web("open source ai", max_results=1)
    assert isinstance(result, dict)
    assert 'query' in result

def test_ddgs_search_smoke():
    asyncio.run(_run())
