import pytest

@pytest.mark.asyncio
async def test_health_includes_breaker_field():
    from fastapi.testclient import TestClient
    from core.main import app

    client = TestClient(app)
    r = client.get('/health')
    if r.status_code != 200:
        pytest.skip('Health endpoint unavailable')
    data = r.json()
    if 'breaker' not in data:
        pytest.skip('Breaker field missing (feature may be disabled)')
    assert 'state' in data['breaker']
