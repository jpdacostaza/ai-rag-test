import pytest
from fastapi.testclient import TestClient
from core.main import app


def test_version_endpoint():
    client = TestClient(app)
    r = client.get('/version')
    assert r.status_code == 200
    data = r.json()
    assert 'build' in data
    assert 'version' in data['build']
    # Added memory_provider field
    assert 'memory_provider' in data


@pytest.mark.asyncio
async def test_readiness_endpoint(monkeypatch):
    client = TestClient(app)
    r = client.get('/health/ready')
    body = r.json()
    assert 'status' in body
    assert 'memory_provider' in body  # may be None if very early
    if r.status_code == 200:
        assert body.get('ready') is True
    else:
        assert body.get('ready') is False
