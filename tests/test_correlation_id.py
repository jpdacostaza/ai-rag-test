from fastapi.testclient import TestClient
from core.main import app

def test_correlation_id_header_generation():
    client = TestClient(app)
    resp = client.get('/health') if client else None
    assert resp is not None
    assert resp.status_code == 200
    assert 'X-Correlation-ID' in resp.headers
    assert resp.headers['X-Correlation-ID']


def test_correlation_id_propagation():
    client = TestClient(app)
    custom_id = 'test-cid-123'
    resp = client.get('/health', headers={'X-Correlation-ID': custom_id})
    assert resp.status_code == 200
    assert resp.headers.get('X-Correlation-ID') == custom_id
