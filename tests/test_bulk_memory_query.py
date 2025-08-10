import pytest
from fastapi.testclient import TestClient
from core.main import app

@pytest.mark.asyncio
async def test_bulk_memory_query_empty(monkeypatch):
    client = TestClient(app)
    # Minimal request; underlying db_manager may not return matches in test context
    payload = {"user_id": "user123", "queries": ["alpha", "beta"], "limit": 3}
    r = client.post('/api/memory/bulk_query', json=payload)
    assert r.status_code in (200, 503)  # 503 if db manager unavailable early
    if r.status_code == 200:
        data = r.json()
        assert data.get('success') is True
        assert data.get('query_count') == 2
        assert 'results' in data
        assert set(data['results'].keys()) == {"alpha", "beta"}

@pytest.mark.asyncio
async def test_bulk_memory_query_validation(monkeypatch):
    client = TestClient(app)
    # Missing user_id
    payload = {"queries": ["only"], "limit": 2}
    r = client.post('/api/memory/bulk_query', json=payload)
    # Should fail validation at FastAPI/Pydantic layer (422)
    assert r.status_code in (400, 422)
