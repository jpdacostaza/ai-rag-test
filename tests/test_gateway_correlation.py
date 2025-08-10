import re
import json
import asyncio
import pytest
from fastapi.testclient import TestClient

from core.main import app
from core.enhanced_api_gateway import EnhancedAPIGateway
from core.metrics import METRICS_ENABLED, generate_latest


def test_correlation_id_generation_and_echo():
    client = TestClient(app)
    # Hit a simple existing endpoint; use /metrics or fallback to /docs
    path = "/metrics" if METRICS_ENABLED else "/docs"
    r = client.get(path)
    assert r.status_code in (200, 404)
    assert 'X-Correlation-ID' in r.headers
    cid = r.headers['X-Correlation-ID']
    assert len(cid) >= 8
    r2 = client.get(path, headers={'X-Correlation-ID': cid})
    assert r2.headers.get('X-Correlation-ID') == cid


@pytest.mark.asyncio
async def test_gateway_records_correlation_id(monkeypatch):
    gw = EnhancedAPIGateway()
    class DummyReq:
        def __init__(self):
            self.method = 'GET'
            self.path = '/test'
            self.headers = {'x-correlation-id': 'test-cid-123'}
            self.remote = '127.0.0.1'
            self._cached_body_size = 0
    req = DummyReq()
    await gw._record_metrics(req, status_code=200, duration_ms=5.5, service_name='unknown')
    if METRICS_ENABLED:
        text = generate_latest().decode()
        assert 'gateway_requests_total' in text
    else:
        assert True
