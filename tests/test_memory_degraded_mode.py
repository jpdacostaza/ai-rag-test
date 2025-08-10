import pytest

@pytest.mark.asyncio
async def test_memory_service_initializes_without_backends(monkeypatch):
    # Simulate missing Redis/Chroma imports by forcing services to raise
    monkeypatch.setenv('DISABLE_EMBEDDINGS', 'true')
    # Force database manager attributes to None if accessed
    try:
        import services.database_manager as dm
        monkeypatch.setattr(dm, 'db_manager', None, raising=False)
    except Exception:
        pass
    from core.main import get_memory_service_or_legacy
    svc = get_memory_service_or_legacy()
    # Service may be None (legacy fallback) but call should not crash
    # MemoryService exposes get_memories (plural)
    assert svc is None or hasattr(svc, 'get_memories')
