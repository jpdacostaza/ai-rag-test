import re
from fastapi.testclient import TestClient
from core.main import app
from core.metrics import METRICS_ENABLED

def test_gateway_latency_histogram_presence():
    client = TestClient(app)
    for _ in range(3):
        client.get('/metrics')  # hit endpoint to record latency
    r = client.get('/metrics')
    if not METRICS_ENABLED or r.text.strip() == 'metrics_disabled':
        return
    # Look for histogram sum or bucket line
    assert 'gateway_request_latency_seconds' in r.text
